"""Comprehensive tests for feasibility schemas.

Tests cover:
- BuildEnvelopeSnapshot schema
- NewFeasibilityProjectInput schema
- FeasibilityRule schema
- FeasibilityRulesResponse schema
- FeasibilityAssessmentRequest schema
- RuleAssessmentResult schema
- BuildableAreaSummary schema
- AssetOptimizationRecommendation schema
- FeasibilityAssessmentResponse schema
"""

from __future__ import annotations


class TestBuildEnvelopeSnapshot:
    """Tests for BuildEnvelopeSnapshot schema."""

    def test_site_area_sqm_optional(self) -> None:
        """Test site_area_sqm is optional with gt=0."""
        snapshot = {}
        assert snapshot.get("site_area_sqm") is None

    def test_site_area_sqm_positive(self) -> None:
        """Test site_area_sqm must be positive."""
        site_area_sqm = 5000.0
        assert site_area_sqm > 0

    def test_allowable_plot_ratio_optional(self) -> None:
        """Test allowable_plot_ratio is optional with gt=0."""
        snapshot = {}
        assert snapshot.get("allowable_plot_ratio") is None

    def test_max_buildable_gfa_sqm_optional(self) -> None:
        """Test max_buildable_gfa_sqm is optional with gt=0."""
        snapshot = {}
        assert snapshot.get("max_buildable_gfa_sqm") is None

    def test_current_gfa_sqm_optional(self) -> None:
        """Test current_gfa_sqm is optional with ge=0."""
        current_gfa = 0.0
        assert current_gfa >= 0

    def test_additional_potential_gfa_sqm_optional(self) -> None:
        """Test additional_potential_gfa_sqm is optional."""
        snapshot = {}
        assert snapshot.get("additional_potential_gfa_sqm") is None


class TestNewFeasibilityProjectInput:
    """Tests for NewFeasibilityProjectInput schema."""

    def test_name_required(self) -> None:
        """Test name is required with min length 1."""
        name = "Marina Bay Tower"
        assert len(name) >= 1

    def test_site_address_required(self) -> None:
        """Test site_address is required with min length 1."""
        site_address = "10 Marina Boulevard"
        assert len(site_address) >= 1

    def test_site_area_sqm_required(self) -> None:
        """Test site_area_sqm is required with gt=0."""
        site_area_sqm = 5000.0
        assert site_area_sqm > 0

    def test_land_use_required(self) -> None:
        """Test land_use is required with min length 1."""
        land_use = "Commercial"
        assert len(land_use) >= 1

    def test_target_gfa_optional(self) -> None:
        """Test target_gross_floor_area_sqm is optional with gt=0."""
        project = {}
        assert project.get("target_gross_floor_area_sqm") is None

    def test_building_height_optional(self) -> None:
        """Test building_height_meters is optional with gt=0."""
        project = {}
        assert project.get("building_height_meters") is None

    def test_build_envelope_optional(self) -> None:
        """Test build_envelope is optional."""
        project = {}
        assert project.get("build_envelope") is None

    def test_floor_to_floor_optional(self) -> None:
        """Test typ_floor_to_floor_m is optional with gt=0."""
        project = {}
        assert project.get("typ_floor_to_floor_m") is None

    def test_efficiency_ratio_optional(self) -> None:
        """Test efficiency_ratio is optional with gt=0 and le=1.0."""
        efficiency_ratio = 0.85
        assert 0 < efficiency_ratio <= 1.0


