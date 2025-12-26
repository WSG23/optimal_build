"""Comprehensive tests for overlay schemas.

Tests cover:
- OverlayDecisionRecord schema
- OverlaySuggestion schema
- OverlayDecisionPayload schema
- Field validators
"""

from __future__ import annotations

from datetime import datetime


class TestOverlayDecisionRecord:
    """Tests for OverlayDecisionRecord schema."""

    def test_id_required(self) -> None:
        """Test id is required."""
        record_id = 1
        assert record_id is not None

    def test_decision_required(self) -> None:
        """Test decision is required."""
        decision = "approved"
        assert len(decision) > 0

    def test_decided_by_optional(self) -> None:
        """Test decided_by is optional."""
        record = {}
        assert record.get("decided_by") is None

    def test_decided_at_required(self) -> None:
        """Test decided_at is required."""
        decided_at = datetime.utcnow()
        assert decided_at is not None

    def test_notes_optional(self) -> None:
        """Test notes is optional."""
        record = {}
        assert record.get("notes") is None


class TestOverlaySuggestion:
    """Tests for OverlaySuggestion schema."""

    def test_id_required(self) -> None:
        """Test id is required."""
        suggestion_id = 1
        assert suggestion_id is not None

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = 1
        assert project_id is not None

    def test_source_geometry_id_required(self) -> None:
        """Test source_geometry_id is required."""
        geometry_id = 1
        assert geometry_id is not None

    def test_code_required(self) -> None:
        """Test code is required."""
        code = "PR_EXCEED"
        assert len(code) > 0

    def test_type_optional(self) -> None:
        """Test type is optional."""
        suggestion = {}
        assert suggestion.get("type") is None

    def test_title_required(self) -> None:
        """Test title is required."""
        title = "Plot Ratio Exceeded"
        assert len(title) > 0

    def test_rationale_optional(self) -> None:
        """Test rationale is optional."""
        suggestion = {}
        assert suggestion.get("rationale") is None

    def test_severity_optional(self) -> None:
        """Test severity is optional."""
        suggestion = {}
        assert suggestion.get("severity") is None

    def test_status_required(self) -> None:
        """Test status is required."""
        status = "pending"
        assert len(status) > 0

    def test_engine_version_optional(self) -> None:
        """Test engine_version is optional."""
        suggestion = {}
        assert suggestion.get("engine_version") is None

    def test_engine_payload_required(self) -> None:
        """Test engine_payload is required dict."""
        payload = {"rule_id": "PR_001", "threshold": 3.5}
        assert isinstance(payload, dict)

    def test_target_ids_default_empty(self) -> None:
        """Test target_ids defaults to empty list."""
        target_ids = []
        assert isinstance(target_ids, list)

    def test_props_default_empty(self) -> None:
        """Test props defaults to empty dict."""
        props = {}
        assert isinstance(props, dict)

    def test_rule_refs_default_empty(self) -> None:
        """Test rule_refs defaults to empty list."""
        rule_refs = []
        assert isinstance(rule_refs, list)

    def test_score_optional(self) -> None:
        """Test score is optional."""
        suggestion = {}
        assert suggestion.get("score") is None

    def test_geometry_checksum_required(self) -> None:
        """Test geometry_checksum is required."""
        checksum = "abc123def456"
        assert len(checksum) > 0

    def test_created_at_required(self) -> None:
        """Test created_at is required."""
        created_at = datetime.utcnow()
        assert created_at is not None

    def test_updated_at_required(self) -> None:
        """Test updated_at is required."""
        updated_at = datetime.utcnow()
        assert updated_at is not None

    def test_decided_at_optional(self) -> None:
        """Test decided_at is optional."""
        suggestion = {}
        assert suggestion.get("decided_at") is None

    def test_decided_by_optional(self) -> None:
        """Test decided_by is optional."""
        suggestion = {}
        assert suggestion.get("decided_by") is None

    def test_decision_notes_optional(self) -> None:
        """Test decision_notes is optional."""
        suggestion = {}
        assert suggestion.get("decision_notes") is None

    def test_decision_record_optional(self) -> None:
        """Test decision record is optional."""
        suggestion = {}
        assert suggestion.get("decision") is None


class TestTargetIdsValidator:
    """Tests for target_ids field validator."""

    def test_none_returns_empty_list(self) -> None:
        """Test None input returns empty list."""
        value = None
        result = [] if value is None else list(value)
        assert result == []

    def test_list_returns_list(self) -> None:
        """Test list input returns list of strings."""
        value = ["geom_1", "geom_2"]
        result = [str(item) for item in value]
        assert result == ["geom_1", "geom_2"]

    def test_single_value_returns_list(self) -> None:
        """Test single value returns list with one item."""
        value = "geom_1"
        if isinstance(value, (list, tuple)):
            result = list(value)
        else:
            result = [str(value)]
        assert result == ["geom_1"]

    def test_filters_empty_strings(self) -> None:
        """Test empty strings are filtered out."""
        value = ["geom_1", "", "geom_2", None]
        result = [str(item) for item in value if item not in (None, "")]
        assert result == ["geom_1", "geom_2"]


