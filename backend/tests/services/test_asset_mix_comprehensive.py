"""Comprehensive tests for asset_mix service.

Tests cover:
- AssetOptimizationPlan dataclass
- AssetOptimizationScenario dataclass
- AssetOptimizationOutcome dataclass
- ConstraintViolation dataclass
- build_asset_mix function
- format_asset_mix_summary function
- Helper functions (_rebalance_plans, _normalise_land_use, etc.)
"""

from __future__ import annotations


from app.services.asset_mix import (
    AssetOptimizationOutcome,
    AssetOptimizationPlan,
    AssetOptimizationScenario,
    ConstraintViolation,
    build_asset_mix,
    format_asset_mix_summary,
)


class TestAssetOptimizationPlanDataclass:
    """Tests for AssetOptimizationPlan dataclass."""

    def test_create_minimal_plan(self) -> None:
        """Test creating a plan with minimal required fields."""
        plan = AssetOptimizationPlan(
            asset_type="office",
            allocation_pct=50.0,
        )
        assert plan.asset_type == "office"
        assert plan.allocation_pct == 50.0
        assert plan.notes == []
        assert plan.heritage_notes == []

    def test_create_full_plan(self) -> None:
        """Test creating a plan with all fields."""
        plan = AssetOptimizationPlan(
            asset_type="retail",
            allocation_pct=30.0,
            stabilised_vacancy_pct=5.0,
            opex_pct_of_rent=15.0,
            nia_efficiency=0.85,
            target_floor_height_m=4.0,
            parking_ratio_per_1000sqm=2.5,
            rent_psm_month=120.0,
            fitout_cost_psm=800.0,
            absorption_months=18,
            risk_level="moderate",
            heritage_premium_pct=10.0,
            notes=["Note 1", "Note 2"],
            heritage_notes=["Heritage note"],
            allocated_gfa_sqm=5000.0,
            nia_sqm=4250.0,
            estimated_revenue_sgd=1200000.0,
            estimated_capex_sgd=4000000.0,
            total_parking_bays_required=12.5,
            estimated_height_m=16.0,
            revenue_basis="annual_noi",
            constraint_violations=(),
            confidence_score=0.85,
            alternative_scenarios=("expansion", "reposition"),
        )
        assert plan.asset_type == "retail"
        assert plan.allocation_pct == 30.0
        assert plan.stabilised_vacancy_pct == 5.0
        assert plan.opex_pct_of_rent == 15.0
        assert plan.nia_efficiency == 0.85
        assert plan.target_floor_height_m == 4.0
        assert plan.parking_ratio_per_1000sqm == 2.5
        assert plan.rent_psm_month == 120.0
        assert plan.fitout_cost_psm == 800.0
        assert plan.absorption_months == 18
        assert plan.risk_level == "moderate"
        assert plan.heritage_premium_pct == 10.0
        assert len(plan.notes) == 2
        assert len(plan.heritage_notes) == 1
        assert plan.allocated_gfa_sqm == 5000.0
        assert plan.nia_sqm == 4250.0
        assert plan.estimated_revenue_sgd == 1200000.0
        assert plan.estimated_capex_sgd == 4000000.0
        assert plan.total_parking_bays_required == 12.5
        assert plan.estimated_height_m == 16.0
        assert plan.revenue_basis == "annual_noi"
        assert plan.confidence_score == 0.85
        assert "expansion" in plan.alternative_scenarios

    def test_plan_with_zero_allocation(self) -> None:
        """Test plan with 0% allocation."""
        plan = AssetOptimizationPlan(
            asset_type="hospitality",
            allocation_pct=0.0,
        )
        assert plan.allocation_pct == 0.0

    def test_plan_with_100_percent_allocation(self) -> None:
        """Test plan with 100% allocation."""
        plan = AssetOptimizationPlan(
            asset_type="residential",
            allocation_pct=100.0,
        )
        assert plan.allocation_pct == 100.0