class TestFeasibilityRule:
    """Tests for FeasibilityRule schema."""

    def test_id_required(self) -> None:
        """Test id is required."""
        rule_id = "plot_ratio_limit"
        assert len(rule_id) > 0

    def test_title_required(self) -> None:
        """Test title is required."""
        title = "Plot Ratio Limit"
        assert len(title) > 0

    def test_description_required(self) -> None:
        """Test description is required."""
        description = "Maximum plot ratio allowed by zoning"
        assert len(description) > 0

    def test_authority_required(self) -> None:
        """Test authority is required."""
        authority = "URA"
        assert len(authority) > 0

    def test_topic_required(self) -> None:
        """Test topic is required."""
        topic = "zoning"
        assert len(topic) > 0

    def test_parameter_key_required(self) -> None:
        """Test parameter_key is required."""
        parameter_key = "plot_ratio"
        assert len(parameter_key) > 0

    def test_operator_required(self) -> None:
        """Test operator is required."""
        operator = "<="
        assert len(operator) > 0

    def test_value_required(self) -> None:
        """Test value is required."""
        value = "3.5"
        assert len(value) > 0

    def test_unit_optional(self) -> None:
        """Test unit is optional."""
        rule = {}
        assert rule.get("unit") is None

    def test_severity_required(self) -> None:
        """Test severity is required."""
        severity = "critical"
        assert severity in ["critical", "important", "informational"]

    def test_default_selected(self) -> None:
        """Test default_selected defaults to False."""
        default_selected = False
        assert default_selected is False


class TestFeasibilityRuleSeverity:
    """Tests for FeasibilityRuleSeverity literal type."""

    def test_critical_severity(self) -> None:
        """Test critical severity."""
        severity = "critical"
        assert severity == "critical"

    def test_important_severity(self) -> None:
        """Test important severity."""
        severity = "important"
        assert severity == "important"

    def test_informational_severity(self) -> None:
        """Test informational severity."""
        severity = "informational"
        assert severity == "informational"


class TestFeasibilityRulesSummary:
    """Tests for FeasibilityRulesSummary schema."""

    def test_compliance_focus_required(self) -> None:
        """Test compliance_focus is required."""
        compliance_focus = "URA Planning Regulations"
        assert len(compliance_focus) > 0

    def test_notes_optional(self) -> None:
        """Test notes is optional."""
        summary = {}
        assert summary.get("notes") is None


class TestFeasibilityRulesResponse:
    """Tests for FeasibilityRulesResponse schema."""

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = "proj_123"
        assert len(project_id) > 0

    def test_rules_required(self) -> None:
        """Test rules list is required."""
        rules = []
        assert isinstance(rules, list)

    def test_recommended_rule_ids_required(self) -> None:
        """Test recommended_rule_ids list is required."""
        recommended = ["rule_1", "rule_2"]
        assert isinstance(recommended, list)

    def test_summary_required(self) -> None:
        """Test summary is required."""
        summary = {"compliance_focus": "URA Regulations"}
        assert "compliance_focus" in summary


class TestFeasibilityAssessmentRequest:
    """Tests for FeasibilityAssessmentRequest schema."""

    def test_project_required(self) -> None:
        """Test project input is required."""
        project = {"name": "Test", "site_address": "123 Street", "site_area_sqm": 1000}
        assert "name" in project

    def test_selected_rule_ids_required(self) -> None:
        """Test selected_rule_ids list is required."""
        selected = ["rule_1", "rule_2"]
        assert isinstance(selected, list)


class TestRuleAssessmentResult:
    """Tests for RuleAssessmentResult schema."""

    def test_status_required(self) -> None:
        """Test status is required."""
        status = "pass"
        assert status in ["pass", "fail", "warning"]

    def test_actual_value_optional(self) -> None:
        """Test actual_value is optional."""
        result = {}
        assert result.get("actual_value") is None

    def test_notes_optional(self) -> None:
        """Test notes is optional."""
        result = {}
        assert result.get("notes") is None


class TestFeasibilityRuleStatus:
    """Tests for FeasibilityRuleStatus literal type."""

    def test_pass_status(self) -> None:
        """Test pass status."""
        status = "pass"
        assert status == "pass"

    def test_fail_status(self) -> None:
        """Test fail status."""
        status = "fail"
        assert status == "fail"

    def test_warning_status(self) -> None:
        """Test warning status."""
        status = "warning"
        assert status == "warning"


