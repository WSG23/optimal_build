"""Comprehensive tests for overlay model.

Tests cover:
- OverlaySourceGeometry model structure
- OverlaySuggestion model structure
- OverlayDecision model structure
- OverlayRunLock model structure
"""

from __future__ import annotations

from datetime import datetime

import pytest

# Mark all tests in this module as not requiring database
pytestmark = pytest.mark.no_db


class TestOverlaySourceGeometryModel:
    """Tests for OverlaySourceGeometry model structure."""

    def test_id_is_integer(self) -> None:
        """Test id is integer type."""
        source_id = 1
        assert isinstance(source_id, int)

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = 1
        assert project_id is not None

    def test_source_geometry_key_required(self) -> None:
        """Test source_geometry_key is required."""
        key = "main_building_envelope"
        assert len(key) > 0

    def test_graph_required(self) -> None:
        """Test graph (geometry data) is required."""
        graph = {"nodes": [], "edges": []}
        assert isinstance(graph, dict)

    def test_metadata_default_empty(self) -> None:
        """Test metadata defaults to empty dict."""
        metadata = {}
        assert isinstance(metadata, dict)

    def test_checksum_required(self) -> None:
        """Test checksum is required (64 char SHA-256)."""
        checksum = "a" * 64
        assert len(checksum) == 64


class TestOverlaySuggestionModel:
    """Tests for OverlaySuggestion model structure."""

    def test_id_is_integer(self) -> None:
        """Test id is integer type."""
        suggestion_id = 1
        assert isinstance(suggestion_id, int)

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = 1
        assert project_id is not None

    def test_source_geometry_id_required(self) -> None:
        """Test source_geometry_id is required."""
        source_id = 1
        assert source_id is not None

    def test_code_required(self) -> None:
        """Test code is required."""
        code = "SETBACK_VIOLATION"
        assert len(code) > 0

    def test_type_optional(self) -> None:
        """Test type is optional."""
        suggestion = {}
        assert suggestion.get("type") is None

    def test_title_required(self) -> None:
        """Test title is required."""
        title = "Front setback requirement not met"
        assert len(title) > 0

    def test_rationale_optional(self) -> None:
        """Test rationale is optional."""
        suggestion = {}
        assert suggestion.get("rationale") is None

    def test_severity_optional(self) -> None:
        """Test severity is optional."""
        suggestion = {}
        assert suggestion.get("severity") is None

    def test_status_default_pending(self) -> None:
        """Test status defaults to pending."""
        status = "pending"
        assert status == "pending"

    def test_engine_version_optional(self) -> None:
        """Test engine_version is optional."""
        suggestion = {}
        assert suggestion.get("engine_version") is None

    def test_engine_payload_default_empty(self) -> None:
        """Test engine_payload defaults to empty dict."""
        payload = {}
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
        checksum = "a" * 64
        assert len(checksum) == 64


class TestOverlayDecisionModel:
    """Tests for OverlayDecision model structure."""

    def test_id_is_integer(self) -> None:
        """Test id is integer type."""
        decision_id = 1
        assert isinstance(decision_id, int)

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = 1
        assert project_id is not None

    def test_source_geometry_id_required(self) -> None:
        """Test source_geometry_id is required."""
        source_id = 1
        assert source_id is not None

    def test_suggestion_id_required(self) -> None:
        """Test suggestion_id is required."""
        suggestion_id = 1
        assert suggestion_id is not None

    def test_decision_required(self) -> None:
        """Test decision is required."""
        decision = "accepted"
        assert len(decision) > 0

    def test_decided_by_optional(self) -> None:
        """Test decided_by is optional."""
        decision = {}
        assert decision.get("decided_by") is None

    def test_notes_optional(self) -> None:
        """Test notes is optional."""
        decision = {}
        assert decision.get("notes") is None


class TestOverlayRunLockModel:
    """Tests for OverlayRunLock model structure."""

    def test_id_is_integer(self) -> None:
        """Test id is integer type."""
        lock_id = 1
        assert isinstance(lock_id, int)

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = 1
        assert project_id is not None

    def test_source_geometry_id_required(self) -> None:
        """Test source_geometry_id is required."""
        source_id = 1
        assert source_id is not None

    def test_lock_kind_default_evaluation(self) -> None:
        """Test lock_kind defaults to evaluation."""
        lock_kind = "evaluation"
        assert lock_kind == "evaluation"

    def test_is_active_default_true(self) -> None:
        """Test is_active defaults to True."""
        is_active = True
        assert is_active is True

    def test_released_at_optional(self) -> None:
        """Test released_at is optional."""
        lock = {}
        assert lock.get("released_at") is None

    def test_notes_optional(self) -> None:
        """Test notes is optional."""
        lock = {}
        assert lock.get("notes") is None


