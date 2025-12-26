"""Comprehensive tests for Workflow models.

Tests cover:
- ApprovalWorkflow and ApprovalStep models
- WorkflowStatus and StepStatus enums
- Status transitions and state machine logic
- Foreign key relationships
- Approval step ordering
"""

from __future__ import annotations

import uuid
from datetime import datetime


from app.models.users import UserRole
from app.models.workflow import (
    ApprovalStep,
    ApprovalWorkflow,
    StepStatus,
    WorkflowStatus,
)
from backend._compat.datetime import UTC


class TestWorkflowStatusEnum:
    """Tests for WorkflowStatus enum."""

    def test_all_statuses_defined(self) -> None:
        """All expected statuses should be defined."""
        expected = ["DRAFT", "IN_PROGRESS", "APPROVED", "REJECTED", "CANCELLED"]
        actual = [s.name for s in WorkflowStatus]
        assert sorted(actual) == sorted(expected)

    def test_status_values(self) -> None:
        """Status values should be lowercase."""
        assert WorkflowStatus.DRAFT.value == "draft"
        assert WorkflowStatus.IN_PROGRESS.value == "in_progress"
        assert WorkflowStatus.APPROVED.value == "approved"
        assert WorkflowStatus.REJECTED.value == "rejected"
        assert WorkflowStatus.CANCELLED.value == "cancelled"

    def test_status_is_string_enum(self) -> None:
        """WorkflowStatus should be a string enum."""
        assert isinstance(WorkflowStatus.DRAFT, str)
        assert WorkflowStatus.DRAFT == "draft"


class TestStepStatusEnum:
    """Tests for StepStatus enum."""

    def test_all_statuses_defined(self) -> None:
        """All expected statuses should be defined."""
        expected = ["PENDING", "IN_REVIEW", "APPROVED", "REJECTED", "SKIPPED"]
        actual = [s.name for s in StepStatus]
        assert sorted(actual) == sorted(expected)

    def test_status_values(self) -> None:
        """Status values should be lowercase."""
        assert StepStatus.PENDING.value == "pending"
        assert StepStatus.IN_REVIEW.value == "in_review"
        assert StepStatus.APPROVED.value == "approved"
        assert StepStatus.REJECTED.value == "rejected"
        assert StepStatus.SKIPPED.value == "skipped"


class TestApprovalWorkflowCreation:
    """Tests for ApprovalWorkflow model creation."""

    def test_create_minimal_workflow(self) -> None:
        """Workflow with required fields should be valid."""
        workflow = ApprovalWorkflow(
            id=uuid.uuid4(),
            project_id=uuid.uuid4(),
            title="Design Review",
            workflow_type="design_review",
            created_by_id=uuid.uuid4(),
        )
        assert workflow.title == "Design Review"
        assert workflow.workflow_type == "design_review"

    def test_create_workflow_with_all_fields(self) -> None:
        """Workflow with all fields should be valid."""
        workflow_id = uuid.uuid4()
        now = datetime.now(UTC)
        workflow = ApprovalWorkflow(
            id=workflow_id,
            project_id=uuid.uuid4(),
            title="Feasibility Signoff",
            description="Complete feasibility signoff for Phase 1",
            workflow_type="feasibility_signoff",
            status=WorkflowStatus.IN_PROGRESS,
            created_by_id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            completed_at=None,
        )
        assert workflow.id == workflow_id
        assert workflow.description == "Complete feasibility signoff for Phase 1"


class TestApprovalWorkflowStatus:
    """Tests for workflow status field."""

    def test_default_status_is_draft(self) -> None:
        """Default status should be DRAFT."""
        workflow = ApprovalWorkflow(
            project_id=uuid.uuid4(),
            title="Test",
            workflow_type="test",
            created_by_id=uuid.uuid4(),
        )
        # Note: Default is set at DB level
        assert workflow.status is None or workflow.status == WorkflowStatus.DRAFT

    def test_status_in_progress(self) -> None:
        """IN_PROGRESS status should be assignable."""
        workflow = ApprovalWorkflow(
            project_id=uuid.uuid4(),
            title="Test",
            workflow_type="test",
            created_by_id=uuid.uuid4(),
            status=WorkflowStatus.IN_PROGRESS,
        )
        assert workflow.status == WorkflowStatus.IN_PROGRESS

    def test_status_approved(self) -> None:
        """APPROVED status should be assignable."""
        workflow = ApprovalWorkflow(
            project_id=uuid.uuid4(),
            title="Test",
            workflow_type="test",
            created_by_id=uuid.uuid4(),
            status=WorkflowStatus.APPROVED,
        )
        assert workflow.status == WorkflowStatus.APPROVED

    def test_status_rejected(self) -> None:
        """REJECTED status should be assignable."""
        workflow = ApprovalWorkflow(
            project_id=uuid.uuid4(),
            title="Test",
            workflow_type="test",
            created_by_id=uuid.uuid4(),
            status=WorkflowStatus.REJECTED,
        )
        assert workflow.status == WorkflowStatus.REJECTED

    def test_status_cancelled(self) -> None:
        """CANCELLED status should be assignable."""
        workflow = ApprovalWorkflow(
            project_id=uuid.uuid4(),
            title="Test",
            workflow_type="test",
            created_by_id=uuid.uuid4(),
            status=WorkflowStatus.CANCELLED,
        )
        assert workflow.status == WorkflowStatus.CANCELLED


