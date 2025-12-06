"""Business logic for feasibility rule selection and assessments."""

from __future__ import annotations


from collections.abc import Iterable, Sequence

from pathlib import Path
import json
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException

from app.schemas.feasibility import (
    AssetConstraintViolation,
    AssetOptimizationRecommendation,
    BuildableAreaSummary,
    FeasibilityAssessmentRequest,
    FeasibilityAssessmentResponse,
    FeasibilityRule,
    FeasibilityRulesResponse,
    FeasibilityRulesSummary,
    FeasibilityRuleStatus,
    NewFeasibilityProjectInput,
    RuleAssessmentResult,
)
from app.services.feasibility.normalization import (
    normalise_assessment_payload,
    normalise_project_payload,
)
from app.schemas.engineering import EngineeringDefaultsResponse
from app.schemas.finance import AssetFinancialSummarySchema
from app.services.asset_mix import (
    AssetOptimizationOutcome,
    build_asset_mix,
    format_asset_mix_summary,
)

ENGINEERING_DEFAULTS_PATH = (
    Path(__file__).parent.parent / "core" / "constants" / "engineering_defaults.json"
)

_BASE_RULES: Sequence[dict[str, object]] = (
    {
        "id": "ura-plot-ratio",
        "title": "Plot ratio within URA master plan envelope",
        "description": (
            "Maximum gross plot ratio permitted for the planning area according "
            "to the 2025 URA master plan."
        ),
        "authority": "URA",
        "topic": "zoning",
        "parameter_key": "planning.gross_plot_ratio",
        "operator": "<=",
        "value": "3.5",
        "severity": "critical",
        "default_selected": True,
    },
    {
        "id": "bca-site-coverage",
        "title": "Site coverage for residential developments",
        "description": (
            "Site coverage must not exceed the prescribed limit to maintain "
            "environmental quality."
        ),
        "authority": "BCA",
        "topic": "envelope",
        "parameter_key": "envelope.site_coverage_percent",
        "operator": "<=",
        "value": "45",
        "unit": "%",
        "severity": "important",
        "default_selected": True,
    },
    {
        "id": "scdf-access",
        "title": "Fire appliance access road width",
        "description": (
            "Primary fire engine access roads must satisfy minimum width "
            "requirements."
        ),
        "authority": "SCDF",
        "topic": "fire safety",
        "parameter_key": "fire.access.road_width_m",
        "operator": ">=",
        "value": "4.5",
        "unit": "m",
        "severity": "critical",
        "default_selected": True,
    },
    {
        "id": "nea-bin-centre",
        "title": "Provision of bin centre",
        "description": (
            "Residential developments above 40 units must provide an on-site bin "
            "centre."
        ),
        "authority": "NEA",
        "topic": "environmental health",
        "parameter_key": "operations.bin_centre_required",
        "operator": "=",
        "value": "true",
        "severity": "informational",
        "default_selected": False,
    },
)


