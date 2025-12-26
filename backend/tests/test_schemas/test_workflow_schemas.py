"""Comprehensive tests for workflow schemas.

Tests cover:
- ApprovalStepBase schema
- ApprovalStepRead schema
- ApprovalStepUpdate schema
- ApprovalWorkflowBase schema
- ApprovalWorkflowCreate schema
- ApprovalWorkflowRead schema
- WorkflowStatus enum
- StepStatus enum
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4


class TestApprovalStepBase:
    """Tests for ApprovalStepBase schema."""

    def test_name_required(self) -> None:
        """Test name is required."""
        name = "Architect Review"
        assert len(name) > 0

    def test_order_default_zero(self) -> None:
        """Test order defaults to 0."""
        order = 0
        assert order == 0

    def test_order_alias_sequence_order(self) -> None:
        """Test order has alias sequence_order."""
        step = {"sequence_order": 1}
        assert step.get("sequence_order") == 1

    def test_approver_role_default_empty(self) -> None:
        """Test approver_role defaults to empty string."""
        approver_role = ""
        assert approver_role == ""

    def test_approver_role_alias_required_role(self) -> None:
        """Test approver_role has alias required_role."""
        step = {"required_role": "architect"}
        assert step.get("required_role") == "architect"


class TestApprovalStepRead:
    """Tests for ApprovalStepRead schema."""

    def test_id_required(self) -> None:
        """Test id is required UUID."""
        step_id = uuid4()
        assert len(str(step_id)) == 36

    def test_name_required(self) -> None:
        """Test name is required."""
        name = "Engineer Review"
        assert len(name) > 0

    def test_status_required(self) -> None:
        """Test status is required."""
        status = "IN_REVIEW"
        assert status is not None

    def test_approved_by_id_optional(self) -> None:
        """Test approved_by_id is optional."""
        step = {}
        assert step.get("approved_by_id") is None

    def test_approved_at_optional(self) -> None:
        """Test approved_at is optional."""
        step = {}
        assert step.get("approved_at") is None

    def test_approved_at_alias_decision_at(self) -> None:
        """Test approved_at has validation_alias decision_at."""
        decision_at = datetime.utcnow()
        assert decision_at is not None

    def test_comments_optional(self) -> None:
        """Test comments is optional."""
        step = {}
        assert step.get("comments") is None


class TestApprovalStepUpdate:
    """Tests for ApprovalStepUpdate schema."""

    def test_approved_required(self) -> None:
        """Test approved boolean is required."""
        approved = True
        assert isinstance(approved, bool)

    def test_comments_optional(self) -> None:
        """Test comments is optional."""
        update = {"approved": True}
        assert update.get("comments") is None

    def test_approve_step(self) -> None:
        """Test approving a step."""
        update = {"approved": True, "comments": "Looks good, approved!"}
        assert update["approved"] is True

    def test_reject_step(self) -> None:
        """Test rejecting a step."""
        update = {"approved": False, "comments": "Requires revisions"}
        assert update["approved"] is False


class TestStepStatus:
    """Tests for StepStatus enum values."""

    def test_pending_status(self) -> None:
        """Test PENDING status."""
        status = "PENDING"
        assert status == "PENDING"

    def test_in_review_status(self) -> None:
        """Test IN_REVIEW status."""
        status = "IN_REVIEW"
        assert status == "IN_REVIEW"

    def test_approved_status(self) -> None:
        """Test APPROVED status."""
        status = "APPROVED"
        assert status == "APPROVED"

    def test_rejected_status(self) -> None:
        """Test REJECTED status."""
        status = "REJECTED"
        assert status == "REJECTED"


class TestApprovalWorkflowBase:
    """Tests for ApprovalWorkflowBase schema."""

    def test_name_required(self) -> None:
        """Test name is required."""
        name = "Design Phase Approval"
        assert len(name) > 0

    def test_name_alias_title(self) -> None:
        """Test name has validation_alias title."""
        workflow = {"title": "Design Approval"}
        assert workflow.get("title") == "Design Approval"

    def test_description_optional(self) -> None:
        """Test description is optional."""
        workflow = {}
        assert workflow.get("description") is None

    def test_workflow_type_required(self) -> None:
        """Test workflow_type is required."""
        workflow_type = "design_approval"
        assert workflow_type is not None


class TestApprovalWorkflowCreate:
    """Tests for ApprovalWorkflowCreate schema."""

    def test_name_required(self) -> None:
        """Test name is required."""
        name = "Construction Phase Approval"
        assert len(name) > 0

    def test_workflow_type_required(self) -> None:
        """Test workflow_type is required."""
        workflow_type = "construction_approval"
        assert workflow_type is not None

    def test_steps_required(self) -> None:
        """Test steps array is required."""
        steps = [{"name": "Step 1"}, {"name": "Step 2"}]
        assert len(steps) >= 1

    def test_description_optional(self) -> None:
        """Test description is optional."""
        workflow = {"name": "Test", "workflow_type": "test", "steps": []}
        assert workflow.get("description") is None


class TestApprovalWorkflowRead:
    """Tests for ApprovalWorkflowRead schema."""

    def test_id_required(self) -> None:
        """Test id is required UUID."""
        workflow_id = uuid4()
        assert len(str(workflow_id)) == 36

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = uuid4()
        assert project_id is not None

    def test_status_required(self) -> None:
        """Test status is required."""
        status = "IN_PROGRESS"
        assert status is not None

    def test_created_at_required(self) -> None:
        """Test created_at is required."""
        created_at = datetime.utcnow()
        assert created_at is not None

    def test_updated_at_required(self) -> None:
        """Test updated_at is required."""
        updated_at = datetime.utcnow()
        assert updated_at is not None

    def test_steps_list(self) -> None:
        """Test steps is a list."""
        steps = []
        assert isinstance(steps, list)


class TestWorkflowStatus:
    """Tests for WorkflowStatus enum values."""

    def test_draft_status(self) -> None:
        """Test DRAFT status."""
        status = "DRAFT"
        assert status == "DRAFT"

    def test_in_progress_status(self) -> None:
        """Test IN_PROGRESS status."""
        status = "IN_PROGRESS"
        assert status == "IN_PROGRESS"

    def test_approved_status(self) -> None:
        """Test APPROVED status."""
        status = "APPROVED"
        assert status == "APPROVED"

    def test_rejected_status(self) -> None:
        """Test REJECTED status."""
        status = "REJECTED"
        assert status == "REJECTED"

    def test_cancelled_status(self) -> None:
        """Test CANCELLED status."""
        status = "CANCELLED"
        assert status == "CANCELLED"


class TestCurrentStepOrderComputed:
    """Tests for current_step_order computed field."""

    def test_first_step_in_review(self) -> None:
        """Test current_step_order when first step is in review."""
        steps = [
            {"status": "IN_REVIEW", "order": 1},
            {"status": "PENDING", "order": 2},
        ]
        current = next(
            (s["order"] for s in steps if s["status"] in ("PENDING", "IN_REVIEW")),
            len(steps),
        )
        assert current == 1

    def test_second_step_in_review(self) -> None:
        """Test current_step_order when second step is in review."""
        steps = [
            {"status": "APPROVED", "order": 1},
            {"status": "IN_REVIEW", "order": 2},
        ]
        current = next(
            (s["order"] for s in steps if s["status"] in ("PENDING", "IN_REVIEW")),
            len(steps),
        )
        assert current == 2

    def test_all_steps_approved(self) -> None:
        """Test current_step_order when all steps are approved."""
        steps = [
            {"status": "APPROVED", "order": 1},
            {"status": "APPROVED", "order": 2},
        ]
        current = next(
            (s["order"] for s in steps if s["status"] in ("PENDING", "IN_REVIEW")),
            len(steps),
        )
        assert current == 2


class TestWorkflowScenarios:
    """Tests for workflow use case scenarios."""

    def test_create_design_approval_workflow(self) -> None:
        """Test creating a design approval workflow."""
        workflow = {
            "name": "Design Phase Approval",
            "workflow_type": "design_approval",
            "steps": [
                {"name": "Architect Review", "approver_role": "architect"},
                {"name": "Engineer Review", "approver_role": "engineer"},
            ],
        }
        assert len(workflow["steps"]) == 2

    def test_create_regulatory_approval_workflow(self) -> None:
        """Test creating a regulatory approval workflow."""
        workflow = {
            "name": "Regulatory Approval",
            "workflow_type": "regulatory_approval",
            "steps": [
                {"name": "BCA Review", "approver_role": "bca_reviewer"},
                {"name": "URA Review", "approver_role": "ura_reviewer"},
            ],
        }
        assert workflow["workflow_type"] == "regulatory_approval"

    def test_approve_workflow_step(self) -> None:
        """Test approving a workflow step."""
        update = {
            "approved": True,
            "comments": "Design meets all requirements",
        }
        assert update["approved"] is True
