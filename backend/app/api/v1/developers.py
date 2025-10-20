"""Developer workspace API endpoints."""

from __future__ import annotations

import html
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional
from uuid import UUID

import structlog
from backend._compat.datetime import utcnow
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.agents import CoordinatePair, QuickAnalysisEnvelope
from app.core.database import get_session
from app.core.jwt_auth import TokenData, get_optional_user
from app.models.developer_checklists import ChecklistStatus, DeveloperChecklistTemplate
from app.models.property import Property
from app.services.agents.gps_property_logger import (
    DevelopmentScenario as CaptureScenario,
    GPSPropertyLogger,
    PropertyLogResult,
)
from app.services.agents.ura_integration import URAIntegrationService
from app.services.asset_mix import build_asset_mix
from app.services.developer_checklist_service import (
    DEFAULT_TEMPLATE_DEFINITIONS,
    DeveloperChecklistService,
)
from app.services.developer_condition_service import (
    ConditionAssessment,
    ConditionInsight,
    ConditionSystem,
    DeveloperConditionService,
)
from app.services.geocoding import Address, GeocodingService
from app.utils.render import render_html_to_pdf
from pydantic import BaseModel, Field

router = APIRouter(prefix="/developers", tags=["developers"])
logger = structlog.get_logger()

_developer_geocoding = GeocodingService()
_developer_ura = URAIntegrationService()
developer_gps_logger = GPSPropertyLogger(_developer_geocoding, _developer_ura)