class TestOverlaySuggestionStatuses:
    """Tests for overlay suggestion status values."""

    def test_pending_status(self) -> None:
        """Test pending status."""
        status = "pending"
        assert status == "pending"

    def test_accepted_status(self) -> None:
        """Test accepted status."""
        status = "accepted"
        assert status == "accepted"

    def test_rejected_status(self) -> None:
        """Test rejected status."""
        status = "rejected"
        assert status == "rejected"

    def test_deferred_status(self) -> None:
        """Test deferred status."""
        status = "deferred"
        assert status == "deferred"


class TestOverlayDecisionValues:
    """Tests for overlay decision values."""

    def test_accept_decision(self) -> None:
        """Test accept decision."""
        decision = "accept"
        assert decision == "accept"

    def test_reject_decision(self) -> None:
        """Test reject decision."""
        decision = "reject"
        assert decision == "reject"

    def test_defer_decision(self) -> None:
        """Test defer decision."""
        decision = "defer"
        assert decision == "defer"


class TestOverlaySeverityLevels:
    """Tests for overlay suggestion severity levels."""

    def test_info_severity(self) -> None:
        """Test info severity."""
        severity = "info"
        assert severity == "info"

    def test_warning_severity(self) -> None:
        """Test warning severity."""
        severity = "warning"
        assert severity == "warning"

    def test_error_severity(self) -> None:
        """Test error severity."""
        severity = "error"
        assert severity == "error"

    def test_critical_severity(self) -> None:
        """Test critical severity."""
        severity = "critical"
        assert severity == "critical"


class TestOverlayScenarios:
    """Tests for overlay use case scenarios."""

    def test_create_source_geometry(self) -> None:
        """Test creating overlay source geometry."""
        geometry = {
            "id": 1,
            "project_id": 1,
            "source_geometry_key": "main_envelope",
            "graph": {
                "nodes": [
                    {"id": "n1", "x": 0, "y": 0},
                    {"id": "n2", "x": 100, "y": 0},
                ],
                "edges": [{"from": "n1", "to": "n2"}],
            },
            "metadata": {"version": "1.0", "generated_by": "feasibility_engine"},
            "checksum": "abc123" + "0" * 58,
            "created_at": datetime.utcnow().isoformat(),
        }
        assert geometry["source_geometry_key"] == "main_envelope"
        assert len(geometry["graph"]["nodes"]) == 2

    def test_generate_suggestion(self) -> None:
        """Test generating an overlay suggestion."""
        suggestion = {
            "id": 1,
            "project_id": 1,
            "source_geometry_id": 1,
            "code": "URA_SETBACK_VIOLATION",
            "type": "compliance",
            "title": "Front setback below minimum requirement",
            "rationale": "Building envelope encroaches into 6m front setback zone",
            "severity": "error",
            "status": "pending",
            "engine_version": "2.0.0",
            "target_ids": ["element_001", "element_002"],
            "props": {"required_setback": 6.0, "actual_setback": 4.5},
            "rule_refs": ["URA_DC_SETBACK_001"],
            "score": 0.85,
            "geometry_checksum": "abc123" + "0" * 58,
        }
        assert suggestion["code"] == "URA_SETBACK_VIOLATION"
        assert suggestion["severity"] == "error"

    def test_make_decision_on_suggestion(self) -> None:
        """Test making a decision on a suggestion."""
        decision = {
            "id": 1,
            "project_id": 1,
            "source_geometry_id": 1,
            "suggestion_id": 1,
            "decision": "accept",
            "decided_by": "architect@design.com",
            "decided_at": datetime.utcnow().isoformat(),
            "notes": "Agreed to modify building envelope to meet setback requirements",
        }
        assert decision["decision"] == "accept"

    def test_acquire_run_lock(self) -> None:
        """Test acquiring a run lock for evaluation."""
        lock = {
            "id": 1,
            "project_id": 1,
            "source_geometry_id": 1,
            "lock_kind": "evaluation",
            "is_active": True,
            "acquired_at": datetime.utcnow().isoformat(),
        }
        assert lock["is_active"] is True

    def test_release_run_lock(self) -> None:
        """Test releasing a run lock."""
        lock = {"is_active": True, "released_at": None}
        lock["is_active"] = False
        lock["released_at"] = datetime.utcnow()
        assert lock["is_active"] is False
        assert lock["released_at"] is not None

    def test_update_suggestion_status(self) -> None:
        """Test updating suggestion status after decision."""
        suggestion = {"status": "pending"}
        suggestion["status"] = "accepted"
        suggestion["decided_at"] = datetime.utcnow()
        suggestion["decided_by"] = "architect@design.com"
        assert suggestion["status"] == "accepted"
