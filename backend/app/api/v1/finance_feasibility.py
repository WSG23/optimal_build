"""Finance feasibility API endpoint.

This module handles:
- POST /feasibility - Execute full finance pipeline for a scenario

This is the main entry point for creating finance scenarios.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from time import perf_counter
from typing import Any

import backend.jobs.finance_sensitivity  # noqa: F401
from backend.jobs import JobDispatch, job_queue
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequestIdentity, require_reviewer
from app.core.config import settings
from app.core.database import get_session
from app.models.finance import (
    FinAssetBreakdown,
    FinCapitalStack,
    FinProject,
    FinResult,
    FinScenario,
)
from app.models.rkp import RefCostIndex
from app.schemas.finance import (
    AssetFinancialSummarySchema,
    CapitalStackSummarySchema,
    ConstructionLoanInterestSchema,
    CostIndexProvenance,
    DscrEntrySchema,
    FinanceAssetBreakdownSchema,
    FinanceFeasibilityRequest,
    FinanceFeasibilityResponse,
    FinanceJobStatusSchema,
    FinanceResultSchema,
    FinanceSensitivityOutcomeSchema,
    FinancingDrawdownScheduleSchema,
)
from app.services.finance import (
    AssetFinanceInput,
    build_asset_financials,
    calculator,
    serialise_breakdown,
    summarise_asset_financials,
)
from app.services.jurisdictions import get_jurisdiction_config
from app.utils import metrics
from app.utils.logging import get_logger, log_event

from .finance_common import (
    build_asset_breakdown_records,
    build_cost_index_snapshot,
    build_facility_metadata_map,
    compute_scalar,
    convert_capital_stack_summary,
    convert_drawdown_schedule,
    convert_dscr_entry,
    decimal_from_value,
    default_job_status,
    json_safe,
    merge_facility_metadata,
    normalise_facility_key,
    normalise_project_id,
    record_async_job,
)
from .finance_export import (
    build_construction_interest_schedule,
    evaluate_sensitivity_bands,
)
from .finance_scenarios import _ensure_project_owner

router = APIRouter(prefix="/finance", tags=["finance"])
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def _build_finance_analytics_summary(
    cash_flows: Sequence[Decimal],
    dscr_entries: Sequence[DscrEntrySchema],
    drawdown: FinancingDrawdownScheduleSchema | None,
) -> dict[str, Any] | None:
    """Assemble advanced analytics (MOIC, DSCR heat map) for the dashboard."""

    from .finance_common import decimal_to_string

    if not cash_flows and not dscr_entries and drawdown is None:
        return None

    invested = Decimal("0")
    distributions = Decimal("0")
    for entry in cash_flows:
        if entry < 0:
            invested += abs(entry)
        elif entry > 0:
            distributions += entry
    moic_value = None
    if invested > 0 and distributions > 0:
        moic_value = distributions / invested
    equity_multiple = moic_value

    dscr_buckets: list[dict[str, Any]] = []
    dscr_bucket_defs: list[tuple[str, str, Decimal | None, Decimal | None]] = [
        ("lt_1", "< 1.00x", None, Decimal("1.0")),
        ("range_1_125", "1.00x – 1.25x", Decimal("1.0"), Decimal("1.25")),
        ("range_125_150", "1.25x – 1.50x", Decimal("1.25"), Decimal("1.5")),
        ("gte_150", "≥ 1.50x", Decimal("1.5"), None),
    ]
    bucket_counters: dict[str, dict[str, Any]] = {}
    for key, label, _lower, _upper in dscr_bucket_defs:
        bucket = {"key": key, "label": label, "count": 0, "periods": []}
        bucket_counters[key] = bucket
        dscr_buckets.append(bucket)

    dscr_entries_payload: list[dict[str, Any]] = []
    for dscr_entry in dscr_entries:
        dscr_value = (
            Decimal(dscr_entry.dscr)
            if dscr_entry.dscr is not None and dscr_entry.dscr not in ("", "None")
            else None
        )
        bucket_key = None
        if dscr_value is not None:
            for key, _, lower, upper in dscr_bucket_defs:
                meets_lower = lower is None or dscr_value >= lower
                meets_upper = upper is None or dscr_value < upper
                if meets_lower and meets_upper:
                    bucket_key = key
                    break
            if bucket_key:
                bucket = bucket_counters[bucket_key]
                bucket["count"] += 1
                bucket["periods"].append(str(dscr_entry.period))
        dscr_entries_payload.append(
            {
                "period": dscr_entry.period,
                "dscr": decimal_to_string(dscr_value) if dscr_value else None,
                "bucket": bucket_key,
            }
        )

    analytics: dict[str, Any] = {
        "cash_flow_summary": {
            "invested_equity": decimal_to_string(invested),
            "distributions": decimal_to_string(distributions),
            "net_cash": decimal_to_string(distributions - invested),
        }
    }
    if moic_value is not None:
        analytics["moic"] = decimal_to_string(moic_value)
    if equity_multiple is not None:
        analytics["equity_multiple"] = decimal_to_string(equity_multiple)
    analytics["dscr_heatmap"] = {
        "buckets": dscr_buckets,
        "entries": dscr_entries_payload,
    }
    if drawdown is not None:
        analytics["drawdown_summary"] = {
            "total_equity": decimal_to_string(drawdown.total_equity, places=2),
            "total_debt": decimal_to_string(drawdown.total_debt, places=2),
            "peak_debt_balance": decimal_to_string(
                drawdown.peak_debt_balance, places=2
            ),
        }
    return analytics


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("/feasibility", response_model=FinanceFeasibilityResponse)
async def run_finance_feasibility(
    payload: FinanceFeasibilityRequest,
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_reviewer),
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
    project_uuid = normalise_project_id(payload.project_id)
    await _ensure_project_owner(session, project_uuid, identity)
    try:
        log_event(
            logger,
            "finance_feasibility_received",
            project_id=str(project_uuid),
            scenario=payload.scenario.name,
        )

        jurisdiction = get_jurisdiction_config(payload.scenario.jurisdiction_code)
        if not payload.scenario.currency or not payload.scenario.currency.strip():
            payload.scenario.currency = jurisdiction.currency_code
        cost_jurisdiction = payload.scenario.cost_escalation.jurisdiction
        if not cost_jurisdiction or not cost_jurisdiction.strip():
            payload.scenario.cost_escalation.jurisdiction = jurisdiction.code

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
                project_id=project_uuid,
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
            project_id=project_uuid,
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

        base_snapshot = build_cost_index_snapshot(base_index)
        latest_snapshot = build_cost_index_snapshot(latest_index)
        cost_provenance = CostIndexProvenance(
            series_name=cost_input.series_name,
            jurisdiction=cost_input.jurisdiction,
            provider=cost_input.provider,
            base_period=cost_input.base_period,
            latest_period=str(latest_snapshot.period) if latest_snapshot else None,
            scalar=compute_scalar(base_snapshot, latest_snapshot),
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
            dscr_entries = [convert_dscr_entry(entry) for entry in timeline]
            dscr_metadata = {
                "entries": [
                    json_safe(entry.model_dump(mode="json")) for entry in dscr_entries
                ],
            }

        facility_metadata_map = build_facility_metadata_map(
            payload.scenario.construction_loan
        )
        capital_stack_summary_schema: CapitalStackSummarySchema | None = None
        capital_stack_result_metadata: dict[str, object] | None = None
        if payload.scenario.capital_stack:
            stack_inputs: list[dict[str, Any]] = []
            for slice_input in payload.scenario.capital_stack:
                facility_key = normalise_facility_key(slice_input.name)
                facility_meta = facility_metadata_map.get(facility_key)
                metadata = merge_facility_metadata(slice_input.metadata, facility_meta)
                stack_inputs.append(
                    {
                        "name": slice_input.name,
                        "source_type": slice_input.source_type,
                        "amount": slice_input.amount,
                        "rate": slice_input.rate,
                        "tranche_order": slice_input.tranche_order,
                        "metadata": metadata,
                    }
                )
            stack_summary = calculator.capital_stack_summary(
                stack_inputs,
                currency=payload.scenario.currency,
                total_development_cost=escalated_cost,
            )
            capital_stack_summary_schema = convert_capital_stack_summary(stack_summary)

            capital_stack_rows: list[FinCapitalStack] = []
            slices_payload: list[dict[str, object]] = []
            for idx, component in enumerate(stack_summary.slices):
                tranche_order = (
                    component.tranche_order
                    if component.tranche_order is not None
                    else idx
                )
                component_metadata = dict(component.metadata or {})
                combined_metadata: dict[str, object] = {}
                if component_metadata:
                    combined_metadata.update(component_metadata)
                combined_metadata.setdefault("category", component.category)
                combined_metadata.setdefault("share", str(component.share))
                capital_stack_rows.append(
                    FinCapitalStack(
                        project_id=project_uuid,
                        scenario=scenario,
                        name=component.name,
                        source_type=component.source_type,
                        tranche_order=tranche_order,
                        amount=component.amount,
                        rate=component.rate,
                        equity_share=component.share,
                        metadata=json_safe(combined_metadata),
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
                        "metadata": json_safe(combined_metadata),
                    }
                )
            if capital_stack_rows:
                session.add_all(capital_stack_rows)
            capital_stack_result_metadata = json_safe(
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
        schedule_summary: calculator.FinancingDrawdownSchedule | None = None
        if payload.scenario.drawdown_schedule:
            schedule_inputs = [
                item.model_dump(mode="json")
                for item in payload.scenario.drawdown_schedule
            ]
            schedule_summary = calculator.drawdown_schedule(
                schedule_inputs,
                currency=payload.scenario.currency,
            )
            drawdown_schedule_schema = convert_drawdown_schedule(schedule_summary)
            drawdown_result_metadata = json_safe(
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

        asset_breakdown_schemas: list[FinanceAssetBreakdownSchema] = []
        asset_mix_summary_schema: AssetFinancialSummarySchema | None = None
        asset_financial_metadata: dict[str, object] | None = None
        asset_breakdown_models: list[FinAssetBreakdown] = []
        if payload.scenario.asset_mix:
            asset_inputs = [
                AssetFinanceInput(
                    asset_type=entry.asset_type,
                    allocation_pct=entry.allocation_pct,
                    nia_sqm=entry.nia_sqm,
                    rent_psm_month=entry.rent_psm_month,
                    stabilised_vacancy_pct=entry.stabilised_vacancy_pct,
                    opex_pct_of_rent=entry.opex_pct_of_rent,
                    estimated_revenue_sgd=entry.estimated_revenue_sgd,
                    estimated_capex_sgd=entry.estimated_capex_sgd,
                    absorption_months=entry.absorption_months,
                    risk_level=entry.risk_level,
                    heritage_premium_pct=entry.heritage_premium_pct,
                    notes=tuple(entry.notes),
                )
                for entry in payload.scenario.asset_mix
            ]
            asset_breakdowns = build_asset_financials(asset_inputs)
            asset_breakdown_schemas = serialise_breakdown(asset_breakdowns)
            asset_mix_summary_schema = summarise_asset_financials(asset_breakdowns)
            asset_financial_metadata = {
                "summary": (
                    asset_mix_summary_schema.model_dump(mode="json")
                    if asset_mix_summary_schema is not None
                    else None
                ),
                "breakdowns": [
                    breakdown.model_dump(mode="json")
                    for breakdown in asset_breakdown_schemas
                ],
            }
            asset_breakdown_models = build_asset_breakdown_records(
                project_uuid, scenario, asset_breakdowns
            )

        construction_interest_schema: ConstructionLoanInterestSchema | None = None
        construction_interest_metadata: dict[str, Any] | None = None
        loan_config = payload.scenario.construction_loan
        if loan_config and schedule_summary is not None:
            facility_payloads = (
                [
                    facility.model_dump(mode="json")
                    for facility in loan_config.facilities
                ]
                if loan_config.facilities
                else None
            )
            (
                construction_interest_schema,
                construction_interest_metadata,
            ) = build_construction_interest_schedule(
                schedule_summary,
                currency=payload.scenario.currency,
                base_interest_rate=loan_config.interest_rate,
                base_periods_per_year=loan_config.periods_per_year,
                capitalise_interest=loan_config.capitalise_interest,
                facilities=facility_payloads,
            )

        base_interest_total = (
            decimal_from_value(construction_interest_schema.total_interest)
            if (
                construction_interest_schema
                and construction_interest_schema.total_interest is not None
            )
            else None
        )
        sensitivity_results: list[FinanceSensitivityOutcomeSchema] = []
        sensitivity_metadata: list[dict[str, Any]] | None = None
        sensitivity_jobs: list[FinanceJobStatusSchema] = []
        sensitivity_bands = payload.scenario.sensitivity_bands or []
        if sensitivity_bands:
            sync_threshold = max(1, settings.FINANCE_SENSITIVITY_MAX_SYNC_BANDS)
            if len(sensitivity_bands) <= sync_threshold:
                (
                    sensitivity_results,
                    sensitivity_metadata,
                ) = evaluate_sensitivity_bands(
                    sensitivity_bands,
                    base_npv=npv_rounded,
                    base_irr=irr_value,
                    escalated_cost=escalated_cost,
                    base_interest_total=base_interest_total,
                    currency=payload.scenario.currency,
                )
                sensitivity_jobs = [default_job_status(scenario.id)]
            else:
                job_context = {
                    "cash_flows": [str(value) for value in cash_inputs.cash_flows],
                    "discount_rate": str(cash_inputs.discount_rate),
                    "escalated_cost": str(escalated_cost),
                    "cost_factor_applicable": bool(payload.scenario.capital_stack),
                    "currency": payload.scenario.currency,
                    "interest_periods": (
                        loan_config.periods_per_year
                        if loan_config and loan_config.periods_per_year
                        else 12
                    ),
                    "capitalise_interest": (
                        loan_config.capitalise_interest if loan_config else True
                    ),
                    "base_interest_rate": (
                        str(loan_config.interest_rate)
                        if loan_config and loan_config.interest_rate is not None
                        else None
                    ),
                    "schedule": (
                        drawdown_schedule_schema.model_dump(mode="json")
                        if drawdown_schedule_schema
                        else None
                    ),
                    "facilities": (
                        [
                            facility.model_dump(mode="json")
                            for facility in (loan_config.facilities or [])
                        ]
                        if loan_config and loan_config.facilities
                        else []
                    ),
                }
                dispatch: JobDispatch = await job_queue.enqueue(
                    "finance.sensitivity",
                    scenario.id,
                    bands=[band.model_dump(mode="json") for band in sensitivity_bands],
                    context=job_context,
                    queue="finance",
                )
                queued_at = datetime.now(timezone.utc)
                job_status = FinanceJobStatusSchema(
                    scenario_id=scenario.id,
                    task_id=dispatch.task_id,
                    status=dispatch.status,
                    backend=dispatch.backend,
                    queued_at=queued_at,
                )
                sensitivity_jobs = [job_status]
                sensitivity_metadata = [
                    {
                        "parameter": "__async__",
                        "status": dispatch.status,
                        "task_id": dispatch.task_id,
                        "queue": dispatch.queue,
                    }
                ]
                record_async_job(scenario, job_status)

        if not sensitivity_jobs:
            sensitivity_jobs = [default_job_status(scenario.id)]

        cash_flow_values: list[Decimal] = []
        for raw in cash_inputs.cash_flows:
            try:
                cash_flow_values.append(decimal_from_value(raw))
            except (InvalidOperation, ValueError):
                continue

        results: list[FinResult] = [
            FinResult(
                project_id=project_uuid,
                scenario=scenario,
                name="escalated_cost",
                value=escalated_cost,
                unit=payload.scenario.currency,
                metadata={
                    "base_amount": str(cost_input.amount),
                    "base_period": cost_input.base_period,
                    "cost_index": json_safe(cost_provenance.model_dump(mode="json")),
                },
            ),
            FinResult(
                project_id=project_uuid,
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
                project_id=project_uuid,
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
                    project_id=project_uuid,
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
                    project_id=project_uuid,
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
                    project_id=project_uuid,
                    scenario=scenario,
                    name="drawdown_schedule",
                    value=None,
                    unit=None,
                    metadata=drawdown_result_metadata,
                )
            )

        if asset_financial_metadata is not None:
            results.append(
                FinResult(
                    project_id=project_uuid,
                    scenario=scenario,
                    name="asset_financials",
                    value=None,
                    unit=None,
                    metadata=json_safe(asset_financial_metadata),
                )
            )
        if sensitivity_metadata is not None:
            results.append(
                FinResult(
                    project_id=project_uuid,
                    scenario=scenario,
                    name="sensitivity_analysis",
                    value=None,
                    unit=None,
                    metadata=json_safe({"bands": sensitivity_metadata}),
                )
            )
        if (
            construction_interest_schema is not None
            and construction_interest_metadata is not None
        ):
            results.append(
                FinResult(
                    project_id=project_uuid,
                    scenario=scenario,
                    name="construction_loan_interest",
                    value=decimal_from_value(
                        construction_interest_schema.total_interest
                        if construction_interest_schema.total_interest is not None
                        else "0"
                    ),
                    unit=payload.scenario.currency,
                    metadata=json_safe(construction_interest_metadata),
                )
            )

        analytics_metadata = _build_finance_analytics_summary(
            cash_flow_values, dscr_entries, drawdown_schedule_schema
        )
        if analytics_metadata:
            results.append(
                FinResult(
                    project_id=project_uuid,
                    scenario=scenario,
                    name="analytics_overview",
                    value=None,
                    unit=None,
                    metadata=json_safe(analytics_metadata),
                )
            )

        if asset_breakdown_models:
            session.add_all(asset_breakdown_models)

        session.add_all(results)

        await session.flush()
        await session.commit()
        await session.refresh(scenario)

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
                    metadata=dict(result.metadata or {}),  # type: ignore[arg-type,has-type]
                )
                for result in results
            ],
            dscr_timeline=dscr_entries,
            capital_stack=capital_stack_summary_schema,
            drawdown_schedule=drawdown_schedule_schema,
            asset_mix_summary=asset_mix_summary_schema,
            asset_breakdowns=asset_breakdown_schemas,
            construction_loan_interest=construction_interest_schema,
            construction_loan=loan_config,
            sensitivity_results=sensitivity_results,
            sensitivity_jobs=sensitivity_jobs,
            sensitivity_bands=payload.scenario.sensitivity_bands or [],
            is_primary=bool(scenario.is_primary),
            is_private=bool(getattr(scenario, "is_private", False)),
            updated_at=scenario.updated_at,
        )
    finally:
        duration_ms = (perf_counter() - start_time) * 1000
        metrics.FINANCE_FEASIBILITY_DURATION_MS.observe(duration_ms)

    assert response is not None
    return response


__all__ = ["router"]
