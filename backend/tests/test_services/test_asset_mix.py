"""Comprehensive tests for asset_mix service module.

Tests focus on pure functions and data transformations without database
or async dependencies. Covers 15-20 tests across helper functions and
the main public API.
"""

from __future__ import annotations

import pytest

from app.services.asset_mix import (
    AssetOptimizationOutcome,
    AssetOptimizationPlan,
    ConstraintViolation,
    _append_plan_note,
    _calc_additional_ratio,
    _format_asset_label,
    _intensity_state,
    _maybe_float,
    _maybe_int,
    _normalise,
    _per_sqm_noi,
    _rebalance_plans,
    _set_plan_risk,
    _update_allocation,
    build_asset_mix,
    format_asset_mix_summary,
)


class TestHelperFunctions:
    """Test low-level utility functions."""

    def test_maybe_float_with_none(self):
        """Test _maybe_float returns None for None input."""
        assert _maybe_float(None) is None

    def test_maybe_float_with_valid_float(self):
        """Test _maybe_float converts strings and numbers to float."""
        assert _maybe_float(3.14) == 3.14
        assert _maybe_float("3.14") == 3.14
        assert _maybe_float(10) == 10.0

    def test_maybe_float_with_invalid_input(self):
        """Test _maybe_float returns None for invalid input."""
        assert _maybe_float("invalid") is None
        assert _maybe_float([]) is None

    def test_maybe_int_with_none(self):
        """Test _maybe_int returns None for None input."""
        assert _maybe_int(None) is None

    def test_maybe_int_with_valid_int(self):
        """Test _maybe_int converts strings and numbers to int."""
        assert _maybe_int(42) == 42
        assert _maybe_int("42") == 42
        assert _maybe_int(3.14) == 3

    def test_maybe_int_with_invalid_input(self):
        """Test _maybe_int returns None for invalid input."""
        assert _maybe_int("invalid") is None
        assert _maybe_int({}) is None

    def test_normalise_empty_list(self):
        """Test _normalise returns empty list for empty input."""
        assert _normalise([]) == []

    def test_normalise_single_value(self):
        """Test _normalise returns 0.5 for equal values."""
        assert _normalise([5.0]) == [0.5]
        assert _normalise([10.0, 10.0, 10.0]) == [0.5, 0.5, 0.5]

    def test_normalise_multiple_values(self):
        """Test _normalise scales values between 0 and 1."""
        result = _normalise([0.0, 50.0, 100.0])
        assert result == [0.0, 0.5, 1.0]

    def test_format_asset_label_with_underscores(self):
        """Test _format_asset_label converts underscores and title-cases."""
        assert _format_asset_label("high_spec_logistics") == "High Spec Logistics"
        assert _format_asset_label("office") == "Office"

    def test_per_sqm_noi_basic(self):
        """Test _per_sqm_noi calculation with typical values."""
        plan = AssetOptimizationPlan(
            asset_type="office",
            allocation_pct=60.0,
            rent_psm_month=128.0,
            stabilised_vacancy_pct=6.0,
            opex_pct_of_rent=18.0,
            nia_efficiency=0.82,
        )
        noi = _per_sqm_noi(plan)
        assert noi > 0
        expected = 128.0 * 12.0 * 0.82 * 0.94 * 0.82
        assert abs(noi - expected) < 0.1

    def test_per_sqm_noi_with_none_values(self):
        """Test _per_sqm_noi handles None values gracefully."""
        plan = AssetOptimizationPlan(
            asset_type="office",
            allocation_pct=60.0,
            rent_psm_month=None,
            stabilised_vacancy_pct=None,
            opex_pct_of_rent=None,
            nia_efficiency=None,
        )
        noi = _per_sqm_noi(plan)
        assert noi == 0.0

    def test_calc_additional_ratio_none_values(self):
        """Test _calc_additional_ratio returns None for invalid inputs."""
        assert _calc_additional_ratio(None, 100.0) is None
        assert _calc_additional_ratio(1000.0, None) is None
        assert _calc_additional_ratio(0, 100.0) is None

    def test_calc_additional_ratio_valid(self):
        """Test _calc_additional_ratio calculates ratio correctly."""
        result = _calc_additional_ratio(achievable_gfa=1000.0, additional_gfa=200.0)
        assert result == 0.2

    def test_calc_additional_ratio_clamped_high(self):
        """Test _calc_additional_ratio clamps high ratios to 1.5."""
        result = _calc_additional_ratio(achievable_gfa=100.0, additional_gfa=200.0)
        assert result == 1.5

    def test_intensity_state_none(self):
        """Test _intensity_state returns 'steady' for None."""
        assert _intensity_state(None) == "steady"

    def test_intensity_state_expansion_high(self):
        """Test _intensity_state returns 'expansion_high' for ratio >= 0.35."""
        assert _intensity_state(0.35) == "expansion_high"
        assert _intensity_state(0.5) == "expansion_high"

    def test_intensity_state_expansion(self):
        """Test _intensity_state returns 'expansion' for ratio 0.2-0.35."""
        assert _intensity_state(0.2) == "expansion"
        assert _intensity_state(0.25) == "expansion"

    def test_intensity_state_reposition(self):
        """Test _intensity_state returns 'reposition' for ratio <= 0.05."""
        assert _intensity_state(0.05) == "reposition"
        assert _intensity_state(-0.2) == "reposition"

    def test_update_allocation_valid(self):
        """Test _update_allocation updates plan allocation correctly."""
        plan = AssetOptimizationPlan(asset_type="office", allocation_pct=60.0)
        lookup = {"office": plan}
        _update_allocation(lookup, "office", 5.0)
        assert lookup["office"].allocation_pct == 65.0

    def test_append_plan_note_valid(self):
        """Test _append_plan_note adds note to plan."""
        plan = AssetOptimizationPlan(asset_type="office", allocation_pct=60.0, notes=[])
        lookup = {"office": plan}
        _append_plan_note(lookup, "office", "Test note")
        assert "Test note" in lookup["office"].notes

    def test_append_plan_note_duplicate(self):
        """Test _append_plan_note doesn't add duplicate notes."""
        plan = AssetOptimizationPlan(
            asset_type="office", allocation_pct=60.0, notes=["Test note"]
        )
        lookup = {"office": plan}
        _append_plan_note(lookup, "office", "Test note")
        assert lookup["office"].notes.count("Test note") == 1

    def test_set_plan_risk_basic(self):
        """Test _set_plan_risk updates risk level."""
        plan = AssetOptimizationPlan(
            asset_type="office", allocation_pct=60.0, risk_level="balanced"
        )
        lookup = {"office": plan}
        _set_plan_risk(lookup, "office", "elevated")
        assert lookup["office"].risk_level == "elevated"

    def test_set_plan_risk_with_absorption_delta(self):
        """Test _set_plan_risk adjusts absorption months."""
        plan = AssetOptimizationPlan(
            asset_type="office",
            allocation_pct=60.0,
            risk_level="balanced",
            absorption_months=12,
        )
        lookup = {"office": plan}
        _set_plan_risk(lookup, "office", "elevated", absorption_delta=6)
        assert lookup["office"].absorption_months == 18

    def test_rebalance_plans_already_balanced(self):
        """Test _rebalance_plans returns unchanged when balanced."""
        plans = [
            AssetOptimizationPlan(asset_type="office", allocation_pct=50.0),
            AssetOptimizationPlan(asset_type="retail", allocation_pct=50.0),
        ]
        result = _rebalance_plans(plans)
        assert result[0].allocation_pct == 50.0
        assert result[1].allocation_pct == 50.0

    def test_rebalance_plans_unbalanced(self):
        """Test _rebalance_plans scales allocations to sum to 100."""
        plans = [
            AssetOptimizationPlan(asset_type="office", allocation_pct=40.0),
            AssetOptimizationPlan(asset_type="retail", allocation_pct=40.0),
        ]
        result = _rebalance_plans(plans)
        assert sum(p.allocation_pct for p in result) == pytest.approx(100.0, abs=0.01)


