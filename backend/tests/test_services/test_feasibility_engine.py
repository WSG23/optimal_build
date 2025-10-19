from __future__ import annotations

from app.schemas.feasibility import (
    BuildEnvelopeSnapshot,
    FeasibilityAssessmentRequest,
    NewFeasibilityProjectInput,
)
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
    assert response.asset_mix_summary is not None
    assert response.asset_mix_summary.total_estimated_revenue_sgd is not None
