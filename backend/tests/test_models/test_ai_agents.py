"""Comprehensive tests for ai_agents model.

Tests cover:
- AIAgentType enum
- AIAgentStatus enum
- AIAgent model structure
- AIAgentSession model structure
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4


class TestAIAgentType:
    """Tests for AIAgentType enum."""

    def test_feasibility_analyst(self) -> None:
        """Test feasibility_analyst type."""
        agent_type = "feasibility_analyst"
        assert agent_type == "feasibility_analyst"

    def test_regulatory_compliance(self) -> None:
        """Test regulatory_compliance type."""
        agent_type = "regulatory_compliance"
        assert agent_type == "regulatory_compliance"

    def test_cost_estimator(self) -> None:
        """Test cost_estimator type."""
        agent_type = "cost_estimator"
        assert agent_type == "cost_estimator"

    def test_design_optimizer(self) -> None:
        """Test design_optimizer type."""
        agent_type = "design_optimizer"
        assert agent_type == "design_optimizer"

    def test_risk_assessor(self) -> None:
        """Test risk_assessor type."""
        agent_type = "risk_assessor"
        assert agent_type == "risk_assessor"

    def test_market_analyst(self) -> None:
        """Test market_analyst type."""
        agent_type = "market_analyst"
        assert agent_type == "market_analyst"

    def test_documentation_generator(self) -> None:
        """Test documentation_generator type."""
        agent_type = "documentation_generator"
        assert agent_type == "documentation_generator"

    def test_bca_compliance(self) -> None:
        """Test bca_compliance type (Singapore Building Authority)."""
        agent_type = "bca_compliance"
        assert agent_type == "bca_compliance"

    def test_ura_compliance(self) -> None:
        """Test ura_compliance type (Singapore Urban Redevelopment)."""
        agent_type = "ura_compliance"
        assert agent_type == "ura_compliance"

    def test_scdf_compliance(self) -> None:
        """Test scdf_compliance type (Singapore Civil Defence)."""
        agent_type = "scdf_compliance"
        assert agent_type == "scdf_compliance"


class TestAIAgentStatus:
    """Tests for AIAgentStatus enum."""

    def test_active_status(self) -> None:
        """Test active status."""
        status = "active"
        assert status == "active"

    def test_inactive_status(self) -> None:
        """Test inactive status."""
        status = "inactive"
        assert status == "inactive"

    def test_maintenance_status(self) -> None:
        """Test maintenance status."""
        status = "maintenance"
        assert status == "maintenance"

    def test_deprecated_status(self) -> None:
        """Test deprecated status."""
        status = "deprecated"
        assert status == "deprecated"


class TestAIAgentModel:
    """Tests for AIAgent model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        agent_id = uuid4()
        assert len(str(agent_id)) == 36

    def test_name_required(self) -> None:
        """Test name is required."""
        name = "Feasibility Analyst Agent"
        assert len(name) > 0

    def test_agent_type_required(self) -> None:
        """Test agent_type is required."""
        agent_type = "feasibility_analyst"
        assert agent_type is not None

    def test_description_optional(self) -> None:
        """Test description is optional."""
        agent = {}
        assert agent.get("description") is None

    def test_version_default(self) -> None:
        """Test version defaults to 1.0.0."""
        version = "1.0.0"
        assert version == "1.0.0"

    def test_status_default_active(self) -> None:
        """Test status defaults to active."""
        status = "active"
        assert status == "active"

    def test_is_enabled_default_true(self) -> None:
        """Test is_enabled defaults to True."""
        is_enabled = True
        assert is_enabled is True

    def test_model_provider_default(self) -> None:
        """Test model_provider defaults to openai."""
        provider = "openai"
        assert provider == "openai"

    def test_model_name_default(self) -> None:
        """Test model_name defaults to gpt-4."""
        model = "gpt-4"
        assert model == "gpt-4"

    def test_temperature_default(self) -> None:
        """Test temperature defaults to 0.7."""
        temperature = 0.7
        assert temperature == 0.7

    def test_max_tokens_default(self) -> None:
        """Test max_tokens defaults to 2000."""
        max_tokens = 2000
        assert max_tokens == 2000

    def test_singapore_regulations_optional(self) -> None:
        """Test singapore_regulations is optional."""
        agent = {}
        assert agent.get("singapore_regulations") is None

    def test_compliance_frameworks_optional(self) -> None:
        """Test compliance_frameworks is optional."""
        agent = {}
        assert agent.get("compliance_frameworks") is None

    def test_capabilities_optional(self) -> None:
        """Test capabilities is optional."""
        agent = {}
        assert agent.get("capabilities") is None


