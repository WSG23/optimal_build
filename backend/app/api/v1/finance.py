"""Finance feasibility API endpoints."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterator, Mapping
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from time import perf_counter
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import require_reviewer, require_viewer
from app.core.database import get_session
from app.models.finance import FinCapitalStack, FinProject, FinResult, FinScenario
from app.models.rkp import RefCostIndex
from app.schemas.finance import (
    CapitalStackSliceSchema,
    CapitalStackSummarySchema,
    CostIndexProvenance,
    CostIndexSnapshot,
    DscrEntrySchema,
    FinanceFeasibilityRequest,
    FinanceFeasibilityResponse,
    FinanceResultSchema,
    FinancingDrawdownEntrySchema,
    FinancingDrawdownScheduleSchema,
)
from app.services.finance import calculator
from app.utils import metrics
from app.utils.logging import get_logger, log_event

router = APIRouter(prefix="/finance", tags=["finance"])
logger = get_logger(__name__)


def _normalise_project_id(project_id: str | int | UUID) -> UUID:
    """Convert the externally supplied project identifier into a UUID."""

    if isinstance(project_id, UUID):
        return project_id
    if isinstance(project_id, int):
        if project_id < 0:
            raise HTTPException(
                status_code=422, detail="project_id must be non-negative"
            )
        return UUID(int=project_id)
    try:
        return UUID(project_id)
    except (AttributeError, TypeError, ValueError) as e:
        raise HTTPException(
            status_code=422, detail="project_id must be a valid UUID"
        ) from e


def _decimal_from_value(value: object) -> Decimal:
    """Safely convert arbitrary numeric inputs into :class:`Decimal`."""

    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _json_safe(value: Any) -> Any:
    """Convert nested data into JSON-serialisable Python primitives."""

    return json.loads(json.dumps(value, default=str))


def _build_cost_index_snapshot(index: RefCostIndex | None) -> CostIndexSnapshot | None:
    """Convert a :class:`RefCostIndex` ORM instance into a schema snapshot."""

    if index is None:
        return None
    return CostIndexSnapshot(
        period=str(index.period),
        value=_decimal_from_value(index.value),
        unit=index.unit,
        source=index.source,
        provider=index.provider,
        methodology=index.methodology,
    )


def _compute_scalar(
    base: CostIndexSnapshot | None, latest: CostIndexSnapshot | None
) -> Decimal | None:
    """Return the escalation scalar derived from the supplied snapshots."""

    if base is None or latest is None:
        return None
    if base.value == 0:
        return None
    try:
        scalar = latest.value / base.value
        return scalar.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ZeroDivisionError):
        return None


def _convert_dscr_entry(entry: calculator.DscrEntry) -> DscrEntrySchema:
    """Serialise a DSCR entry into the API schema representation."""

    dscr_value = entry.dscr
    if isinstance(dscr_value, Decimal):
        if dscr_value.is_infinite():
            dscr_repr = str(dscr_value)
        else:
            dscr_repr = str(
                dscr_value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            )
    elif dscr_value is None:
        dscr_repr = None
    else:
        dscr_repr = str(dscr_value)

    return DscrEntrySchema(
        period=str(entry.period),
        noi=entry.noi,
        debt_service=entry.debt_service,
        dscr=dscr_repr,
        currency=entry.currency,
    )


async def _load_cost_indices(
    session: AsyncSession,
    *,
    series_name: str,
    jurisdiction: str,
    provider: str | None,
) -> list[RefCostIndex]:
    stmt = select(RefCostIndex).where(
        RefCostIndex.series_name == series_name,
        RefCostIndex.jurisdiction == jurisdiction,
    )
    if provider:
        stmt = stmt.where(RefCostIndex.provider == provider)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def _summarise_persisted_scenario(
    scenario: FinScenario,
    *,
    session: AsyncSession,
) -> FinanceFeasibilityResponse:
    assumptions: dict[str, Any] = dict(scenario.assumptions or {})
    fin_project = scenario.fin_project
    if fin_project is None:
        raise HTTPException(
            status_code=500, detail="Finance project missing for scenario"
        )

    cost_config = assumptions.get("cost_escalation") or {}
    cash_config = assumptions.get("cash_flow") or {}
    dscr_config = assumptions.get("dscr")
    capital_stack_config = assumptions.get("capital_stack")
    drawdown_config = assumptions.get("drawdown_schedule")

    try:
        amount_value = _decimal_from_value(cost_config["amount"])
    except (
        KeyError
    ) as exc:  # pragma: no cover - seeded data always includes cost config
        raise HTTPException(
            status_code=500, detail="Scenario missing cost escalation data"
        ) from exc

    indices = await _load_cost_indices(
        session,
        series_name=cost_config.get("series_name", ""),
        jurisdiction=cost_config.get("jurisdiction", ""),
        provider=cost_config.get("provider"),
    )

    escalated_cost = calculator.escalate_amount(
        amount_value,
        base_period=cost_config.get("base_period", ""),
        indices=indices,
        series_name=cost_config.get("series_name"),
        jurisdiction=cost_config.get("jurisdiction"),
        provider=cost_config.get("provider"),
    )

    latest_index = RefCostIndex.latest(
        indices,
        jurisdiction=cost_config.get("jurisdiction"),
        provider=cost_config.get("provider"),
        series_name=cost_config.get("series_name"),
    )
    base_index: RefCostIndex | None = None
    for index in indices:
        if str(index.period) != cost_config.get("base_period"):
            continue
        if index.series_name != cost_config.get("series_name"):
            continue
        if index.jurisdiction != cost_config.get("jurisdiction"):
            continue
        if cost_config.get("provider") and index.provider != cost_config.get(
            "provider"
        ):
            continue
        base_index = index
        break

    cost_provenance = CostIndexProvenance(
        series_name=cost_config.get("series_name", ""),
        jurisdiction=cost_config.get("jurisdiction", ""),
        provider=cost_config.get("provider"),
        base_period=cost_config.get("base_period", ""),
        latest_period=str(latest_index.period) if latest_index else None,
        scalar=_compute_scalar(
            _build_cost_index_snapshot(base_index),
            _build_cost_index_snapshot(latest_index),
        ),
        base_index=_build_cost_index_snapshot(base_index),
        latest_index=_build_cost_index_snapshot(latest_index),
    )

    discount_rate = cash_config.get("discount_rate", "0")
    cash_flows = cash_config.get("cash_flows") or []
    npv_value = calculator.npv(discount_rate, cash_flows)
    npv_rounded = npv_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    irr_value: Decimal | None = None
    irr_metadata = {
        "cash_flows": [str(value) for value in cash_flows],
        "discount_rate": str(discount_rate),
    }
    try:
        irr_raw = calculator.irr(cash_flows)
        irr_value = irr_raw.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    except ValueError:
        irr_metadata["warning"] = (
            "IRR could not be computed for the provided cash flows"
        )

    dscr_entries: list[DscrEntrySchema] = []
    if dscr_config:
        timeline = calculator.dscr_timeline(
            dscr_config.get("net_operating_incomes", []),
            dscr_config.get("debt_services", []),
            period_labels=dscr_config.get("period_labels"),
            currency=fin_project.currency,
        )
        dscr_entries = [_convert_dscr_entry(entry) for entry in timeline]

    capital_stack_inputs: list[Mapping[str, Any]] = []
    if scenario.capital_stack:
        ordered = sorted(
            scenario.capital_stack,
            key=lambda item: (
                item.tranche_order if item.tranche_order is not None else item.id
            ),
        )
        for entry in ordered:
            capital_stack_inputs.append(
                {
                    "name": entry.name,
                    "source_type": entry.source_type or "other",
                    "amount": entry.amount or Decimal("0"),
                    "rate": entry.rate,
                    "tranche_order": entry.tranche_order,
                    "metadata": dict(entry.metadata or {}),
                }
            )
    elif isinstance(capital_stack_config, list):
        for item in capital_stack_config:
            capital_stack_inputs.append(
                {
                    "name": item.get("name", ""),
                    "source_type": item.get("source_type", "other"),
                    "amount": _decimal_from_value(item.get("amount", "0")),
                    "rate": (
                        _decimal_from_value(item.get("rate"))
                        if item.get("rate") is not None
                        else None
                    ),
                    "tranche_order": item.get("tranche_order"),
                }
            )

    capital_stack_summary = None
    if capital_stack_inputs:
        capital_stack_summary = calculator.capital_stack_summary(
            capital_stack_inputs,
            currency=fin_project.currency,
            total_development_cost=escalated_cost,
        )

    drawdown_summary = None
    if isinstance(drawdown_config, list) and drawdown_config:
        schedule_inputs = []
        for entry in drawdown_config:
            schedule_inputs.append(
                {
                    "period": entry.get("period", ""),
                    "equity_draw": _decimal_from_value(entry.get("equity_draw", "0")),
                    "debt_draw": _decimal_from_value(entry.get("debt_draw", "0")),
                }
            )
        drawdown_summary = calculator.drawdown_schedule(
            schedule_inputs,
            currency=fin_project.currency,
        )

    dscr_metadata = {}
    if dscr_entries:
        dscr_metadata = {
            "entries": [
                _json_safe(entry.model_dump(mode="json")) for entry in dscr_entries
            ],
        }

    capital_metadata = None
    if capital_stack_summary:
        capital_metadata = {
            "currency": capital_stack_summary.currency,
            "totals": {
                "total": str(capital_stack_summary.total),
                "equity": str(capital_stack_summary.equity_total),
                "debt": str(capital_stack_summary.debt_total),
                "other": str(capital_stack_summary.other_total),
            },
            "ratios": {
                "equity": (
                    str(capital_stack_summary.equity_ratio)
                    if capital_stack_summary.equity_ratio is not None
                    else None
                ),
                "debt": (
                    str(capital_stack_summary.debt_ratio)
                    if capital_stack_summary.debt_ratio is not None
                    else None
                ),
                "other": (
                    str(capital_stack_summary.other_ratio)
                    if capital_stack_summary.other_ratio is not None
                    else None
                ),
                "loan_to_cost": (
                    str(capital_stack_summary.loan_to_cost)
                    if capital_stack_summary.loan_to_cost is not None
                    else None
                ),
                "weighted_average_debt_rate": (
                    str(capital_stack_summary.weighted_average_debt_rate)
                    if capital_stack_summary.weighted_average_debt_rate is not None
                    else None
                ),
            },
            "slices": [
                {
                    "name": component.name,
                    "source_type": component.source_type,
                    "category": component.category,
                    "amount": str(component.amount),
                    "share": str(component.share),
                    "rate": str(component.rate) if component.rate is not None else None,
                    "tranche_order": component.tranche_order,
                }
                for component in capital_stack_summary.slices
            ],
        }

    drawdown_metadata = None
    if drawdown_summary:
        drawdown_metadata = {
            "currency": drawdown_summary.currency,
            "totals": {
                "equity": str(drawdown_summary.total_equity),
                "debt": str(drawdown_summary.total_debt),
                "peak_debt_balance": str(drawdown_summary.peak_debt_balance),
                "final_debt_balance": str(drawdown_summary.final_debt_balance),
            },
            "entries": [
                {
                    "period": entry.period,
                    "equity_draw": str(entry.equity_draw),
                    "debt_draw": str(entry.debt_draw),
                    "total_draw": str(entry.total_draw),
                    "cumulative_equity": str(entry.cumulative_equity),
                    "cumulative_debt": str(entry.cumulative_debt),
                    "outstanding_debt": str(entry.outstanding_debt),
                }
                for entry in drawdown_summary.entries
            ],
        }

    results: list[FinanceResultSchema] = [
        FinanceResultSchema(
            name="escalated_cost",
            value=escalated_cost,
            unit=fin_project.currency,
            metadata={
                "base_amount": str(amount_value),
                "base_period": cost_config.get("base_period"),
                "cost_index": _json_safe(cost_provenance.model_dump(mode="json")),
            },
        ),
        FinanceResultSchema(
            name="npv",
            value=npv_rounded,
            unit=fin_project.currency,
            metadata={
                "discount_rate": str(discount_rate),
                "cash_flows": [str(value) for value in cash_flows],
            },
        ),
        FinanceResultSchema(
            name="irr",
            value=irr_value,
            unit="ratio",
            metadata=irr_metadata,
        ),
    ]

    if dscr_entries:
        results.append(
            FinanceResultSchema(
                name="dscr_timeline",
                value=None,
                metadata=dscr_metadata,
            )
        )

    if capital_metadata and capital_stack_summary:
        results.append(
            FinanceResultSchema(
                name="capital_stack",
                value=capital_stack_summary.total,
                unit=fin_project.currency,
                metadata=capital_metadata,
            )
        )

    if drawdown_metadata:
        results.append(
            FinanceResultSchema(
                name="drawdown_schedule",
                value=None,
                metadata=drawdown_metadata,
            )
        )

    drawdown_schema = None
    if drawdown_summary:
        drawdown_schema = _convert_drawdown_schedule(drawdown_summary)

    return FinanceFeasibilityResponse(
        scenario_id=scenario.id,
        project_id=str(scenario.project_id),
        fin_project_id=scenario.fin_project_id,
        scenario_name=scenario.name,
        currency=fin_project.currency,
        escalated_cost=escalated_cost,
        cost_index=cost_provenance,
        results=results,
        dscr_timeline=dscr_entries,
        capital_stack=(
            _convert_capital_stack_summary(capital_stack_summary)
            if capital_stack_summary
            else None
        ),
        drawdown_schedule=drawdown_schema,
    )


def _convert_capital_stack_summary(
    summary: calculator.CapitalStackSummary,
) -> CapitalStackSummarySchema:
    """Convert a calculator summary into the API schema representation."""

    slices = [
        CapitalStackSliceSchema(
            name=component.name,
            source_type=component.source_type,
            category=component.category,
            amount=component.amount,
            share=component.share,
            rate=component.rate,
            tranche_order=component.tranche_order,
            metadata=dict(component.metadata),
        )
        for component in summary.slices
    ]
    return CapitalStackSummarySchema(
        currency=summary.currency,
        total=summary.total,
        equity_total=summary.equity_total,
        debt_total=summary.debt_total,
        other_total=summary.other_total,
        equity_ratio=summary.equity_ratio,
        debt_ratio=summary.debt_ratio,
        other_ratio=summary.other_ratio,
        loan_to_cost=summary.loan_to_cost,
        weighted_average_debt_rate=summary.weighted_average_debt_rate,
        slices=slices,
    )


def _convert_drawdown_schedule(
    schedule: calculator.FinancingDrawdownSchedule,
) -> FinancingDrawdownScheduleSchema:
    """Convert calculator drawdown schedule into the API schema."""

    entries = [
        FinancingDrawdownEntrySchema(
            period=entry.period,
            equity_draw=entry.equity_draw,
            debt_draw=entry.debt_draw,
            total_draw=entry.total_draw,
            cumulative_equity=entry.cumulative_equity,
            cumulative_debt=entry.cumulative_debt,
            outstanding_debt=entry.outstanding_debt,
        )
        for entry in schedule.entries
    ]
    return FinancingDrawdownScheduleSchema(
        currency=schedule.currency,
        entries=entries,
        total_equity=schedule.total_equity,
        total_debt=schedule.total_debt,
        peak_debt_balance=schedule.peak_debt_balance,
        final_debt_balance=schedule.final_debt_balance,
    )


def _flush_buffer(stream: io.StringIO) -> bytes | None:
    """Read and reset the buffer returning encoded CSV content."""

    data = stream.getvalue()
    stream.seek(0)
    stream.truncate(0)
    if not data:
        return None
    return data.encode("utf-8")


def _iter_results_csv(scenario: FinScenario, *, currency: str) -> Iterator[bytes]:
    """Yield CSV rows describing a scenario and its persisted results."""

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Metric", "Value", "Unit"])
    chunk = _flush_buffer(buffer)
    if chunk:
        yield chunk

    ordered_results = sorted(
        scenario.results, key=lambda item: getattr(item, "id", 0) or 0
    )
    for result in ordered_results:
        value = result.value
        value_repr = "" if value is None else str(value)
        unit_repr = result.unit or ""
        writer.writerow([result.name, value_repr, unit_repr])
        chunk = _flush_buffer(buffer)
        if chunk:
            yield chunk

        if result.name == "dscr_timeline":
            timeline = None
            if isinstance(result.metadata, dict):
                timeline = result.metadata.get("entries")
            if timeline:
                writer.writerow([])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                writer.writerow(["Period", "NOI", "Debt Service", "DSCR", "Currency"])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                for entry in timeline:
                    writer.writerow(
                        [
                            entry.get("period", ""),
                            entry.get("noi", ""),
                            entry.get("debt_service", ""),
                            entry.get("dscr", ""),
                            entry.get("currency", currency),
                        ]
                    )
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk

    escalated = next(
        (item for item in ordered_results if item.name == "escalated_cost"), None
    )
    cost_meta = None
    if escalated is not None and isinstance(escalated.metadata, dict):
        cost_meta = escalated.metadata.get("cost_index")

    if cost_meta:
        writer.writerow([])
        chunk = _flush_buffer(buffer)
        if chunk:
            yield chunk
        writer.writerow(["Cost Index Provenance"])
        chunk = _flush_buffer(buffer)
        if chunk:
            yield chunk
        for key, value in cost_meta.items():
            if isinstance(value, dict):
                writer.writerow([key])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                for sub_key, sub_value in value.items():
                    writer.writerow([f"  {sub_key}", sub_value])
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk
            else:
                writer.writerow([key, value])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk

    chunk = _flush_buffer(buffer)
    if chunk:
        yield chunk


@router.post("/feasibility", response_model=FinanceFeasibilityResponse)
async def run_finance_feasibility(
    payload: FinanceFeasibilityRequest,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_reviewer),
) -> FinanceFeasibilityResponse:
    """Execute the full finance pipeline for the submitted scenario.

    The endpoint escalates base construction costs, calculates NPV and IRR
    figures, optionally derives a DSCR timeline, persists the scenario to the
    database, and returns a structured summary that the frontend can render.
    A ``404`` error is returned if the referenced finance project cannot be
    located.
    """

    metrics.REQUEST_COUNTER.labels(endpoint="finance_feasibility").inc()
    metrics.FINANCE_FEASIBILITY_TOTAL.inc()
    start_time = perf_counter()
    response: FinanceFeasibilityResponse | None = None
    project_uuid = _normalise_project_id(payload.project_id)
    try:
        log_event(
            logger,
            "finance_feasibility_received",
            project_id=str(project_uuid),
            scenario=payload.scenario.name,
        )

        fin_project: FinProject | None = None
        if payload.fin_project_id is not None:
            fin_project = await session.get(FinProject, payload.fin_project_id)
            if fin_project is None:
                raise HTTPException(status_code=404, detail="Finance project not found")
            if fin_project.project_id != project_uuid:
                raise HTTPException(
                    status_code=403,
                    detail="Finance project does not belong to the requested project",
                )
        else:
            stmt = (
                select(FinProject)
                .where(FinProject.project_id == project_uuid)
                .order_by(FinProject.id)
                .limit(1)
            )
            result = await session.execute(stmt)
            fin_project = result.scalar_one_or_none()

        if fin_project is None:
            fin_project = FinProject(
                project_id=str(project_uuid),
                name=payload.project_name or payload.scenario.name,
                currency=payload.scenario.currency,
                discount_rate=payload.scenario.cash_flow.discount_rate,
                metadata={},
            )
            session.add(fin_project)
            await session.flush()
        else:
            fin_project.currency = payload.scenario.currency
            fin_project.discount_rate = payload.scenario.cash_flow.discount_rate

        scenario = FinScenario(
            project_id=str(project_uuid),
            fin_project_id=fin_project.id,
            name=payload.scenario.name,
            description=payload.scenario.description,
            assumptions=payload.scenario.model_dump(mode="json"),
            is_primary=payload.scenario.is_primary,
        )
        session.add(scenario)
        await session.flush()

        cost_input = payload.scenario.cost_escalation
        stmt = select(RefCostIndex).where(
            RefCostIndex.series_name == cost_input.series_name,
            RefCostIndex.jurisdiction == cost_input.jurisdiction,
        )
        if cost_input.provider:
            stmt = stmt.where(RefCostIndex.provider == cost_input.provider)
        indices_result = await session.execute(stmt)
        indices: list[RefCostIndex] = list(indices_result.scalars().all())

        escalated_cost = calculator.escalate_amount(
            cost_input.amount,
            base_period=cost_input.base_period,
            indices=indices,
            series_name=cost_input.series_name,
            jurisdiction=cost_input.jurisdiction,
            provider=cost_input.provider,
        )

        latest_index = RefCostIndex.latest(
            indices,
            jurisdiction=cost_input.jurisdiction,
            provider=cost_input.provider,
            series_name=cost_input.series_name,
        )
        base_index: RefCostIndex | None = None
        for index in indices:
            if str(index.period) != cost_input.base_period:
                continue
            if index.series_name != cost_input.series_name:
                continue
            if index.jurisdiction != cost_input.jurisdiction:
                continue
            if cost_input.provider and index.provider != cost_input.provider:
                continue
            base_index = index
            break

        base_snapshot = _build_cost_index_snapshot(base_index)
        latest_snapshot = _build_cost_index_snapshot(latest_index)
        cost_provenance = CostIndexProvenance(
            series_name=cost_input.series_name,
            jurisdiction=cost_input.jurisdiction,
            provider=cost_input.provider,
            base_period=cost_input.base_period,
            latest_period=str(latest_snapshot.period) if latest_snapshot else None,
            scalar=_compute_scalar(base_snapshot, latest_snapshot),
            base_index=base_snapshot,
            latest_index=latest_snapshot,
        )

        cash_inputs = payload.scenario.cash_flow
        npv_value = calculator.npv(cash_inputs.discount_rate, cash_inputs.cash_flows)
        npv_rounded = npv_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        irr_value: Decimal | None = None
        irr_metadata = {
            "cash_flows": [str(value) for value in cash_inputs.cash_flows],
            "discount_rate": str(cash_inputs.discount_rate),
        }
        try:
            irr_raw = calculator.irr(cash_inputs.cash_flows)
            irr_value = irr_raw.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        except ValueError:
            irr_metadata["warning"] = (
                "IRR could not be computed for the provided cash flows"
            )

        dscr_entries: list[DscrEntrySchema] = []
        dscr_metadata: dict[str, list[dict[str, object]]] = {}
        if payload.scenario.dscr:
            try:
                timeline = calculator.dscr_timeline(
                    payload.scenario.dscr.net_operating_incomes,
                    payload.scenario.dscr.debt_services,
                    period_labels=payload.scenario.dscr.period_labels,
                    currency=payload.scenario.currency,
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            dscr_entries = [_convert_dscr_entry(entry) for entry in timeline]
            dscr_metadata = {
                "entries": [
                    _json_safe(entry.model_dump(mode="json")) for entry in dscr_entries
                ],
            }

        capital_stack_summary_schema: CapitalStackSummarySchema | None = None
        capital_stack_result_metadata: dict[str, object] | None = None
        if payload.scenario.capital_stack:
            stack_inputs = [
                item.model_dump(mode="json") for item in payload.scenario.capital_stack
            ]
            stack_summary = calculator.capital_stack_summary(
                stack_inputs,
                currency=payload.scenario.currency,
                total_development_cost=escalated_cost,
            )
            capital_stack_summary_schema = _convert_capital_stack_summary(stack_summary)

            capital_stack_rows: list[FinCapitalStack] = []
            slices_payload: list[dict[str, object]] = []
            for idx, component in enumerate(stack_summary.slices):
                tranche_order = (
                    component.tranche_order
                    if component.tranche_order is not None
                    else idx
                )
                component_metadata = _json_safe(dict(component.metadata))
                capital_stack_rows.append(
                    FinCapitalStack(
                        project_id=str(project_uuid),
                        scenario=scenario,
                        name=component.name,
                        source_type=component.source_type,
                        tranche_order=tranche_order,
                        amount=component.amount,
                        rate=component.rate,
                        equity_share=component.share,
                        metadata={
                            "category": component.category,
                            "share": str(component.share),
                            "detail": component_metadata,
                        },
                    )
                )
                slices_payload.append(
                    {
                        "name": component.name,
                        "source_type": component.source_type,
                        "category": component.category,
                        "amount": str(component.amount),
                        "share": str(component.share),
                        "rate": (
                            str(component.rate) if component.rate is not None else None
                        ),
                        "tranche_order": component.tranche_order,
                        "metadata": component_metadata,
                    }
                )
            if capital_stack_rows:
                session.add_all(capital_stack_rows)
            capital_stack_result_metadata = _json_safe(
                {
                    "currency": capital_stack_summary_schema.currency,
                    "totals": {
                        "total": str(stack_summary.total),
                        "equity": str(stack_summary.equity_total),
                        "debt": str(stack_summary.debt_total),
                        "other": str(stack_summary.other_total),
                    },
                    "ratios": {
                        "equity": (
                            str(stack_summary.equity_ratio)
                            if stack_summary.equity_ratio is not None
                            else None
                        ),
                        "debt": (
                            str(stack_summary.debt_ratio)
                            if stack_summary.debt_ratio is not None
                            else None
                        ),
                        "other": (
                            str(stack_summary.other_ratio)
                            if stack_summary.other_ratio is not None
                            else None
                        ),
                        "loan_to_cost": (
                            str(stack_summary.loan_to_cost)
                            if stack_summary.loan_to_cost is not None
                            else None
                        ),
                        "weighted_average_debt_rate": (
                            str(stack_summary.weighted_average_debt_rate)
                            if stack_summary.weighted_average_debt_rate is not None
                            else None
                        ),
                    },
                    "slices": slices_payload,
                }
            )

        drawdown_schedule_schema: FinancingDrawdownScheduleSchema | None = None
        drawdown_result_metadata: dict[str, object] | None = None
        if payload.scenario.drawdown_schedule:
            schedule_inputs = [
                item.model_dump(mode="json")
                for item in payload.scenario.drawdown_schedule
            ]
            schedule_summary = calculator.drawdown_schedule(
                schedule_inputs,
                currency=payload.scenario.currency,
            )
            drawdown_schedule_schema = _convert_drawdown_schedule(schedule_summary)
            drawdown_result_metadata = _json_safe(
                {
                    "currency": drawdown_schedule_schema.currency,
                    "totals": {
                        "equity": str(schedule_summary.total_equity),
                        "debt": str(schedule_summary.total_debt),
                        "peak_debt_balance": str(schedule_summary.peak_debt_balance),
                        "final_debt_balance": str(schedule_summary.final_debt_balance),
                    },
                    "entries": [
                        {
                            "period": entry.period,
                            "equity_draw": str(entry.equity_draw),
                            "debt_draw": str(entry.debt_draw),
                            "total_draw": str(entry.total_draw),
                            "cumulative_equity": str(entry.cumulative_equity),
                            "cumulative_debt": str(entry.cumulative_debt),
                            "outstanding_debt": str(entry.outstanding_debt),
                        }
                        for entry in schedule_summary.entries
                    ],
                }
            )

        results: list[FinResult] = [
            FinResult(
                project_id=str(project_uuid),
                scenario=scenario,
                name="escalated_cost",
                value=escalated_cost,
                unit=payload.scenario.currency,
                metadata={
                    "base_amount": str(cost_input.amount),
                    "base_period": cost_input.base_period,
                    "cost_index": _json_safe(cost_provenance.model_dump(mode="json")),
                },
            ),
            FinResult(
                project_id=str(project_uuid),
                scenario=scenario,
                name="npv",
                value=npv_rounded,
                unit=payload.scenario.currency,
                metadata={
                    "discount_rate": str(cash_inputs.discount_rate),
                    "cash_flows": [str(value) for value in cash_inputs.cash_flows],
                },
            ),
            FinResult(
                project_id=str(project_uuid),
                scenario=scenario,
                name="irr",
                value=irr_value,
                unit="ratio",
                metadata=irr_metadata,
            ),
        ]

        if dscr_entries:
            results.append(
                FinResult(
                    project_id=str(project_uuid),
                    scenario=scenario,
                    name="dscr_timeline",
                    value=None,
                    unit=None,
                    metadata=dscr_metadata,
                )
            )

        if (
            capital_stack_summary_schema is not None
            and capital_stack_result_metadata is not None
        ):
            results.append(
                FinResult(
                    project_id=str(project_uuid),
                    scenario=scenario,
                    name="capital_stack",
                    value=capital_stack_summary_schema.total,
                    unit=payload.scenario.currency,
                    metadata=capital_stack_result_metadata,
                )
            )

        if (
            drawdown_schedule_schema is not None
            and drawdown_result_metadata is not None
        ):
            results.append(
                FinResult(
                    project_id=str(project_uuid),
                    scenario=scenario,
                    name="drawdown_schedule",
                    value=None,
                    unit=None,
                    metadata=drawdown_result_metadata,
                )
            )

        session.add_all(results)

        await session.flush()
        await session.commit()

        log_event(
            logger,
            "finance_feasibility_completed",
            scenario_id=scenario.id,
            project_id=str(project_uuid),
        )

        response = FinanceFeasibilityResponse(
            scenario_id=scenario.id,
            project_id=str(project_uuid),
            fin_project_id=scenario.fin_project_id,
            scenario_name=scenario.name,
            currency=payload.scenario.currency,
            escalated_cost=escalated_cost,
            cost_index=cost_provenance,
            results=[
                FinanceResultSchema(
                    name=result.name,
                    value=result.value,
                    unit=result.unit,
                    metadata=dict(result.metadata or {}),
                )
                for result in results
            ],
            dscr_timeline=dscr_entries,
            capital_stack=capital_stack_summary_schema,
            drawdown_schedule=drawdown_schedule_schema,
        )
    finally:
        duration_ms = (perf_counter() - start_time) * 1000
        metrics.FINANCE_FEASIBILITY_DURATION_MS.observe(duration_ms)

    assert response is not None
    return response


@router.get("/scenarios", response_model=list[FinanceFeasibilityResponse])
async def list_finance_scenarios(
    project_id: str | int | UUID | None = Query(None),
    fin_project_id: int | None = Query(None),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> list[FinanceFeasibilityResponse]:
    """Return previously persisted finance scenarios for the requested project."""

    if project_id is None and fin_project_id is None:
        raise HTTPException(
            status_code=400,
            detail="project_id or fin_project_id must be provided",
        )

    stmt = (
        select(FinScenario)
        .options(
            selectinload(FinScenario.fin_project),
            selectinload(FinScenario.capital_stack),
        )
        .order_by(FinScenario.id)
    )

    if fin_project_id is not None:
        stmt = stmt.where(FinScenario.fin_project_id == fin_project_id)

    if project_id is not None:
        try:
            if isinstance(project_id, str):
                stripped = project_id.strip()
                if stripped.isdigit():
                    normalised = _normalise_project_id(int(stripped))
                else:
                    normalised = _normalise_project_id(stripped)
            else:
                normalised = _normalise_project_id(project_id)
        except HTTPException as exc:
            raise exc
        except Exception as exc:  # pragma: no cover - defensive for unexpected types
            raise HTTPException(
                status_code=422, detail="project_id must be a valid UUID"
            ) from exc

        stmt = stmt.where(FinScenario.project_id == str(normalised))

    result = await session.execute(stmt)
    scenarios = list(result.scalars().all())

    summaries: list[FinanceFeasibilityResponse] = []
    for scenario in scenarios:
        summaries.append(await _summarise_persisted_scenario(scenario, session=session))

    return summaries


@router.get("/export")
async def export_finance_scenario(
    scenario_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> StreamingResponse:
    """Stream a CSV export describing the requested finance scenario.

    The export is optimised for spreadsheet workflows and mirrors the data that
    is persisted after running the feasibility analysis. Consumers receive the
    same escalated cost provenance, headline ratios, and the optional DSCR
    timeline that appear in the UI. A ``400`` error is raised for non-positive
    scenario identifiers while a ``404`` is returned when the scenario cannot be
    found.
    """

    metrics.REQUEST_COUNTER.labels(endpoint="finance_export").inc()
    metrics.FINANCE_EXPORT_TOTAL.inc()
    start_time = perf_counter()
    response: StreamingResponse | None = None
    try:
        if scenario_id < 1:
            raise HTTPException(status_code=400, detail="scenario_id must be positive")
        stmt = (
            select(FinScenario)
            .where(FinScenario.id == scenario_id)
            .options(
                selectinload(FinScenario.results),
                selectinload(FinScenario.fin_project),
            )
            .limit(1)
        )
        result = await session.execute(stmt)
        scenario = result.scalar_one_or_none()
        if scenario is None:
            raise HTTPException(status_code=404, detail="Finance scenario not found")

        assumptions = scenario.assumptions or {}
        currency = assumptions.get("currency") or getattr(
            scenario.fin_project, "currency", "USD"
        )

        iterator = _iter_results_csv(scenario, currency=str(currency))
        filename = f"finance_scenario_{scenario.id}.csv"
        response = StreamingResponse(iterator, media_type="text/csv")
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'

        log_event(logger, "finance_feasibility_export", scenario_id=scenario.id)
    finally:
        duration_ms = (perf_counter() - start_time) * 1000
        metrics.FINANCE_EXPORT_DURATION_MS.observe(duration_ms)

    assert response is not None
    return response


__all__ = ["router"]
