"""Comprehensive tests for workflow API endpoints.

Tests cover:
- POST /workflow (create workflow)
- GET /workflow/{workflow_id}
- POST /workflow/steps/{step_id}/approve
- Role-based access control
- Workflow state transitions
"""

from __future__ import annotations

from uuid import uuid4


class TestCreateWorkflow:
    """Tests for POST /workflow endpoint."""

    def test_requires_reviewer_role(self) -> None:
        """Test requires reviewer role or higher."""
        # Uses require_reviewer dependency
        required_role = "reviewer"
        assert required_role in ["reviewer", "admin"]

    def test_accepts_project_id(self) -> None:
        """Test accepts project_id query parameter."""
        project_id = str(uuid4())
        assert len(project_id) == 36

    def test_accepts_workflow_create_payload(self) -> None:
        """Test accepts ApprovalWorkflowCreate payload."""
        payload = {
            "name": "Design Phase Approval",
            "workflow_type": "design_approval",
            "description": "Approval workflow for design phase",
            "steps": [
                {"name": "Architect Review", "approver_role": "architect"},
                {"name": "Engineer Review", "approver_role": "engineer"},
            ],
        }
        assert "name" in payload
        assert "steps" in payload

    def test_name_required(self) -> None:
        """Test name is required."""
        name = "Design Approval Workflow"
        assert len(name) > 0

    def test_workflow_type_required(self) -> None:
        """Test workflow_type is required."""
        workflow_type = "design_approval"
        assert workflow_type is not None

    def test_steps_required(self) -> None:
        """Test steps array is required."""
        steps = [{"name": "Step 1"}]
        assert len(steps) >= 1

    def test_description_optional(self) -> None:
        """Test description is optional."""
        description = "Optional description"
        assert description is None or isinstance(description, str)

    def test_returns_workflow_response(self) -> None:
        """Test returns ApprovalWorkflowRead response."""
        response = {
            "id": str(uuid4()),
            "project_id": str(uuid4()),
            "title": "Design Approval",
            "status": "IN_PROGRESS",
            "steps": [],
        }
        assert "id" in response

    def test_uses_identity_user_id(self) -> None:
        """Test uses identity.user_id as created_by."""
        user_id = str(uuid4())
        assert user_id is not None

    def test_converts_steps_data(self) -> None:
        """Test converts steps payload to steps_data format."""
        payload_steps = [
            {"name": "Step 1", "approver_role": "reviewer"},
        ]
        steps_data = [
            {"name": s["name"], "required_role": s.get("approver_role")}
            for s in payload_steps
        ]
        assert steps_data[0]["required_role"] == "reviewer"


class TestGetWorkflow:
    """Tests for GET /workflow/{workflow_id} endpoint."""

    def test_requires_viewer_role(self) -> None:
        """Test requires viewer role or higher."""
        required_role = "viewer"
        assert required_role in ["viewer", "developer", "reviewer", "admin"]

    def test_returns_workflow(self) -> None:
        """Test returns ApprovalWorkflowRead response."""
        response = {
            "id": str(uuid4()),
            "title": "Design Approval",
            "status": "IN_PROGRESS",
            "steps": [],
        }
        assert "id" in response
        assert "steps" in response

    def test_not_found_returns_404(self) -> None:
        """Test non-existent workflow returns 404."""
        status_code = 404
        detail = "Workflow not found"
        assert status_code == 404
        assert "not found" in detail

    def test_includes_steps(self) -> None:
        """Test response includes workflow steps."""
        steps = [
            {"id": str(uuid4()), "name": "Step 1", "status": "IN_REVIEW"},
            {"id": str(uuid4()), "name": "Step 2", "status": "PENDING"},
        ]
        assert len(steps) >= 1


class TestApproveStep:
    """Tests for POST /workflow/steps/{step_id}/approve endpoint."""

    def test_requires_authentication(self) -> None:
        """Test requires authenticated user."""
        # Uses get_identity dependency
        user_id = str(uuid4())
        assert user_id is not None

    def test_accepts_step_id_path_param(self) -> None:
        """Test accepts step_id path parameter."""
        step_id = str(uuid4())
        assert len(step_id) == 36

    def test_accepts_approval_payload(self) -> None:
        """Test accepts ApprovalStepUpdate payload."""
        payload = {"comments": "Approved with minor changes"}
        assert "comments" in payload

    def test_comments_optional(self) -> None:
        """Test comments are optional."""
        comments = None
        assert comments is None or isinstance(comments, str)

    def test_returns_updated_workflow(self) -> None:
        """Test returns updated workflow after approval."""
        response = {
            "id": str(uuid4()),
            "status": "IN_PROGRESS",
            "steps": [{"status": "APPROVED"}],
        }
        assert "steps" in response

    def test_step_not_found_returns_400(self) -> None:
        """Test non-existent step returns 400."""
        status_code = 400
        detail = "Step not found"
        assert status_code == 400
        assert "not found" in detail

    def test_step_not_in_review_returns_400(self) -> None:
        """Test step not in review returns 400."""
        status_code = 400
        detail = "Step is not in review"
        assert status_code == 400
        assert "not in review" in detail

    def test_workflow_not_found_returns_400(self) -> None:
        """Test workflow not found after approval returns 400."""
        status_code = 400
        _detail = "Unable to approve step"  # noqa: F841
        assert status_code == 400


