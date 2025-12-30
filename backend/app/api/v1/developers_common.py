"""Shared Pydantic models and utilities for developer workspace API."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Mapping, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.services.preview_jobs import PreviewJobStatus


# =============================================================================
# Helper Functions
# =============================================================================


def _to_mapping(value: Any) -> Mapping[str, Any] | None:
    """Convert various types to a Mapping."""
    if value is None:
        return None
    if isinstance(value, Mapping):
        return value
    if hasattr(value, "model_dump"):
        try:
            return value.model_dump()
        except Exception:  # pragma: no cover - defensive
            return None
    if hasattr(value, "dict"):
        try:
            return value.dict()
        except Exception:  # pragma: no cover - defensive
            return None
    return None


def _coerce_float(value: Any) -> Optional[float]:
    """Attempt to coerce arbitrary values into floats."""
    if value is None:
        return None
    if isinstance(value, float):
        return value
    if isinstance(value, (int, Decimal)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _round_optional(value: Optional[float]) -> Optional[float]:
    """Round float to 2 decimal places, or return None."""
    return None if value is None else round(value, 2)


def _decimal_or_none(value: Any) -> Decimal | None:
    """Convert value to Decimal or return None."""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


SQM_PER_SQFT = Decimal("0.09290304")
SQFT_PER_SQM = Decimal("10.7639104")


def _convert_area_to_sqm(value: Decimal | None, *, from_units: str) -> Decimal | None:
    """Convert area to square meters."""
    if value is None:
        return None
    if from_units.lower() == "sqft":
        return (value * SQM_PER_SQFT).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return value


def _convert_rent_to_psm(value: Decimal | None, *, rent_metric: str) -> Decimal | None:
    """Convert rent to per-square-meter."""
    if value is None:
        return None
    metric = rent_metric.lower()
    if metric in {"psf_month", "psf"}:
        return (value * SQFT_PER_SQM).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return value


def _normalise_scenario_param(value: Optional[str]) -> Optional[str]:
    """Normalise scenario parameter to lowercase slug or None."""
    if value is None:
        return None
    slug = value.strip().lower()
    if not slug or slug == "all":
        return None
    return slug


def _format_scenario_label(scenario: Optional[str]) -> str:
    """Format scenario key as human-readable label."""
    if not scenario:
        return "All scenarios"
    return scenario.replace("_", " ").title()


# =============================================================================
# Shared Pydantic Models
# =============================================================================


class DeveloperBuildEnvelope(BaseModel):
    """Summary of zoning envelope and buildability heuristics."""

    zone_code: Optional[str] = None
    zone_description: Optional[str] = None
    site_area_sqm: Optional[float] = None
    allowable_plot_ratio: Optional[float] = None
    max_buildable_gfa_sqm: Optional[float] = None
    current_gfa_sqm: Optional[float] = None
    additional_potential_gfa_sqm: Optional[float] = None
    building_height_limit_m: Optional[float] = None
    site_coverage_pct: Optional[float] = None
    assumptions: list[str] = Field(default_factory=list)
    source_reference: Optional[str] = None  # Data source attribution


class DeveloperMassingLayer(BaseModel):
    """Stubbed massing data for 3D preview integration."""

    asset_type: str
    allocation_pct: float
    gfa_sqm: float | None = None
    nia_sqm: float | None = None
    estimated_height_m: float | None = None
    color: str


class DeveloperColorLegendEntry(BaseModel):
    """Colour legend entry for the preview stub."""

    asset_type: str
    label: str
    color: str
    description: str | None = None


class PreviewJobSchema(BaseModel):
    """Preview generation job status representation."""

    id: UUID
    property_id: UUID
    scenario: str
    status: str
    preview_url: str | None = None
    metadata_url: str | None = None
    thumbnail_url: str | None = None
    asset_version: str | None = None
    requested_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    message: str | None = None
    geometry_detail_level: str | None = None


class DeveloperConstraintViolation(BaseModel):
    """Constraint outcome generated by the optimiser."""

    constraint_type: str
    severity: str
    message: str
    asset_type: str | None = None


class DeveloperAssetOptimization(BaseModel):
    """Asset-specific allocation recommendation."""

    asset_type: str
    allocation_pct: float
    nia_efficiency: float | None = None
    allocated_gfa_sqm: float | None = None
    target_floor_height_m: float | None = None
    parking_ratio_per_1000sqm: float | None = None
    rent_psm_month: float | None = None
    stabilised_vacancy_pct: float | None = None
    opex_pct_of_rent: float | None = None
    estimated_revenue_sgd: float | None = None
    estimated_capex_sgd: float | None = None
    fitout_cost_psm: float | None = None
    absorption_months: int | None = None
    risk_level: str | None = None
    heritage_premium_pct: float | None = None
    notes: list[str] = Field(default_factory=list)
    nia_sqm: float | None = None
    estimated_height_m: float | None = None
    total_parking_bays_required: float | None = None
    revenue_basis: str | None = None
    constraint_violations: list[DeveloperConstraintViolation] = Field(
        default_factory=list
    )
    confidence_score: float | None = None
    alternative_scenarios: list[str] = Field(default_factory=list)


class DeveloperVisualizationSummary(BaseModel):
    """Lightweight signal about 3D preview availability."""

    status: str
    preview_available: bool
    notes: list[str] = Field(default_factory=list)
    concept_mesh_url: str | None = None
    preview_metadata_url: str | None = None
    thumbnail_url: str | None = None
    camera_orbit_hint: dict[str, float] | None = None
    preview_seed: int | None = None
    preview_job_id: UUID | None = None
    massing_layers: list[DeveloperMassingLayer] = Field(default_factory=list)
    color_legend: list[DeveloperColorLegendEntry] = Field(default_factory=list)


# =============================================================================
# Finance Blueprint Models (Phase 2B)
# =============================================================================


class DeveloperCapitalStructureScenario(BaseModel):
    """Phase 2B capital structure target."""

    scenario: str
    equity_pct: float
    debt_pct: float
    preferred_equity_pct: float
    target_ltv: float
    target_ltc: float
    target_dscr: float
    comments: str | None = None


class DeveloperDebtFacility(BaseModel):
    """Phase 2B debt facility assumption."""

    facility_type: str
    amount_expression: str
    interest_rate: str
    tenor_years: float | None = None
    amortisation: str | None = None
    drawdown_schedule_notes: str | None = None
    covenants_triggers: str | None = None


class DeveloperEquityWaterfallTier(BaseModel):
    """Promote tier definition."""

    hurdle_irr_pct: float
    promote_pct: float


class DeveloperEquityWaterfall(BaseModel):
    """Equity waterfall structure."""

    tiers: list[DeveloperEquityWaterfallTier] = Field(default_factory=list)
    preferred_return_pct: float | None = None
    catch_up_notes: str | None = None


class DeveloperCashFlowMilestone(BaseModel):
    """Cash flow timeline milestone."""

    item: str
    start_month: int
    duration_months: int
    notes: str | None = None


class DeveloperExitAssumptions(BaseModel):
    """Exit, sale, and refinance markers."""

    exit_cap_rates: dict[str, float] = Field(default_factory=dict)
    sale_costs_pct: float
    sale_costs_breakdown: str | None = None
    refinance_terms: str | None = None


class DeveloperSensitivityBand(BaseModel):
    """Sensitivity band for key parameters."""

    parameter: str
    low: float
    base: float
    high: float
    comments: str | None = None


class DeveloperFinanceBlueprint(BaseModel):
    """Phase 2B finance blueprint surfaced with capture response."""

    capital_structure: list[DeveloperCapitalStructureScenario] = Field(
        default_factory=list
    )
    debt_facilities: list[DeveloperDebtFacility] = Field(default_factory=list)
    equity_waterfall: DeveloperEquityWaterfall | None = None
    cash_flow_timeline: list[DeveloperCashFlowMilestone] = Field(default_factory=list)
    exit_assumptions: DeveloperExitAssumptions | None = None
    sensitivity_bands: list[DeveloperSensitivityBand] = Field(default_factory=list)


class DeveloperFinancialSummary(BaseModel):
    """Aggregated financial signals derived from asset optimisation."""

    total_estimated_revenue_sgd: float | None = None
    total_estimated_capex_sgd: float | None = None
    dominant_risk_profile: str | None = None
    notes: list[str] = Field(default_factory=list)
    finance_blueprint: DeveloperFinanceBlueprint | None = None
    constraint_log: list[DeveloperConstraintViolation] = Field(default_factory=list)
    optimizer_confidence: float | None = None
    currency_code: str = "SGD"
    currency_symbol: str = "S$"
    asset_mix_finance_inputs: list[dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# Preview Job Serialization
# =============================================================================


def _serialise_preview_job(job: Any) -> PreviewJobSchema:
    """Convert a preview job ORM object to response schema."""
    status = (
        job.status.value
        if isinstance(job.status, PreviewJobStatus)
        else str(job.status)
    )
    preview_url = job.preview_url if status == PreviewJobStatus.READY.value else None
    metadata_url = job.metadata_url if status == PreviewJobStatus.READY.value else None
    thumbnail_url = (
        job.thumbnail_url if status == PreviewJobStatus.READY.value else None
    )
    detail_level = None
    if isinstance(job.metadata, dict):
        raw_level = job.metadata.get("geometry_detail_level")
        if isinstance(raw_level, str):
            detail_level = raw_level
    return PreviewJobSchema(
        id=job.id,
        property_id=job.property_id,
        scenario=job.scenario,
        status=status,
        preview_url=preview_url,
        metadata_url=metadata_url,
        thumbnail_url=thumbnail_url,
        requested_at=job.requested_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        message=job.message,
        asset_version=job.asset_version,
        geometry_detail_level=detail_level,
    )