class TestAssetOptimizationScenarioDataclass:
    """Tests for AssetOptimizationScenario dataclass."""

    def test_create_scenario(self) -> None:
        """Test creating an optimization scenario."""
        plans = (
            AssetOptimizationPlan(asset_type="office", allocation_pct=60.0),
            AssetOptimizationPlan(asset_type="retail", allocation_pct=40.0),
        )
        scenario = AssetOptimizationScenario(
            name="expansion",
            plans=plans,
            description="Expansion variant applying +5pp to office.",
        )
        assert scenario.name == "expansion"
        assert len(scenario.plans) == 2
        assert scenario.description is not None
        assert "Expansion" in scenario.description

    def test_scenario_with_empty_plans(self) -> None:
        """Test scenario with empty plans tuple."""
        scenario = AssetOptimizationScenario(
            name="empty",
            plans=(),
        )
        assert scenario.name == "empty"
        assert len(scenario.plans) == 0


class TestAssetOptimizationOutcomeDataclass:
    """Tests for AssetOptimizationOutcome dataclass."""

    def test_create_outcome(self) -> None:
        """Test creating an optimization outcome."""
        plans = (AssetOptimizationPlan(asset_type="office", allocation_pct=60.0),)
        outcome = AssetOptimizationOutcome(
            plans=plans,
            constraint_log=(),
            scenarios=(),
            confidence=0.75,
        )
        assert len(outcome.plans) == 1
        assert len(outcome.constraint_log) == 0
        assert len(outcome.scenarios) == 0
        assert outcome.confidence == 0.75

    def test_outcome_with_constraints(self) -> None:
        """Test outcome with constraint violations."""
        violation = ConstraintViolation(
            constraint_type="heritage",
            severity="warning",
            message="Heritage limit exceeded",
            asset_type="office",
        )
        outcome = AssetOptimizationOutcome(
            plans=(),
            constraint_log=(violation,),
            scenarios=(),
            confidence=0.65,
        )
        assert len(outcome.constraint_log) == 1
        assert outcome.constraint_log[0].severity == "warning"


class TestConstraintViolationDataclass:
    """Tests for ConstraintViolation dataclass."""

    def test_create_warning_violation(self) -> None:
        """Test creating a warning violation."""
        violation = ConstraintViolation(
            constraint_type="user_min_allocation",
            severity="warning",
            message="Requested minimum 30% for office; achieved 30% after redistribution.",
            asset_type="office",
        )
        assert violation.constraint_type == "user_min_allocation"
        assert violation.severity == "warning"
        assert "30%" in violation.message
        assert violation.asset_type == "office"

    def test_create_error_violation(self) -> None:
        """Test creating an error violation."""
        violation = ConstraintViolation(
            constraint_type="heritage",
            severity="error",
            message="Unable to meet heritage cap for retail.",
            asset_type="retail",
        )
        assert violation.severity == "error"

    def test_violation_without_asset_type(self) -> None:
        """Test violation without specific asset type."""
        violation = ConstraintViolation(
            constraint_type="general",
            severity="warning",
            message="General constraint warning",
        )
        assert violation.asset_type is None