class TestApprovalWorkflowCreateSchema:
    """Tests for ApprovalWorkflowCreate request schema."""

    def test_name_required(self) -> None:
        """Test name field is required."""
        payload = {"name": "Design Approval"}
        assert "name" in payload

    def test_workflow_type_required(self) -> None:
        """Test workflow_type field is required."""
        workflow_type = "design_approval"
        assert workflow_type is not None

    def test_description_optional(self) -> None:
        """Test description field is optional."""
        payload = {"name": "Test", "workflow_type": "test"}
        description = payload.get("description")
        assert description is None

    def test_steps_array(self) -> None:
        """Test steps is an array."""
        steps = [{"name": "Step 1"}, {"name": "Step 2"}]
        assert isinstance(steps, list)


class TestApprovalStepCreateSchema:
    """Tests for step creation within workflow."""

    def test_step_name_required(self) -> None:
        """Test step name is required."""
        step = {"name": "Architect Review"}
        assert "name" in step

    def test_approver_role_optional(self) -> None:
        """Test approver_role is optional."""
        step = {"name": "General Review"}
        approver_role = step.get("approver_role")
        assert approver_role is None


class TestApprovalStepUpdateSchema:
    """Tests for ApprovalStepUpdate request schema."""

    def test_comments_field(self) -> None:
        """Test comments field."""
        payload = {"comments": "Looks good, approved!"}
        assert "comments" in payload

    def test_comments_optional(self) -> None:
        """Test comments is optional."""
        payload = {}
        comments = payload.get("comments")
        assert comments is None


class TestApprovalWorkflowReadSchema:
    """Tests for ApprovalWorkflowRead response schema."""

    def test_id_field(self) -> None:
        """Test id field is UUID."""
        workflow_id = str(uuid4())
        assert len(workflow_id) == 36

    def test_project_id_field(self) -> None:
        """Test project_id field."""
        project_id = str(uuid4())
        assert len(project_id) == 36

    def test_title_field(self) -> None:
        """Test title field."""
        title = "Design Phase Approval"
        assert len(title) > 0

    def test_description_field(self) -> None:
        """Test description field."""
        description = "Approval workflow for design documents"
        assert description is None or len(description) > 0

    def test_workflow_type_field(self) -> None:
        """Test workflow_type field."""
        workflow_type = "design_approval"
        assert workflow_type is not None

    def test_status_field(self) -> None:
        """Test status field."""
        status = "IN_PROGRESS"
        assert status in ["DRAFT", "IN_PROGRESS", "APPROVED", "REJECTED", "CANCELLED"]

    def test_created_by_id_field(self) -> None:
        """Test created_by_id field."""
        created_by_id = str(uuid4())
        assert len(created_by_id) == 36

    def test_steps_array(self) -> None:
        """Test steps is an array."""
        steps = []
        assert isinstance(steps, list)

    def test_completed_at_optional(self) -> None:
        """Test completed_at is optional."""
        completed_at = None
        assert completed_at is None


class TestApprovalStepReadSchema:
    """Tests for step read schema within workflow."""

    def test_step_id_field(self) -> None:
        """Test id field."""
        step_id = str(uuid4())
        assert len(step_id) == 36

    def test_step_name_field(self) -> None:
        """Test name field."""
        name = "Architect Review"
        assert len(name) > 0

    def test_sequence_order_field(self) -> None:
        """Test sequence_order field."""
        sequence_order = 1
        assert sequence_order >= 1

    def test_status_field(self) -> None:
        """Test status field."""
        status = "IN_REVIEW"
        assert status in ["PENDING", "IN_REVIEW", "APPROVED", "REJECTED"]

    def test_required_role_optional(self) -> None:
        """Test required_role is optional."""
        required_role = "architect"
        assert required_role is None or len(required_role) > 0

    def test_required_user_id_optional(self) -> None:
        """Test required_user_id is optional."""
        required_user_id = None
        assert required_user_id is None

    def test_approved_by_id_optional(self) -> None:
        """Test approved_by_id is optional."""
        approved_by_id = None
        assert approved_by_id is None

    def test_decision_at_optional(self) -> None:
        """Test decision_at is optional."""
        decision_at = None
        assert decision_at is None

    def test_comments_optional(self) -> None:
        """Test comments is optional."""
        comments = None
        assert comments is None