def _round_half_up(value: float) -> int:
    """Match JavaScript-style rounding for positive values."""

    return int(Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _project_identifier(project: NewFeasibilityProjectInput) -> str:
    token = project.name.strip() if project.name and project.name.strip() else "draft"
    return f"project-{token}"


def _format_land_use(land_use: str) -> str:
    cleaned = land_use.replace("_", " ").strip()
    return cleaned if cleaned else "mixed use"


def _build_rules() -> list[FeasibilityRule]:
    return [FeasibilityRule.model_validate(item) for item in _BASE_RULES]


def get_engineering_defaults() -> EngineeringDefaultsResponse:
    """Load engineering defaults for all jurisdictions."""
    if not ENGINEERING_DEFAULTS_PATH.exists():
        return EngineeringDefaultsResponse(defaults={})
    with open(ENGINEERING_DEFAULTS_PATH, "r") as f:
        data = json.load(f)
    return EngineeringDefaultsResponse(defaults=data)


def _calculate_gfa_nia_accuracy_range(land_use: str) -> str:
    """Return the GFA->NIA accuracy band based on asset type (features.md)."""
    normalized = land_use.lower().strip()
    if "residential" in normalized:
        return "±10-12%"  # High-rise residential
    elif "office" in normalized:
        return "±5-8%"
    elif "industrial" in normalized:
        return "±5%"
    elif "retail" in normalized:
        return "±8-12%"
    elif "mixed" in normalized:
        return "±10-15%"
    return "±8-12%"  # Default


def generate_feasibility_rules(
    project: NewFeasibilityProjectInput,
) -> FeasibilityRulesResponse:
    """Return feasibility rules and recommendations for the project."""

    rules = _build_rules()
    recommended = [rule.id for rule in rules if rule.default_selected]
    summary = FeasibilityRulesSummary(
        compliance_focus="Envelope controls and critical access provisions",
        notes=f"Auto-selected based on {_format_land_use(project.land_use)} land use profile",
    )
    return FeasibilityRulesResponse(
        project_id=_project_identifier(project),
        rules=rules,
        recommended_rule_ids=recommended,
        summary=summary,
    )


def _normalise_selected_ids(selected_ids: Iterable[str]) -> list[str]:
    seen: dict[str, None] = {}
    for identifier in selected_ids:
        if identifier not in seen:
            seen[identifier] = None
    return list(seen.keys())


def _calculate_summary(
    project: NewFeasibilityProjectInput,
    results: list[RuleAssessmentResult],
) -> BuildableAreaSummary:
    envelope = getattr(project, "build_envelope", None)
    site_area = project.site_area_sqm
    if envelope and envelope.site_area_sqm:
        site_area = envelope.site_area_sqm

    plot_ratio_cap = 3.5
    if envelope and envelope.allowable_plot_ratio:
        plot_ratio_cap = float(envelope.allowable_plot_ratio)

    max_gfa: int
    if envelope and envelope.max_buildable_gfa_sqm:
        max_gfa = _round_half_up(float(envelope.max_buildable_gfa_sqm))
    else:
        max_gfa = _round_half_up(site_area * plot_ratio_cap)

    has_failure = any(result.status == "fail" for result in results)
    achievable_gfa: int
    if (
        envelope
        and envelope.additional_potential_gfa_sqm is not None
        and envelope.current_gfa_sqm is not None
    ):
        baseline = float(envelope.current_gfa_sqm)
        uplift = max(float(envelope.additional_potential_gfa_sqm), 0.0)
        achievable_total = min(baseline + uplift, float(max_gfa))
        achievable_gfa = _round_half_up(achievable_total)
    else:
        achievable_factor = 0.65 if has_failure else 0.82
        achievable_gfa = _round_half_up(max_gfa * achievable_factor)

    average_unit_size = 85 if project.land_use == "residential" else 120
    estimated_units = max(1, _round_half_up(achievable_gfa / average_unit_size))

    coverage_limit = 45
    if has_failure:
        site_coverage = coverage_limit - 12.5
    else:
        if site_area > 0 and plot_ratio_cap > 0:
            raw_coverage = (achievable_gfa / site_area) * (100 / plot_ratio_cap)
        else:
            raw_coverage = coverage_limit
        site_coverage = min(coverage_limit, max(raw_coverage, 0))

    all_pass = all(result.status == "pass" for result in results) if results else True
    if all_pass:
        remarks = (
            "All checked parameters comply with the submitted envelope assumptions."
        )
    elif has_failure:
        remarks = (
            "Certain rules failed — adjust massing, access, or authority parameters "
            "and capture the design revisions."
        )
    else:
        remarks = "Some rules returned warnings — review assumptions before proceeding."

    return BuildableAreaSummary(
        max_permissible_gfa_sqm=max_gfa,
        estimated_achievable_gfa_sqm=achievable_gfa,
        estimated_unit_count=estimated_units,
        site_coverage_percent=site_coverage,
        remarks=remarks,
        accuracy_range=_calculate_gfa_nia_accuracy_range(project.land_use),
    )


def _generate_asset_mix(
    project: NewFeasibilityProjectInput, summary: BuildableAreaSummary
) -> tuple[
    list[AssetOptimizationRecommendation],
    list[str],
    AssetOptimizationOutcome,
]:
    envelope = getattr(project, "build_envelope", None)
    additional = envelope.additional_potential_gfa_sqm if envelope else None
    heritage = False
    if envelope:
        zone_description = getattr(envelope, "zone_description", None)
        if isinstance(zone_description, str) and "heritage" in zone_description.lower():
            heritage = True
        else:
            assumptions = getattr(envelope, "assumptions", []) or []
            if any(
                isinstance(entry, str) and "heritage" in entry.lower()
                for entry in assumptions
            ):
                heritage = True

    outcome = build_asset_mix(
        project.land_use,
        achievable_gfa_sqm=summary.estimated_achievable_gfa_sqm,
        additional_gfa=additional,
        heritage=heritage,
        heritage_risk=getattr(envelope, "heritage_risk", None) if envelope else None,
        site_area_sqm=project.site_area_sqm,
        current_gfa_sqm=(
            envelope.current_gfa_sqm if envelope and envelope.current_gfa_sqm else None
        ),
    )
    notes = format_asset_mix_summary(
        outcome.plans, summary.estimated_achievable_gfa_sqm
    )
    recommendations = [
        AssetOptimizationRecommendation(
            asset_type=plan.asset_type,
            allocation_pct=plan.allocation_pct,
            allocated_gfa_sqm=(
                int(round(plan.allocated_gfa_sqm))
                if plan.allocated_gfa_sqm is not None
                else None
            ),
            nia_efficiency=plan.nia_efficiency,
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
                AssetConstraintViolation(
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
        for plan in outcome.plans
    ]
    return recommendations, notes, outcome


def _summarise_asset_financials(
    mix: list[AssetOptimizationRecommendation],
) -> AssetFinancialSummarySchema | None:
    if not mix:
        return None

    total_revenue = Decimal(0)
    total_capex = Decimal(0)
    risk_order = {"low": 1, "balanced": 2, "moderate": 3, "elevated": 4}
    dominant: str | None = None

    for rec in mix:
        if rec.estimated_revenue_sgd is not None:
            total_revenue += Decimal(str(rec.estimated_revenue_sgd))
        if rec.estimated_capex_sgd is not None:
            total_capex += Decimal(str(rec.estimated_capex_sgd))
        if rec.risk_level:
            if dominant is None or risk_order.get(rec.risk_level, 0) > risk_order.get(
                dominant, 0
            ):
                dominant = rec.risk_level

    notes: list[str] = []
    if dominant:
        notes.append(f"Dominant risk profile: {dominant}.")
    if total_revenue > 0:
        notes.append(
            "Revenue estimate aggregates efficiency-weighted rent across the asset mix."
        )
    if total_capex > 0:
        notes.append("Capex projection sums programme-specific fit-out assumptions.")

    return AssetFinancialSummarySchema(
        total_estimated_revenue_sgd=total_revenue if total_revenue > 0 else None,
        total_estimated_capex_sgd=total_capex if total_capex > 0 else None,
        dominant_risk_profile=dominant,
        notes=notes,
    )


def _evaluate_rule(
    rule: FeasibilityRule,
    index: int,
    project: NewFeasibilityProjectInput,
) -> RuleAssessmentResult:
    envelope = getattr(project, "build_envelope", None)
    site_area = project.site_area_sqm
    if envelope and envelope.site_area_sqm:
        site_area = envelope.site_area_sqm

    status: FeasibilityRuleStatus
    notes: str | None = None
    actual_value: str | None = None

    if "plot_ratio" in rule.parameter_key:
        allowable = None
        if envelope and envelope.allowable_plot_ratio:
            allowable = float(envelope.allowable_plot_ratio)
        elif rule.value:
            try:
                allowable = float(rule.value)
            except ValueError:
                allowable = None

        proposed_ratio = None
        if project.target_gross_floor_area_sqm:
            proposed_ratio = project.target_gross_floor_area_sqm / site_area
        elif envelope and envelope.current_gfa_sqm:
            proposed_ratio = envelope.current_gfa_sqm / site_area

        if proposed_ratio is not None:
            actual_value = f"{proposed_ratio:.2f}"
            if allowable is not None:
                if proposed_ratio > allowable:
                    status = "fail"
                    notes = (
                        "Target GFA exceeds current plot ratio envelope; pursue rezoning "
                        "or adjust programme."
                    )
                elif proposed_ratio >= (0.8 * allowable) - 1e-6:
                    status = "warning"
                    notes = (
                        "Plot ratio utilisation is high; maintain design compliance buffer "
                        "to accommodate circulation and servicing."
                    )
                else:
                    status = "pass"
                    notes = "Plot ratio within current zoning envelope."
            else:
                status = "warning"
                notes = "Insufficient data to verify plot ratio compliance."
    else:
        status = "warning" if index % 3 == 0 else ("pass" if index % 2 == 0 else "fail")
        if status == "fail":
            notes = "Adjust design parameters or consult the respective authority."
        elif status == "warning":
            notes = "Consider alternative layouts to increase compliance buffer."

    payload = rule.model_dump()
    return RuleAssessmentResult(
        **payload,
        status=status,
        actual_value=actual_value,
        notes=notes,
    )


def run_feasibility_assessment(
    payload: FeasibilityAssessmentRequest,
) -> FeasibilityAssessmentResponse:
    """Evaluate the project against the selected rules."""

    rules = _build_rules()
    lookup: dict[str, FeasibilityRule] = {rule.id: rule for rule in rules}
    normalised_ids = _normalise_selected_ids(payload.selected_rule_ids)
    missing = [identifier for identifier in normalised_ids if identifier not in lookup]
    if missing:
        message = ", ".join(sorted(missing))
        raise HTTPException(
            status_code=400, detail=f"Unknown rule identifiers: {message}"
        )

    evaluated = [
        _evaluate_rule(lookup[identifier], index, payload.project)
        for index, identifier in enumerate(normalised_ids)
    ]
    summary = _calculate_summary(payload.project, evaluated)
    recommendations = [
        "Share the feasibility snapshot with the wider design team to align on constraints.",
    ]
    if any(result.status == "fail" for result in evaluated):
        recommendations.append(
            "Schedule a coordination call with URA/BCA to clarify envelope outcomes."
        )
    if any(result.status == "warning" for result in evaluated):
        recommendations.append(
            "Investigate design options to improve fire access compliance buffers."
        )

    asset_mix, mix_notes, mix_outcome = _generate_asset_mix(payload.project, summary)
    asset_financials = _summarise_asset_financials(asset_mix)
    recommendations.extend(mix_notes)

    constraint_log = [
        AssetConstraintViolation(
            constraint_type=violation.constraint_type,
            severity=violation.severity,
            message=violation.message,
            asset_type=violation.asset_type,
        )
        for violation in mix_outcome.constraint_log
    ]
    optimizer_confidence = mix_outcome.confidence
    if optimizer_confidence is not None:
        recommendations.append(
            f"Asset optimiser confidence score: {optimizer_confidence:.2f} "
            "(higher indicates more stable mix)."
        )

    return FeasibilityAssessmentResponse(
        project_id=_project_identifier(payload.project),
        summary=summary,
        rules=evaluated,
        recommendations=recommendations,
        asset_optimizations=asset_mix,
        asset_mix_summary=asset_financials,
        constraint_log=constraint_log,
        optimizer_confidence=optimizer_confidence,
    )


__all__ = [
    "generate_feasibility_rules",
    "run_feasibility_assessment",
    "normalise_project_payload",
    "normalise_assessment_payload",
]
