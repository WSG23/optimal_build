"""Finance feasibility API endpoints."""

from __future__ import annotations

import csv
import io
import json
import zipfile
from collections.abc import AsyncIterator, Iterator, Mapping, Sequence
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from time import perf_counter
from typing import Any
from uuid import UUID

import backend.jobs.finance_sensitivity  # noqa: F401
from backend.jobs import JobDispatch, job_queue
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator

from app.api.deps import RequestIdentity, require_reviewer, require_viewer
from app.core.config import settings
from app.core.database import get_session
from app.models.finance import (
    FinAssetBreakdown,
    FinCapitalStack,
    FinProject,
    FinResult,
    FinScenario,
)
from app.models.projects import Project
from app.models.rkp import RefCostIndex
from app.schemas.finance import (
    AssetFinancialSummarySchema,
    CapitalStackSliceSchema,
    CapitalStackSummarySchema,
    ConstructionLoanFacilityInput,
    ConstructionLoanInput,
    ConstructionLoanInterestSchema,
    CostIndexProvenance,
    CostIndexSnapshot,
    DscrEntrySchema,
    FinanceAssetBreakdownSchema,
    FinanceFeasibilityRequest,
    FinanceFeasibilityResponse,
    FinanceJobStatusSchema,
    FinanceResultSchema,
    FinanceSensitivityOutcomeSchema,
    FinancingDrawdownEntrySchema,
    FinancingDrawdownScheduleSchema,
    SensitivityBandInput,
)
from app.services.finance import (
    AssetFinanceInput,
    build_asset_financials,
    calculator,
    serialise_breakdown,
    summarise_asset_financials,
)
from app.services.finance.asset_models import AssetFinanceBreakdown
from app.utils import metrics
from app.utils.logging import get_logger, log_event
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified

router = APIRouter(prefix="/finance", tags=["finance"])
logger = get_logger(__name__)


class ConstructionLoanUpdatePayload(BaseModel):
    construction_loan: ConstructionLoanInput


class FinanceScenarioUpdatePayload(BaseModel):
    """Mutable fields for a persisted finance scenario."""

    scenario_name: str | None = None
    description: str | None = None
    is_primary: bool | None = None


class FinanceSensitivityRunPayload(BaseModel):
    """Payload for rerunning sensitivity analysis on a scenario."""

    sensitivity_bands: list[SensitivityBandInput]

    @field_validator("sensitivity_bands")
    @classmethod
    def _validate_bands(
        cls, value: list[SensitivityBandInput]
    ) -> list[SensitivityBandInput]:
        if not value:
            raise ValueError("At least one sensitivity band must be provided.")
        for index, band in enumerate(value, start=1):
            if not band.parameter or not band.parameter.strip():
                raise ValueError(f"Sensitivity band #{index} is missing a parameter.")
            if band.low is None and band.base is None and band.high is None:
                raise ValueError(
                    f"Sensitivity band '{band.parameter}' must define at least one delta."
                )
        return value


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