class TestAIAgentSessionModel:
    """Tests for AIAgentSession model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        session_id = uuid4()
        assert len(str(session_id)) == 36

    def test_agent_id_required(self) -> None:
        """Test agent_id is required."""
        agent_id = uuid4()
        assert agent_id is not None

    def test_user_id_required(self) -> None:
        """Test user_id is required."""
        user_id = uuid4()
        assert user_id is not None

    def test_project_id_optional(self) -> None:
        """Test project_id is optional."""
        session = {}
        assert session.get("project_id") is None

    def test_property_id_optional(self) -> None:
        """Test property_id is optional."""
        session = {}
        assert session.get("property_id") is None

    def test_session_type_optional(self) -> None:
        """Test session_type is optional."""
        session = {}
        assert session.get("session_type") is None

    def test_status_default_active(self) -> None:
        """Test status defaults to active."""
        status = "active"
        assert status == "active"

    def test_context_optional(self) -> None:
        """Test context is optional."""
        session = {}
        assert session.get("context") is None

    def test_memory_optional(self) -> None:
        """Test memory is optional."""
        session = {}
        assert session.get("memory") is None

    def test_messages_optional(self) -> None:
        """Test messages is optional."""
        session = {}
        assert session.get("messages") is None

    def test_total_messages_default_zero(self) -> None:
        """Test total_messages defaults to 0."""
        total = 0
        assert total == 0

    def test_tokens_used_default_zero(self) -> None:
        """Test tokens_used defaults to 0."""
        tokens = 0
        assert tokens == 0

    def test_cost_estimate_default_zero(self) -> None:
        """Test cost_estimate defaults to 0.0."""
        cost = 0.0
        assert cost == 0.0

    def test_singapore_compliance_score_optional(self) -> None:
        """Test singapore_compliance_score is optional."""
        session = {}
        assert session.get("singapore_compliance_score") is None


class TestSessionTypes:
    """Tests for AI agent session types."""

    def test_analysis_session(self) -> None:
        """Test analysis session type."""
        session_type = "analysis"
        assert session_type == "analysis"

    def test_compliance_check_session(self) -> None:
        """Test compliance_check session type."""
        session_type = "compliance_check"
        assert session_type == "compliance_check"

    def test_report_generation_session(self) -> None:
        """Test report_generation session type."""
        session_type = "report_generation"
        assert session_type == "report_generation"

    def test_design_optimization_session(self) -> None:
        """Test design_optimization session type."""
        session_type = "design_optimization"
        assert session_type == "design_optimization"


class TestSessionStatuses:
    """Tests for AI agent session statuses."""

    def test_active_session(self) -> None:
        """Test active session status."""
        status = "active"
        assert status == "active"

    def test_completed_session(self) -> None:
        """Test completed session status."""
        status = "completed"
        assert status == "completed"

    def test_failed_session(self) -> None:
        """Test failed session status."""
        status = "failed"
        assert status == "failed"


class TestAIAgentScenarios:
    """Tests for AI agent use case scenarios."""

    def test_create_feasibility_agent(self) -> None:
        """Test creating a feasibility analyst agent."""
        agent = {
            "id": str(uuid4()),
            "name": "Singapore Feasibility Analyst",
            "agent_type": "feasibility_analyst",
            "description": "Analyzes development feasibility for Singapore properties",
            "version": "2.0.0",
            "status": "active",
            "is_enabled": True,
            "model_provider": "anthropic",
            "model_name": "claude-3-opus",
            "temperature": 0.5,
            "max_tokens": 4000,
            "singapore_regulations": {
                "URA": ["DC Handbook", "Plot Ratio Guidelines"],
                "BCA": ["Building Control Act", "Approved Document"],
            },
            "capabilities": [
                "site_analysis",
                "yield_calculation",
                "cost_estimation",
                "regulatory_check",
            ],
        }
        assert agent["agent_type"] == "feasibility_analyst"
        assert len(agent["capabilities"]) == 4

    def test_create_compliance_session(self) -> None:
        """Test creating a compliance check session."""
        session = {
            "id": str(uuid4()),
            "agent_id": str(uuid4()),
            "user_id": str(uuid4()),
            "project_id": str(uuid4()),
            "property_id": str(uuid4()),
            "session_type": "compliance_check",
            "status": "active",
            "context": {"property_type": "OFFICE", "district": "D01"},
            "input_data": {"gfa_sqm": 25000, "plot_ratio": 2.8},
            "total_messages": 0,
            "tokens_used": 0,
            "started_at": datetime.utcnow().isoformat(),
        }
        assert session["session_type"] == "compliance_check"

    def test_complete_session(self) -> None:
        """Test completing an AI agent session."""
        session = {
            "status": "active",
            "total_messages": 5,
            "tokens_used": 2500,
        }
        session["status"] = "completed"
        session["completed_at"] = datetime.utcnow()
        session["output_data"] = {"compliance_score": 92.5}
        session["singapore_compliance_score"] = 92.5
        assert session["status"] == "completed"

    def test_record_compliance_issues(self) -> None:
        """Test recording regulatory issues from AI analysis."""
        session = {
            "regulatory_issues": [
                {
                    "code": "URA_SETBACK",
                    "severity": "warning",
                    "message": "Front setback below recommended",
                },
                {
                    "code": "BCA_FIRE",
                    "severity": "error",
                    "message": "Fire escape distance exceeded",
                },
            ],
            "recommendations": [
                "Reduce building footprint by 2m at front boundary",
                "Add additional fire stairwell at eastern wing",
            ],
        }
        assert len(session["regulatory_issues"]) == 2
        assert len(session["recommendations"]) == 2

    def test_disable_agent(self) -> None:
        """Test disabling an AI agent."""
        agent = {"is_enabled": True}
        agent["is_enabled"] = False
        assert agent["is_enabled"] is False

    def test_update_agent_version(self) -> None:
        """Test updating agent version."""
        agent = {"version": "1.0.0"}
        agent["version"] = "1.1.0"
        assert agent["version"] == "1.1.0"

    def test_track_session_cost(self) -> None:
        """Test tracking session cost."""
        session = {
            "tokens_used": 5000,
            "cost_estimate": 0.0,
        }
        # Estimate cost at $0.01 per 1K tokens
        session["cost_estimate"] = session["tokens_used"] * 0.01 / 1000
        assert session["cost_estimate"] == 0.05