class TestApprovalWorkflowTypes:
    """Tests for workflow_type field."""

    def test_feasibility_signoff_type(self) -> None:
        """feasibility_signoff type should be valid."""
        workflow = ApprovalWorkflow(
            project_id=uuid.uuid4(),
            title="Test",
            workflow_type="feasibility_signoff",
            created_by_id=uuid.uuid4(),
        )
        assert workflow.workflow_type == "feasibility_signoff"

    def test_design_review_type(self) -> None:
        """design_review type should be valid."""
        workflow = ApprovalWorkflow(
            project_id=uuid.uuid4(),
            title="Test",
            workflow_type="design_review",
            created_by_id=uuid.uuid4(),
        )
        assert workflow.workflow_type == "design_review"

    def test_custom_workflow_type(self) -> None:
        """Custom workflow types should be accepted."""
        workflow = ApprovalWorkflow(
            project_id=uuid.uuid4(),
            title="Test",
            workflow_type="custom_approval_process",
            created_by_id=uuid.uuid4(),
        )
        assert workflow.workflow_type == "custom_approval_process"


class TestApprovalWorkflowTimestamps:
    """Tests for workflow timestamp fields."""

    def test_created_at(self) -> None:
        """created_at should be settable."""
        now = datetime.now(UTC)
        workflow = ApprovalWorkflow(
            project_id=uuid.uuid4(),
            title="Test",
            workflow_type="test",
            created_by_id=uuid.uuid4(),
            created_at=now,
        )
        assert workflow.created_at == now

    def test_completed_at(self) -> None:
        """completed_at should be settable."""
        now = datetime.now(UTC)
        workflow = ApprovalWorkflow(
            project_id=uuid.uuid4(),
            title="Test",
            workflow_type="test",
            created_by_id=uuid.uuid4(),
            status=WorkflowStatus.APPROVED,
            completed_at=now,
        )
        assert workflow.completed_at == now

    def test_completed_at_none(self) -> None:
        """completed_at should be nullable."""
        workflow = ApprovalWorkflow(
            project_id=uuid.uuid4(),
            title="Test",
            workflow_type="test",
            created_by_id=uuid.uuid4(),
            completed_at=None,
        )
        assert workflow.completed_at is None


class TestApprovalStepCreation:
    """Tests for ApprovalStep model creation."""

    def test_create_minimal_step(self) -> None:
        """Step with required fields should be valid."""
        step = ApprovalStep(
            id=uuid.uuid4(),
            workflow_id=uuid.uuid4(),
            name="Initial Review",
            sequence_order=1,
        )
        assert step.name == "Initial Review"
        assert step.sequence_order == 1

    def test_create_step_with_all_fields(self) -> None:
        """Step with all fields should be valid."""
        step_id = uuid.uuid4()
        datetime.now(UTC)
        step = ApprovalStep(
            id=step_id,
            workflow_id=uuid.uuid4(),
            name="Final Approval",
            sequence_order=3,
            required_role=UserRole.ADMIN,
            required_user_id=None,
            status=StepStatus.PENDING,
            approved_by_id=None,
            decision_at=None,
            comments=None,
        )
        assert step.id == step_id
        assert step.required_role == UserRole.ADMIN


class TestApprovalStepStatus:
    """Tests for step status field."""

    def test_default_status_is_pending(self) -> None:
        """Default status should be PENDING."""
        step = ApprovalStep(
            workflow_id=uuid.uuid4(),
            name="Test",
            sequence_order=1,
        )
        # Note: Default is set at DB level
        assert step.status is None or step.status == StepStatus.PENDING

    def test_status_in_review(self) -> None:
        """IN_REVIEW status should be assignable."""
        step = ApprovalStep(
            workflow_id=uuid.uuid4(),
            name="Test",
            sequence_order=1,
            status=StepStatus.IN_REVIEW,
        )
        assert step.status == StepStatus.IN_REVIEW

    def test_status_approved(self) -> None:
        """APPROVED status should be assignable."""
        step = ApprovalStep(
            workflow_id=uuid.uuid4(),
            name="Test",
            sequence_order=1,
            status=StepStatus.APPROVED,
        )
        assert step.status == StepStatus.APPROVED

    def test_status_rejected(self) -> None:
        """REJECTED status should be assignable."""
        step = ApprovalStep(
            workflow_id=uuid.uuid4(),
            name="Test",
            sequence_order=1,
            status=StepStatus.REJECTED,
        )
        assert step.status == StepStatus.REJECTED

    def test_status_skipped(self) -> None:
        """SKIPPED status should be assignable."""
        step = ApprovalStep(
            workflow_id=uuid.uuid4(),
            name="Test",
            sequence_order=1,
            status=StepStatus.SKIPPED,
        )
        assert step.status == StepStatus.SKIPPED


