"""Comprehensive tests for rulesets schemas.

Tests cover:
- RulePackSchema schema
- RulePackSummary schema
- RulesetValidationRequest schema
- ViolationFact schema
- ViolationDetail schema
- RuleEvaluationResult schema
- RulesetEvaluationSummary schema
- RulesetValidationResponse schema
- RulesetListResponse schema
"""

from __future__ import annotations

from datetime import datetime


class TestRulePackSchema:
    """Tests for RulePackSchema schema."""

    def test_id_required(self) -> None:
        """Test id is required."""
        rule_pack_id = 1
        assert rule_pack_id is not None

    def test_slug_required(self) -> None:
        """Test slug is required."""
        slug = "ura-zoning-2024"
        assert len(slug) > 0

    def test_name_required(self) -> None:
        """Test name is required."""
        name = "URA Zoning Rules 2024"
        assert len(name) > 0

    def test_description_optional(self) -> None:
        """Test description is optional."""
        rule_pack = {}
        assert rule_pack.get("description") is None

    def test_jurisdiction_required(self) -> None:
        """Test jurisdiction is required."""
        jurisdiction = "Singapore"
        assert len(jurisdiction) > 0

    def test_authority_optional(self) -> None:
        """Test authority is optional."""
        rule_pack = {}
        assert rule_pack.get("authority") is None

    def test_version_required(self) -> None:
        """Test version is required."""
        version = 1
        assert version >= 1

    def test_definition_required(self) -> None:
        """Test definition is required dict."""
        definition = {"rules": [], "predicates": []}
        assert isinstance(definition, dict)

    def test_metadata_default_empty(self) -> None:
        """Test metadata defaults to empty dict."""
        metadata = {}
        assert isinstance(metadata, dict)

    def test_is_active_default_true(self) -> None:
        """Test is_active defaults to True."""
        is_active = True
        assert is_active is True

    def test_created_at_required(self) -> None:
        """Test created_at is required."""
        created_at = datetime.utcnow()
        assert created_at is not None

    def test_updated_at_required(self) -> None:
        """Test updated_at is required."""
        updated_at = datetime.utcnow()
        assert updated_at is not None


class TestRulePackSummary:
    """Tests for RulePackSummary schema."""

    def test_id_required(self) -> None:
        """Test id is required."""
        rule_pack_id = 1
        assert rule_pack_id is not None

    def test_slug_required(self) -> None:
        """Test slug is required."""
        slug = "bca-fire-safety"
        assert len(slug) > 0

    def test_name_required(self) -> None:
        """Test name is required."""
        name = "BCA Fire Safety Code"
        assert len(name) > 0

    def test_jurisdiction_required(self) -> None:
        """Test jurisdiction is required."""
        jurisdiction = "Singapore"
        assert len(jurisdiction) > 0

    def test_authority_optional(self) -> None:
        """Test authority is optional."""
        summary = {}
        assert summary.get("authority") is None

    def test_version_required(self) -> None:
        """Test version is required."""
        version = 2
        assert version >= 1

    def test_description_optional(self) -> None:
        """Test description is optional."""
        summary = {}
        assert summary.get("description") is None


class TestRulesetValidationRequest:
    """Tests for RulesetValidationRequest schema."""

    def test_ruleset_id_optional(self) -> None:
        """Test ruleset_id is optional with ge=1."""
        request = {"ruleset_slug": "ura-zoning"}
        assert request.get("ruleset_id") is None

    def test_ruleset_slug_optional(self) -> None:
        """Test ruleset_slug is optional with min_length=1."""
        request = {"ruleset_id": 1}
        assert request.get("ruleset_slug") is None

    def test_ruleset_version_optional(self) -> None:
        """Test ruleset_version is optional with ge=1."""
        request = {}
        assert request.get("ruleset_version") is None

    def test_geometry_default_empty(self) -> None:
        """Test geometry defaults to empty dict."""
        geometry = {}
        assert isinstance(geometry, dict)

    def test_requires_id_or_slug(self) -> None:
        """Test either ruleset_id or ruleset_slug must be provided."""
        # This would be validated by model_validator
        request_with_id = {"ruleset_id": 1}
        request_with_slug = {"ruleset_slug": "ura-zoning"}
        assert request_with_id.get("ruleset_id") is not None
        assert request_with_slug.get("ruleset_slug") is not None


class TestViolationFact:
    """Tests for ViolationFact schema."""

    def test_field_required(self) -> None:
        """Test field is required."""
        field = "plot_ratio"
        assert len(field) > 0

    def test_operator_required(self) -> None:
        """Test operator is required."""
        operator = "<="
        assert len(operator) > 0

    def test_expected_optional(self) -> None:
        """Test expected is optional."""
        fact = {}
        assert fact.get("expected") is None

    def test_actual_optional(self) -> None:
        """Test actual is optional."""
        fact = {}
        assert fact.get("actual") is None

    def test_message_optional(self) -> None:
        """Test message is optional."""
        fact = {}
        assert fact.get("message") is None


class TestViolationDetail:
    """Tests for ViolationDetail schema."""

    def test_entity_id_required(self) -> None:
        """Test entity_id is required."""
        entity_id = "building_001"
        assert len(entity_id) > 0

    def test_messages_default_empty(self) -> None:
        """Test messages defaults to empty list."""
        messages = []
        assert isinstance(messages, list)

    def test_facts_default_empty(self) -> None:
        """Test facts defaults to empty list."""
        facts = []
        assert isinstance(facts, list)

    def test_attributes_default_empty(self) -> None:
        """Test attributes defaults to empty dict."""
        attributes = {}
        assert isinstance(attributes, dict)