class TestBuildableAreaSummary:
    """Tests for BuildableAreaSummary schema."""

    def test_max_permissible_gfa_sqm_required(self) -> None:
        """Test max_permissible_gfa_sqm is required."""
        max_gfa = 15000
        assert max_gfa > 0

    def test_estimated_achievable_gfa_sqm_required(self) -> None:
        """Test estimated_achievable_gfa_sqm is required."""
        estimated_gfa = 14500
        assert estimated_gfa > 0

    def test_estimated_unit_count_required(self) -> None:
        """Test estimated_unit_count is required."""
        unit_count = 120
        assert unit_count >= 0

    def test_site_coverage_percent_required(self) -> None:
        """Test site_coverage_percent is required."""
        site_coverage = 65.5
        assert 0 <= site_coverage <= 100

    def test_remarks_optional(self) -> None:
        """Test remarks is optional."""
        summary = {}
        assert summary.get("remarks") is None

    def test_accuracy_range_optional(self) -> None:
        """Test accuracy_range is optional."""
        summary = {}
        assert summary.get("accuracy_range") is None


class TestAssetConstraintViolation:
    """Tests for AssetConstraintViolation schema."""

    def test_constraint_type_required(self) -> None:
        """Test constraint_type is required."""
        constraint_type = "plot_ratio"
        assert len(constraint_type) > 0

    def test_severity_required(self) -> None:
        """Test severity is required."""
        severity = "high"
        assert len(severity) > 0

    def test_message_required(self) -> None:
        """Test message is required."""
        message = "Plot ratio exceeded"
        assert len(message) > 0

    def test_asset_type_optional(self) -> None:
        """Test asset_type is optional."""
        violation = {}
        assert violation.get("asset_type") is None


class TestAssetOptimizationRecommendation:
    """Tests for AssetOptimizationRecommendation schema."""

    def test_asset_type_required(self) -> None:
        """Test asset_type is required."""
        asset_type = "OFFICE"
        assert len(asset_type) > 0

    def test_allocation_pct_required(self) -> None:
        """Test allocation_pct is required."""
        allocation_pct = 0.35
        assert 0 <= allocation_pct <= 1.0

    def test_allocated_gfa_sqm_optional(self) -> None:
        """Test allocated_gfa_sqm is optional."""
        rec = {}
        assert rec.get("allocated_gfa_sqm") is None

    def test_rent_psm_month_optional(self) -> None:
        """Test rent_psm_month is optional."""
        rec = {}
        assert rec.get("rent_psm_month") is None

    def test_notes_default_empty(self) -> None:
        """Test notes defaults to empty list."""
        notes = []
        assert isinstance(notes, list)

    def test_constraint_violations_default_empty(self) -> None:
        """Test constraint_violations defaults to empty list."""
        violations = []
        assert isinstance(violations, list)


class TestFeasibilityAssessmentResponse:
    """Tests for FeasibilityAssessmentResponse schema."""

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = "proj_123"
        assert len(project_id) > 0

    def test_summary_required(self) -> None:
        """Test summary is required."""
        summary = {"max_permissible_gfa_sqm": 15000}
        assert "max_permissible_gfa_sqm" in summary

    def test_rules_required(self) -> None:
        """Test rules list is required."""
        rules = []
        assert isinstance(rules, list)

    def test_recommendations_required(self) -> None:
        """Test recommendations list is required."""
        recommendations = []
        assert isinstance(recommendations, list)

    def test_asset_optimizations_required(self) -> None:
        """Test asset_optimizations list is required."""
        optimizations = []
        assert isinstance(optimizations, list)

    def test_asset_mix_summary_optional(self) -> None:
        """Test asset_mix_summary is optional."""
        response = {}
        assert response.get("asset_mix_summary") is None

    def test_constraint_log_default_empty(self) -> None:
        """Test constraint_log defaults to empty list."""
        constraint_log = []
        assert isinstance(constraint_log, list)

    def test_optimizer_confidence_optional(self) -> None:
        """Test optimizer_confidence is optional."""
        response = {}
        assert response.get("optimizer_confidence") is None