class TestPublicFunctions:
    """Test main public API functions."""

    def test_build_asset_mix_commercial(self):
        """Test build_asset_mix for commercial land use."""
        outcome = build_asset_mix("commercial", achievable_gfa_sqm=10000.0)
        assert isinstance(outcome, AssetOptimizationOutcome)
        assert len(outcome.plans) > 0
        assert sum(p.allocation_pct for p in outcome.plans) == pytest.approx(
            100.0, abs=0.1
        )

    def test_build_asset_mix_residential(self):
        """Test build_asset_mix for residential land use."""
        outcome = build_asset_mix("residential", achievable_gfa_sqm=10000.0)
        assert len(outcome.plans) > 0
        residential = [p for p in outcome.plans if p.asset_type == "residential"]
        assert len(residential) > 0

    def test_build_asset_mix_mixed_use(self):
        """Test build_asset_mix for mixed-use land use."""
        outcome = build_asset_mix("mixed_use", achievable_gfa_sqm=10000.0)
        assert len(outcome.plans) > 0

    def test_build_asset_mix_industrial(self):
        """Test build_asset_mix for industrial land use."""
        outcome = build_asset_mix("industrial", achievable_gfa_sqm=10000.0)
        assert len(outcome.plans) > 0

    def test_build_asset_mix_with_heritage(self):
        """Test build_asset_mix applies heritage rules."""
        outcome = build_asset_mix(
            "commercial",
            achievable_gfa_sqm=10000.0,
            heritage=True,
            heritage_risk="high",
        )
        assert outcome.confidence is not None
        assert any(p.risk_level == "elevated" for p in outcome.plans)

    def test_build_asset_mix_with_expansion(self):
        """Test build_asset_mix handles expansion scenario."""
        outcome = build_asset_mix(
            "commercial",
            achievable_gfa_sqm=10000.0,
            additional_gfa=2000.0,
            site_area_sqm=1000.0,
            current_gfa_sqm=5000.0,
        )
        assert len(outcome.plans) > 0
        assert any(p.allocated_gfa_sqm is not None for p in outcome.plans)

    def test_build_asset_mix_with_constraints(self):
        """Test build_asset_mix enforces user constraints."""
        outcome = build_asset_mix(
            "commercial",
            achievable_gfa_sqm=10000.0,
            quick_metrics={
                "user_constraints": {
                    "min": {"office": 50.0},
                    "max": {"retail": 40.0},
                }
            },
        )
        office = [p for p in outcome.plans if p.asset_type == "office"][0]
        retail = [p for p in outcome.plans if p.asset_type == "retail"][0]
        assert office.allocation_pct >= 50.0
        assert retail.allocation_pct <= 40.0

    def test_build_asset_mix_confidence_score(self):
        """Test build_asset_mix calculates confidence score."""
        outcome = build_asset_mix(
            "commercial",
            achievable_gfa_sqm=10000.0,
            heritage=False,
        )
        if outcome.confidence is not None:
            assert 0.0 <= outcome.confidence <= 1.0

    def test_format_asset_mix_summary_basic(self):
        """Test format_asset_mix_summary generates recommendations."""
        plans = [
            AssetOptimizationPlan(
                asset_type="office",
                allocation_pct=60.0,
                notes=["Test note"],
            ),
            AssetOptimizationPlan(
                asset_type="retail",
                allocation_pct=40.0,
            ),
        ]
        result = format_asset_mix_summary(plans, 10000)
        assert isinstance(result, list)
        assert len(result) > 0
        assert any("office" in r.lower() for r in result)

    def test_format_asset_mix_summary_with_revenue(self):
        """Test format_asset_mix_summary includes revenue estimates."""
        plans = [
            AssetOptimizationPlan(
                asset_type="office",
                allocation_pct=60.0,
                allocated_gfa_sqm=6000.0,
                estimated_revenue_sgd=1000000.0,
            ),
        ]
        result = format_asset_mix_summary(plans, 10000)
        assert any("revenue" in r.lower() or "noi" in r.lower() for r in result)

    def test_build_asset_mix_integration_end_to_end(self):
        """Integration test: full asset mix optimization flow."""
        outcome = build_asset_mix(
            land_use="mixed_use",
            achievable_gfa_sqm=50000.0,
            additional_gfa=10000.0,
            heritage=True,
            heritage_risk="medium",
            existing_use="office complex",
            site_area_sqm=5000.0,
            current_gfa_sqm=30000.0,
            quick_metrics={
                "existing_vacancy_rate": 0.08,
                "existing_average_rent_psm": 110.0,
                "underused_mrt_count": 1.5,
                "user_constraints": {
                    "min": {"office": 30.0},
                    "max": {"hospitality": 25.0},
                },
            },
        )
        assert isinstance(outcome, AssetOptimizationOutcome)
        assert len(outcome.plans) > 0
        assert sum(p.allocation_pct for p in outcome.plans) == pytest.approx(
            100.0, abs=0.1
        )
        assert all(p.allocated_gfa_sqm is not None for p in outcome.plans)
        assert outcome.confidence is not None

    def test_build_asset_mix_none_gfa(self):
        """Test build_asset_mix handles None achievable_gfa gracefully."""
        outcome = build_asset_mix(
            "commercial",
            achievable_gfa_sqm=None,
        )
        assert len(outcome.plans) > 0

    def test_constraint_violation_structure(self):
        """Test ConstraintViolation data structure."""
        violation = ConstraintViolation(
            constraint_type="user_min_allocation",
            severity="warning",
            message="Minimum not met",
            asset_type="office",
        )
        assert violation.constraint_type == "user_min_allocation"
        assert violation.severity == "warning"
        assert violation.asset_type == "office"

    def test_asset_optimization_plan_structure(self):
        """Test AssetOptimizationPlan data structure."""
        plan = AssetOptimizationPlan(
            asset_type="office",
            allocation_pct=60.0,
            rent_psm_month=128.0,
            stabilised_vacancy_pct=6.0,
            constraint_violations=(
                ConstraintViolation(
                    constraint_type="test",
                    severity="warning",
                    message="test",
                ),
            ),
        )
        assert plan.asset_type == "office"
        assert plan.allocation_pct == 60.0
        assert len(plan.constraint_violations) == 1

    def test_asset_optimization_outcome_structure(self):
        """Test AssetOptimizationOutcome data structure."""
        plans = (
            AssetOptimizationPlan(asset_type="office", allocation_pct=60.0),
            AssetOptimizationPlan(asset_type="retail", allocation_pct=40.0),
        )
        outcome = AssetOptimizationOutcome(
            plans=plans,
            confidence=0.85,
        )
        assert len(outcome.plans) == 2
        assert outcome.confidence == 0.85
        assert len(outcome.constraint_log) == 0