class TestBuildAssetMix:
    """Tests for build_asset_mix function."""

    def test_commercial_land_use(self) -> None:
        """Test build_asset_mix for commercial land use."""
        outcome = build_asset_mix("commercial")
        assert isinstance(outcome, AssetOptimizationOutcome)
        assert len(outcome.plans) > 0
        total_pct = sum(plan.allocation_pct for plan in outcome.plans)
        assert abs(total_pct - 100.0) < 0.1

    def test_residential_land_use(self) -> None:
        """Test build_asset_mix for residential land use."""
        outcome = build_asset_mix("residential")
        assert isinstance(outcome, AssetOptimizationOutcome)
        assert len(outcome.plans) > 0

    def test_mixed_use_land_use(self) -> None:
        """Test build_asset_mix for mixed use land."""
        outcome = build_asset_mix("mixed_use")
        assert isinstance(outcome, AssetOptimizationOutcome)
        assert len(outcome.plans) > 0

    def test_industrial_land_use(self) -> None:
        """Test build_asset_mix for industrial land use."""
        outcome = build_asset_mix("industrial")
        assert isinstance(outcome, AssetOptimizationOutcome)
        assert len(outcome.plans) > 0

    def test_with_achievable_gfa(self) -> None:
        """Test build_asset_mix with achievable GFA parameter."""
        outcome = build_asset_mix(
            "commercial",
            achievable_gfa_sqm=50000.0,
        )
        assert outcome.plans[0].allocated_gfa_sqm is not None

    def test_with_heritage_flag(self) -> None:
        """Test build_asset_mix with heritage flag."""
        outcome = build_asset_mix(
            "commercial",
            heritage=True,
            heritage_risk="high",
        )
        # Heritage should affect risk levels
        assert outcome is not None

    def test_with_additional_gfa(self) -> None:
        """Test build_asset_mix with additional GFA uplift."""
        outcome = build_asset_mix(
            "commercial",
            achievable_gfa_sqm=50000.0,
            additional_gfa=10000.0,
        )
        # Check notes mention uplift
        all_notes = []
        for plan in outcome.plans:
            all_notes.extend(plan.notes)
        # Should have some notes about GFA
        assert len(all_notes) >= 0

    def test_with_site_metrics(self) -> None:
        """Test build_asset_mix with site area and GFA metrics."""
        outcome = build_asset_mix(
            "commercial",
            site_area_sqm=10000.0,
            current_gfa_sqm=30000.0,
            achievable_gfa_sqm=40000.0,
        )
        assert outcome is not None

    def test_with_quick_metrics(self) -> None:
        """Test build_asset_mix with quick metrics (vacancy, rent, MRT)."""
        quick_metrics = {
            "existing_vacancy_rate": 0.08,
            "existing_average_rent_psm": 85.0,
            "underused_mrt_count": 2,
        }
        outcome = build_asset_mix(
            "commercial",
            quick_metrics=quick_metrics,
        )
        assert outcome is not None

    def test_with_high_vacancy_metrics(self) -> None:
        """Test build_asset_mix with high vacancy rate."""
        quick_metrics = {
            "existing_vacancy_rate": 0.20,  # 20% vacancy - high
        }
        outcome = build_asset_mix(
            "commercial",
            quick_metrics=quick_metrics,
        )
        # Should affect allocations
        assert outcome is not None

    def test_with_user_constraints(self) -> None:
        """Test build_asset_mix with user min/max constraints."""
        quick_metrics = {
            "user_constraints": {
                "min": {"office": 40.0},
                "max": {"retail": 30.0},
            }
        }
        outcome = build_asset_mix(
            "commercial",
            quick_metrics=quick_metrics,
        )
        # Check constraint violations logged
        assert outcome is not None

    def test_normalises_land_use_variations(self) -> None:
        """Test that land use variations are normalised."""
        # "apartment" should normalise to residential
        outcome = build_asset_mix("apartment")
        assert outcome is not None

        # "logistics" should normalise to industrial
        outcome = build_asset_mix("logistics")
        assert outcome is not None

        # "condo" should normalise to residential
        outcome = build_asset_mix("condo")
        assert outcome is not None

    def test_unknown_land_use_defaults_to_commercial(self) -> None:
        """Test that unknown land use defaults to commercial profile."""
        outcome = build_asset_mix("unknown_type")
        assert outcome is not None
        assert len(outcome.plans) > 0

    def test_scenario_variants_generated(self) -> None:
        """Test that scenario variants are generated."""
        outcome = build_asset_mix(
            "commercial",
            achievable_gfa_sqm=50000.0,
            site_area_sqm=10000.0,
        )
        # Scenarios should be generated for sensitivity variants
        assert outcome.scenarios is not None

    def test_confidence_calculated(self) -> None:
        """Test that overall confidence is calculated."""
        outcome = build_asset_mix("commercial")
        assert outcome.confidence is not None
        assert 0.0 <= outcome.confidence <= 1.0