class TestApprovalStepRequirements:
    """Tests for step requirement fields."""

    def test_required_role(self) -> None:
        """required_role should accept UserRole enum."""
        step = ApprovalStep(
            workflow_id=uuid.uuid4(),
            name="Developer Review",
            sequence_order=1,
            required_role=UserRole.DEVELOPER,
        )
        assert step.required_role == UserRole.DEVELOPER

    def test_required_user_id(self) -> None:
        """required_user_id for specific user requirement."""
        user_id = uuid.uuid4()
        step = ApprovalStep(
            workflow_id=uuid.uuid4(),
            name="Manager Approval",
            sequence_order=2,
            required_user_id=user_id,
        )
        assert step.required_user_id == user_id

    def test_both_role_and_user_nullable(self) -> None:
        """Both required_role and required_user_id can be null."""
        step = ApprovalStep(
            workflow_id=uuid.uuid4(),
            name="Open Review",
            sequence_order=1,
            required_role=None,
            required_user_id=None,
        )
        assert step.required_role is None
        assert step.required_user_id is None


class TestApprovalStepOutcome:
    """Tests for step outcome fields."""

    def test_approved_by_id(self) -> None:
        """approved_by_id should be settable."""
        approver_id = uuid.uuid4()
        step = ApprovalStep(
            workflow_id=uuid.uuid4(),
            name="Test",
            sequence_order=1,
            status=StepStatus.APPROVED,
            approved_by_id=approver_id,
        )
        assert step.approved_by_id == approver_id

    def test_decision_at(self) -> None:
        """decision_at should be settable."""
        now = datetime.now(UTC)
        step = ApprovalStep(
            workflow_id=uuid.uuid4(),
            name="Test",
            sequence_order=1,
            status=StepStatus.APPROVED,
            decision_at=now,
        )
        assert step.decision_at == now

    def test_comments(self) -> None:
        """comments should accept text."""
        step = ApprovalStep(
            workflow_id=uuid.uuid4(),
            name="Test",
            sequence_order=1,
            status=StepStatus.APPROVED,
            comments="Approved with minor corrections needed.",
        )
        assert "Approved" in step.comments


class TestApprovalStepOrdering:
    """Tests for step sequence ordering."""

    def test_sequence_order_positive(self) -> None:
        """Sequence order should be positive."""
        step = ApprovalStep(
            workflow_id=uuid.uuid4(),
            name="Step 1",
            sequence_order=1,
        )
        assert step.sequence_order == 1

    def test_multiple_sequence_orders(self) -> None:
        """Multiple steps with different orders."""
        workflow_id = uuid.uuid4()
        steps = [
            ApprovalStep(workflow_id=workflow_id, name="Step 1", sequence_order=1),
            ApprovalStep(workflow_id=workflow_id, name="Step 2", sequence_order=2),
            ApprovalStep(workflow_id=workflow_id, name="Step 3", sequence_order=3),
        ]
        orders = [s.sequence_order for s in steps]
        assert orders == [1, 2, 3]


class TestWorkflowRelationships:
    """Tests for workflow model relationships."""

    def test_workflow_has_steps_attribute(self) -> None:
        """Workflow should have steps relationship."""
        workflow = ApprovalWorkflow(
            project_id=uuid.uuid4(),
            title="Test",
            workflow_type="test",
            created_by_id=uuid.uuid4(),
        )
        assert hasattr(workflow, "steps")

    def test_workflow_has_project_attribute(self) -> None:
        """Workflow should have project relationship."""
        workflow = ApprovalWorkflow(
            project_id=uuid.uuid4(),
            title="Test",
            workflow_type="test",
            created_by_id=uuid.uuid4(),
        )
        assert hasattr(workflow, "project")

    def test_step_has_workflow_attribute(self) -> None:
        """Step should have workflow relationship."""
        step = ApprovalStep(
            workflow_id=uuid.uuid4(),
            name="Test",
            sequence_order=1,
        )
        assert hasattr(step, "workflow")