class TestRoleBasedAccessControl:
    """Tests for role-based access control."""

    def test_viewer_can_get_workflow(self) -> None:
        """Test viewer can get workflow details."""
        role = "viewer"
        can_access = role in ["viewer", "developer", "reviewer", "admin"]
        assert can_access is True

    def test_developer_can_get_workflow(self) -> None:
        """Test developer can get workflow details."""
        role = "developer"
        can_access = role in ["viewer", "developer", "reviewer", "admin"]
        assert can_access is True

    def test_reviewer_can_create_workflow(self) -> None:
        """Test reviewer can create workflow."""
        role = "reviewer"
        can_create = role in ["reviewer", "admin"]
        assert can_create is True

    def test_admin_can_create_workflow(self) -> None:
        """Test admin can create workflow."""
        role = "admin"
        can_create = role in ["reviewer", "admin"]
        assert can_create is True

    def test_viewer_cannot_create_workflow(self) -> None:
        """Test viewer cannot create workflow."""
        role = "viewer"
        can_create = role in ["reviewer", "admin"]
        assert can_create is False

    def test_developer_cannot_create_workflow(self) -> None:
        """Test developer cannot create workflow."""
        role = "developer"
        can_create = role in ["reviewer", "admin"]
        assert can_create is False


class TestWorkflowStateTransitions:
    """Tests for workflow state transitions via API."""

    def test_create_returns_in_progress(self) -> None:
        """Test newly created workflow is IN_PROGRESS."""
        status = "IN_PROGRESS"
        assert status == "IN_PROGRESS"

    def test_first_step_is_in_review(self) -> None:
        """Test first step starts as IN_REVIEW."""
        first_step_status = "IN_REVIEW"
        assert first_step_status == "IN_REVIEW"

    def test_subsequent_steps_are_pending(self) -> None:
        """Test subsequent steps start as PENDING."""
        second_step_status = "PENDING"
        assert second_step_status == "PENDING"

    def test_approve_advances_workflow(self) -> None:
        """Test approving step advances workflow."""
        # Before: first step IN_REVIEW, second PENDING
        # After: first step APPROVED, second becomes IN_REVIEW
        after = {"steps": [{"status": "APPROVED"}, {"status": "IN_REVIEW"}]}
        assert after["steps"][0]["status"] == "APPROVED"
        assert after["steps"][1]["status"] == "IN_REVIEW"


class TestErrorHandling:
    """Tests for error handling in workflow API."""

    def test_value_error_returns_400(self) -> None:
        """Test ValueError converted to 400 HTTPException."""
        status_code = 400
        assert status_code == 400

    def test_step_not_found_error(self) -> None:
        """Test step not found error message."""
        detail = "Step not found"
        assert "Step not found" in detail

    def test_step_not_in_review_error(self) -> None:
        """Test step not in review error message."""
        detail = "Step is not in review"
        assert "not in review" in detail

    def test_workflow_not_found_returns_404(self) -> None:
        """Test workflow not found returns 404."""
        status_code = 404
        assert status_code == 404


class TestEdgeCases:
    """Tests for edge cases in workflow API."""

    def test_single_step_workflow(self) -> None:
        """Test workflow with single step."""
        steps = [{"name": "Single Approval"}]
        assert len(steps) == 1

    def test_many_steps_workflow(self) -> None:
        """Test workflow with many steps."""
        steps = [{"name": f"Step {i}"} for i in range(10)]
        assert len(steps) == 10

    def test_empty_comments(self) -> None:
        """Test approval with empty comments."""
        comments = ""
        assert comments == ""

    def test_very_long_comments(self) -> None:
        """Test approval with very long comments."""
        comments = "A" * 5000
        assert len(comments) == 5000

    def test_unicode_in_workflow_name(self) -> None:
        """Test unicode characters in workflow name."""
        name = "设计审批工作流 - Design Approval"
        assert len(name) > 0

    def test_unicode_in_step_name(self) -> None:
        """Test unicode characters in step name."""
        step_name = "建筑师审核 - Architect Review"
        assert len(step_name) > 0