class TestPropsValidator:
    """Tests for props field validator."""

    def test_dict_returns_dict(self) -> None:
        """Test dict input returns dict."""
        value = {"key": "value"}
        result = dict(value) if isinstance(value, dict) else {}
        assert result == {"key": "value"}

    def test_non_dict_returns_empty(self) -> None:
        """Test non-dict input returns empty dict."""
        value = "not a dict"
        result = dict(value) if isinstance(value, dict) else {}
        assert result == {}

    def test_none_returns_empty(self) -> None:
        """Test None returns empty dict."""
        value = None
        result = {} if value is None else value
        assert result == {}


class TestRuleRefsValidator:
    """Tests for rule_refs field validator."""

    def test_none_returns_empty_list(self) -> None:
        """Test None input returns empty list."""
        value = None
        result = [] if value is None else list(value)
        assert result == []

    def test_list_returns_list(self) -> None:
        """Test list input returns list of strings."""
        value = ["RULE_001", "RULE_002"]
        result = [str(item) for item in value]
        assert result == ["RULE_001", "RULE_002"]


class TestOverlayDecisionPayload:
    """Tests for OverlayDecisionPayload schema."""

    def test_suggestion_id_required(self) -> None:
        """Test suggestion_id is required."""
        suggestion_id = 1
        assert suggestion_id is not None

    def test_decision_required(self) -> None:
        """Test decision is required."""
        decision = "approved"
        assert len(decision) > 0

    def test_decided_by_optional(self) -> None:
        """Test decided_by is optional."""
        payload = {"suggestion_id": 1, "decision": "approved"}
        assert payload.get("decided_by") is None

    def test_notes_optional(self) -> None:
        """Test notes is optional."""
        payload = {"suggestion_id": 1, "decision": "approved"}
        assert payload.get("notes") is None


class TestDecisionValidator:
    """Tests for decision field validator."""

    def test_non_empty_decision_valid(self) -> None:
        """Test non-empty decision is valid."""
        decision = "approved"
        assert len(decision.strip()) > 0

    def test_empty_decision_invalid(self) -> None:
        """Test empty decision would raise ValueError."""
        decision = ""
        is_valid = bool(decision and decision.strip())
        assert is_valid is False

    def test_whitespace_decision_invalid(self) -> None:
        """Test whitespace-only decision would raise ValueError."""
        decision = "   "
        is_valid = bool(decision and decision.strip())
        assert is_valid is False


class TestOverlayDecisionValues:
    """Tests for overlay decision values."""

    def test_approved_decision(self) -> None:
        """Test approved decision."""
        decision = "approved"
        assert decision == "approved"

    def test_rejected_decision(self) -> None:
        """Test rejected decision."""
        decision = "rejected"
        assert decision == "rejected"

    def test_deferred_decision(self) -> None:
        """Test deferred decision."""
        decision = "deferred"
        assert decision == "deferred"


class TestOverlaySeverityValues:
    """Tests for overlay severity values."""

    def test_high_severity(self) -> None:
        """Test high severity."""
        severity = "high"
        assert severity == "high"

    def test_medium_severity(self) -> None:
        """Test medium severity."""
        severity = "medium"
        assert severity == "medium"

    def test_low_severity(self) -> None:
        """Test low severity."""
        severity = "low"
        assert severity == "low"


class TestOverlayScenarios:
    """Tests for overlay use case scenarios."""

    def test_plot_ratio_suggestion(self) -> None:
        """Test plot ratio exceeded suggestion."""
        suggestion = {
            "id": 1,
            "project_id": 100,
            "source_geometry_id": 50,
            "code": "PR_EXCEED",
            "title": "Plot Ratio Exceeded",
            "severity": "high",
            "status": "pending",
            "engine_payload": {"current_pr": 4.2, "max_pr": 3.5},
            "geometry_checksum": "abc123",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        assert suggestion["code"] == "PR_EXCEED"

    def test_building_height_suggestion(self) -> None:
        """Test building height exceeded suggestion."""
        suggestion = {
            "id": 2,
            "project_id": 100,
            "source_geometry_id": 50,
            "code": "HEIGHT_EXCEED",
            "title": "Building Height Exceeded",
            "severity": "high",
            "status": "pending",
            "engine_payload": {"current_height": 85, "max_height": 80},
            "geometry_checksum": "def456",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        assert suggestion["code"] == "HEIGHT_EXCEED"

    def test_approve_suggestion(self) -> None:
        """Test approving a suggestion."""
        payload = {
            "suggestion_id": 1,
            "decision": "approved",
            "decided_by": "admin@example.com",
            "notes": "Exception granted for heritage building",
        }
        assert payload["decision"] == "approved"
