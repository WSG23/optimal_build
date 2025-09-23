"""Finance feasibility API endpoints."""

from __future__ import annotations

import csv
import io
from time import perf_counter
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Iterator, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models.finance import FinProject, FinResult, FinScenario
from app.models.rkp import RefCostIndex
from app.schemas.finance import (
    CostIndexProvenance,
    CostIndexSnapshot,
    DscrEntrySchema,
    FinanceFeasibilityRequest,
    FinanceFeasibilityResponse,
    FinanceResultSchema,
)
from app.services.finance import calculator
from app.utils import metrics
from app.utils.logging import get_logger, log_event


router = APIRouter(prefix="/finance", tags=["finance"])
logger = get_logger(__name__)


def _decimal_from_value(value: object) -> Decimal:
    """Safely convert arbitrary numeric inputs into :class:`Decimal`."""

    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


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
) -> Optional[Decimal]:
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
            dscr_repr = str(dscr_value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))
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


def _flush_buffer(stream: io.StringIO) -> Optional[bytes]:
    """Read and reset the buffer returning encoded CSV content."""

    data = stream.getvalue()
    stream.seek(0)
    stream.truncate(0)
    if not data:
        return None
    return data.encode("utf-8")


def _iter_results_csv(
    scenario: FinScenario, *, currency: str
) -> Iterator[bytes]:
    """Yield CSV rows describing a scenario and its persisted results."""

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Metric", "Value", "Unit"])
    chunk = _flush_buffer(buffer)
    if chunk:
        yield chunk

    ordered_results = sorted(scenario.results, key=lambda item: getattr(item, "id", 0) or 0)
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

    escalated = next((item for item in ordered_results if item.name == "escalated_cost"), None)
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
) -> FinanceFeasibilityResponse:
    """Compute feasibility metrics, persist results and return a summary."""

    metrics.REQUEST_COUNTER.labels(endpoint="finance_feasibility").inc()
    metrics.FINANCE_FEASIBILITY_TOTAL.inc()
    start_time = perf_counter()
    response: FinanceFeasibilityResponse | None = None
    try:
        log_event(
            logger,
            "finance_feasibility_received",
            project_id=payload.project_id,
            scenario=payload.scenario.name,
        )

        fin_project: FinProject | None = None
        if payload.fin_project_id is not None:
            fin_project = await session.get(FinProject, payload.fin_project_id)
            if fin_project is None:
                raise HTTPException(status_code=404, detail="Finance project not found")
        else:
            stmt = (
                select(FinProject)
                .where(FinProject.project_id == payload.project_id)
                .order_by(FinProject.id)
                .limit(1)
            )
            result = await session.execute(stmt)
            fin_project = result.scalar_one_or_none()

        if fin_project is None:
            fin_project = FinProject(
                project_id=payload.project_id,
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
            project_id=payload.project_id,
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
        indices: List[RefCostIndex] = list(indices_result.scalars().all())

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

        irr_value: Optional[Decimal] = None
        irr_metadata = {
            "cash_flows": [str(value) for value in cash_inputs.cash_flows],
            "discount_rate": str(cash_inputs.discount_rate),
        }
        try:
            irr_raw = calculator.irr(cash_inputs.cash_flows)
            irr_value = irr_raw.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        except ValueError:
            irr_metadata["warning"] = "IRR could not be computed for the provided cash flows"

        dscr_entries: List[DscrEntrySchema] = []
        dscr_metadata: dict[str, List[dict[str, object]]] = {}
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
                "entries": [entry.model_dump(mode="json") for entry in dscr_entries],
            }

        results: List[FinResult] = [
            FinResult(
                project_id=payload.project_id,
                scenario_id=scenario.id,
                name="escalated_cost",
                value=escalated_cost,
                unit=payload.scenario.currency,
                metadata={
                    "base_amount": str(cost_input.amount),
                    "base_period": cost_input.base_period,
                    "cost_index": cost_provenance.model_dump(mode="json"),
                },
            ),
            FinResult(
                project_id=payload.project_id,
                scenario_id=scenario.id,
                name="npv",
                value=npv_rounded,
                unit=payload.scenario.currency,
                metadata={
                    "discount_rate": str(cash_inputs.discount_rate),
                    "cash_flows": [str(value) for value in cash_inputs.cash_flows],
                },
            ),
            FinResult(
                project_id=payload.project_id,
                scenario_id=scenario.id,
                name="irr",
                value=irr_value,
                unit="ratio",
                metadata=irr_metadata,
            ),
        ]

        if dscr_entries:
            results.append(
                FinResult(
                    project_id=payload.project_id,
                    scenario_id=scenario.id,
                    name="dscr_timeline",
                    value=None,
                    unit=None,
                    metadata=dscr_metadata,
                )
            )

        session.add_all(results)
        scenario.results.extend(results)

        await session.flush()
        await session.commit()

        log_event(
            logger,
            "finance_feasibility_completed",
            scenario_id=scenario.id,
            project_id=payload.project_id,
        )

        response = FinanceFeasibilityResponse(
            scenario_id=scenario.id,
            project_id=scenario.project_id,
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
        )
    finally:
        duration_ms = (perf_counter() - start_time) * 1000
        metrics.FINANCE_FEASIBILITY_DURATION_MS.observe(duration_ms)

    assert response is not None
    return response


@router.get("/export")
async def export_finance_scenario(
    scenario_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """Stream a CSV export describing the requested finance scenario."""

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
        currency = assumptions.get("currency") or getattr(scenario.fin_project, "currency", "USD")

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