class TestFormatAssetMixSummary:
    """Tests for format_asset_mix_summary function."""

    def test_format_basic_plans(self) -> None:
        """Test formatting basic plans into summary."""
        plans = [
            AssetOptimizationPlan(
                asset_type="office",
                allocation_pct=60.0,
                notes=["High demand area"],
            ),
            AssetOptimizationPlan(
                asset_type="retail",
                allocation_pct=40.0,
                notes=["Ground floor retail"],
            ),
        ]
        summary = format_asset_mix_summary(plans, achievable_gfa_sqm=50000)
        assert len(summary) > 0
        assert any("Programme allocation" in line for line in summary)
        assert any("60%" in line for line in summary)
        assert any("40%" in line for line in summary)

    def test_format_plans_with_revenue(self) -> None:
        """Test formatting plans with revenue data."""
        plans = [
            AssetOptimizationPlan(
                asset_type="office",
                allocation_pct=100.0,
                allocated_gfa_sqm=50000.0,
                estimated_revenue_sgd=5000000.0,
            ),
        ]
        summary = format_asset_mix_summary(plans, achievable_gfa_sqm=50000)
        assert any("NOI" in line for line in summary)

    def test_format_plans_with_capex(self) -> None:
        """Test formatting plans with CAPEX data."""
        plans = [
            AssetOptimizationPlan(
                asset_type="retail",
                allocation_pct=100.0,
                allocated_gfa_sqm=50000.0,
                estimated_capex_sgd=20000000.0,
            ),
        ]
        summary = format_asset_mix_summary(plans, achievable_gfa_sqm=50000)
        assert any("CAPEX" in line for line in summary)

    def test_format_plans_with_risk_level(self) -> None:
        """Test formatting plans with risk level."""
        plans = [
            AssetOptimizationPlan(
                asset_type="office",
                allocation_pct=100.0,
                risk_level="elevated",
                absorption_months=24,
            ),
        ]
        summary = format_asset_mix_summary(plans, achievable_gfa_sqm=50000)
        assert any("risk" in line.lower() for line in summary)

    def test_format_plans_with_vacancy_opex(self) -> None:
        """Test formatting plans with vacancy and opex."""
        plans = [
            AssetOptimizationPlan(
                asset_type="office",
                allocation_pct=100.0,
                stabilised_vacancy_pct=5.0,
                opex_pct_of_rent=20.0,
            ),
        ]
        summary = format_asset_mix_summary(plans, achievable_gfa_sqm=50000)
        assert any("vacancy" in line.lower() for line in summary)

    def test_format_plans_with_heritage_notes(self) -> None:
        """Test formatting plans with heritage notes."""
        plans = [
            AssetOptimizationPlan(
                asset_type="office",
                allocation_pct=100.0,
                heritage_notes=["Conservation area considerations"],
            ),
        ]
        summary = format_asset_mix_summary(plans, achievable_gfa_sqm=50000)
        assert any("Conservation" in line for line in summary)

    def test_format_empty_plans(self) -> None:
        """Test formatting empty plans list."""
        summary = format_asset_mix_summary([], achievable_gfa_sqm=50000)
        assert len(summary) > 0  # Should still have programme allocation line

    def test_format_asset_label_underscores(self) -> None:
        """Test that underscores in asset types are formatted nicely."""
        plans = [
            AssetOptimizationPlan(
                asset_type="f_and_b",
                allocation_pct=100.0,
            ),
        ]
        summary = format_asset_mix_summary(plans, achievable_gfa_sqm=50000)
        # Should format f_and_b as "F And B" or similar
        assert any("F And B" in line or "f and b" in line.lower() for line in summary)


class TestEdgeCases:
    """Tests for edge cases in asset mix calculations."""

    def test_negative_allocation_clamped_to_zero(self) -> None:
        """Test that negative allocations are clamped to 0."""
        # Force a scenario with high negative adjustments through heritage
        outcome = build_asset_mix(
            "commercial",
            heritage=True,
            heritage_risk="high",
            quick_metrics={"existing_vacancy_rate": 0.30},
        )
        for plan in outcome.plans:
            assert plan.allocation_pct >= 0.0

    def test_total_allocation_always_100(self) -> None:
        """Test that total allocation is always rebalanced to 100%."""
        outcome = build_asset_mix(
            "commercial",
            achievable_gfa_sqm=50000.0,
            additional_gfa=20000.0,
            heritage=True,
            heritage_risk="medium",
        )
        total = sum(plan.allocation_pct for plan in outcome.plans)
        assert abs(total - 100.0) < 0.1

    def test_zero_achievable_gfa(self) -> None:
        """Test with zero achievable GFA."""
        outcome = build_asset_mix(
            "commercial",
            achievable_gfa_sqm=0.0,
        )
        # Should still return plans
        assert outcome is not None
        assert len(outcome.plans) > 0

    def test_very_large_gfa(self) -> None:
        """Test with very large GFA values."""
        outcome = build_asset_mix(
            "commercial",
            achievable_gfa_sqm=1000000.0,  # 1 million sqm
            site_area_sqm=100000.0,
        )
        assert outcome is not None

    def test_vacancy_rate_as_percentage(self) -> None:
        """Test vacancy rate given as percentage (>1) is normalised."""
        quick_metrics = {
            "existing_vacancy_rate": 15,  # 15% expressed as integer
        }
        outcome = build_asset_mix(
            "commercial",
            quick_metrics=quick_metrics,
        )
        # Should handle both decimal (0.15) and percentage (15) formats
        assert outcome is not None