class DeveloperGPSLogRequest(BaseModel):
    """GPS capture request tailored for developers."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    development_scenarios: list[CaptureScenario] | None = Field(
        None,
        description=(
            "Optional set of development scenarios to evaluate during capture. "
            "Defaults to the core commercial scenarios if omitted."
        ),
    )


class DeveloperBuildEnvelope(BaseModel):
    """Summary of zoning envelope and buildability heuristics."""

    zone_code: Optional[str] = None
    zone_description: Optional[str] = None
    site_area_sqm: Optional[float] = None
    allowable_plot_ratio: Optional[float] = None
    max_buildable_gfa_sqm: Optional[float] = None
    current_gfa_sqm: Optional[float] = None
    additional_potential_gfa_sqm: Optional[float] = None
    assumptions: list[str] = Field(default_factory=list)


class DeveloperVisualizationSummary(BaseModel):
    """Lightweight signal about 3D preview availability."""

    status: str
    preview_available: bool
    notes: list[str] = Field(default_factory=list)
    concept_mesh_url: str | None = None
    camera_orbit_hint: dict[str, float] | None = None
    preview_seed: int | None = None


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


PHASE2B_FINANCE_BLUEPRINT = DeveloperFinanceBlueprint(
    capital_structure=[
        DeveloperCapitalStructureScenario(
            scenario="Base Case",
            equity_pct=35.0,
            debt_pct=60.0,
            preferred_equity_pct=5.0,
            target_ltv=60.0,
            target_ltc=65.0,
            target_dscr=1.35,
            comments=(
                "Core Singapore development structure assuming SORA + 250 bps blended cost of debt."
            ),
        ),
        DeveloperCapitalStructureScenario(
            scenario="Upside",
            equity_pct=30.0,
            debt_pct=65.0,
            preferred_equity_pct=5.0,
            target_ltv=58.0,
            target_ltc=63.0,
            target_dscr=1.40,
            comments="Higher pre-leasing allows additional leverage with tighter DSCR covenants.",
        ),
        DeveloperCapitalStructureScenario(
            scenario="Downside",
            equity_pct=45.0,
            debt_pct=50.0,
            preferred_equity_pct=5.0,
            target_ltv=55.0,
            target_ltc=60.0,
            target_dscr=1.25,
            comments="De-risked case with additional sponsor equity and conservative leverage headroom.",
        ),
    ],
    debt_facilities=[
        DeveloperDebtFacility(
            facility_type="Construction Loan",
            amount_expression="0.60 x total_dev_cost",
            interest_rate="4.8% (SORA 3M + 240 bps)",
            tenor_years=4.0,
            amortisation="Interest-only during build; convert to 20-yr schedule at PC",
            drawdown_schedule_notes="15%/30%/30%/25% drawn by construction quarter.",
            covenants_triggers="DSCR >= 1.20 post-income; quarterly cost-to-complete tests.",
        ),
        DeveloperDebtFacility(
            facility_type="Bridge / Mezzanine",
            amount_expression="0.10 x total_dev_cost",
            interest_rate="8.5% fixed",
            tenor_years=2.0,
            amortisation="Bullet",
            drawdown_schedule_notes="Tranche alongside equity for land completion and top-up costs.",
            covenants_triggers="LTV hard cap 72%; cash sweep if DSCR falls below 1.15.",
        ),
        DeveloperDebtFacility(
            facility_type="Permanent Debt",
            amount_expression="0.55 x stabilised_value",
            interest_rate="4.2% (SORA 3M + 180 bps)",
            tenor_years=7.0,
            amortisation="20-year amortisation with 30% balloon",
            drawdown_schedule_notes="Funds post-PC once 70% stabilised occupancy achieved.",
            covenants_triggers="DSCR >= 1.35; maintain LTV <= 60%; cash sweep above 1.45 DSCR.",
        ),
    ],
    equity_waterfall=DeveloperEquityWaterfall(
        tiers=[
            DeveloperEquityWaterfallTier(hurdle_irr_pct=12.0, promote_pct=10.0),
            DeveloperEquityWaterfallTier(hurdle_irr_pct=18.0, promote_pct=20.0),
        ],
        preferred_return_pct=9.0,
        catch_up_notes=(
            "50/50 catch-up after preferred return; clawback if project IRR falls below 12% on exit."
        ),
    ),
    cash_flow_timeline=[
        DeveloperCashFlowMilestone(
            item="Land Acquisition",
            start_month=0,
            duration_months=3,
            notes="Due diligence, option exercise, completion, and stamping.",
        ),
        DeveloperCashFlowMilestone(
            item="Construction",
            start_month=3,
            duration_months=30,
            notes="Includes enabling works plus six-month interior fit-out buffer.",
        ),
        DeveloperCashFlowMilestone(
            item="Leasing / Sales",
            start_month=24,
            duration_months=18,
            notes="Marketing and pre-commitments begin during final construction year.",
        ),
        DeveloperCashFlowMilestone(
            item="Stabilisation",
            start_month=42,
            duration_months=12,
            notes="Target >=90% leased with NOI run-rate established.",
        ),
        DeveloperCashFlowMilestone(
            item="Exit / Refinance",
            start_month=48,
            duration_months=3,
            notes="Refinance or partial asset sale once DSCR covenant achieved.",
        ),
    ],
    exit_assumptions=DeveloperExitAssumptions(
        exit_cap_rates={"base": 4.0, "upside": 3.6, "downside": 4.5},
        sale_costs_pct=2.25,
        sale_costs_breakdown="1.75% broker + 0.25% legal + 0.25% stamp/fees.",
        refinance_terms="65% LTV senior loan at SORA + 170 bps, 5-year tenor, 25-year amortisation.",
    ),
    sensitivity_bands=[
        DeveloperSensitivityBand(
            parameter="Rent",
            low=-8.0,
            base=0.0,
            high=6.0,
            comments="URA quarterly ranges for CBD office and prime retail benchmarks.",
        ),
        DeveloperSensitivityBand(
            parameter="Exit Cap Rate (delta bps)",
            low=0.40,
            base=0.0,
            high=-0.30,
            comments="Stress ± basis points around 4.0% base exit yield.",
        ),
        DeveloperSensitivityBand(
            parameter="Construction Cost",
            low=10.0,
            base=0.0,
            high=-5.0,
            comments="2024 BCA tender price index volatility band.",
        ),
        DeveloperSensitivityBand(
            parameter="Interest Rate (delta %)",
            low=1.50,
            base=0.0,
            high=-0.75,
            comments="SORA tightening/easing swing assumptions.",
        ),
    ],
)


def _phase2b_finance_blueprint() -> DeveloperFinanceBlueprint:
    """Return a defensive copy of the Phase 2B finance blueprint."""

    return PHASE2B_FINANCE_BLUEPRINT.model_copy(deep=True)


class DeveloperGPSLogResponse(BaseModel):
    """Response envelope for developer GPS capture."""

    property_id: UUID
    address: Address
    coordinates: CoordinatePair
    ura_zoning: Dict[str, Any]
    existing_use: str
    property_info: Optional[Dict[str, Any]]
    nearby_amenities: Optional[Dict[str, Any]]
    quick_analysis: QuickAnalysisEnvelope
    build_envelope: DeveloperBuildEnvelope
    visualization: DeveloperVisualizationSummary
    optimizations: list[DeveloperAssetOptimization]
    financial_summary: "DeveloperFinancialSummary"
    timestamp: datetime


class DeveloperFinancialSummary(BaseModel):
    """Aggregated financial signals derived from asset optimisation."""

    total_estimated_revenue_sgd: float | None = None
    total_estimated_capex_sgd: float | None = None
    dominant_risk_profile: str | None = None
    notes: list[str] = Field(default_factory=list)
    finance_blueprint: DeveloperFinanceBlueprint | None = None


DeveloperGPSLogResponse.model_rebuild()


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
    return None if value is None else round(value, 2)


def _derive_build_envelope(result: PropertyLogResult) -> DeveloperBuildEnvelope:
    """Construct zoning/buildability summary from capture payload."""

    ura_data = result.ura_zoning or {}
    property_info = result.property_info or {}

    zone_code = ura_data.get("zone_code") or ura_data.get("zoneCode")
    zone_description = ura_data.get("zone_description") or ura_data.get(
        "zoneDescription"
    )
    plot_ratio = _coerce_float(ura_data.get("plot_ratio") or ura_data.get("plotRatio"))

    site_area = _coerce_float(
        property_info.get("site_area_sqm") or property_info.get("siteAreaSqm")
    )
    current_gfa = _coerce_float(
        property_info.get("gross_floor_area_sqm")
        or property_info.get("grossFloorAreaSqm")
        or property_info.get("gfa_approved")
        or property_info.get("gfaApproved")
    )

    max_buildable: Optional[float]
    if site_area is not None and plot_ratio is not None:
        max_buildable = site_area * plot_ratio
    else:
        max_buildable = None

    additional: Optional[float] = None
    if max_buildable is not None and current_gfa is not None:
        additional = max(max_buildable - current_gfa, 0.0)

    assumptions: list[str] = []
    if plot_ratio is not None and site_area is not None:
        assumptions.append(
            f"Assumes URA plot ratio {plot_ratio:g} applies uniformly across "
            f"{site_area:,.0f} sqm site area."
        )
    if zone_description:
        assumptions.append(
            f"Envelope derived from {str(zone_description).lower()} zoning guidance."
        )
    if not assumptions:
        assumptions.append(
            "Plot ratio or site area unavailable; envelope estimated from captured metadata."
        )

    return DeveloperBuildEnvelope(
        zone_code=str(zone_code) if zone_code else None,
        zone_description=str(zone_description) if zone_description else None,
        site_area_sqm=_round_optional(site_area),
        allowable_plot_ratio=_round_optional(plot_ratio),
        max_buildable_gfa_sqm=_round_optional(max_buildable),
        current_gfa_sqm=_round_optional(current_gfa),
        additional_potential_gfa_sqm=_round_optional(additional),
        assumptions=assumptions,
    )


def _build_visualization_summary(
    quick_analysis: dict[str, Any] | None,
    property_id: UUID,
) -> DeveloperVisualizationSummary:
    """Return messaging about 3D preview readiness."""

    scenario_count = 0
    if quick_analysis and isinstance(quick_analysis.get("scenarios"), list):
        scenario_count = len(quick_analysis["scenarios"])

    notes: list[str] = []
    if scenario_count:
        plural = "s" if scenario_count != 1 else ""
        notes.append(
            f"{scenario_count} scenario{plural} prepared for feasibility review."
        )
    notes.append(
        "High-fidelity 3D previews will ship with Phase 2B visualisation work."
    )
    notes.append("Download the concept mesh stub to brief the visualisation team.")

    concept_mesh_url = f"/static/dev-previews/{property_id}.glb"
    camera_orbit = {"theta": 48.0, "phi": 32.0, "radius": 1.6}

    return DeveloperVisualizationSummary(
        status="placeholder",
        preview_available=False,
        notes=notes,
        concept_mesh_url=concept_mesh_url,
        camera_orbit_hint=camera_orbit,
        preview_seed=scenario_count or 1,
    )


def _build_asset_optimizations(
    land_use: str,
    envelope: DeveloperBuildEnvelope,
) -> list[DeveloperAssetOptimization]:
    total_gfa = envelope.max_buildable_gfa_sqm or envelope.current_gfa_sqm
    if (
        total_gfa is None
        and envelope.current_gfa_sqm is not None
        and envelope.additional_potential_gfa_sqm is not None
    ):
        total_gfa = envelope.current_gfa_sqm + max(
            envelope.additional_potential_gfa_sqm, 0.0
        )
    total_gfa_value = float(total_gfa) if total_gfa is not None else None
    heritage_flag = False
    if envelope.zone_description and "heritage" in envelope.zone_description.lower():
        heritage_flag = True
    elif any("heritage" in assumption.lower() for assumption in envelope.assumptions):
        heritage_flag = True
    plans = build_asset_mix(
        land_use,
        achievable_gfa_sqm=total_gfa_value,
        additional_gfa=envelope.additional_potential_gfa_sqm,
        heritage=heritage_flag,
    )
    return [
        DeveloperAssetOptimization(
            asset_type=plan.asset_type,
            allocation_pct=plan.allocation_pct,
            nia_efficiency=plan.nia_efficiency,
            allocated_gfa_sqm=plan.allocated_gfa_sqm,
            target_floor_height_m=plan.target_floor_height_m,
            parking_ratio_per_1000sqm=plan.parking_ratio_per_1000sqm,
            rent_psm_month=plan.rent_psm_month,
            stabilised_vacancy_pct=plan.stabilised_vacancy_pct,
            opex_pct_of_rent=plan.opex_pct_of_rent,
            estimated_revenue_sgd=plan.estimated_revenue_sgd,
            estimated_capex_sgd=plan.estimated_capex_sgd,
            fitout_cost_psm=plan.fitout_cost_psm,
            absorption_months=plan.absorption_months,
            risk_level=plan.risk_level,
            heritage_premium_pct=plan.heritage_premium_pct,
            notes=list(plan.notes),
        )
        for plan in plans
    ]


def _summarise_financials(
    optimizations: list[DeveloperAssetOptimization],
) -> DeveloperFinancialSummary:
    total_revenue = sum(
        (opt.estimated_revenue_sgd or 0.0)
        for opt in optimizations
        if opt.estimated_revenue_sgd
    )
    total_capex = sum(
        (opt.estimated_capex_sgd or 0.0)
        for opt in optimizations
        if opt.estimated_capex_sgd
    )
    risk_order = {"low": 1, "balanced": 2, "moderate": 3, "elevated": 4}
    dominant = None
    for opt in optimizations:
        level = opt.risk_level
        if level is None:
            continue
        if dominant is None or risk_order.get(level, 0) > risk_order.get(dominant, 0):
            dominant = level

    notes: list[str] = []
    if dominant:
        notes.append(f"Dominant risk profile driven by {dominant} allocations.")
    if total_revenue:
        notes.append(
            "Total estimated revenue assumes NIA efficiency-weighted rent across the suggested mix."
        )
    if total_capex:
        notes.append(
            "Capex estimate aggregates fit-out assumptions for each programmed use."
        )

    finance_blueprint = _phase2b_finance_blueprint()
    notes.append(
        "Phase 2B finance blueprint attached with capital stack, debt facility, and sensitivity defaults."
    )

    return DeveloperFinancialSummary(
        total_estimated_revenue_sgd=total_revenue or None,
        total_estimated_capex_sgd=total_capex or None,
        dominant_risk_profile=dominant,
        notes=notes,
        finance_blueprint=finance_blueprint,
    )


# Request/Response Models
@router.post(
    "/properties/log-gps",
    response_model=DeveloperGPSLogResponse,
)
async def developer_log_property_by_gps(
    request: DeveloperGPSLogRequest,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
) -> DeveloperGPSLogResponse:
    """Log a property for developer workflows using GPS coordinates."""

    user_uuid: Optional[UUID] = None
    if token and token.user_id:
        try:
            user_uuid = UUID(token.user_id)
        except ValueError:
            logger.warning(
                "developer_gps_invalid_user_id",
                supplied_user_id=token.user_id,
            )

    result = await developer_gps_logger.log_property_from_gps(
        latitude=request.latitude,
        longitude=request.longitude,
        session=session,
        user_id=user_uuid,
        scenarios=request.development_scenarios,
    )

    quick_analysis_payload = result.quick_analysis or {
        "generated_at": utcnow().isoformat(),
        "scenarios": [],
    }
    quick_analysis = QuickAnalysisEnvelope.model_validate(quick_analysis_payload)

    build_envelope = _derive_build_envelope(result)
    visualization = _build_visualization_summary(
        result.quick_analysis, result.property_id
    )
    optimizations = _build_asset_optimizations(result.existing_use, build_envelope)
    financial_summary = _summarise_financials(optimizations)

    return DeveloperGPSLogResponse(
        property_id=result.property_id,
        address=result.address,
        coordinates=CoordinatePair(
            latitude=result.coordinates[0],
            longitude=result.coordinates[1],
        ),
        ura_zoning=result.ura_zoning,
        existing_use=result.existing_use,
        property_info=result.property_info,
        nearby_amenities=result.nearby_amenities,
        quick_analysis=quick_analysis,
        build_envelope=build_envelope,
        visualization=visualization,
        optimizations=optimizations,
        financial_summary=financial_summary,
        timestamp=result.timestamp,
    )


class ChecklistItemResponse(BaseModel):
    """Response model for a single checklist item."""

    id: str
    property_id: str
    development_scenario: str
    category: str
    item_title: str
    item_description: Optional[str]
    priority: str
    status: str
    assigned_to: Optional[str]
    due_date: Optional[str]
    completed_date: Optional[str]
    completed_by: Optional[str]
    notes: Optional[str]
    metadata: dict
    created_at: str
    updated_at: str
    requires_professional: Optional[bool] = None
    professional_type: Optional[str] = None
    typical_duration_days: Optional[int] = None
    display_order: Optional[int] = None


class ChecklistItemsResponse(BaseModel):
    """Envelope for checklist item collections."""

    items: List[ChecklistItemResponse]
    total: int


class ChecklistSummaryResponse(BaseModel):
    """Response model for checklist summary."""

    property_id: str
    total: int
    completed: int
    in_progress: int
    pending: int
    not_applicable: int
    completion_percentage: int
    by_category_status: dict[str, dict[str, int]]


class ChecklistTemplateResponse(BaseModel):
    """Serialized checklist template record."""

    model_config = {"populate_by_name": True}

    id: str
    development_scenario: str = Field(alias="developmentScenario")
    category: str
    item_title: str = Field(alias="itemTitle")
    item_description: Optional[str] = Field(default=None, alias="itemDescription")
    priority: str
    typical_duration_days: Optional[int] = Field(
        default=None, alias="typicalDurationDays"
    )
    requires_professional: bool = Field(alias="requiresProfessional")
    professional_type: Optional[str] = Field(default=None, alias="professionalType")
    display_order: int = Field(alias="displayOrder")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")


class ChecklistTemplateBaseRequest(BaseModel):
    """Base payload for template authoring."""

    model_config = {"populate_by_name": True}

    development_scenario: str = Field(alias="developmentScenario")
    category: str
    item_title: str = Field(alias="itemTitle")
    item_description: Optional[str] = Field(default=None, alias="itemDescription")
    priority: str
    typical_duration_days: Optional[int] = Field(
        default=None, alias="typicalDurationDays", ge=0
    )
    requires_professional: bool = Field(default=False, alias="requiresProfessional")
    professional_type: Optional[str] = Field(default=None, alias="professionalType")
    display_order: Optional[int] = Field(default=None, alias="displayOrder")


class ChecklistTemplateCreateRequest(ChecklistTemplateBaseRequest):
    """Create payload (inherits base fields)."""


class ChecklistTemplateUpdateRequest(BaseModel):
    """Partial update payload for checklist templates."""

    model_config = {"populate_by_name": True}

    development_scenario: Optional[str] = Field(
        default=None, alias="developmentScenario"
    )
    category: Optional[str] = None
    item_title: Optional[str] = Field(default=None, alias="itemTitle")
    item_description: Optional[str] = Field(default=None, alias="itemDescription")
    priority: Optional[str] = None
    typical_duration_days: Optional[int] = Field(
        default=None, alias="typicalDurationDays", ge=0
    )
    requires_professional: Optional[bool] = Field(
        default=None, alias="requiresProfessional"
    )
    professional_type: Optional[str] = Field(default=None, alias="professionalType")
    display_order: Optional[int] = Field(default=None, alias="displayOrder")


class ChecklistTemplateBulkImportRequest(BaseModel):
    """Bulk authoring payload for template definitions."""

    model_config = {"populate_by_name": True}

    templates: List[ChecklistTemplateBaseRequest] = Field(default_factory=list)
    replace_existing: bool = Field(default=False, alias="replaceExisting")


class ChecklistTemplateBulkImportResponse(BaseModel):
    """Summary of bulk import results."""

    model_config = {"populate_by_name": True}

    created: int
    updated: int
    deleted: int


class UpdateChecklistStatusRequest(BaseModel):
    """Request model for updating checklist status."""

    status: str  # pending, in_progress, completed, not_applicable
    notes: Optional[str] = None


class ConditionSystemResponse(BaseModel):
    """System-level assessment details."""

    name: str
    rating: str
    score: int
    notes: str
    recommended_actions: List[str]


class ConditionInsightResponse(BaseModel):
    """Insight surfaced from condition assessment heuristics."""

    id: str
    severity: str
    title: str
    detail: str
    specialist: Optional[str] = None


class ConditionAssessmentResponse(BaseModel):
    """Developer-friendly property condition assessment."""

    model_config = {"populate_by_name": True}

    property_id: str
    scenario: Optional[str] = None
    overall_score: int
    overall_rating: str
    risk_level: str
    summary: str
    scenario_context: Optional[str] = None
    systems: List[ConditionSystemResponse]
    recommended_actions: List[str]
    recorded_at: Optional[str] = None
    inspector_name: Optional[str] = Field(default=None, alias="inspectorName")
    recorded_by: Optional[str] = Field(default=None, alias="recordedBy")
    attachments: List[dict[str, Any]] = Field(default_factory=list)
    insights: List[ConditionInsightResponse] = Field(default_factory=list)


class ConditionSystemRequest(BaseModel):
    """Payload for persisting inspection system data."""

    model_config = {"populate_by_name": True}

    name: str
    rating: str
    score: int
    notes: str
    recommended_actions: List[str] = Field(
        default_factory=list, alias="recommendedActions"
    )


class ConditionAssessmentUpsertRequest(BaseModel):
    """Payload for saving developer inspection assessments."""

    model_config = {"populate_by_name": True}

    scenario: Optional[str] = None
    overall_rating: str = Field(alias="overallRating")
    overall_score: int = Field(alias="overallScore")
    risk_level: str = Field(alias="riskLevel")
    summary: str
    scenario_context: Optional[str] = Field(default=None, alias="scenarioContext")
    systems: List[ConditionSystemRequest]
    recommended_actions: List[str] = Field(
        default_factory=list, alias="recommendedActions"
    )
    inspector_name: Optional[str] = Field(default=None, alias="inspectorName")
    recorded_at: Optional[str] = Field(default=None, alias="recordedAt")
    attachments: List[dict[str, Any]] = Field(default_factory=list)


class ChecklistProgressResponse(BaseModel):
    """Summary of checklist completion."""

    model_config = {"populate_by_name": True}

    total: int
    completed: int
    in_progress: int = Field(alias="inProgress")
    pending: int
    not_applicable: int = Field(alias="notApplicable")
    completion_percentage: int = Field(alias="completionPercentage")


class ScenarioComparisonEntryResponse(BaseModel):
    """Aggregated comparison entry for scenario scorecards."""

    model_config = {"populate_by_name": True}

    scenario: Optional[str] = None
    label: str
    recorded_at: Optional[str] = Field(default=None, alias="recordedAt")
    overall_score: Optional[int] = Field(default=None, alias="overallScore")
    overall_rating: Optional[str] = Field(default=None, alias="overallRating")
    risk_level: Optional[str] = Field(default=None, alias="riskLevel")
    checklist_completed: Optional[int] = Field(default=None, alias="checklistCompleted")
    checklist_total: Optional[int] = Field(default=None, alias="checklistTotal")
    checklist_percent: Optional[int] = Field(default=None, alias="checklistPercent")
    primary_insight: Optional[ConditionInsightResponse] = Field(
        default=None, alias="primaryInsight"
    )
    insight_count: int = Field(default=0, alias="insightCount")
    recommended_action: Optional[str] = Field(default=None, alias="recommendedAction")
    inspector_name: Optional[str] = Field(default=None, alias="inspectorName")
    source: str


class ConditionReportResponse(BaseModel):
    """Structured condition assessment export."""

    model_config = {"populate_by_name": True}

    property_id: str = Field(alias="propertyId")
    property_name: Optional[str] = Field(default=None, alias="propertyName")
    address: Optional[str] = None
    generated_at: str = Field(alias="generatedAt")
    scenario_assessments: List[ConditionAssessmentResponse] = Field(
        alias="scenarioAssessments"
    )
    history: List[ConditionAssessmentResponse]
    checklist_summary: Optional[ChecklistProgressResponse] = Field(
        default=None, alias="checklistSummary"
    )
    scenario_comparison: List[ScenarioComparisonEntryResponse] = Field(
        default_factory=list, alias="scenarioComparison"
    )


@router.get(
    "/checklists/templates",
    response_model=List[ChecklistTemplateResponse],
)
async def list_checklist_templates(
    development_scenario: Optional[str] = Query(
        default=None, alias="developmentScenario"
    ),
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
    """Return checklist templates, optionally filtered by development scenario."""

    await DeveloperChecklistService.ensure_templates_seeded(session)
    templates = await DeveloperChecklistService.list_templates(
        session, development_scenario=development_scenario
    )
    return [_serialize_checklist_template(template) for template in templates]


@router.post(
    "/checklists/templates",
    response_model=ChecklistTemplateResponse,
    status_code=201,
)
async def create_checklist_template(
    request: ChecklistTemplateCreateRequest,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
    """Create a new checklist template definition."""

    try:
        template = await DeveloperChecklistService.create_template(
            session, request.model_dump(exclude_none=True, by_alias=False)
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    await session.commit()
    return _serialize_checklist_template(template)


@router.put(
    "/checklists/templates/{template_id}",
    response_model=ChecklistTemplateResponse,
)
async def update_checklist_template(
    template_id: UUID,
    request: ChecklistTemplateUpdateRequest,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
    """Update an existing checklist template definition."""

    try:
        template = await DeveloperChecklistService.update_template(
            session, template_id, request.model_dump(exclude_none=True, by_alias=False)
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    await session.commit()
    return _serialize_checklist_template(template)


@router.delete(
    "/checklists/templates/{template_id}",
    status_code=204,
)
async def delete_checklist_template(
    template_id: UUID,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
    """Delete a checklist template."""

    deleted = await DeveloperChecklistService.delete_template(session, template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Template not found")

    await session.commit()
    return Response(status_code=204)


@router.post(
    "/checklists/templates/import",
    response_model=ChecklistTemplateBulkImportResponse,
)
async def bulk_import_checklist_templates(
    request: ChecklistTemplateBulkImportRequest,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
    """Bulk import checklist templates from a JSON payload."""

    templates_payload = [
        template.model_dump(exclude_none=True, by_alias=False)
        for template in request.templates
    ]

    result = await DeveloperChecklistService.bulk_upsert_templates(
        session, templates_payload, replace_existing=request.replace_existing
    )
    await session.commit()
    return ChecklistTemplateBulkImportResponse(**result)


@router.get(
    "/properties/{property_id}/checklists",
    response_model=ChecklistItemsResponse,
)
async def get_property_checklists(
    property_id: UUID,
    development_scenario: Optional[str] = None,
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
    """
    Get due diligence checklist items for a property.

    Optionally filter by development scenario and/or status.
    """
    await DeveloperChecklistService.ensure_templates_seeded(session)

    # Parse status if provided
    checklist_status = None
    if status:
        try:
            checklist_status = ChecklistStatus(status)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. Must be one of: pending, in_progress, completed, not_applicable",
            ) from exc

    items = await DeveloperChecklistService.get_property_checklist(
        session,
        property_id,
        development_scenario=development_scenario,
        status=checklist_status,
    )

    if not items:
        if development_scenario:
            scenarios_to_seed = [development_scenario]
        else:
            scenarios_to_seed = sorted(
                {
                    str(defn["development_scenario"])
                    for defn in DEFAULT_TEMPLATE_DEFINITIONS
                }
            )
        created = await DeveloperChecklistService.auto_populate_checklist(
            session=session,
            property_id=property_id,
            development_scenarios=scenarios_to_seed,
        )
        if created:
            await session.commit()
            items = await DeveloperChecklistService.get_property_checklist(
                session,
                property_id,
                development_scenario=development_scenario,
                status=checklist_status,
            )

    payloads = DeveloperChecklistService.format_property_checklist_items(items)
    response_items = [ChecklistItemResponse(**payload) for payload in payloads]

    return ChecklistItemsResponse(items=response_items, total=len(response_items))


@router.get(
    "/properties/{property_id}/checklists/summary",
    response_model=ChecklistSummaryResponse,
)
async def get_checklist_summary(
    property_id: UUID,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
    """Get a summary of checklist completion status for a property."""
    summary = await DeveloperChecklistService.get_checklist_summary(
        session, property_id
    )
    return ChecklistSummaryResponse(**summary)


@router.patch(
    "/checklists/{checklist_id}",
    response_model=ChecklistItemResponse,
)
async def update_checklist_item(
    checklist_id: UUID,
    request: UpdateChecklistStatusRequest,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
    """Update a checklist item's status and notes."""
    try:
        checklist_status = ChecklistStatus(request.status)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {request.status}. Must be one of: pending, in_progress, completed, not_applicable",
        ) from exc

    # Get user_id if authenticated
    completed_by = UUID(token.user_id) if token and token.user_id else None

    updated_item = await DeveloperChecklistService.update_checklist_status(
        session,
        checklist_id,
        checklist_status,
        completed_by=completed_by,
        notes=request.notes,
    )

    if not updated_item:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    await session.commit()

    return ChecklistItemResponse(**updated_item.to_dict())


