from __future__ import annotations

from app.schemas.feasibility import (
    BuildEnvelopeSnapshot,
    FeasibilityAssessmentRequest,
    NewFeasibilityProjectInput,
)
from app.services.asset_mix import build_asset_mix
from app.services.feasibility import run_feasibility_assessment


def test_feasibility_summary_uses_envelope_inputs() -> None:
    project = NewFeasibilityProjectInput(
        name="Commercial Redevelopment",
        site_address="1 Developer Way",
        site_area_sqm=3800,
        land_use="commercial",
        target_gross_floor_area_sqm=None,
        build_envelope=BuildEnvelopeSnapshot(
            site_area_sqm=4500,
            allowable_plot_ratio=4.2,
            max_buildable_gfa_sqm=18900,
            current_gfa_sqm=12500,
            additional_potential_gfa_sqm=5200,
        ),
    )
    request = FeasibilityAssessmentRequest(
        project=project, selected_rule_ids=["ura-plot-ratio"]
    )

    response = run_feasibility_assessment(request)

    summary = response.summary
    assert summary.max_permissible_gfa_sqm == 18900
    assert summary.estimated_achievable_gfa_sqm <= 18900
    assert summary.estimated_achievable_gfa_sqm >= 15000
    assert summary.site_coverage_percent <= 45
    assert response.rules[0].actual_value is not None
    assert response.rules[0].status in {"pass", "warning"}
    assert any(
        "Grade A office floors" in rec or "GFA" in rec
        for rec in response.recommendations
    )
    assert response.asset_optimizations
    assert response.asset_optimizations[0].asset_type == "office"
    assert response.asset_optimizations[0].allocated_gfa_sqm is not None
    assert response.asset_optimizations[0].estimated_revenue_sgd is not None
    assert response.asset_optimizations[0].risk_level is not None
    assert response.asset_optimizations[0].rent_psm_month is not None
    assert response.asset_optimizations[0].stabilised_vacancy_pct is not None
    assert response.asset_optimizations[0].opex_pct_of_rent is not None
    assert response.asset_optimizations[0].fitout_cost_psm is not None
    assert response.asset_mix_summary is not None
    assert response.asset_mix_summary.total_estimated_revenue_sgd is not None
    assert isinstance(response.constraint_log, list)
    assert response.optimizer_confidence is not None


def test_build_asset_mix_expansion_adjusts_allocations() -> None:
    outcome = build_asset_mix(
        "commercial",
        achievable_gfa_sqm=20000.0,
        additional_gfa=6000.0,
        existing_use="Commercial Tower",
    )
    plans = outcome.plans

    office_plan = next(plan for plan in plans if plan.asset_type == "office")
    amenities_plan = next(plan for plan in plans if plan.asset_type == "amenities")

    assert office_plan.allocation_pct > 60.0
    assert office_plan.risk_level == "elevated"
    assert any("density" in note.lower() for note in office_plan.notes)
    assert amenities_plan.allocation_pct < 15.0
    assert outcome.confidence is not None
    assert outcome.scenarios


def test_build_asset_mix_vacancy_rebalances_mix() -> None:
    outcome = build_asset_mix(
        "commercial",
        achievable_gfa_sqm=15000.0,
        additional_gfa=1000.0,
        existing_use="commercial",
        site_area_sqm=5000.0,
        current_gfa_sqm=11000.0,
        quick_metrics={"existing_vacancy_rate": 0.18},
    )
    plans = outcome.plans

    office_plan = next(plan for plan in plans if plan.asset_type == "office")
    amenities_plan = next(plan for plan in plans if plan.asset_type == "amenities")

    assert office_plan.allocation_pct < 60.0
    assert any("vacancy" in note.lower() for note in office_plan.notes)
    assert amenities_plan.allocation_pct > 15.0
    assert isinstance(outcome.constraint_log, tuple)


def test_build_asset_mix_user_constraints_logged() -> None:
    outcome = build_asset_mix(
        "commercial",
        achievable_gfa_sqm=12000.0,
        quick_metrics={
            "user_constraints": {"min": {"retail": 40.0}},
            "existing_vacancy_rate": 0.1,
        },
    )
    retail_plan = next(plan for plan in outcome.plans if plan.asset_type == "retail")
    assert retail_plan.allocation_pct >= 39.0
    assert retail_plan.constraint_violations
    assert any(
        violation.constraint_type == "user_min_allocation"
        for violation in retail_plan.constraint_violations
    )
    assert any(
        violation.constraint_type == "user_min_allocation"
        for violation in outcome.constraint_log
    )
