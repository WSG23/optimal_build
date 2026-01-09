"""Shared helpers and Pydantic models for finance API endpoints.

This module centralizes:
- Pydantic request/response models used across finance_scenarios, finance_jobs, finance_export
- Pure helper functions (no FastAPI Depends or HTTP concerns)
- Type converters and formatters
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, field_validator

from app.models.finance import FinAssetBreakdown, FinResult, FinScenario
from app.models.rkp import RefCostIndex
from app.schemas.finance import (
    CapitalStackSliceSchema,
    CapitalStackSummarySchema,
    ConstructionLoanInput,
    CostIndexSnapshot,
    DscrEntrySchema,
    FinanceAssetBreakdownSchema,
    FinanceJobStatusSchema,
    FinancingDrawdownEntrySchema,
    FinancingDrawdownScheduleSchema,
    SensitivityBandInput,
)
from app.services.finance import calculator
from app.utils import metrics
from app.utils.logging import get_logger, log_event

from app.api.deps import RequestIdentity

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class ConstructionLoanUpdatePayload(BaseModel):
    """Payload for updating construction loan configuration."""

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


# ---------------------------------------------------------------------------
# Project ID Normalisation
# ---------------------------------------------------------------------------


def normalise_project_id(project_id: str | int | UUID) -> UUID:
    """Convert the externally supplied project identifier into a UUID.

    For integer IDs (like 191), creates a zero-padded UUID string format:
    191 -> 00000000-0000-0000-0000-000000000191

    This matches the convention used in the database for simple integer IDs.
    """
    if isinstance(project_id, UUID):
        return project_id

    # Helper to create zero-padded UUID from integer
    def int_to_padded_uuid(val: int) -> UUID:
        if val < 0:
            raise HTTPException(
                status_code=422, detail="project_id must be non-negative"
            )
        # Create zero-padded UUID: 00000000-0000-0000-0000-XXXXXXXXXXXX
        # where X is the zero-padded decimal representation
        padded = str(val).zfill(12)
        uuid_str = f"00000000-0000-0000-0000-{padded}"
        return UUID(uuid_str)

    if isinstance(project_id, int):
        return int_to_padded_uuid(project_id)

    # For strings, first try to parse as integer
    try:
        int_val = int(project_id)
        return int_to_padded_uuid(int_val)
    except ValueError:
        pass  # Not an integer string, try as UUID

    try:
        return UUID(project_id)
    except (AttributeError, TypeError, ValueError) as e:
        raise HTTPException(
            status_code=422, detail="project_id must be a valid UUID"
        ) from e


def project_uuid_from_scenario(scenario: FinScenario) -> UUID:
    """Extract and normalise the project UUID from a scenario."""

    try:
        return normalise_project_id(scenario.project_id)
    except Exception as exc:  # pragma: no cover - defensive guard
        raise HTTPException(
            status_code=500,
            detail="Scenario project association is invalid",
        ) from exc


# ---------------------------------------------------------------------------
# Privacy / Authorisation Helpers
# ---------------------------------------------------------------------------


def raise_finance_privacy_error(
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


# ---------------------------------------------------------------------------
# Decimal / Value Converters
# ---------------------------------------------------------------------------


def decimal_from_value(value: object) -> Decimal:
    """Safely convert arbitrary numeric inputs into :class:`Decimal`."""

    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def decimal_to_string(value: Decimal | None, places: int | None = None) -> str | None:
    """Format a Decimal to a string with optional rounding."""

    if value is None:
        return None
    if places is not None:
        quant = Decimal(1).scaleb(-places)
        try:
            value = value.quantize(quant, rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError):
            pass
    return format(value, "f")


def quantize_currency(value: Decimal | None) -> Decimal | None:
    """Round a Decimal to 2 decimal places for currency display."""

    if value is None:
        return None
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def json_safe(value: Any) -> Any:
    """Convert nested data into JSON-serialisable Python primitives."""

    return json.loads(json.dumps(value, default=str))


def format_percentage_label(delta: Decimal) -> str:
    """Format a percentage delta as a signed label."""

    quantized = delta.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{quantized:+.2f}%"


# ---------------------------------------------------------------------------
# Facility / Loan Helpers
# ---------------------------------------------------------------------------


def normalise_facility_key(value: str | None) -> str | None:
    """Normalise a facility name for dictionary lookups."""

    if value is None:
        return None
    trimmed = value.strip().lower()
    return trimmed or None


def facility_metadata_from_input(
    facility: Any,
) -> dict[str, str | bool | int]:
    """Extract metadata from a facility input for storage."""

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


def build_facility_metadata_map(
    loan_config: Any | None,
) -> dict[str, dict[str, str | bool | int]]:
    """Index construction loan facilities by a normalised name for lookups."""

    metadata_map: dict[str, dict[str, str | bool | int]] = {}
    if not loan_config or not loan_config.facilities:
        return metadata_map

    for idx, facility in enumerate(loan_config.facilities):
        key = normalise_facility_key(facility.name) or f"facility_{idx}"
        meta = facility_metadata_from_input(facility)
        if meta:
            metadata_map[key] = meta
    return metadata_map


def merge_facility_metadata(
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


# ---------------------------------------------------------------------------
# Cost Index Helpers
# ---------------------------------------------------------------------------


def build_cost_index_snapshot(index: RefCostIndex | None) -> CostIndexSnapshot | None:
    """Convert a :class:`RefCostIndex` ORM instance into a schema snapshot."""

    if index is None:
        return None
    return CostIndexSnapshot(
        period=str(index.period),
        value=decimal_from_value(index.value),
        unit=index.unit,
        source=index.source,
        provider=index.provider,
        methodology=index.methodology,
    )


def compute_scalar(
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


# ---------------------------------------------------------------------------
# DSCR Helpers
# ---------------------------------------------------------------------------


def convert_dscr_entry(entry: calculator.DscrEntry) -> DscrEntrySchema:
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


# ---------------------------------------------------------------------------
# Capital Stack Helpers
# ---------------------------------------------------------------------------


def convert_capital_stack_summary(
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
            metadata=component.metadata,
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


# ---------------------------------------------------------------------------
# Drawdown Schedule Helpers
# ---------------------------------------------------------------------------


def convert_drawdown_schedule(
    schedule: calculator.FinancingDrawdownSchedule,
) -> FinancingDrawdownScheduleSchema:
    """Convert a calculator schedule into the API schema representation."""

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
        total_equity=schedule.total_equity,
        total_debt=schedule.total_debt,
        peak_debt_balance=schedule.peak_debt_balance,
        final_debt_balance=schedule.final_debt_balance,
        entries=entries,
    )


def rebuild_drawdown_summary(
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
                "equity_draw": decimal_from_value(entry.get("equity_draw", "0")),
                "debt_draw": decimal_from_value(entry.get("debt_draw", "0")),
            }
        )
    if not schedule_inputs:
        return None
    return calculator.drawdown_schedule(
        schedule_inputs,
        currency=currency,
    )


# ---------------------------------------------------------------------------
# Asset Breakdown Helpers
# ---------------------------------------------------------------------------


def serialise_asset_breakdown_model(
    record: FinAssetBreakdown,
) -> FinanceAssetBreakdownSchema:
    """Convert an ORM asset breakdown record into the API schema."""

    return FinanceAssetBreakdownSchema(
        asset_type=record.asset_type,
        allocation_pct=decimal_to_string(record.allocation_pct, places=4),
        nia_sqm=decimal_to_string(record.nia_sqm, places=2),
        rent_psm_month=decimal_to_string(record.rent_psm_month, places=2),
        gross_rent_annual_sgd=decimal_to_string(record.annual_revenue_sgd, places=2),
        annual_revenue_sgd=decimal_to_string(record.annual_revenue_sgd, places=2),
        vacancy_loss_sgd=None,
        effective_gross_income_sgd=None,
        operating_expenses_sgd=None,
        annual_opex_sgd=None,
        noi_annual_sgd=decimal_to_string(record.annual_noi_sgd, places=2),
        annual_noi_sgd=decimal_to_string(record.annual_noi_sgd, places=2),
        estimated_capex_sgd=decimal_to_string(record.estimated_capex_sgd, places=2),
        capex_sgd=decimal_to_string(record.estimated_capex_sgd, places=2),
        payback_years=decimal_to_string(record.payback_years, places=2),
        absorption_months=decimal_to_string(record.absorption_months, places=1),
        stabilised_yield_pct=decimal_to_string(record.stabilised_yield_pct, places=4),
        risk_level=record.risk_level,
        risk_priority=record.risk_priority,
        heritage_premium_pct=None,
        notes=list(record.notes_json or []),
    )


def build_asset_breakdown_records(
    project_uuid: UUID,
    scenario: FinScenario,
    breakdowns: Any | Sequence[Any] | None,
) -> list[FinAssetBreakdown]:
    """Convert calculated asset breakdowns into ORM rows for persistence."""

    from app.services.finance.asset_models import AssetFinanceBreakdown

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


# ---------------------------------------------------------------------------
# Job Status Helpers
# ---------------------------------------------------------------------------


def parse_datetime_value(value: object) -> datetime | None:
    """Parse a datetime from various input formats."""

    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def default_job_status(scenario_id: int) -> FinanceJobStatusSchema:
    """Return a default completed job status for a scenario."""

    return FinanceJobStatusSchema(
        scenario_id=scenario_id,
        task_id=None,
        status="completed",
        backend=None,
        queued_at=None,
    )


def scenario_job_statuses(scenario: FinScenario) -> list[FinanceJobStatusSchema]:
    """Extract job status entries from scenario assumptions."""

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
                        queued_at=parse_datetime_value(raw.get("queued_at")),
                    )
                )
    if not job_entries:
        job_entries.append(default_job_status(scenario.id))
    return job_entries


def has_pending_sensitivity_job(scenario: FinScenario) -> bool:
    """Check if a scenario has any pending sensitivity jobs."""

    jobs = scenario_job_statuses(scenario)
    return any(job.status not in {"completed", "failed"} for job in jobs)


def status_payload(scenario: FinScenario) -> dict[str, Any]:
    """Build a status payload for a scenario."""

    jobs = scenario_job_statuses(scenario)
    pending = any(job.status not in {"completed", "failed"} for job in jobs)
    return {
        "scenario_id": scenario.id,
        "pending_jobs": pending,
        "jobs": [job.model_dump(mode="json") for job in jobs],
        "updated_at": scenario.updated_at,
    }


def record_async_job(scenario: FinScenario, job_status: FinanceJobStatusSchema) -> None:
    """Persist async job bookkeeping inside scenario assumptions."""

    from app.core.config import settings

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
    max_entries = max(1, settings.FINANCE_SENSITIVITY_MAX_PENDING_JOBS)
    while len(sensitivity_jobs) > max_entries:
        sensitivity_jobs.pop(0)
    async_jobs["sensitivity"] = sensitivity_jobs
    assumptions["async_jobs"] = async_jobs
    scenario.assumptions = assumptions


def clear_sensitivity_jobs(scenario: FinScenario) -> None:
    """Remove tracked sensitivity jobs from scenario assumptions."""

    assumptions = dict(scenario.assumptions or {})
    async_jobs = assumptions.get("async_jobs")
    if isinstance(async_jobs, dict) and async_jobs.pop("sensitivity", None) is not None:
        if async_jobs:
            assumptions["async_jobs"] = async_jobs
        else:
            assumptions.pop("async_jobs", None)
        scenario.assumptions = assumptions


def store_sensitivity_metadata(
    session: Any,
    scenario: FinScenario,
    entries: Sequence[Mapping[str, Any] | Any],
) -> None:
    """Persist sensitivity metadata on the scenario's results."""

    from app.schemas.finance import FinanceSensitivityOutcomeSchema

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
            serialised.append(json_safe(entry))

    from sqlalchemy.orm.attributes import flag_modified

    existing_result.metadata = {"bands": serialised}
    flag_modified(existing_result, "metadata_json")