@router.get(
    "/properties/{property_id}/condition-assessment",
    response_model=ConditionAssessmentResponse,
)
async def get_condition_assessment(
    property_id: UUID,
    scenario: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
    """
    Generate a developer property condition assessment.

    Optionally pass `scenario` (e.g. existing_building, heritage_property) to
    contextualise the recommendation set.
    """

    scenario_key = _normalise_scenario_param(scenario)
    try:
        assessment: ConditionAssessment = (
            await DeveloperConditionService.generate_assessment(
                session=session,
                property_id=property_id,
                scenario=scenario_key,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return _serialize_condition_assessment(assessment)


@router.put(
    "/properties/{property_id}/condition-assessment",
    response_model=ConditionAssessmentResponse,
)
async def upsert_condition_assessment(
    property_id: UUID,
    request: ConditionAssessmentUpsertRequest,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
    """Persist a developer inspection assessment for a property."""

    scenario_key = _normalise_scenario_param(request.scenario)
    recorded_by = UUID(token.user_id) if token and token.user_id else None
    systems = [
        ConditionSystem(
            name=item.name,
            rating=item.rating,
            score=item.score,
            notes=item.notes,
            recommended_actions=item.recommended_actions,
        )
        for item in request.systems
    ]

    recorded_at_override: Optional[datetime] = None
    if request.recorded_at:
        iso_value = request.recorded_at.strip()
        if iso_value.endswith("Z"):
            iso_value = iso_value[:-1] + "+00:00"
        try:
            recorded_at_override = datetime.fromisoformat(iso_value)
        except ValueError as exc:  # pragma: no cover - validated client input
            raise HTTPException(
                status_code=400,
                detail="Invalid recordedAt timestamp. Use ISO 8601 format.",
            ) from exc

    attachments_payload = []
    for attachment in request.attachments:
        if isinstance(attachment, dict):
            attachments_payload.append(dict(attachment))

    assessment = await DeveloperConditionService.record_assessment(
        session=session,
        property_id=property_id,
        scenario=scenario_key,
        overall_rating=request.overall_rating,
        overall_score=request.overall_score,
        risk_level=request.risk_level,
        summary=request.summary,
        scenario_context=request.scenario_context,
        systems=systems,
        recommended_actions=request.recommended_actions,
        inspector_name=request.inspector_name,
        recorded_at=recorded_at_override,
        attachments=attachments_payload,
        recorded_by=recorded_by,
    )
    await session.commit()
    return _serialize_condition_assessment(assessment)


@router.get(
    "/properties/{property_id}/condition-assessment/history",
    response_model=List[ConditionAssessmentResponse],
)
async def get_condition_assessment_history(
    property_id: UUID,
    scenario: Optional[str] = None,
    limit: int = Query(20, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
    """Return stored inspection assessments ordered by most recent first."""

    scenario_key = _normalise_scenario_param(scenario)
    history = await DeveloperConditionService.get_assessment_history(
        session=session,
        property_id=property_id,
        scenario=scenario_key,
        limit=limit,
    )
    return [_serialize_condition_assessment(item) for item in history]


@router.get(
    "/properties/{property_id}/condition-assessment/scenarios",
    response_model=List[ConditionAssessmentResponse],
)
async def get_condition_assessment_scenarios(
    property_id: UUID,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
    """Return the latest stored inspection assessment for each scenario."""

    assessments = await DeveloperConditionService.get_latest_assessments_by_scenario(
        session=session,
        property_id=property_id,
    )
    return [_serialize_condition_assessment(assessment) for assessment in assessments]


@router.get(
    "/properties/{property_id}/condition-assessment/report",
)
async def export_condition_report(
    property_id: UUID,
    report_format: str = Query("json", alias="format", pattern="^(json|pdf)$"),
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
):
    """Return a structured condition report in JSON (default) or PDF format."""

    property_record = await session.get(Property, property_id)
    if property_record is None:
        raise HTTPException(status_code=404, detail="Property not found")

    scenario_assessments = (
        await DeveloperConditionService.get_latest_assessments_by_scenario(
            session=session,
            property_id=property_id,
        )
    )
    history = await DeveloperConditionService.get_assessment_history(
        session=session,
        property_id=property_id,
        scenario=None,
        limit=10,
    )
    checklist_summary_raw = await DeveloperChecklistService.get_checklist_summary(
        session, property_id
    )
    try:
        checklist_items = await DeveloperChecklistService.get_property_checklist(
            session,
            property_id,
        )
    except Exception:  # pragma: no cover - fallback if table bootstrap fails
        checklist_items = []

    scenario_comparison = _build_scenario_comparison_entries(
        scenario_assessments=scenario_assessments,
        checklist_items=checklist_items,
    )

    report = ConditionReportResponse(
        property_id=str(property_id),
        property_name=property_record.name,
        address=property_record.address,
        generated_at=datetime.utcnow().isoformat(),
        scenario_assessments=[
            _serialize_condition_assessment(assessment)
            for assessment in scenario_assessments
        ],
        history=[_serialize_condition_assessment(assessment) for assessment in history],
        checklist_summary=(
            ChecklistProgressResponse(
                total=checklist_summary_raw["total"],
                completed=checklist_summary_raw["completed"],
                in_progress=checklist_summary_raw["in_progress"],
                pending=checklist_summary_raw["pending"],
                not_applicable=checklist_summary_raw["not_applicable"],
                completion_percentage=checklist_summary_raw["completion_percentage"],
            )
            if checklist_summary_raw
            else None
        ),
        scenario_comparison=scenario_comparison,
    )

    if report_format == "pdf":
        html_body = _render_condition_report_html(report)
        pdf_data = render_html_to_pdf(html_body)
        if pdf_data is None:
            raise HTTPException(
                status_code=503,
                detail="PDF generation not available on this environment.",
            )
        filename = f"condition-report-{property_id}.pdf"
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    return JSONResponse(content=report.model_dump(by_alias=True))


def _serialize_condition_system(system: ConditionSystem) -> ConditionSystemResponse:
    return ConditionSystemResponse(
        name=system.name,
        rating=system.rating,
        score=system.score,
        notes=system.notes,
        recommended_actions=system.recommended_actions,
    )


def _serialize_condition_insight(insight: ConditionInsight) -> ConditionInsightResponse:
    return ConditionInsightResponse(
        id=insight.id,
        severity=insight.severity,
        title=insight.title,
        detail=insight.detail,
        specialist=insight.specialist,
    )


def _serialize_condition_assessment(
    assessment: ConditionAssessment,
) -> ConditionAssessmentResponse:
    recorded_at = assessment.recorded_at.isoformat() if assessment.recorded_at else None
    return ConditionAssessmentResponse(
        property_id=str(assessment.property_id),
        scenario=assessment.scenario,
        overall_score=assessment.overall_score,
        overall_rating=assessment.overall_rating,
        risk_level=assessment.risk_level,
        summary=assessment.summary,
        scenario_context=assessment.scenario_context,
        systems=[_serialize_condition_system(system) for system in assessment.systems],
        recommended_actions=assessment.recommended_actions,
        recorded_at=recorded_at,
        inspector_name=assessment.inspector_name,
        recorded_by=str(assessment.recorded_by) if assessment.recorded_by else None,
        attachments=list(assessment.attachments or []),
        insights=[
            _serialize_condition_insight(insight) for insight in assessment.insights
        ],
    )


_SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2, "positive": 3}


def _build_scenario_comparison_entries(
    *,
    scenario_assessments: List[ConditionAssessment],
    checklist_items: Iterable[Any],
) -> List[ScenarioComparisonEntryResponse]:
    progress_by_scenario = _summarise_checklist_progress(checklist_items)

    entries: List[ScenarioComparisonEntryResponse] = []
    for assessment in scenario_assessments:
        scenario_key = assessment.scenario
        label = _format_scenario_label(scenario_key)
        progress_key = scenario_key or "all"
        checklist_progress = progress_by_scenario.get(progress_key)

        primary_insight = _select_primary_insight(assessment.insights)
        entry = ScenarioComparisonEntryResponse(
            scenario=scenario_key,
            label=label,
            recorded_at=(
                assessment.recorded_at.isoformat() if assessment.recorded_at else None
            ),
            overall_score=assessment.overall_score,
            overall_rating=assessment.overall_rating,
            risk_level=assessment.risk_level,
            checklist_completed=(
                checklist_progress["completed"] if checklist_progress else None
            ),
            checklist_total=(
                checklist_progress["total"] if checklist_progress else None
            ),
            checklist_percent=(
                checklist_progress["percent"] if checklist_progress else None
            ),
            primary_insight=(
                _serialize_condition_insight(primary_insight)
                if primary_insight
                else None
            ),
            insight_count=len(assessment.insights),
            recommended_action=(
                assessment.recommended_actions[0]
                if assessment.recommended_actions
                else None
            ),
            inspector_name=assessment.inspector_name,
            source="manual" if assessment.recorded_at else "heuristic",
        )
        entries.append(entry)

    return entries


def _summarise_checklist_progress(
    checklist_items: Iterable[Any],
) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {}

    for item in checklist_items:
        scenario_key = _normalise_scenario_param(item.development_scenario)
        key = scenario_key or "all"
        bucket = summary.setdefault(
            key,
            {
                "total": 0,
                "completed": 0,
                "in_progress": 0,
                "pending": 0,
                "not_applicable": 0,
                "percent": 0,
            },
        )
        bucket["total"] += 1
        status = item.status
        if status == ChecklistStatus.COMPLETED:
            bucket["completed"] += 1
        elif status == ChecklistStatus.IN_PROGRESS:
            bucket["in_progress"] += 1
        elif status == ChecklistStatus.PENDING:
            bucket["pending"] += 1
        elif status == ChecklistStatus.NOT_APPLICABLE:
            bucket["not_applicable"] += 1
        else:
            bucket["pending"] += 1

    for bucket in summary.values():
        denominator = bucket["total"] - bucket["not_applicable"]
        if denominator > 0:
            bucket["percent"] = int((bucket["completed"] / denominator) * 100)
        else:
            bucket["percent"] = 0

    return summary


def _select_primary_insight(
    insights: List[ConditionInsight],
) -> Optional[ConditionInsight]:
    if not insights:
        return None
    ranked = sorted(
        insights,
        key=lambda item: (_SEVERITY_ORDER.get(item.severity, 99), insights.index(item)),
    )
    return ranked[0]


def _format_scenario_label(scenario: Optional[str]) -> str:
    if not scenario:
        return "All scenarios"
    return scenario.replace("_", " ").title()


def _normalise_scenario_param(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    slug = value.strip().lower()
    if not slug or slug == "all":
        return None
    return slug


__all__ = ["router"]


def _serialize_checklist_template(
    template: DeveloperChecklistTemplate,
) -> ChecklistTemplateResponse:
    return ChecklistTemplateResponse(
        id=str(template.id),
        development_scenario=template.development_scenario,
        category=template.category.value,
        item_title=template.item_title,
        item_description=template.item_description,
        priority=template.priority.value,
        typical_duration_days=template.typical_duration_days,
        requires_professional=template.requires_professional,
        professional_type=template.professional_type,
        display_order=template.display_order,
        created_at=template.created_at.isoformat(),
        updated_at=template.updated_at.isoformat(),
    )


def _render_condition_report_html(report: ConditionReportResponse) -> str:
    """Render a simple HTML report suitable for PDF conversion."""

    def _escape(value: Optional[str]) -> str:
        return html.escape(value or "")

    scenario_rows = []
    for scenario_assessment in report.scenario_assessments:
        systems_html = "".join(
            f"<li><strong>{_escape(system.name)}</strong>: "
            f"rating {_escape(system.rating)}, score {system.score}/100 "
            f"- {_escape(system.notes)}</li>"
            for system in scenario_assessment.systems
        )
        recommended_html = "".join(
            f"<li>{_escape(action)}</li>"
            for action in scenario_assessment.recommended_actions
        )
        scenario_rows.append(
            f"""
            <section>
              <h3>{_escape(scenario_assessment.scenario or "All scenarios")}</h3>
              <p><strong>Rating:</strong> {scenario_assessment.overall_rating} &nbsp;
                 <strong>Score:</strong> {scenario_assessment.overall_score}/100 &nbsp;
                 <strong>Risk:</strong> {_escape(scenario_assessment.risk_level)}</p>
              <p>{_escape(scenario_assessment.summary)}</p>
              {"<p><em>" + _escape(scenario_assessment.scenario_context) + "</em></p>" if scenario_assessment.scenario_context else ""}
              <h4>Systems</h4>
              <ul>{systems_html}</ul>
              {"<h4>Recommended actions</h4><ul>" + recommended_html + "</ul>" if recommended_html else ""}
            </section>
            """
        )

    history_rows = []
    for history_entry in report.history:
        history_rows.append(
            f"""
            <li>
              <strong>{_escape(history_entry.recorded_at or '')}</strong>:
              scenario {_escape(history_entry.scenario or 'n/a')},
              rating {history_entry.overall_rating},
              score {history_entry.overall_score}/100,
              risk {_escape(history_entry.risk_level)}
            </li>
            """
        )

    comparison_html = ""
    if report.scenario_comparison:
        comparison_rows = []
        for entry in report.scenario_comparison:
            progress = (
                f"{entry.checklist_completed}/{entry.checklist_total}"
                if entry.checklist_completed is not None
                and entry.checklist_total is not None
                else "N/A"
            )
            if entry.checklist_percent is not None and progress != "N/A":
                progress = f"{progress} ({entry.checklist_percent}%)"

            if entry.primary_insight:
                insight_text = (
                    f"<strong>{_escape(entry.primary_insight.title)}</strong><br/>"
                    f"{_escape(entry.primary_insight.detail)}"
                )
            else:
                insight_text = "N/A"

            comparison_rows.append(
                f"""
                <tr>
                  <td>{_escape(entry.label)}</td>
                  <td>{_escape(entry.overall_rating or '–')}</td>
                  <td>{entry.overall_score if entry.overall_score is not None else '–'}</td>
                  <td>{_escape(entry.risk_level or '–')}</td>
                  <td>{progress}</td>
                  <td>{insight_text}</td>
                  <td>{_escape(entry.recommended_action or 'None')}</td>
                  <td>{_escape(entry.inspector_name or 'N/A')}</td>
                  <td>{_escape('Manual inspection' if entry.source == 'manual' else 'Automated baseline')}</td>
                </tr>
                """
            )

        comparison_html = f"""
        <section>
          <h3>Scenario Comparison</h3>
          <table style=\"width:100%; border-collapse: collapse;\">
            <thead>
              <tr>
                <th style=\"text-align:left; border-bottom:1px solid #d4d4d8; padding:0.5rem;\">Scenario</th>
                <th style=\"text-align:left; border-bottom:1px solid #d4d4d8; padding:0.5rem;\">Rating</th>
                <th style=\"text-align:left; border-bottom:1px solid #d4d4d8; padding:0.5rem;\">Score</th>
                <th style=\"text-align:left; border-bottom:1px solid #d4d4d8; padding:0.5rem;\">Risk</th>
                <th style=\"text-align:left; border-bottom:1px solid #d4d4d8; padding:0.5rem;\">Checklist</th>
                <th style=\"text-align:left; border-bottom:1px solid #d4d4d8; padding:0.5rem;\">Primary insight</th>
                <th style=\"text-align:left; border-bottom:1px solid #d4d4d8; padding:0.5rem;\">Next action</th>
                <th style=\"text-align:left; border-bottom:1px solid #d4d4d8; padding:0.5rem;\">Inspector</th>
                <th style=\"text-align:left; border-bottom:1px solid #d4d4d8; padding:0.5rem;\">Source</th>
              </tr>
            </thead>
            <tbody>
              {''.join(comparison_rows)}
            </tbody>
          </table>
        </section>
        """

    checklist_html = ""
    if report.checklist_summary:
        summary = report.checklist_summary
        checklist_html = f"""
        <section>
          <h3>Checklist Summary</h3>
          <p>
            Total {summary.total} · Completed {summary.completed} ·
            In progress {summary.in_progress} · Pending {summary.pending} ·
            Not applicable {summary.not_applicable} ·
            Completion {summary.completion_percentage}%
          </p>
        </section>
        """

    html_report = f"""
    <html>
      <head>
        <meta charset="utf-8" />
        <title>Condition Report</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 2rem; color: #1d1d1f; }}
          h1, h2, h3 {{ margin-bottom: 0.5rem; }}
          section {{ margin-bottom: 2rem; }}
          ul {{ padding-left: 1.2rem; }}
        </style>
      </head>
      <body>
        <h1>Condition Summary</h1>
        <p><strong>Property:</strong> {_escape(report.property_name)}<br/>
           <strong>Address:</strong> {_escape(report.address)}<br/>
           <strong>Generated:</strong> {_escape(report.generated_at)}</p>

        {comparison_html}

        <h2>Scenario Assessments</h2>
        {''.join(scenario_rows)}

        {checklist_html}

        <section>
          <h3>Recent History</h3>
          <ul>
            {''.join(history_rows)}
          </ul>
        </section>
      </body>
    </html>
    """
    return html_report