def _normalise_facility_key(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip().lower()
    return trimmed or None


def _raise_finance_privacy_error(
    *,
    project_uuid: UUID,
    identity: RequestIdentity,
    reason: str,
    detail: str,
) -> None:
    """Log and surface a consistent privacy denial response."""

    metrics.FINANCE_PRIVACY_DENIALS.labels(reason=reason).inc()
    log_event(
        logger,
        "finance_privacy_denied",
        project_id=str(project_uuid),
        role=identity.role,
        user_id=identity.user_id,
        email=identity.email,
        reason=reason,
    )
    raise HTTPException(status_code=403, detail=detail)


async def _ensure_project_owner(
    session: AsyncSession,
    project_uuid: UUID,
    identity: RequestIdentity,
) -> None:
    """Verify that the caller owns the referenced project (admin bypass)."""

    if identity.role == "admin":
        return

    stmt = select(Project.owner_id, Project.owner_email).where(
        Project.id == project_uuid
    )
    result = await session.execute(stmt)
    row = result.first()
    if row is None:
        _raise_finance_privacy_error(
            project_uuid=project_uuid,
            identity=identity,
            reason="project_missing",
            detail="Finance data restricted to project owner.",
        )

    owner_id, owner_email = row
    if owner_id is None and owner_email is None:
        _raise_finance_privacy_error(
            project_uuid=project_uuid,
            identity=identity,
            reason="owner_metadata_missing",
            detail="Finance data restricted to project owner.",
        )

    if not identity.user_id and not identity.email:
        _raise_finance_privacy_error(
            project_uuid=project_uuid,
            identity=identity,
            reason="identity_metadata_missing",
            detail=(
                "Finance data restricted to project owner; "
                "supply X-User-Id or X-User-Email headers."
            ),
        )

    matches = False
    if identity.user_id and owner_id is not None:
        matches |= str(owner_id) == identity.user_id
    if identity.email and owner_email:
        matches |= owner_email.lower() == identity.email.lower()

    if not matches:
        _raise_finance_privacy_error(
            project_uuid=project_uuid,
            identity=identity,
            reason="ownership_mismatch",
            detail="Finance data restricted to project owner.",
        )


def _facility_metadata_from_input(
    facility: ConstructionLoanFacilityInput,
) -> dict[str, str | bool | int]:
    metadata: dict[str, str | bool | int] = {}
    if facility.upfront_fee_pct is not None:
        metadata["upfront_fee_pct"] = str(facility.upfront_fee_pct)
    if facility.exit_fee_pct is not None:
        metadata["exit_fee_pct"] = str(facility.exit_fee_pct)
    if facility.reserve_months is not None:
        metadata["reserve_months"] = int(facility.reserve_months)
    if facility.amortisation_months is not None:
        metadata["amortisation_months"] = int(facility.amortisation_months)
    if facility.periods_per_year is not None:
        metadata["periods_per_year"] = int(facility.periods_per_year)
    if facility.capitalise_interest is not None:
        metadata["capitalise_interest"] = bool(facility.capitalise_interest)
    return metadata


def _decimal_to_string(value: Decimal | None, places: int | None = None) -> str | None:
    if value is None:
        return None
    if places is not None:
        quant = Decimal(1).scaleb(-places)
        try:
            value = value.quantize(quant, rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError):
            pass
    return format(value, "f")


def _serialise_asset_breakdown_model(
    record: FinAssetBreakdown,
) -> FinanceAssetBreakdownSchema:
    return FinanceAssetBreakdownSchema(
        asset_type=record.asset_type,
        allocation_pct=_decimal_to_string(record.allocation_pct, places=4),
        nia_sqm=_decimal_to_string(record.nia_sqm, places=2),
        rent_psm_month=_decimal_to_string(record.rent_psm_month, places=2),
        gross_rent_annual_sgd=_decimal_to_string(record.annual_revenue_sgd, places=2),
        annual_revenue_sgd=_decimal_to_string(record.annual_revenue_sgd, places=2),
        vacancy_loss_sgd=None,
        effective_gross_income_sgd=None,
        operating_expenses_sgd=None,
        annual_opex_sgd=None,
        noi_annual_sgd=_decimal_to_string(record.annual_noi_sgd, places=2),
        annual_noi_sgd=_decimal_to_string(record.annual_noi_sgd, places=2),
        estimated_capex_sgd=_decimal_to_string(record.estimated_capex_sgd, places=2),
        capex_sgd=_decimal_to_string(record.estimated_capex_sgd, places=2),
        payback_years=_decimal_to_string(record.payback_years, places=2),
        absorption_months=_decimal_to_string(record.absorption_months, places=1),
        stabilised_yield_pct=_decimal_to_string(record.stabilised_yield_pct, places=4),
        risk_level=record.risk_level,
        risk_priority=record.risk_priority,
        heritage_premium_pct=None,
        notes=list(record.notes_json or []),
    )


def _build_asset_breakdown_records(
    project_uuid: UUID,
    scenario: FinScenario,
    breakdowns: AssetFinanceBreakdown | Sequence[AssetFinanceBreakdown] | None,
) -> list[FinAssetBreakdown]:
    """Convert calculated asset breakdowns into ORM rows for persistence."""

    if breakdowns is None:
        return []

    if isinstance(breakdowns, AssetFinanceBreakdown):
        queue: Sequence[AssetFinanceBreakdown] = (breakdowns,)
    else:
        queue = tuple(breakdowns)

    records: list[FinAssetBreakdown] = []
    for entry in queue:
        notes = entry.notes or ()
        records.append(
            FinAssetBreakdown(
                project_id=project_uuid,
                scenario=scenario,
                asset_type=entry.asset_type,
                allocation_pct=entry.allocation_pct,
                nia_sqm=entry.nia_sqm,
                rent_psm_month=entry.rent_psm_month,
                annual_noi_sgd=entry.annual_noi_sgd,
                annual_revenue_sgd=entry.annual_revenue_sgd,
                estimated_capex_sgd=entry.estimated_capex_sgd,
                payback_years=entry.payback_years,
                absorption_months=entry.absorption_months,
                stabilised_yield_pct=entry.stabilised_yield_pct,
                risk_level=entry.risk_level,
                risk_priority=entry.risk_priority,
                notes_json=list(notes),
            )
        )
    return records


def _build_facility_metadata_map(
    loan_config: ConstructionLoanInput | None,
) -> dict[str, dict[str, str | bool | int]]:
    """Index construction loan facilities by a normalised name for lookups."""

    metadata_map: dict[str, dict[str, str | bool | int]] = {}
    if not loan_config or not loan_config.facilities:
        return metadata_map

    for idx, facility in enumerate(loan_config.facilities):
        key = _normalise_facility_key(facility.name) or f"facility_{idx}"
        meta = _facility_metadata_from_input(facility)
        if meta:
            metadata_map[key] = meta
    return metadata_map


def _merge_facility_metadata(
    metadata: Mapping[str, Any] | None,
    facility_meta: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Normalise slice metadata and append facility details when available."""

    merged: dict[str, Any] = dict(metadata or {})
    facility_block: dict[str, Any] | None = None

    def _ensure_facility_block() -> dict[str, Any]:
        nonlocal facility_block
        if facility_block is None:
            existing = merged.get("facility")
            facility_block = dict(existing) if isinstance(existing, Mapping) else {}
            merged["facility"] = facility_block
        return facility_block

    detail = merged.pop("detail", None)
    if isinstance(detail, Mapping):
        nested = detail.get("facility")
        if isinstance(nested, Mapping):
            _ensure_facility_block().update(nested)
        else:
            _ensure_facility_block().update(detail)

    if facility_meta:
        _ensure_facility_block().update(facility_meta)

    if facility_block is not None and not facility_block:
        merged.pop("facility", None)

    return merged


def _store_sensitivity_metadata(
    session: AsyncSession,
    scenario: FinScenario,
    entries: Sequence[Mapping[str, Any] | FinanceSensitivityOutcomeSchema],
) -> None:
    """Persist sensitivity metadata on the scenario's results."""

    existing_result: FinResult | None = None
    for candidate in scenario.results:
        if candidate.name == "sensitivity_analysis":
            existing_result = candidate
            break
    if existing_result is None:
        existing_result = FinResult(
            project_id=scenario.project_id,
            scenario=scenario,
            name="sensitivity_analysis",
            value=None,
            unit=None,
            metadata={},
        )
        session.add(existing_result)

    serialised: list[dict[str, Any]] = []
    for entry in entries:
        if isinstance(entry, FinanceSensitivityOutcomeSchema):
            serialised.append(entry.model_dump(mode="json"))
        else:
            serialised.append(_json_safe(entry))

    existing_result.metadata = {"bands": serialised}  # type: ignore[assignment,has-type]
    flag_modified(existing_result, "metadata_json")


def _clear_sensitivity_jobs(scenario: FinScenario) -> None:
    """Remove tracked sensitivity jobs from scenario assumptions."""

    assumptions = dict(scenario.assumptions or {})
    async_jobs = assumptions.get("async_jobs")
    if isinstance(async_jobs, dict) and async_jobs.pop("sensitivity", None) is not None:
        if async_jobs:
            assumptions["async_jobs"] = async_jobs
        else:
            assumptions.pop("async_jobs", None)
        scenario.assumptions = assumptions


def _base_finance_metrics(
    scenario: FinScenario,
) -> tuple[Decimal, Decimal | None, Decimal, Decimal | None]:
    """Extract baseline finance metrics required for sensitivity runs."""

    escalated_cost: Decimal | None = None
    base_npv: Decimal | None = None
    base_irr: Decimal | None = None
    interest_total: Decimal | None = None

    for result in scenario.results:
        if result.name == "escalated_cost" and result.value is not None:
            escalated_cost = _decimal_from_value(result.value)
        elif result.name == "npv" and result.value is not None:
            base_npv = _decimal_from_value(result.value)
        elif result.name == "irr" and result.value is not None:
            base_irr = _decimal_from_value(result.value)
        elif result.name == "construction_loan_interest" and result.value is not None:
            interest_total = _decimal_from_value(result.value)

    if escalated_cost is None or base_npv is None:
        raise HTTPException(
            status_code=409,
            detail="Scenario is missing baseline finance results for sensitivity analysis.",
        )
    return base_npv, base_irr, escalated_cost, interest_total


def _rebuild_drawdown_summary(
    assumptions: Mapping[str, Any],
    *,
    currency: str,
) -> calculator.FinancingDrawdownSchedule | None:
    """Derive the drawdown summary from stored assumptions."""

    drawdown_config = assumptions.get("drawdown_schedule")
    if not isinstance(drawdown_config, list) or not drawdown_config:
        return None

    schedule_inputs = []
    for entry in drawdown_config:
        if not isinstance(entry, Mapping):
            continue
        schedule_inputs.append(
            {
                "period": str(entry.get("period", "")),
                "equity_draw": _decimal_from_value(entry.get("equity_draw", "0")),
                "debt_draw": _decimal_from_value(entry.get("debt_draw", "0")),
            }
        )
    if not schedule_inputs:
        return None
    return calculator.drawdown_schedule(
        schedule_inputs,
        currency=currency,
    )


def _build_sensitivity_job_context(
    scenario: FinScenario,
    *,
    assumptions: Mapping[str, Any],
    escalated_cost: Decimal,
    drawdown_summary: calculator.FinancingDrawdownSchedule | None,
    loan_config: ConstructionLoanInput | None,
) -> dict[str, Any]:
    """Construct the job context payload for async sensitivity runs."""

    cash_config = assumptions.get("cash_flow") or {}
    cash_flows = cash_config.get("cash_flows") or []
    discount_rate = cash_config.get("discount_rate", "0")
    currency = (
        getattr(scenario.fin_project, "currency", None)
        or assumptions.get("currency")
        or "SGD"
    )
    drawdown_schema = (
        _convert_drawdown_schedule(drawdown_summary)
        if drawdown_summary is not None
        else None
    )

    return {
        "cash_flows": [str(value) for value in cash_flows],
        "discount_rate": str(discount_rate),
        "escalated_cost": str(escalated_cost),
        "currency": currency,
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
            drawdown_schema.model_dump(mode="json") if drawdown_schema else None
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


def _project_uuid_from_scenario(scenario: FinScenario) -> UUID:
    try:
        return _normalise_project_id(scenario.project_id)
    except Exception as exc:  # pragma: no cover - defensive guard
        raise HTTPException(
            status_code=500,
            detail="Scenario project association is invalid",
        ) from exc


def _build_construction_interest_schedule(
    schedule: calculator.FinancingDrawdownSchedule,
    *,
    currency: str,
    base_interest_rate: Decimal | None,
    base_periods_per_year: int | None,
    capitalise_interest: bool,
    facilities: Sequence[Mapping[str, Any]] | None = None,
) -> tuple[ConstructionLoanInterestSchema, dict[str, Any]]:
    rate = base_interest_rate or Decimal("0.04")
    periods = max(1, base_periods_per_year or 12)
    period_rate = rate / Decimal(periods)

    opening_balance = Decimal("0")
    entry_payloads: list[dict[str, str]] = []
    total_interest = Decimal("0")
    for entry in schedule.entries:
        closing_balance = _decimal_from_value(entry.outstanding_debt)
        average_balance = (opening_balance + closing_balance) / Decimal("2")
        interest_accrued = _quantize_currency(average_balance * period_rate) or Decimal(
            "0"
        )
        total_interest += interest_accrued
        entry_payloads.append(
            {
                "period": str(entry.period),
                "opening_balance": str(
                    _quantize_currency(opening_balance) or opening_balance
                ),
                "closing_balance": str(
                    _quantize_currency(closing_balance) or closing_balance
                ),
                "average_balance": str(
                    _quantize_currency(average_balance) or average_balance
                ),
                "interest_accrued": str(interest_accrued),
            }
        )
        opening_balance = closing_balance

    facility_payloads: list[dict[str, str | bool | None]] = []
    upfront_total = Decimal("0")
    exit_total = Decimal("0")
    facility_interest_total = Decimal("0")
    for facility in facilities or []:
        amount = _decimal_from_value(facility.get("amount", "0"))
        if amount is None:
            amount = Decimal("0")
        raw_rate = facility.get("interest_rate")
        facility_rate = _decimal_from_value(raw_rate) if raw_rate is not None else rate
        facility_interest = _quantize_currency(amount * facility_rate) or Decimal("0")
        facility_interest_total += facility_interest
        upfront_pct_raw = facility.get("upfront_fee_pct")
        upfront_pct = (
            _decimal_from_value(upfront_pct_raw)
            if upfront_pct_raw is not None
            else None
        )
        upfront_fee = None
        if upfront_pct is not None:
            upfront_fee = _quantize_currency(amount * (upfront_pct / Decimal("100")))
            if upfront_fee is not None:
                upfront_total += upfront_fee
        exit_pct_raw = facility.get("exit_fee_pct")
        exit_pct = (
            _decimal_from_value(exit_pct_raw) if exit_pct_raw is not None else None
        )
        exit_fee = None
        if exit_pct is not None:
            exit_fee = _quantize_currency(amount * (exit_pct / Decimal("100")))
            if exit_fee is not None:
                exit_total += exit_fee
        facility_payloads.append(
            {
                "name": facility.get("name", "Facility"),
                "amount": str(_quantize_currency(amount) or amount),
                "interest_rate": str(facility_rate),
                "periods_per_year": facility.get("periods_per_year"),
                "capitalised": bool(facility.get("capitalise_interest", True)),
                "total_interest": str(facility_interest),
                "upfront_fee": str(upfront_fee) if upfront_fee is not None else None,
                "exit_fee": str(exit_fee) if exit_fee is not None else None,
                "reserve_months": facility.get("reserve_months"),
                "amortisation_months": facility.get("amortisation_months"),
            }
        )

    total_interest = facility_interest_total or total_interest

    schema_payload = {
        "currency": currency,
        "interest_rate": str(rate),
        "periods_per_year": periods,
        "capitalised": capitalise_interest,
        "total_interest": str(_quantize_currency(total_interest) or total_interest),
        "upfront_fee_total": str(_quantize_currency(upfront_total) or upfront_total),
        "exit_fee_total": str(_quantize_currency(exit_total) or exit_total),
        "facilities": facility_payloads,
        "entries": entry_payloads,
    }
    schema = ConstructionLoanInterestSchema.model_validate(schema_payload)
    return schema, schema_payload


def _decimal_from_value(value: object) -> Decimal:
    """Safely convert arbitrary numeric inputs into :class:`Decimal`."""

    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _json_safe(value: Any) -> Any:
    """Convert nested data into JSON-serialisable Python primitives."""

    return json.loads(json.dumps(value, default=str))


def _format_percentage_label(delta: Decimal) -> str:
    quantized = delta.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{quantized:+.2f}%"


def _decimal_to_string(value: Decimal | None, *, places: int = 4) -> str | None:
    if value is None:
        return None
    quantiser = Decimal(1).scaleb(-places)
    try:
        quantized = value.quantize(quantiser, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        quantized = value
    return format(quantized, "f")


def _build_finance_analytics_summary(
    cash_flows: Sequence[Decimal],
    dscr_entries: Sequence[calculator.DscrEntry],
    drawdown: FinancingDrawdownScheduleSchema | None,
) -> dict[str, Any] | None:
    """Assemble advanced analytics (MOIC, DSCR heat map) for the dashboard."""

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
    for entry in dscr_entries:
        dscr_value = entry.dscr
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
                bucket["periods"].append(str(entry.period))
        dscr_entries_payload.append(
            {
                "period": entry.period,
                "dscr": _decimal_to_string(dscr_value),
                "bucket": bucket_key,
            }
        )

    analytics: dict[str, Any] = {
        "cash_flow_summary": {
            "invested_equity": _decimal_to_string(invested),
            "distributions": _decimal_to_string(distributions),
            "net_cash": _decimal_to_string(distributions - invested),
        }
    }
    if moic_value is not None:
        analytics["moic"] = _decimal_to_string(moic_value)
    if equity_multiple is not None:
        analytics["equity_multiple"] = _decimal_to_string(equity_multiple)
    analytics["dscr_heatmap"] = {
        "buckets": dscr_buckets,
        "entries": dscr_entries_payload,
    }
    if drawdown is not None:
        analytics["drawdown_summary"] = {
            "total_equity": _decimal_to_string(drawdown.total_equity, places=2),
            "total_debt": _decimal_to_string(drawdown.total_debt, places=2),
            "peak_debt_balance": _decimal_to_string(
                drawdown.peak_debt_balance, places=2
            ),
        }
    return analytics


def _evaluate_sensitivity_bands(
    bands: Sequence[SensitivityBandInput],
    *,
    base_npv: Decimal,
    base_irr: Decimal | None,
    escalated_cost: Decimal,
    base_interest_total: Decimal | None,
    currency: str,
) -> tuple[list[FinanceSensitivityOutcomeSchema], list[dict[str, Any]]]:
    """Derive sensitivity scenarios for the supplied parameter bands."""

    results: list[FinanceSensitivityOutcomeSchema] = []
    metadata_entries: list[dict[str, Any]] = []
    for band in bands:
        for label, delta in (
            ("Low", band.low),
            ("Base", band.base),
            ("High", band.high),
        ):
            if delta is None:
                continue
            delta_decimal = _decimal_from_value(delta)
            npv_factor = Decimal("1") + (delta_decimal / Decimal("100"))
            cost_factor = Decimal("1") + (delta_decimal / Decimal("200"))
            irr_value: Decimal | None = None
            if base_irr is not None:
                irr_value = (base_irr + (delta_decimal / Decimal("1000"))).quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_UP
                )
            npv_value = _quantize_currency(base_npv * npv_factor)
            escalated_value = _quantize_currency(escalated_cost * cost_factor)
            interest_value = (
                _quantize_currency(base_interest_total * cost_factor)
                if base_interest_total is not None
                else None
            )
            notes = list(band.notes or [])
            notes.append(
                f"{label} case applies {delta_decimal:+g}% adjustment to {band.parameter}"
            )
            entry = FinanceSensitivityOutcomeSchema(
                parameter=band.parameter,
                scenario=label,
                delta_label=_format_percentage_label(delta_decimal),
                npv=npv_value,
                irr=irr_value,
                escalated_cost=escalated_value,
                total_interest=interest_value,
                notes=notes,
            )
            results.append(entry)
            metadata_entries.append(entry.model_dump(mode="json"))
    return results, metadata_entries


def _default_job_status(scenario_id: int) -> FinanceJobStatusSchema:
    return FinanceJobStatusSchema(
        scenario_id=scenario_id,
        task_id=None,
        status="completed",
        backend=None,
        queued_at=None,
    )


def _parse_datetime_value(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def _scenario_job_statuses(scenario: FinScenario) -> list[FinanceJobStatusSchema]:
    assumptions = scenario.assumptions or {}
    async_jobs = assumptions.get("async_jobs")
    job_entries: list[FinanceJobStatusSchema] = []
    if isinstance(async_jobs, Mapping):
        sensitivity_jobs = async_jobs.get("sensitivity")
        if isinstance(sensitivity_jobs, list):
            for raw in sensitivity_jobs:
                if not isinstance(raw, Mapping):
                    continue
                job_entries.append(
                    FinanceJobStatusSchema(
                        scenario_id=scenario.id,
                        task_id=(
                            str(raw.get("task_id"))
                            if raw.get("task_id") not in (None, "")
                            else None
                        ),
                        status=str(raw.get("status") or "queued"),
                        backend=raw.get("backend"),
                        queued_at=_parse_datetime_value(raw.get("queued_at")),
                    )
                )
    if not job_entries:
        job_entries.append(_default_job_status(scenario.id))
    return job_entries


def _status_payload(scenario: FinScenario) -> dict[str, Any]:
    jobs = _scenario_job_statuses(scenario)
    pending = any(job.status not in {"completed", "failed"} for job in jobs)
    return {
        "scenario_id": scenario.id,
        "pending_jobs": pending,
        "jobs": [job.model_dump(mode="json") for job in jobs],
        "updated_at": scenario.updated_at,
    }


def _record_async_job(
    scenario: FinScenario, job_status: FinanceJobStatusSchema
) -> None:
    """Persist async job bookkeeping inside scenario assumptions."""

    assumptions = dict(scenario.assumptions or {})
    async_jobs = assumptions.get("async_jobs")
    if not isinstance(async_jobs, dict):
        async_jobs = {}
    sensitivity_jobs = async_jobs.get("sensitivity")
    if not isinstance(sensitivity_jobs, list):
        sensitivity_jobs = []
    payload = {
        "task_id": job_status.task_id,
        "status": job_status.status,
        "backend": job_status.backend,
        "queued_at": (
            job_status.queued_at.isoformat()
            if job_status.queued_at is not None
            else None
        ),
    }
    sensitivity_jobs.append(payload)
    async_jobs["sensitivity"] = sensitivity_jobs
    assumptions["async_jobs"] = async_jobs
    scenario.assumptions = assumptions


def _quantize_currency(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


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
    sensitivity_results: list[FinanceSensitivityOutcomeSchema] = []
    construction_loan_config: ConstructionLoanInput | None = None
    raw_construction = assumptions.get("construction_loan")
    if isinstance(raw_construction, Mapping):
        try:
            construction_loan_config = ConstructionLoanInput.model_validate(
                raw_construction
            )
        except Exception:  # pragma: no cover - defensive for legacy records
            construction_loan_config = None
    fin_project = scenario.fin_project
    sensitivity_jobs = _scenario_job_statuses(scenario)
    if fin_project is None:
        raise HTTPException(
            status_code=500, detail="Finance project missing for scenario"
        )

    sensitivity_band_inputs: list[SensitivityBandInput] = []
    raw_bands = assumptions.get("sensitivity_bands")
    if isinstance(raw_bands, list):
        for entry in raw_bands:
            if not isinstance(entry, Mapping):
                continue
            try:
                sensitivity_band_inputs.append(
                    SensitivityBandInput.model_validate(entry)
                )
            except Exception:  # pragma: no cover - tolerate invalid legacy rows
                continue

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

    facility_metadata_map = _build_facility_metadata_map(construction_loan_config)

    capital_stack_inputs: list[Mapping[str, Any]] = []
    if scenario.capital_stack:
        ordered = sorted(
            scenario.capital_stack,
            key=lambda item: (
                item.tranche_order if item.tranche_order is not None else item.id
            ),
        )
        for entry in ordered:
            facility_key = _normalise_facility_key(entry.name)
            facility_meta = facility_metadata_map.get(facility_key)
            metadata = _merge_facility_metadata(entry.metadata, facility_meta)
            capital_stack_inputs.append(
                {
                    "name": entry.name,
                    "source_type": entry.source_type or "other",
                    "amount": entry.amount or Decimal("0"),
                    "rate": entry.rate,
                    "tranche_order": entry.tranche_order,
                    "metadata": metadata,
                }
            )
    elif isinstance(capital_stack_config, list):
        for item in capital_stack_config:
            slice_payload = item.model_dump(mode="json")
            facility_key = _normalise_facility_key(slice_payload.get("name"))
            facility_meta = facility_metadata_map.get(facility_key)
            metadata = _merge_facility_metadata(
                slice_payload.get("metadata"), facility_meta
            )
            capital_stack_inputs.append(
                {
                    "name": slice_payload.get("name", ""),
                    "source_type": slice_payload.get("source_type", "other"),
                    "amount": _decimal_from_value(slice_payload.get("amount", "0")),
                    "rate": (
                        _decimal_from_value(slice_payload.get("rate"))
                        if slice_payload.get("rate") is not None
                        else None
                    ),
                    "tranche_order": slice_payload.get("tranche_order"),
                    "metadata": metadata,
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

    asset_mix_summary_schema: AssetFinancialSummarySchema | None = None
    asset_breakdown_schemas: list[FinanceAssetBreakdownSchema] = []
    if getattr(scenario, "asset_breakdowns", None):
        asset_breakdown_schemas = [
            _serialise_asset_breakdown_model(record)
            for record in sorted(
                scenario.asset_breakdowns,
                key=lambda item: getattr(item, "id", 0) or 0,
            )
        ]
    construction_interest_schema: ConstructionLoanInterestSchema | None = None
    construction_interest_metadata: dict[str, Any] | None = None
    construction_interest_value: Decimal | None = None
    ordered_results = sorted(
        scenario.results, key=lambda item: getattr(item, "id", 0) or 0
    )
    asset_processed = False
    sensitivity_metadata_rows: list[dict[str, Any]] | None = None
    for stored in ordered_results:
        metadata: dict[str, Any] | None = stored.metadata if isinstance(stored.metadata, dict) else None  # type: ignore[assignment,has-type]
        if stored.name == "asset_financials" and metadata and not asset_processed:
            summary_meta = metadata.get("summary")
            if summary_meta:
                try:
                    asset_mix_summary_schema = (
                        AssetFinancialSummarySchema.model_validate(summary_meta)
                    )
                except Exception:  # pragma: no cover - defensive for historical data
                    asset_mix_summary_schema = None
            breakdown_meta = metadata.get("breakdowns")
            if isinstance(breakdown_meta, list) and not asset_breakdown_schemas:
                converted: list[FinanceAssetBreakdownSchema] = []
                for entry in breakdown_meta:
                    if not isinstance(entry, dict):
                        continue
                    try:
                        converted.append(
                            FinanceAssetBreakdownSchema.model_validate(entry)
                        )
                    except Exception:  # pragma: no cover - defensive
                        continue
                asset_breakdown_schemas = converted
            asset_processed = True
            continue

        if stored.name == "sensitivity_analysis" and metadata:
            bands_meta = metadata.get("bands")
            if isinstance(bands_meta, list):
                parsed_entries: list[FinanceSensitivityOutcomeSchema] = []
                cleaned_metadata: list[dict[str, Any]] = []
                for entry in bands_meta:
                    if not isinstance(entry, dict):
                        continue
                    cleaned_metadata.append(entry)
                    if entry.get("parameter") == "__async__":
                        continue
                    try:
                        parsed_entries.append(
                            FinanceSensitivityOutcomeSchema.model_validate(entry)
                        )
                    except Exception:  # pragma: no cover - tolerate legacy rows
                        continue
                if parsed_entries:
                    sensitivity_results = parsed_entries
                if cleaned_metadata:
                    sensitivity_metadata_rows = cleaned_metadata
            continue

        if stored.name == "construction_loan_interest" and metadata:
            try:
                construction_interest_schema = (
                    ConstructionLoanInterestSchema.model_validate(metadata)
                )
                construction_interest_metadata = metadata
                construction_interest_value = stored.value
            except Exception:  # pragma: no cover - defensive for historical data
                construction_interest_schema = None

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

    if asset_mix_summary_schema or asset_breakdown_schemas:
        results.append(
            FinanceResultSchema(
                name="asset_financials",
                value=None,
                metadata={
                    "summary": (
                        asset_mix_summary_schema.model_dump(mode="json")
                        if asset_mix_summary_schema
                        else None
                    ),
                    "breakdowns": [
                        breakdown.model_dump(mode="json")
                        for breakdown in asset_breakdown_schemas
                    ],
                },
            )
        )

    if construction_interest_schema and construction_interest_metadata:
        results.append(
            FinanceResultSchema(
                name="construction_loan_interest",
                value=construction_interest_value,
                unit=fin_project.currency,
                metadata=construction_interest_metadata,
            )
        )
    if sensitivity_metadata_rows:
        results.append(
            FinanceResultSchema(
                name="sensitivity_analysis",
                value=None,
                unit=None,
                metadata={"bands": sensitivity_metadata_rows},
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
        asset_mix_summary=asset_mix_summary_schema,
        asset_breakdowns=asset_breakdown_schemas,
        construction_loan_interest=construction_interest_schema,
        construction_loan=construction_loan_config,
        sensitivity_results=sensitivity_results,
        sensitivity_jobs=sensitivity_jobs,
        sensitivity_bands=sensitivity_band_inputs,
        is_primary=bool(scenario.is_primary),
        is_private=bool(getattr(scenario, "is_private", False)),
        updated_at=scenario.updated_at,
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


def _capital_stack_to_csv(summary: CapitalStackSummarySchema) -> str:
    """Serialise capital stack slices into CSV rows."""

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Name", "Source", "Category", "Amount", "Share", "Rate"])
    for component in summary.slices:
        writer.writerow(
            [
                component.name,
                component.source_type,
                component.category,
                component.amount,
                component.share,
                component.rate or "",
            ]
        )
    return buffer.getvalue()


def _iter_results_csv(scenario: FinScenario, *, currency: str) -> Iterator[bytes]:
    """Yield CSV rows describing a scenario and its persisted results."""

    def _stringify(value: object) -> str:
        return "" if value is None else str(value)

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
        value_repr = _stringify(result.value)
        unit_repr = result.unit or ""
        writer.writerow([result.name, value_repr, unit_repr])
        chunk = _flush_buffer(buffer)
        if chunk:
            yield chunk

        metadata: dict[str, Any] | None = result.metadata if isinstance(result.metadata, dict) else None  # type: ignore[assignment,has-type]
        if result.name == "dscr_timeline" and metadata:
            timeline = metadata.get("entries")
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

        if result.name == "capital_stack" and metadata:
            section_currency = metadata.get("currency") or unit_repr or currency
            writer.writerow([])
            chunk = _flush_buffer(buffer)
            if chunk:
                yield chunk
            writer.writerow(["Capital Stack Summary"])
            chunk = _flush_buffer(buffer)
            if chunk:
                yield chunk

            totals = metadata.get("totals")
            if isinstance(totals, dict):
                total_rows = (
                    ("Total Financing", totals.get("total"), section_currency),
                    ("Equity Financing", totals.get("equity"), section_currency),
                    ("Debt Financing", totals.get("debt"), section_currency),
                    ("Other Financing", totals.get("other"), section_currency),
                )
                for label, raw_value, unit in total_rows:
                    if raw_value is None:
                        continue
                    writer.writerow([label, _stringify(raw_value), unit])
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk

            ratios = metadata.get("ratios")
            if isinstance(ratios, dict):
                ratio_rows = (
                    ("Equity Ratio", ratios.get("equity")),
                    ("Debt Ratio", ratios.get("debt")),
                    ("Other Ratio", ratios.get("other")),
                    ("Loan To Cost", ratios.get("loan_to_cost")),
                    (
                        "Weighted Average Debt Rate",
                        ratios.get("weighted_average_debt_rate"),
                    ),
                )
                for label, raw_value in ratio_rows:
                    if raw_value is None:
                        continue
                    writer.writerow([label, _stringify(raw_value), "ratio"])
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk

            slices = metadata.get("slices")
            if isinstance(slices, list) and slices:
                writer.writerow([])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                writer.writerow(
                    [
                        "Capital Stack Slices",
                    ]
                )
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                writer.writerow(
                    [
                        "Name",
                        "Source Type",
                        "Category",
                        "Amount",
                        "Share",
                        "Rate",
                        "Tranche Order",
                    ]
                )
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                for component in slices:
                    writer.writerow(
                        [
                            component.get("name", ""),
                            component.get("source_type", ""),
                            component.get("category", ""),
                            _stringify(component.get("amount")),
                            _stringify(component.get("share")),
                            _stringify(component.get("rate")),
                            _stringify(component.get("tranche_order")),
                        ]
                    )
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk

        if result.name == "drawdown_schedule" and metadata:
            schedule_currency = metadata.get("currency") or unit_repr or currency
            writer.writerow([])
            chunk = _flush_buffer(buffer)
            if chunk:
                yield chunk
            writer.writerow(["Drawdown Schedule Summary"])
            chunk = _flush_buffer(buffer)
            if chunk:
                yield chunk

            totals = metadata.get("totals")
            if isinstance(totals, dict):
                total_rows = (
                    ("Total Equity Draw", totals.get("equity"), schedule_currency),
                    ("Total Debt Draw", totals.get("debt"), schedule_currency),
                    (
                        "Peak Debt Balance",
                        totals.get("peak_debt_balance"),
                        schedule_currency,
                    ),
                    (
                        "Final Debt Balance",
                        totals.get("final_debt_balance"),
                        schedule_currency,
                    ),
                )
                for label, raw_value, unit in total_rows:
                    if raw_value is None:
                        continue
                    writer.writerow([label, _stringify(raw_value), unit])
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk

            entries = metadata.get("entries")
            if isinstance(entries, list) and entries:
                writer.writerow([])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                writer.writerow(
                    [
                        "Period",
                        "Equity Draw",
                        "Debt Draw",
                        "Total Draw",
                        "Cumulative Equity",
                        "Cumulative Debt",
                        "Outstanding Debt",
                        "Currency",
                    ]
                )
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                for entry in entries:
                    writer.writerow(
                        [
                            entry.get("period", ""),
                            _stringify(entry.get("equity_draw")),
                            _stringify(entry.get("debt_draw")),
                            _stringify(entry.get("total_draw")),
                            _stringify(entry.get("cumulative_equity")),
                            _stringify(entry.get("cumulative_debt")),
                            _stringify(entry.get("outstanding_debt")),
                            schedule_currency,
                        ]
                    )
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk

        if result.name == "asset_financials" and metadata:
            writer.writerow([])
            chunk = _flush_buffer(buffer)
            if chunk:
                yield chunk
            writer.writerow(["Asset Financial Summary"])
            chunk = _flush_buffer(buffer)
            if chunk:
                yield chunk
            summary_meta = metadata.get("summary")
            if isinstance(summary_meta, dict):
                summary_rows = (
                    (
                        "Total Estimated Revenue",
                        summary_meta.get("total_estimated_revenue_sgd"),
                        currency,
                    ),
                    (
                        "Total Estimated Capex",
                        summary_meta.get("total_estimated_capex_sgd"),
                        currency,
                    ),
                    (
                        "Dominant Risk Profile",
                        summary_meta.get("dominant_risk_profile"),
                        "",
                    ),
                )
                for label, value, unit in summary_rows:
                    if value is None:
                        continue
                    writer.writerow([label, _stringify(value), unit])
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk
                notes = summary_meta.get("notes")
                if isinstance(notes, list) and notes:
                    writer.writerow(["Notes"])
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk
                    for note in notes:
                        writer.writerow([_stringify(note)])
                        chunk = _flush_buffer(buffer)
                        if chunk:
                            yield chunk

            breakdowns_meta = metadata.get("breakdowns")
            if isinstance(breakdowns_meta, list) and breakdowns_meta:
                writer.writerow([])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                writer.writerow(
                    [
                        "Asset Type",
                        "Allocation %",
                        "NOI (Annual)",
                        "Capex",
                        "Payback (years)",
                        "Absorption (months)",
                        "Risk Level",
                    ]
                )
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                for entry in breakdowns_meta:
                    if not isinstance(entry, dict):
                        continue
                    writer.writerow(
                        [
                            entry.get("asset_type", ""),
                            _stringify(entry.get("allocation_pct")),
                            _stringify(entry.get("noi_annual_sgd")),
                            _stringify(entry.get("estimated_capex_sgd")),
                            _stringify(entry.get("payback_years")),
                            _stringify(entry.get("absorption_months")),
                            entry.get("risk_level", ""),
                        ]
                    )
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk

        if result.name == "construction_loan_interest" and metadata:
            writer.writerow([])
            chunk = _flush_buffer(buffer)
            if chunk:
                yield chunk
            writer.writerow(["Construction Loan Summary"])
            chunk = _flush_buffer(buffer)
            if chunk:
                yield chunk
            summary_rows = (
                ("Base Interest Rate", metadata.get("interest_rate"), "ratio"),
                ("Total Interest", metadata.get("total_interest"), currency),
                ("Upfront Fees", metadata.get("upfront_fee_total"), currency),
                ("Exit Fees", metadata.get("exit_fee_total"), currency),
            )
            for label, value, unit in summary_rows:
                if value in (None, ""):
                    continue
                writer.writerow([label, value, unit])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk

            facilities = metadata.get("facilities")
            if isinstance(facilities, list) and facilities:
                writer.writerow([])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                writer.writerow(["Construction Loan Facilities"])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                writer.writerow(
                    [
                        "Name",
                        "Amount",
                        "Interest Rate",
                        "Capitalised",
                        "Upfront Fee",
                        "Exit Fee",
                    ]
                )
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                for facility in facilities:
                    if not isinstance(facility, dict):
                        continue
                    writer.writerow(
                        [
                            facility.get("name", ""),
                            facility.get("amount", ""),
                            facility.get("interest_rate", ""),
                            "Y" if facility.get("capitalised") else "N",
                            facility.get("upfront_fee", ""),
                            facility.get("exit_fee", ""),
                        ]
                    )
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk

        if result.name == "sensitivity_analysis" and metadata:
            bands = metadata.get("bands")
            if isinstance(bands, list) and bands:
                writer.writerow([])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                writer.writerow(["Sensitivity Analysis Outcomes"])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                writer.writerow(
                    [
                        "Parameter",
                        "Scenario",
                        "Delta",
                        "NPV",
                        "IRR",
                        "Escalated Cost",
                        "Total Interest",
                        "Notes",
                    ]
                )
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                for entry in bands:
                    if not isinstance(entry, dict):
                        continue
                    if entry.get("parameter") == "__async__":
                        continue
                    notes_value = entry.get("notes")
                    if isinstance(notes_value, list):
                        notes_text = "; ".join(
                            str(item) for item in notes_value if item not in (None, "")
                        )
                    else:
                        notes_text = (
                            "" if notes_value in (None, "", []) else str(notes_value)
                        )
                    writer.writerow(
                        [
                            entry.get("parameter", ""),
                            entry.get("scenario", ""),
                            entry.get("delta_label") or entry.get("deltaLabel") or "",
                            entry.get("npv", ""),
                            entry.get("irr", ""),
                            entry.get("escalated_cost", ""),
                            entry.get("total_interest", ""),
                            notes_text,
                        ]
                    )
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk

    escalated = next(
        (item for item in ordered_results if item.name == "escalated_cost"), None
    )
    cost_meta = None
    if escalated is not None and isinstance(escalated.metadata, dict):  # type: ignore[has-type]
        cost_meta = escalated.metadata.get("cost_index")  # type: ignore[union-attr,has-type]

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
    project_uuid = _normalise_project_id(payload.project_id)
    await _ensure_project_owner(session, project_uuid, identity)
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

        facility_metadata_map = _build_facility_metadata_map(
            payload.scenario.construction_loan
        )
        capital_stack_summary_schema: CapitalStackSummarySchema | None = None
        capital_stack_result_metadata: dict[str, object] | None = None
        if payload.scenario.capital_stack:
            stack_inputs: list[dict[str, Any]] = []
            for slice_input in payload.scenario.capital_stack:
                facility_key = _normalise_facility_key(slice_input.name)
                facility_meta = facility_metadata_map.get(facility_key)
                metadata = _merge_facility_metadata(slice_input.metadata, facility_meta)
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
            capital_stack_summary_schema = _convert_capital_stack_summary(stack_summary)

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
                        metadata=_json_safe(combined_metadata),
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
                        "metadata": _json_safe(combined_metadata),
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
            asset_breakdown_models = _build_asset_breakdown_records(
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
            ) = _build_construction_interest_schedule(
                schedule_summary,
                currency=payload.scenario.currency,
                base_interest_rate=loan_config.interest_rate,
                base_periods_per_year=loan_config.periods_per_year,
                capitalise_interest=loan_config.capitalise_interest,
                facilities=facility_payloads,
            )

        base_interest_total = (
            _decimal_from_value(construction_interest_schema.total_interest)
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
                ) = _evaluate_sensitivity_bands(
                    sensitivity_bands,
                    base_npv=npv_rounded,
                    base_irr=irr_value,
                    escalated_cost=escalated_cost,
                    base_interest_total=base_interest_total,
                    currency=payload.scenario.currency,
                )
                sensitivity_jobs = [_default_job_status(scenario.id)]
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
                _record_async_job(scenario, job_status)

        if not sensitivity_jobs:
            sensitivity_jobs = [_default_job_status(scenario.id)]

        cash_flow_values: list[Decimal] = []
        for raw in cash_inputs.cash_flows:
            try:
                cash_flow_values.append(_decimal_from_value(raw))
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
                    "cost_index": _json_safe(cost_provenance.model_dump(mode="json")),
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
                    metadata=_json_safe(asset_financial_metadata),
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
                    metadata=_json_safe({"bands": sensitivity_metadata}),
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
                    value=_decimal_from_value(
                        construction_interest_schema.total_interest
                        if construction_interest_schema.total_interest is not None
                        else "0"
                    ),
                    unit=payload.scenario.currency,
                    metadata=_json_safe(construction_interest_metadata),
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
                    metadata=_json_safe(analytics_metadata),
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


@router.get("/scenarios", response_model=list[FinanceFeasibilityResponse])
async def list_finance_scenarios(
    project_id: str | int | UUID | None = Query(None),
    fin_project_id: int | None = Query(None),
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_viewer),
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
            selectinload(FinScenario.results),
            selectinload(FinScenario.asset_breakdowns),
        )
        .order_by(FinScenario.id)
    )
    checked_projects: set[UUID] = set()

    if fin_project_id is not None:
        fin_project = await session.get(FinProject, fin_project_id)
        if fin_project is None:
            raise HTTPException(status_code=404, detail="Finance project not found")
        fin_project_uuid = _normalise_project_id(fin_project.project_id)
        await _ensure_project_owner(session, fin_project_uuid, identity)
        checked_projects.add(fin_project_uuid)
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

        await _ensure_project_owner(session, normalised, identity)
        checked_projects.add(normalised)
        stmt = stmt.where(FinScenario.project_id == str(normalised))

    result = await session.execute(stmt)
    scenarios = list(result.scalars().all())

    summaries: list[FinanceFeasibilityResponse] = []
    for scenario in scenarios:
        project_uuid = _project_uuid_from_scenario(scenario)
        if project_uuid not in checked_projects:
            await _ensure_project_owner(session, project_uuid, identity)
            checked_projects.add(project_uuid)
        summaries.append(await _summarise_persisted_scenario(scenario, session=session))

    return summaries


@router.patch(
    "/scenarios/{scenario_id}",
    response_model=FinanceFeasibilityResponse,
)
async def update_finance_scenario(
    scenario_id: int,
    payload: FinanceScenarioUpdatePayload,
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_reviewer),
) -> FinanceFeasibilityResponse:
    """Update mutable fields on a persisted finance scenario."""

    base_stmt = (
        select(FinScenario)
        .where(FinScenario.id == scenario_id)
        .options(
            selectinload(FinScenario.fin_project),
            selectinload(FinScenario.capital_stack),
            selectinload(FinScenario.results),
            selectinload(FinScenario.asset_breakdowns),
        )
    )
    scenario = (await session.execute(base_stmt)).scalars().first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Finance scenario not found")

    project_uuid = _project_uuid_from_scenario(scenario)
    await _ensure_project_owner(session, project_uuid, identity)

    updated = False
    if payload.scenario_name is not None:
        name = payload.scenario_name.strip()
        if name and name != scenario.name:
            scenario.name = name
            updated = True
    if payload.description is not None and payload.description != scenario.description:
        scenario.description = payload.description
        updated = True
    if payload.is_primary is not None and payload.is_primary != scenario.is_primary:
        scenario.is_primary = payload.is_primary
        updated = True
        if payload.is_primary:
            await session.execute(
                update(FinScenario)
                .where(
                    FinScenario.fin_project_id == scenario.fin_project_id,
                    FinScenario.id != scenario.id,
                )
                .values(is_primary=False)
            )

    if updated:
        await session.commit()
        scenario = (await session.execute(base_stmt)).scalars().first()
        if scenario is None:
            raise HTTPException(status_code=404, detail="Finance scenario not found")
    return await _summarise_persisted_scenario(scenario, session=session)


@router.delete("/scenarios/{scenario_id}", status_code=204)
async def delete_finance_scenario(
    scenario_id: int,
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_reviewer),
) -> Response:
    """Delete a persisted finance scenario and associated modelling data."""

    stmt = (
        select(FinScenario)
        .where(FinScenario.id == scenario_id)
        .options(selectinload(FinScenario.fin_project))
    )
    scenario = (await session.execute(stmt)).scalars().first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Finance scenario not found")

    project_uuid = _project_uuid_from_scenario(scenario)
    await _ensure_project_owner(session, project_uuid, identity)
    await session.delete(scenario)
    await session.commit()

    log_event(
        logger,
        "finance_feasibility_deleted",
        scenario_id=scenario_id,
        project_id=str(project_uuid),
    )
    return Response(status_code=204)


@router.get("/jobs", response_model=list[FinanceJobStatusSchema])
async def list_finance_jobs(
    scenario_id: int = Query(..., ge=1),
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_viewer),
) -> list[FinanceJobStatusSchema]:
    """Return pending finance job metadata for a persisted scenario."""

    stmt = (
        select(FinScenario)
        .where(FinScenario.id == scenario_id)
        .options(
            selectinload(FinScenario.fin_project),
            selectinload(FinScenario.asset_breakdowns),
        )
    )
    scenario = (await session.execute(stmt)).scalars().first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Finance scenario not found")
    await _ensure_project_owner(
        session, _project_uuid_from_scenario(scenario), identity
    )
    return _scenario_job_statuses(scenario)


async def _load_scenario_for_status(
    session: AsyncSession,
    scenario_id: int,
    identity: RequestIdentity,
) -> FinScenario:
    stmt = (
        select(FinScenario)
        .where(FinScenario.id == scenario_id)
        .options(selectinload(FinScenario.fin_project))
    )
    scenario = (await session.execute(stmt)).scalars().first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Finance scenario not found")
    await _ensure_project_owner(
        session, _project_uuid_from_scenario(scenario), identity
    )
    return scenario


@router.get("/scenarios/{scenario_id}/status")
async def finance_scenario_status(
    scenario_id: int,
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_viewer),
) -> dict[str, Any]:
    """Expose job status metadata for polling clients."""

    scenario = await _load_scenario_for_status(session, scenario_id, identity)
    return _status_payload(scenario)


@router.get("/scenarios/{scenario_id}/status-stream")
async def finance_scenario_status_stream(
    scenario_id: int,
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_reviewer),
) -> StreamingResponse:
    """Server-sent events feed mirroring :func:`finance_scenario_status`."""

    scenario = await _load_scenario_for_status(session, scenario_id, identity)
    payload = _status_payload(scenario)

    async def _event_stream() -> AsyncIterator[bytes]:
        data = json.dumps(payload, default=str)
        yield f"data: {data}\n\n".encode("utf-8")

    return StreamingResponse(_event_stream(), media_type="text/event-stream")


@router.patch(
    "/scenarios/{scenario_id}/construction-loan",
    response_model=FinanceFeasibilityResponse,
)
async def update_construction_loan(
    scenario_id: int,
    payload: ConstructionLoanUpdatePayload,
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_reviewer),
) -> FinanceFeasibilityResponse:
    """Update a persisted scenario's construction loan configuration."""

    stmt = (
        select(FinScenario)
        .where(FinScenario.id == scenario_id)
        .options(
            selectinload(FinScenario.fin_project),
            selectinload(FinScenario.capital_stack),
            selectinload(FinScenario.results),
            selectinload(FinScenario.asset_breakdowns),
        )
    )
    scenario = (await session.execute(stmt)).scalars().first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Finance scenario not found")
    await _ensure_project_owner(
        session, _project_uuid_from_scenario(scenario), identity
    )

    if payload.construction_loan is None:
        raise HTTPException(status_code=400, detail="construction_loan is required")

    assumptions = dict(scenario.assumptions or {})
    assumptions["construction_loan"] = payload.construction_loan.model_dump(mode="json")
    scenario.assumptions = assumptions

    drawdown_data = assumptions.get("drawdown_schedule")
    schedule_summary = None
    if isinstance(drawdown_data, list) and drawdown_data:
        schedule_inputs = []
        for entry in drawdown_data:
            if not isinstance(entry, Mapping):
                continue
            schedule_inputs.append(
                {
                    "period": entry.get("period", ""),
                    "equity_draw": _decimal_from_value(entry.get("equity_draw", "0")),
                    "debt_draw": _decimal_from_value(entry.get("debt_draw", "0")),
                }
            )
        if schedule_inputs:
            schedule_summary = calculator.drawdown_schedule(
                schedule_inputs,
                currency=assumptions.get("currency")
                or getattr(scenario.fin_project, "currency", "SGD"),
            )

    construction_interest_schema = None
    construction_interest_metadata = None
    if schedule_summary is not None:
        facility_payloads = (
            [
                facility.model_dump(mode="json")
                for facility in payload.construction_loan.facilities
            ]
            if payload.construction_loan.facilities
            else None
        )
        (
            construction_interest_schema,
            construction_interest_metadata,
        ) = _build_construction_interest_schedule(
            schedule_summary,
            currency=schedule_summary.currency,
            base_interest_rate=payload.construction_loan.interest_rate,
            base_periods_per_year=payload.construction_loan.periods_per_year,
            capitalise_interest=payload.construction_loan.capitalise_interest,
            facilities=facility_payloads,
        )

    if construction_interest_schema and construction_interest_metadata:
        interest_value = _decimal_from_value(
            construction_interest_schema.total_interest
            if construction_interest_schema.total_interest is not None
            else "0"
        )
        existing_result = None
        for stored in scenario.results:
            if stored.name == "construction_loan_interest":
                existing_result = stored
                break
        if existing_result is None:
            existing_result = FinResult(
                project_id=str(_project_uuid_from_scenario(scenario)),
                scenario=scenario,
                name="construction_loan_interest",
                value=interest_value,
                unit=schedule_summary.currency,
                metadata=_json_safe(construction_interest_metadata),
            )
            session.add(existing_result)
        else:
            existing_result.value = interest_value
            existing_result.unit = schedule_summary.currency
            existing_result.metadata = _json_safe(construction_interest_metadata)

    await session.commit()
    scenario = (await session.execute(stmt)).scalars().first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Finance scenario not found")
    return await _summarise_persisted_scenario(scenario, session=session)


@router.post(
    "/scenarios/{scenario_id}/sensitivity",
    response_model=FinanceFeasibilityResponse,
)
async def rerun_finance_sensitivity(
    scenario_id: int,
    payload: FinanceSensitivityRunPayload,
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_reviewer),
) -> FinanceFeasibilityResponse:
    """Recompute or enqueue sensitivity analysis for an existing scenario."""

    base_stmt = (
        select(FinScenario)
        .where(FinScenario.id == scenario_id)
        .options(
            selectinload(FinScenario.fin_project),
            selectinload(FinScenario.capital_stack),
            selectinload(FinScenario.results),
            selectinload(FinScenario.asset_breakdowns),
        )
    )
    scenario = (await session.execute(base_stmt)).scalars().first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Finance scenario not found")

    project_uuid = _project_uuid_from_scenario(scenario)
    await _ensure_project_owner(session, project_uuid, identity)

    try:
        base_npv, base_irr, escalated_cost, base_interest_total = _base_finance_metrics(
            scenario
        )
    except HTTPException:
        raise

    currency = (
        getattr(scenario.fin_project, "currency", None)
        or (scenario.assumptions or {}).get("currency")
        or "SGD"
    )

    assumptions = dict(scenario.assumptions or {})
    assumptions["sensitivity_bands"] = [
        band.model_dump(mode="json") for band in payload.sensitivity_bands
    ]
    scenario.assumptions = assumptions

    drawdown_summary = _rebuild_drawdown_summary(assumptions, currency=currency)
    raw_loan = assumptions.get("construction_loan")
    loan_config: ConstructionLoanInput | None = None
    if isinstance(raw_loan, Mapping):
        try:
            loan_config = ConstructionLoanInput.model_validate(raw_loan)
        except Exception:  # pragma: no cover - tolerate legacy payloads
            loan_config = None

    sync_threshold = max(1, settings.FINANCE_SENSITIVITY_MAX_SYNC_BANDS)
    if len(payload.sensitivity_bands) <= sync_threshold:
        (
            sensitivity_results,
            sensitivity_metadata,
        ) = _evaluate_sensitivity_bands(
            payload.sensitivity_bands,
            base_npv=base_npv,
            base_irr=base_irr,
            escalated_cost=escalated_cost,
            base_interest_total=base_interest_total,
            currency=currency,
        )
        _store_sensitivity_metadata(session, scenario, sensitivity_metadata or [])
        _clear_sensitivity_jobs(scenario)
        await session.commit()
    else:
        job_context = _build_sensitivity_job_context(
            scenario,
            assumptions=assumptions,
            escalated_cost=escalated_cost,
            drawdown_summary=drawdown_summary,
            loan_config=loan_config,
        )
        dispatch: JobDispatch = await job_queue.enqueue(
            "finance.sensitivity",
            scenario.id,
            bands=[band.model_dump(mode="json") for band in payload.sensitivity_bands],
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
        _record_async_job(scenario, job_status)
        _store_sensitivity_metadata(
            session,
            scenario,
            [
                {
                    "parameter": "__async__",
                    "status": dispatch.status,
                    "task_id": dispatch.task_id,
                    "queue": dispatch.queue,
                }
            ],
        )
        await session.commit()

    scenario = (await session.execute(base_stmt)).scalars().first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Finance scenario not found")
    return await _summarise_persisted_scenario(scenario, session=session)


@router.get("/export")
async def export_finance_scenario(
    scenario_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_reviewer),
) -> StreamingResponse:
    """Stream a ZIP bundle with CSV/JSON finance scenario artefacts."""

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
        await _ensure_project_owner(
            session, _project_uuid_from_scenario(scenario), identity
        )

        assumptions = scenario.assumptions or {}
        currency = assumptions.get("currency") or getattr(
            scenario.fin_project, "currency", "USD"
        )

        summary = await _summarise_persisted_scenario(scenario, session=session)
        summary_payload = summary.model_dump(mode="json")

        csv_buffer = io.BytesIO()
        for chunk in _iter_results_csv(scenario, currency=str(currency)):
            csv_buffer.write(chunk)
        csv_bytes = csv_buffer.getvalue()

        archive_buffer = io.BytesIO()
        with zipfile.ZipFile(archive_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("scenario.csv", csv_bytes)
            archive.writestr(
                "scenario.json",
                json.dumps(summary_payload, indent=2, sort_keys=True),
            )
            if summary.capital_stack is not None:
                archive.writestr(
                    "capital_stack.csv", _capital_stack_to_csv(summary.capital_stack)
                )
            if summary.sensitivity_results:
                archive.writestr(
                    "sensitivity.json",
                    json.dumps(summary.sensitivity_results, indent=2, default=str),
                )

        archive_buffer.seek(0)
        archive_bytes = archive_buffer.getvalue()
        filename = f"finance_scenario_{scenario.id}.zip"
        response = StreamingResponse(
            iter([archive_bytes]),
            media_type="application/zip",
        )
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'

        log_event(logger, "finance_feasibility_export", scenario_id=scenario.id)
    finally:
        duration_ms = (perf_counter() - start_time) * 1000
        metrics.FINANCE_EXPORT_DURATION_MS.observe(duration_ms)

    assert response is not None
    return response


__all__ = ["router"]