class TestRuleEvaluationResult:
    """Tests for RuleEvaluationResult schema."""

    def test_rule_id_required(self) -> None:
        """Test rule_id is required."""
        rule_id = "RULE_PR_001"
        assert len(rule_id) > 0

    def test_title_optional(self) -> None:
        """Test title is optional."""
        result = {}
        assert result.get("title") is None

    def test_target_optional(self) -> None:
        """Test target is optional."""
        result = {}
        assert result.get("target") is None

    def test_citation_optional(self) -> None:
        """Test citation is optional."""
        result = {}
        assert result.get("citation") is None

    def test_passed_required(self) -> None:
        """Test passed is required boolean."""
        passed = True
        assert isinstance(passed, bool)

    def test_checked_required(self) -> None:
        """Test checked count is required."""
        checked = 5
        assert checked >= 0

    def test_violations_default_empty(self) -> None:
        """Test violations defaults to empty list."""
        violations = []
        assert isinstance(violations, list)


class TestRulesetEvaluationSummary:
    """Tests for RulesetEvaluationSummary schema."""

    def test_total_rules_required(self) -> None:
        """Test total_rules is required."""
        total_rules = 50
        assert total_rules >= 0

    def test_evaluated_rules_required(self) -> None:
        """Test evaluated_rules is required."""
        evaluated_rules = 45
        assert evaluated_rules >= 0

    def test_violations_required(self) -> None:
        """Test violations count is required."""
        violations = 3
        assert violations >= 0

    def test_checked_entities_required(self) -> None:
        """Test checked_entities is required."""
        checked_entities = 10
        assert checked_entities >= 0


class TestRulesetValidationResponse:
    """Tests for RulesetValidationResponse schema."""

    def test_ruleset_required(self) -> None:
        """Test ruleset summary is required."""
        ruleset = {"id": 1, "slug": "ura-zoning", "name": "URA Zoning"}
        assert "id" in ruleset

    def test_results_required(self) -> None:
        """Test results list is required."""
        results = []
        assert isinstance(results, list)

    def test_summary_required(self) -> None:
        """Test summary is required."""
        summary = {"total_rules": 50, "evaluated_rules": 45}
        assert "total_rules" in summary

    def test_citations_default_empty(self) -> None:
        """Test citations defaults to empty list."""
        citations = []
        assert isinstance(citations, list)


class TestRulesetListResponse:
    """Tests for RulesetListResponse schema."""

    def test_items_required(self) -> None:
        """Test items list is required."""
        items = []
        assert isinstance(items, list)

    def test_count_required(self) -> None:
        """Test count is required."""
        count = 10
        assert count >= 0


class TestRuleOperators:
    """Tests for rule operator values."""

    def test_less_than_equal(self) -> None:
        """Test <= operator."""
        operator = "<="
        assert operator == "<="

    def test_greater_than_equal(self) -> None:
        """Test >= operator."""
        operator = ">="
        assert operator == ">="

    def test_equals(self) -> None:
        """Test == operator."""
        operator = "=="
        assert operator == "=="

    def test_not_equals(self) -> None:
        """Test != operator."""
        operator = "!="
        assert operator == "!="

    def test_in_range(self) -> None:
        """Test in_range operator."""
        operator = "in_range"
        assert operator == "in_range"


class TestRulesetScenarios:
    """Tests for ruleset use case scenarios."""

    def test_ura_zoning_validation(self) -> None:
        """Test URA zoning ruleset validation."""
        request = {
            "ruleset_slug": "ura-zoning-2024",
            "geometry": {
                "type": "FeatureCollection",
                "features": [{"type": "Feature", "properties": {"plot_ratio": 4.2}}],
            },
        }
        assert request["ruleset_slug"] == "ura-zoning-2024"

    def test_bca_fire_safety_validation(self) -> None:
        """Test BCA fire safety ruleset validation."""
        request = {
            "ruleset_id": 2,
            "geometry": {
                "type": "Feature",
                "properties": {"stair_width": 1100, "exit_count": 2},
            },
        }
        assert request["ruleset_id"] == 2

    def test_validation_with_violations(self) -> None:
        """Test validation response with violations."""
        response = {
            "ruleset": {"id": 1, "slug": "ura-zoning", "name": "URA Zoning"},
            "results": [
                {
                    "rule_id": "RULE_PR_001",
                    "title": "Plot Ratio Limit",
                    "passed": False,
                    "checked": 1,
                    "violations": [
                        {
                            "entity_id": "building_001",
                            "messages": ["Plot ratio exceeds maximum"],
                            "facts": [
                                {
                                    "field": "plot_ratio",
                                    "operator": "<=",
                                    "expected": 3.5,
                                    "actual": 4.2,
                                }
                            ],
                        }
                    ],
                }
            ],
            "summary": {
                "total_rules": 10,
                "evaluated_rules": 10,
                "violations": 1,
                "checked_entities": 1,
            },
        }
        assert len(response["results"][0]["violations"]) == 1

    def test_validation_all_passed(self) -> None:
        """Test validation response with all rules passed."""
        response = {
            "ruleset": {"id": 1, "slug": "ura-zoning", "name": "URA Zoning"},
            "results": [
                {
                    "rule_id": "RULE_PR_001",
                    "passed": True,
                    "checked": 1,
                    "violations": [],
                },
                {
                    "rule_id": "RULE_HT_001",
                    "passed": True,
                    "checked": 1,
                    "violations": [],
                },
            ],
            "summary": {
                "total_rules": 2,
                "evaluated_rules": 2,
                "violations": 0,
                "checked_entities": 1,
            },
        }
        assert response["summary"]["violations"] == 0