def band_payloads_equal(
    existing: Sequence[Mapping[str, Any]] | None,
    new_payloads: Sequence[Mapping[str, Any]],
) -> bool:
    """Check if two sets of sensitivity band payloads are equivalent."""

    if existing is None:
        return False

    def _normalise(entries: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        cleaned: list[dict[str, Any]] = []
        for entry in entries:
            if not isinstance(entry, Mapping):
                continue
            snapshot = json.loads(json.dumps(entry, default=str, sort_keys=True))
            cleaned.append(snapshot)
        cleaned.sort(key=lambda item: json.dumps(item, sort_keys=True))
        return cleaned

    return _normalise(existing) == _normalise(new_payloads)


__all__ = [
    # Pydantic models
    "ConstructionLoanUpdatePayload",
    "FinanceScenarioUpdatePayload",
    "FinanceSensitivityRunPayload",
    # Project ID
    "normalise_project_id",
    "project_uuid_from_scenario",
    # Privacy
    "raise_finance_privacy_error",
    # Decimal/value converters
    "decimal_from_value",
    "decimal_to_string",
    "quantize_currency",
    "json_safe",
    "format_percentage_label",
    # Facility helpers
    "normalise_facility_key",
    "facility_metadata_from_input",
    "build_facility_metadata_map",
    "merge_facility_metadata",
    # Cost index helpers
    "build_cost_index_snapshot",
    "compute_scalar",
    # DSCR helpers
    "convert_dscr_entry",
    # Capital stack helpers
    "convert_capital_stack_summary",
    # Drawdown helpers
    "convert_drawdown_schedule",
    "rebuild_drawdown_summary",
    # Asset breakdown helpers
    "serialise_asset_breakdown_model",
    "build_asset_breakdown_records",
    # Job status helpers
    "parse_datetime_value",
    "default_job_status",
    "scenario_job_statuses",
    "has_pending_sensitivity_job",
    "status_payload",
    "record_async_job",
    "clear_sensitivity_jobs",
    "store_sensitivity_metadata",
    "band_payloads_equal",
]
