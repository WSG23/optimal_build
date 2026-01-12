"""GPS logging and preview job API endpoints for developer workspace."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Sequence
from uuid import UUID, uuid4

import structlog
from backend._compat.datetime import utcnow
from fastapi import APIRouter, Depends, HTTPException
from pydantic import AliasChoices, BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.agents import CoordinatePair, QuickAnalysisEnvelope
from app.api.v1.developers_common import (
    DeveloperAssetOptimization,
    DeveloperBuildEnvelope,
    DeveloperCashFlowMilestone,
    DeveloperCapitalStructureScenario,
    DeveloperColorLegendEntry,
    DeveloperConstraintViolation,
    DeveloperDebtFacility,
    DeveloperEquityWaterfall,
    DeveloperEquityWaterfallTier,
    DeveloperExitAssumptions,
    DeveloperFinanceBlueprint,
    DeveloperFinancialSummary,
    DeveloperMassingLayer,
    DeveloperSensitivityBand,
    DeveloperVisualizationSummary,
    PreviewJobSchema,
    _coerce_float,
    _convert_area_to_sqm,
    _convert_rent_to_psm,
    _decimal_or_none,
    _round_optional,
    _serialise_preview_job,
    _to_mapping,
)
from app.core.database import get_session
from app.core.jwt_auth import TokenData, get_optional_user
from app.api.deps import RequestIdentity, require_reviewer
from app.models.property import Property
from app.models.projects import Project, ProjectPhase, ProjectType
from app.schemas.finance import FinanceAssetMixInput
from app.services.finance_project_creation import (
    create_finance_project_from_capture,
)
from app.services.agents.gps_property_logger import (
    DevelopmentScenario as CaptureScenario,
    GPSPropertyLogger,
    PropertyLogResult,
)
from app.services.agents.ura_integration import URAIntegrationService
from app.services.asset_mix import AssetOptimizationOutcome, build_asset_mix
from app.services import preview_generator
from app.services.geocoding import Address, GeocodingService
from app.services.jurisdictions import get_jurisdiction_config
from app.services.preview_jobs import PreviewJobService, PreviewJobStatus

router = APIRouter(prefix="/developers", tags=["developers"])
logger = structlog.get_logger()

_developer_geocoding = GeocodingService()
_developer_ura = URAIntegrationService()
developer_gps_logger = GPSPropertyLogger(_developer_geocoding, _developer_ura)


# =============================================================================
# Asset Type Colors and Formatting
# =============================================================================

_ASSET_TYPE_COLORS: dict[str, str] = {
    "office": "#1C7ED6",
    "retail": "#F76707",
    "hospitality": "#F59F00",
    "amenities": "#12B886",
    "serviced_apartments": "#845EF7",
    "residential": "#5C7CFA",
    "high-spec logistics": "#339AF0",
    "high_spec_logistics": "#339AF0",
    "production": "#FF922B",
    "support services": "#20C997",
    "support_services": "#20C997",
}


def _resolve_asset_color(asset_type: str) -> str:
    key = asset_type.lower().replace("-", "_").replace(" ", "_")
    if key in _ASSET_TYPE_COLORS:
        return _ASSET_TYPE_COLORS[key]
    if asset_type.lower() in _ASSET_TYPE_COLORS:
        return _ASSET_TYPE_COLORS[asset_type.lower()]
    return "#ADB5BD"


def _format_asset_label(value: str) -> str:
    cleaned = value.replace("_", " ").replace("-", " ").strip()
    if not cleaned:
        return value
    return cleaned.title()


# =============================================================================
# Heritage Context Extraction
# =============================================================================


def _extract_heritage_context(
    envelope: DeveloperBuildEnvelope,
    property_info: dict[str, Any] | None,
    quick_analysis: dict[str, Any] | None,
    heritage_overlay: dict[str, Any] | None,
) -> dict[str, Any]:
    constraints: list[str] = []
    notes: list[str] = []
    risk: str | None = None
    flag = False

    if envelope.zone_description and "heritage" in envelope.zone_description.lower():
        flag = True
        constraints.append(f"Zoning guidance: {envelope.zone_description}")
    for assumption in envelope.assumptions or []:
        if "heritage" in assumption.lower():
            flag = True
            constraints.append(str(assumption))

    if heritage_overlay:
        flag = True
        overlay_name = heritage_overlay.get("name")
        overlay_source = heritage_overlay.get("source")
        overlay_notes = heritage_overlay.get("notes") or []
        overlay_risk = heritage_overlay.get("risk")
        if overlay_risk:
            risk = str(overlay_risk).lower()
        if overlay_name:
            constraints.append(f"Overlay: {overlay_name}")
        if overlay_source:
            notes.append(f"Source: {overlay_source}")
        for note in overlay_notes:
            text = str(note).strip()
            if text:
                notes.append(text)
                constraints.append(text)
        premium = heritage_overlay.get("heritage_premium_pct")
        if premium:
            notes.append(f"Estimated heritage premium: {premium}% fit-out uplift")

    property_mapping = _to_mapping(property_info)
    if property_mapping:
        for key in (
            "heritage_constraints",
            "conservation_requirements",
            "heritage_notes",
        ):
            value = property_mapping.get(key)
            if isinstance(value, Sequence):
                for item in value:
                    text = str(item).strip()
                    if text:
                        constraints.append(text)
                        flag = True
        for key in (
            "heritage_status",
            "conservation_status",
            "ura_conservation_category",
        ):
            status = property_mapping.get(key)
            if status:
                flag = True
                status_text = str(status).lower()
                if any(
                    token in status_text
                    for token in ("national", "strict", "conserved")
                ):
                    risk = risk or "high"
                else:
                    risk = risk or "medium"

        if property_mapping.get("is_conservation"):
            flag = True
            risk = risk or "high"
            constraints.append("Property flagged as conservation asset.")

    qa_mapping = _to_mapping(quick_analysis)
    if qa_mapping:
        scenarios = qa_mapping.get("scenarios")
        if isinstance(scenarios, Sequence):
            for entry in scenarios:
                scenario = _to_mapping(entry)
                if not scenario:
                    continue
                scenario_name = str(scenario.get("scenario", "")).lower()
                if (
                    "heritage" not in scenario_name
                    and "conservation" not in scenario_name
                ):
                    continue
                flag = True
                metrics = _to_mapping(scenario.get("metrics"))
                qa_risk = None
                if metrics:
                    qa_risk = metrics.get("heritage_risk") or metrics.get("risk_level")
                if qa_risk:
                    risk = str(qa_risk).lower()
                scenario_notes = scenario.get("notes")
                if isinstance(scenario_notes, Sequence):
                    for note in scenario_notes:
                        text = str(note).strip()
                        if text:
                            notes.append(text)
                            constraints.append(text)

    seen: set[str] = set()
    deduped_constraints: list[str] = []
    for item in constraints:
        text = str(item).strip()
        if not text:
            continue
        key = text.lower()
        if key not in seen:
            seen.add(key)
            deduped_constraints.append(text)

    if risk:
        risk = risk.lower()
    else:
        risk = "low"
    flag = flag or bool(risk) or bool(deduped_constraints)

    assumption_note = None
    if flag:
        if risk == "high":
            assumption_note = "Heritage overlay detected (high sensitivity)."
        elif risk == "medium":
            assumption_note = (
                "Heritage overlay detected (monitor compliance requirements)."
            )
        else:
            assumption_note = "Heritage overlay detected; confirm authority guidance."

    return {
        "flag": flag,
        "risk": risk,
        "constraints": deduped_constraints,
        "notes": notes,
        "assumption": assumption_note,
        "overlay": heritage_overlay,
    }


def _collect_quick_metrics(
    quick_analysis: dict[str, Any] | None,
) -> dict[str, float | str]:
    if not quick_analysis:
        return {}
    mapping = _to_mapping(quick_analysis)
    if mapping is None:
        return {}
    scenarios = mapping.get("scenarios")
    if not isinstance(scenarios, Sequence):
        return {}

    metrics: dict[str, float | str] = {}

    def _coerce_float_inner(value: object) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    for entry in scenarios:
        scenario_map = _to_mapping(entry)
        if scenario_map is None:
            continue
        scenario_name = str(scenario_map.get("scenario", "")).lower()
        raw_metrics = _to_mapping(scenario_map.get("metrics"))
        if raw_metrics is None:
            continue
        lower_metrics = {str(key).lower(): value for key, value in raw_metrics.items()}

        if scenario_name == "heritage_property":
            heritage_risk = lower_metrics.get("heritage_risk") or lower_metrics.get(
                "risk_level"
            )
            if isinstance(heritage_risk, str):
                metrics["heritage_risk"] = heritage_risk

        if scenario_name == "existing_building":
            vacancy = lower_metrics.get("vacancy_rate") or lower_metrics.get(
                "vacancy_pct"
            )
            vacancy = vacancy or lower_metrics.get("vacancy_percent")
            vacancy_value = _coerce_float_inner(vacancy)
            if vacancy_value is not None:
                if vacancy_value > 1:
                    vacancy_value /= 100.0
                metrics["existing_vacancy_rate"] = vacancy_value

            avg_rent = (
                lower_metrics.get("average_monthly_rent")
                or lower_metrics.get("average_rent_psm")
                or lower_metrics.get("avg_rent_psm")
            )
            avg_rent_value = _coerce_float_inner(avg_rent)
            if avg_rent_value is not None:
                metrics["existing_average_rent_psm"] = avg_rent_value

        if scenario_name == "underused_asset":
            mrt_count = lower_metrics.get("nearby_mrt_count")
            mrt_value = _coerce_float_inner(mrt_count)
            if mrt_value is not None:
                metrics["underused_mrt_count"] = mrt_value

    return metrics


# =============================================================================
# Build Envelope and Asset Optimization
# =============================================================================


async def _derive_build_envelope(
    result: PropertyLogResult,
    session: AsyncSession,
    jurisdiction: str = "SG",
) -> DeveloperBuildEnvelope:
    """Construct zoning/buildability summary from RefRule database.

    Queries the RefRule database for zoning parameters (plot ratio, height limits,
    site coverage) instead of using hardcoded mock values from URAIntegrationService.
    """
    from app.services.rules.zone_rules import get_zoning_rules_for_zone

    ura_data = result.ura_zoning or {}
    property_info = result.property_info or {}

    # Get zone code from URA service (still used for zone identification)
    raw_zone_code = ura_data.get("zone_code") or ura_data.get("zoneCode")

    # Query RefRule database for zoning parameters
    rules_result = await get_zoning_rules_for_zone(
        session=session,
        zone_code=raw_zone_code,
        jurisdiction=jurisdiction,
    )

    # Use rules data if available, otherwise fall back to URA service data
    if rules_result.has_data:
        plot_ratio = rules_result.plot_ratio
        zone_code = rules_result.zone_code
        zone_description = rules_result.zone_description
        building_height_limit = rules_result.building_height_limit_m
        site_coverage = rules_result.site_coverage_pct
        source_reference = rules_result.source_reference
    else:
        # Fallback to URA service data (mocked)
        plot_ratio = _coerce_float(
            ura_data.get("plot_ratio") or ura_data.get("plotRatio")
        )
        zone_code = str(raw_zone_code) if raw_zone_code else None
        zone_description = ura_data.get("zone_description") or ura_data.get(
            "zoneDescription"
        )
        building_height_limit = _coerce_float(
            ura_data.get("building_height_limit") or ura_data.get("buildingHeightLimit")
        )
        site_coverage = _coerce_float(
            ura_data.get("site_coverage") or ura_data.get("siteCoverage")
        )
        source_reference = "URA Service (Mock Data - RefRule not found)"

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
            f"Plot ratio {plot_ratio:g} applied to {site_area:,.0f} sqm site area."
        )
    if zone_description:
        assumptions.append(
            f"Envelope derived from {str(zone_description).lower()} zoning rules."
        )
    if rules_result.rules_found > 0:
        assumptions.append(f"Data from {rules_result.rules_found} RefRule entries.")
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
        building_height_limit_m=_round_optional(building_height_limit),
        site_coverage_pct=_round_optional(site_coverage),
        assumptions=assumptions,
        source_reference=source_reference,
    )


def _build_visualization_summary(
    quick_analysis: dict[str, Any] | None,
    property_id: UUID,
    optimizations: list[DeveloperAssetOptimization],
    envelope: DeveloperBuildEnvelope,
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
        "Preview generation queued. High-fidelity renders will replace the stub when ready."
    )

    camera_orbit = {"theta": 48.0, "phi": 32.0, "radius": 1.6}

    massing_layers: list[DeveloperMassingLayer] = []
    legend_entries: dict[str, DeveloperColorLegendEntry] = {}
    site_area = envelope.site_area_sqm or 0.0

    for opt in optimizations:
        gfa = opt.allocated_gfa_sqm
        nia = None
        if gfa is not None and opt.nia_efficiency:
            nia = gfa * opt.nia_efficiency
        height = None
        if site_area and site_area > 0 and gfa:
            floor_height = opt.target_floor_height_m or 4.0
            height = (gfa / site_area) * floor_height
        color = _resolve_asset_color(opt.asset_type)
        massing_layers.append(
            DeveloperMassingLayer(
                asset_type=opt.asset_type,
                allocation_pct=opt.allocation_pct,
                gfa_sqm=round(gfa, 2) if gfa is not None else None,
                nia_sqm=round(nia, 2) if nia is not None else None,
                estimated_height_m=round(height, 1) if height is not None else None,
                color=color,
            )
        )
        legend_entries.setdefault(
            opt.asset_type,
            DeveloperColorLegendEntry(
                asset_type=opt.asset_type,
                label=_format_asset_label(opt.asset_type),
                color=color,
                description=(
                    f"Risk level: {opt.risk_level.title()}" if opt.risk_level else None
                ),
            ),
        )

    massing_layers.sort(key=lambda layer: layer.allocation_pct, reverse=True)
    color_legend: list[DeveloperColorLegendEntry] = []
    seen_assets: set[str] = set()
    for layer in massing_layers:
        entry = legend_entries.get(layer.asset_type)
        if entry and entry.asset_type not in seen_assets:
            color_legend.append(entry)
            seen_assets.add(entry.asset_type)

    if massing_layers:
        primary = massing_layers[0]
        label = _format_asset_label(primary.asset_type)
        if primary.estimated_height_m:
            summary_note = f"{label} stack drives the stub massing (~{primary.estimated_height_m:.0f} m)."
        else:
            summary_note = (
                f"{label} stack drives {primary.allocation_pct:.0f}% of the programme."
            )
        if summary_note not in notes:
            notes.append(summary_note)

    return DeveloperVisualizationSummary(
        status=PreviewJobStatus.QUEUED.value,
        preview_available=False,
        notes=notes,
        concept_mesh_url=None,
        preview_metadata_url=None,
        camera_orbit_hint=camera_orbit,
        preview_seed=scenario_count or 1,
        massing_layers=massing_layers,
        color_legend=color_legend,
    )


def _build_asset_optimizations(
    land_use: str,
    envelope: DeveloperBuildEnvelope,
    existing_use: str | None,
    property_info: dict[str, Any] | None,
    quick_analysis: dict[str, Any] | None,
    heritage_overlay: dict[str, Any] | None,
) -> tuple[list[DeveloperAssetOptimization], dict[str, Any], AssetOptimizationOutcome]:
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

    heritage_context = _extract_heritage_context(
        envelope, property_info, quick_analysis, heritage_overlay
    )
    heritage_flag = heritage_context["flag"]
    heritage_risk = heritage_context["risk"]
    quick_metrics = _collect_quick_metrics(quick_analysis)

    assumption_note = heritage_context.get("assumption")
    if assumption_note and assumption_note not in envelope.assumptions:
        envelope.assumptions.append(assumption_note)

    outcome = build_asset_mix(
        land_use,
        achievable_gfa_sqm=total_gfa_value,
        additional_gfa=envelope.additional_potential_gfa_sqm,
        heritage=heritage_flag,
        heritage_risk=heritage_risk,
        existing_use=existing_use,
        site_area_sqm=envelope.site_area_sqm,
        current_gfa_sqm=envelope.current_gfa_sqm,
        quick_metrics=quick_metrics,
    )
    plans = outcome.plans
    constraint_summary: str | None = None
    constraints = heritage_context.get("constraints") or []
    if constraints:
        if len(constraints) > 2:
            constraint_summary = (
                "; ".join(constraints[:2]) + " + additional constraints"
            )
        else:
            constraint_summary = "; ".join(constraints)
    if constraint_summary:
        for plan in plans:
            if constraint_summary not in plan.notes:
                plan.notes.append(constraint_summary)

    optimizations = [
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
            nia_sqm=plan.nia_sqm,
            estimated_height_m=plan.estimated_height_m,
            total_parking_bays_required=plan.total_parking_bays_required,
            revenue_basis=plan.revenue_basis,
            constraint_violations=[
                DeveloperConstraintViolation(
                    constraint_type=violation.constraint_type,
                    severity=violation.severity,
                    message=violation.message,
                    asset_type=violation.asset_type,
                )
                for violation in plan.constraint_violations
            ],
            confidence_score=plan.confidence_score,
            alternative_scenarios=list(plan.alternative_scenarios),
        )
        for plan in plans
    ]
    heritage_context["optimizer_confidence"] = outcome.confidence
    if outcome.constraint_log:
        heritage_context.setdefault("constraints", [])
        for violation in outcome.constraint_log:
            message = f"{violation.constraint_type}: {violation.message}"
            if message not in heritage_context["constraints"]:
                heritage_context["constraints"].append(message)
    return optimizations, heritage_context, outcome


# =============================================================================
# Finance Helpers
# =============================================================================


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


def _build_finance_asset_mix_inputs(
    optimizations: Sequence[DeveloperAssetOptimization],
    *,
    jurisdiction_code: str,
) -> list[dict[str, Any]]:
    jurisdiction = get_jurisdiction_config(jurisdiction_code)
    finance_inputs: list[dict[str, Any]] = []
    for opt in optimizations:
        nia = _convert_area_to_sqm(
            _decimal_or_none(opt.nia_sqm), from_units=jurisdiction.area_units
        )
        rent_psm = _convert_rent_to_psm(
            _decimal_or_none(opt.rent_psm_month), rent_metric=jurisdiction.rent_metric
        )
        finance_input = FinanceAssetMixInput(
            asset_type=opt.asset_type,
            allocation_pct=_decimal_or_none(opt.allocation_pct),
            nia_sqm=nia,
            rent_psm_month=rent_psm,
            stabilised_vacancy_pct=_decimal_or_none(opt.stabilised_vacancy_pct),
            opex_pct_of_rent=_decimal_or_none(opt.opex_pct_of_rent),
            estimated_revenue_sgd=_decimal_or_none(opt.estimated_revenue_sgd),
            estimated_capex_sgd=_decimal_or_none(opt.estimated_capex_sgd),
            absorption_months=_decimal_or_none(opt.absorption_months),
            risk_level=opt.risk_level,
            heritage_premium_pct=_decimal_or_none(opt.heritage_premium_pct),
            notes=list(opt.notes),
        )
        finance_inputs.append(finance_input.model_dump(mode="json"))
    return finance_inputs


def _summarise_financials(
    optimizations: list[DeveloperAssetOptimization],
    *,
    constraint_log: Sequence[DeveloperConstraintViolation] | None = None,
    optimizer_confidence: float | None = None,
    jurisdiction_code: str = "SG",
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

    jurisdiction = get_jurisdiction_config(jurisdiction_code)
    summary = DeveloperFinancialSummary(
        total_estimated_revenue_sgd=total_revenue or None,
        total_estimated_capex_sgd=total_capex or None,
        dominant_risk_profile=dominant,
        notes=notes,
        finance_blueprint=finance_blueprint,
        currency_code=jurisdiction.currency_code,
        currency_symbol=jurisdiction.currency_symbol,
    )
    summary.asset_mix_finance_inputs = _build_finance_asset_mix_inputs(
        optimizations, jurisdiction_code=jurisdiction.code
    )
    if constraint_log:
        summary.constraint_log = list(constraint_log)
    if optimizer_confidence is not None:
        summary.optimizer_confidence = optimizer_confidence
        summary.notes.append(
            f"Optimiser confidence score: {optimizer_confidence:.2f} (1.0 = high certainty)."
        )
    return summary


# =============================================================================
# Request/Response Models
# =============================================================================


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
    preview_geometry_detail_level: str | None = Field(
        default=None,
        description="Optional geometry detail override for the generated preview job.",
    )
    jurisdiction_code: str | None = Field(
        default="SG",
        alias="jurisdictionCode",
        validation_alias=AliasChoices("jurisdictionCode", "jurisdiction_code"),
        description="Jurisdiction code for the captured property (e.g. 'SG', 'HK').",
    )

    @field_validator("preview_geometry_detail_level")
    @classmethod
    def _validate_preview_detail_level(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalised = value.strip().lower()
        if normalised not in preview_generator.SUPPORTED_GEOMETRY_DETAIL_LEVELS:
            valid = ", ".join(
                sorted(preview_generator.SUPPORTED_GEOMETRY_DETAIL_LEVELS)
            )
            raise ValueError(f"preview_geometry_detail_level must be one of: {valid}")
        return normalised

    @field_validator("jurisdiction_code")
    @classmethod
    def _normalise_jurisdiction(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip().upper()
        return trimmed or "SG"


class PreviewJobRefreshRequest(BaseModel):
    """Request body for preview job refresh operations."""

    geometry_detail_level: str | None = Field(
        default=None, description="Optional geometry detail level override"
    )
    color_legend: list[DeveloperColorLegendEntry] | None = Field(
        default=None,
        description="Optional colour legend overrides to persist on the preview job",
    )

    @field_validator("geometry_detail_level")
    @classmethod
    def _validate_detail_level(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalised = value.strip().lower()
        if normalised not in preview_generator.SUPPORTED_GEOMETRY_DETAIL_LEVELS:
            valid = ", ".join(
                sorted(preview_generator.SUPPORTED_GEOMETRY_DETAIL_LEVELS)
            )
            raise ValueError(f"geometry_detail_level must be one of: {valid}")
        return normalised


class DeveloperGPSLogResponse(BaseModel):
    """Response envelope for developer GPS capture."""

    property_id: UUID
    address: Address
    coordinates: CoordinatePair
    jurisdiction_code: str
    ura_zoning: Dict[str, Any]
    existing_use: str
    property_info: Optional[Dict[str, Any]]
    nearby_amenities: Optional[Dict[str, Any]]
    quick_analysis: QuickAnalysisEnvelope
    build_envelope: DeveloperBuildEnvelope
    visualization: DeveloperVisualizationSummary
    optimizations: list[DeveloperAssetOptimization]
    financial_summary: DeveloperFinancialSummary
    heritage_context: dict[str, Any] | None = None
    preview_jobs: list[PreviewJobSchema] = Field(default_factory=list)
    timestamp: datetime


DeveloperGPSLogResponse.model_rebuild()


class FinanceProjectCreateRequest(BaseModel):
    """Request body for creating a finance project/scenario from a GPS capture."""

    project_name: str | None = Field(
        default=None, validation_alias=AliasChoices("project_name", "projectName")
    )
    scenario_name: str | None = Field(
        default=None, validation_alias=AliasChoices("scenario_name", "scenarioName")
    )
    total_estimated_capex_sgd: float | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "total_estimated_capex_sgd",
            "totalEstimatedCapexSgd",
            "total_estimated_capex",
            "totalEstimatedCapex",
        ),
    )
    total_estimated_revenue_sgd: float | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "total_estimated_revenue_sgd",
            "totalEstimatedRevenueSgd",
            "total_estimated_revenue",
            "totalEstimatedRevenue",
        ),
    )


class FinanceProjectCreateResponse(BaseModel):
    """Response envelope for finance project creation."""

    project_id: UUID
    fin_project_id: int
    scenario_id: int
    project_name: str


class CaptureProjectCreateRequest(BaseModel):
    """Request body for saving a capture as a project."""

    project_name: str | None = Field(
        default=None, validation_alias=AliasChoices("project_name", "projectName")
    )


class CaptureProjectLinkRequest(BaseModel):
    """Request body for linking a capture to an existing project."""

    project_id: UUID = Field(
        ..., validation_alias=AliasChoices("project_id", "projectId")
    )


class CaptureProjectLinkResponse(BaseModel):
    """Response envelope for capture/project linkage."""

    project_id: UUID
    project_name: str
    property_id: UUID


# =============================================================================
# Route Handlers
# =============================================================================


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

    try:
        result = await developer_gps_logger.log_property_from_gps(
            latitude=request.latitude,
            longitude=request.longitude,
            session=session,
            user_id=user_uuid,
            scenarios=request.development_scenarios,
            jurisdiction_code=request.jurisdiction_code,
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail="GPS capture unavailable: geocoding failed",
        ) from exc

    quick_analysis_payload = result.quick_analysis or {
        "generated_at": utcnow().isoformat(),
        "scenarios": [],
    }
    quick_analysis = QuickAnalysisEnvelope.model_validate(quick_analysis_payload)

    property_metadata = await session.get(Property, result.property_id)
    property_jurisdiction = (
        property_metadata.jurisdiction_code if property_metadata else "SG"
    )
    property_info_payload = _to_mapping(result.property_info)
    property_info_dict: dict[str, Any] = (
        dict(property_info_payload) if property_info_payload else {}
    )
    property_info_dict.setdefault("jurisdiction_code", property_jurisdiction)
    if property_metadata is not None:
        if property_metadata.is_conservation is not None:
            property_info_dict.setdefault(
                "is_conservation", property_metadata.is_conservation
            )
        if property_metadata.conservation_status:
            property_info_dict.setdefault(
                "conservation_status", property_metadata.conservation_status
            )
            property_info_dict.setdefault(
                "heritage_status", property_metadata.conservation_status
            )
        if property_metadata.heritage_constraints:
            property_info_dict.setdefault(
                "heritage_constraints", property_metadata.heritage_constraints
            )

    property_info_for_mix: dict[str, Any] | None = (
        property_info_dict if property_info_dict else None
    )
    quick_analysis_dict = quick_analysis.model_dump()
    heritage_overlay = getattr(result, "heritage_overlay", None)

    build_envelope = await _derive_build_envelope(
        result, session, property_jurisdiction
    )
    optimizations, heritage_context, optimization_outcome = _build_asset_optimizations(
        result.existing_use,
        build_envelope,
        result.existing_use,
        property_info_for_mix,
        quick_analysis_dict,
        heritage_overlay,
    )
    visualization = _build_visualization_summary(
        quick_analysis_dict,
        result.property_id,
        optimizations,
        build_envelope,
    )
    preview_service = PreviewJobService(session)
    massing_payload = [
        layer.model_dump() if hasattr(layer, "model_dump") else layer.__dict__
        for layer in visualization.massing_layers
    ]
    legend_payload = [
        entry.model_dump() if hasattr(entry, "model_dump") else entry.__dict__
        for entry in visualization.color_legend
    ]
    preview_job = await preview_service.queue_preview(
        property_id=result.property_id,
        scenario="base",
        massing_layers=massing_payload,
        camera_orbit=visualization.camera_orbit_hint or {},
        geometry_detail_level=request.preview_geometry_detail_level,
        color_legend=legend_payload,
    )
    preview_status = (
        preview_job.status.value
        if isinstance(preview_job.status, PreviewJobStatus)
        else str(preview_job.status)
    )
    preview_available = preview_status == PreviewJobStatus.READY.value
    concept_mesh_url = preview_job.preview_url if preview_available else None
    preview_metadata_url = preview_job.metadata_url if preview_available else None
    thumbnail_url = preview_job.thumbnail_url if preview_available else None
    status_for_response = preview_status
    visualization = visualization.model_copy(
        update={
            "status": status_for_response,
            "preview_available": preview_available,
            "concept_mesh_url": concept_mesh_url,
            "preview_metadata_url": preview_metadata_url,
            "thumbnail_url": thumbnail_url,
            "preview_job_id": preview_job.id,
        }
    )
    preview_jobs_payload = [_serialise_preview_job(preview_job)]
    constraint_log = [
        DeveloperConstraintViolation(
            constraint_type=violation.constraint_type,
            severity=violation.severity,
            message=violation.message,
            asset_type=violation.asset_type,
        )
        for violation in optimization_outcome.constraint_log
    ]
    financial_summary = _summarise_financials(
        optimizations,
        constraint_log=constraint_log,
        optimizer_confidence=optimization_outcome.confidence,
        jurisdiction_code=property_jurisdiction,
    )

    heritage_constraints = heritage_context.get("constraints") or []
    if heritage_constraints:
        constraint_text = heritage_constraints[0]
        if constraint_text not in financial_summary.notes:
            financial_summary.notes.insert(0, constraint_text)
    heritage_risk = heritage_context.get("risk")
    if heritage_risk == "high":
        financial_summary.dominant_risk_profile = "elevated"
    elif heritage_risk == "medium" and not financial_summary.dominant_risk_profile:
        financial_summary.dominant_risk_profile = "balanced"

    await session.commit()

    return DeveloperGPSLogResponse(
        property_id=result.property_id,
        address=result.address,
        coordinates=CoordinatePair(
            latitude=result.coordinates[0],
            longitude=result.coordinates[1],
        ),
        jurisdiction_code=property_jurisdiction,
        ura_zoning=result.ura_zoning,
        existing_use=result.existing_use,
        nearby_amenities=result.nearby_amenities,
        quick_analysis=quick_analysis,
        build_envelope=build_envelope,
        visualization=visualization,
        optimizations=optimizations,
        financial_summary=financial_summary,
        heritage_context=heritage_context,
        preview_jobs=preview_jobs_payload,
        property_info=property_info_dict or None,
        timestamp=result.timestamp,
    )


@router.post(
    "/properties/{property_id}/create-project",
    response_model=FinanceProjectCreateResponse,
)
async def create_finance_project_for_capture(
    property_id: UUID,
    payload: FinanceProjectCreateRequest | None = None,
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_reviewer),
) -> FinanceProjectCreateResponse:
    """Create a finance project/scenario seeded from the GPS capture."""

    request_payload = payload or FinanceProjectCreateRequest()
    try:
        result = await create_finance_project_from_capture(
            session=session,
            identity=identity,
            property_id=property_id,
            project_name=request_payload.project_name,
            scenario_name=request_payload.scenario_name,
            total_estimated_capex_sgd=request_payload.total_estimated_capex_sgd,
            total_estimated_revenue_sgd=request_payload.total_estimated_revenue_sgd,
        )
    except ValueError as exc:
        if str(exc) == "identity_required":
            raise HTTPException(
                status_code=403,
                detail=(
                    "Finance project creation requires identity headers "
                    "(X-User-Email or X-User-Id)."
                ),
            ) from exc
        if str(exc) == "property_not_found":
            raise HTTPException(status_code=404, detail="Property not found") from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return FinanceProjectCreateResponse(
        project_id=result.project_id,
        fin_project_id=result.fin_project_id,
        scenario_id=result.scenario_id,
        project_name=result.project_name,
    )


@router.post(
    "/properties/{property_id}/save-project",
    response_model=CaptureProjectLinkResponse,
)
async def save_project_from_capture(
    property_id: UUID,
    payload: CaptureProjectCreateRequest | None = None,
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_reviewer),
) -> CaptureProjectLinkResponse:
    """Create a project from a capture and link the property."""

    property_record = await session.get(Property, property_id)
    if property_record is None:
        raise HTTPException(status_code=404, detail="Property not found")

    if property_record.project_id:
        project = await session.get(Project, property_record.project_id)
        if project is not None:
            return CaptureProjectLinkResponse(
                project_id=project.id,
                project_name=project.project_name,
                property_id=property_id,
            )

    request_payload = payload or CaptureProjectCreateRequest()
    cleaned_project_name = (
        request_payload.project_name or property_record.name or "Capture Project"
    ).strip()
    if not cleaned_project_name:
        cleaned_project_name = "Capture Project"

    project_code = f"gps_{property_id.hex}"
    existing = await session.execute(
        select(Project).where(Project.project_code == project_code)
    )
    if existing.scalar_one_or_none():
        project_code = f"{project_code}_{uuid4().hex[:6]}"

    owner_email = (identity.email or "").strip() or None
    owner_id: UUID | None = None
    if identity.user_id:
        try:
            owner_id = UUID(identity.user_id)
        except ValueError:
            owner_id = None

    project = Project(
        project_name=cleaned_project_name,
        project_code=project_code,
        project_type=ProjectType.NEW_DEVELOPMENT,
        current_phase=ProjectPhase.CONCEPT,
        owner_id=owner_id,
        owner_email=owner_email,
    )
    session.add(project)
    await session.flush()

    property_record.project_id = project.id
    if owner_email and not property_record.owner_email:
        property_record.owner_email = owner_email

    await session.commit()

    return CaptureProjectLinkResponse(
        project_id=project.id,
        project_name=project.project_name,
        property_id=property_id,
    )


@router.post(
    "/properties/{property_id}/link-project",
    response_model=CaptureProjectLinkResponse,
)
async def link_capture_to_project(
    property_id: UUID,
    payload: CaptureProjectLinkRequest,
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_reviewer),
) -> CaptureProjectLinkResponse:
    """Link a capture to an existing project."""

    property_record = await session.get(Property, property_id)
    if property_record is None:
        raise HTTPException(status_code=404, detail="Property not found")

    project = await session.get(Project, payload.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    property_record.project_id = project.id
    if identity.email and not property_record.owner_email:
        property_record.owner_email = identity.email

    await session.commit()

    return CaptureProjectLinkResponse(
        project_id=project.id,
        project_name=project.project_name,
        property_id=property_id,
    )


@router.get(
    "/properties/{property_id}/preview-jobs",
    response_model=list[PreviewJobSchema],
)
async def list_preview_jobs(
    property_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> list[PreviewJobSchema]:
    """Return preview jobs associated with the property."""

    service = PreviewJobService(session)
    jobs = await service.list_jobs(property_id)
    return [_serialise_preview_job(job) for job in jobs]


@router.get(
    "/preview-jobs/{job_id}",
    response_model=PreviewJobSchema,
)
async def get_preview_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> PreviewJobSchema:
    """Fetch a preview job by id."""

    service = PreviewJobService(session)
    job = await service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Preview job not found")
    return _serialise_preview_job(job)


@router.post(
    "/preview-jobs/{job_id}/refresh",
    response_model=PreviewJobSchema,
)
async def refresh_preview_job(
    job_id: UUID,
    refresh_request: PreviewJobRefreshRequest | None = None,
    session: AsyncSession = Depends(get_session),
) -> PreviewJobSchema:
    """Re-render a preview job using stored metadata."""

    service = PreviewJobService(session)
    job = await service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Preview job not found")
    try:
        await service.refresh_job(
            job,
            geometry_detail_level=(
                refresh_request.geometry_detail_level if refresh_request else None
            ),
            color_legend=(refresh_request.color_legend if refresh_request else None),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await session.commit()
    await session.refresh(job)
    return _serialise_preview_job(job)
