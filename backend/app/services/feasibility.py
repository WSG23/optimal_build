"""Business logic for feasibility rule selection and assessments."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException

from app.schemas.feasibility import (
    BuildableAreaSummary,
    FeasibilityAssessmentRequest,
    FeasibilityAssessmentResponse,
    FeasibilityRule,
    FeasibilityRulesResponse,
    FeasibilityRulesSummary,
    NewFeasibilityProjectInput,
    RuleAssessmentResult,
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
    max_plot_ratio = 3.5
    max_gfa = _round_half_up(project.site_area_sqm * max_plot_ratio)
    has_failure = any(result.status == "fail" for result in results)
    achievable_factor = 0.65 if has_failure else 0.82
    achievable_gfa = _round_half_up(max_gfa * achievable_factor)
    average_unit_size = 85 if project.land_use == "residential" else 120
    estimated_units = max(1, _round_half_up(achievable_gfa / average_unit_size))
    coverage_limit = 45
    site_coverage = min(coverage_limit, (achievable_factor * 100) / 2)
    all_pass = all(result.status == "pass" for result in results) if results else True
    remarks = (
        "All checked parameters comply with the default envelope."
        if all_pass
        else "Certain parameters require design revisions before proceeding."
    )
    return BuildableAreaSummary(
        max_permissible_gfa_sqm=max_gfa,
        estimated_achievable_gfa_sqm=achievable_gfa,
        estimated_unit_count=estimated_units,
        site_coverage_percent=site_coverage,
        remarks=remarks,
    )


def _evaluate_rule(
    rule: FeasibilityRule,
    index: int,
    project: NewFeasibilityProjectInput,
) -> RuleAssessmentResult:
    status = "warning" if index % 3 == 0 else ("pass" if index % 2 == 0 else "fail")
    actual_value: str | None = None
    if "plot_ratio" in rule.parameter_key and project.target_gross_floor_area_sqm:
        ratio = project.target_gross_floor_area_sqm / project.site_area_sqm
        actual_value = f"{ratio:.2f}"
    notes = None
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

    return FeasibilityAssessmentResponse(
        project_id=_project_identifier(payload.project),
        summary=summary,
        rules=evaluated,
        recommendations=recommendations,
    )


__all__ = [
    "generate_feasibility_rules",
    "run_feasibility_assessment",
]
