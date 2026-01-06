"""Tests for workflow_service permission checking and approval workflows.

Tests focus on the permission checking logic in WorkflowService._check_step_permission:
1. Permission granted when step.required_user_id matches user_id
2. Permission granted when user has required_role in the project
3. Permission granted when no specific requirements (any user can approve)
4. Permission denied scenarios
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

pytest.importorskip("sqlalchemy")

from app.models.team import TeamMember
from app.models.workflow import (
    ApprovalStep,
    ApprovalWorkflow,
    StepStatus,
)


class TestCheckStepPermission:
    """Test WorkflowService._check_step_permission."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def workflow_service(self, mock_session):
        """Create WorkflowService instance with mock session."""
        from app.services.team.workflow_service import WorkflowService

        return WorkflowService(mock_session)

    @pytest.mark.asyncio
    async def test_permission_granted_when_user_matches_required_user(
        self, workflow_service
    ):
        """Test permission granted when required_user_id matches user_id."""
        user_id = uuid4()
        step = MagicMock(spec=ApprovalStep)
        step.required_user_id = user_id
        step.required_role = None

        result = await workflow_service._check_step_permission(step, user_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_permission_denied_when_user_mismatch(self, workflow_service):
        """Test permission denied when required_user_id doesn't match user_id."""
        required_user = uuid4()
        actual_user = uuid4()
        step = MagicMock(spec=ApprovalStep)
        step.required_user_id = required_user
        step.required_role = None

        result = await workflow_service._check_step_permission(step, actual_user)

        assert result is False

    @pytest.mark.asyncio
    async def test_permission_granted_when_user_has_required_role(
        self, workflow_service, mock_session
    ):
        """Test permission granted when user has the required role in the project."""
        user_id = uuid4()
        project_id = uuid4()
        workflow_id = uuid4()

        step = MagicMock(spec=ApprovalStep)
        step.required_user_id = None
        step.required_role = "reviewer"
        step.workflow_id = workflow_id

        # Mock workflow with project_id
        mock_workflow = MagicMock(spec=ApprovalWorkflow)
        mock_workflow.project_id = project_id

        # Mock team member with matching role
        mock_member = MagicMock(spec=TeamMember)
        mock_member.role = "reviewer"  # String role

        # Setup get_workflow to return mock workflow
        with patch.object(
            workflow_service, "get_workflow", return_value=mock_workflow
        ) as mock_get_workflow:
            # Setup session.execute to return member
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_member
            mock_session.execute.return_value = mock_result

            result = await workflow_service._check_step_permission(step, user_id)

            assert result is True
            mock_get_workflow.assert_called_once_with(workflow_id)

    @pytest.mark.asyncio
    async def test_permission_granted_when_role_is_enum(
        self, workflow_service, mock_session
    ):
        """Test permission handles enum role values correctly."""
        user_id = uuid4()
        project_id = uuid4()
        workflow_id = uuid4()

        step = MagicMock(spec=ApprovalStep)
        step.required_user_id = None
        step.required_role = MagicMock(value="admin")  # Enum-like
        step.workflow_id = workflow_id

        mock_workflow = MagicMock(spec=ApprovalWorkflow)
        mock_workflow.project_id = project_id

        mock_member = MagicMock(spec=TeamMember)
        mock_member.role = MagicMock(value="admin")  # Enum-like

        with patch.object(workflow_service, "get_workflow", return_value=mock_workflow):
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_member
            mock_session.execute.return_value = mock_result

            result = await workflow_service._check_step_permission(step, user_id)

            assert result is True

    @pytest.mark.asyncio
    async def test_permission_denied_when_role_mismatch(
        self, workflow_service, mock_session
    ):
        """Test permission denied when user's role doesn't match required role."""
        user_id = uuid4()
        project_id = uuid4()
        workflow_id = uuid4()

        step = MagicMock(spec=ApprovalStep)
        step.required_user_id = None
        step.required_role = "admin"
        step.workflow_id = workflow_id

        mock_workflow = MagicMock(spec=ApprovalWorkflow)
        mock_workflow.project_id = project_id

        mock_member = MagicMock(spec=TeamMember)
        mock_member.role = "viewer"  # Different role

        with patch.object(workflow_service, "get_workflow", return_value=mock_workflow):
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_member
            mock_session.execute.return_value = mock_result

            result = await workflow_service._check_step_permission(step, user_id)

            assert result is False

    @pytest.mark.asyncio
    async def test_permission_denied_when_user_not_team_member(
        self, workflow_service, mock_session
    ):
        """Test permission denied when user is not a team member."""
        user_id = uuid4()
        project_id = uuid4()
        workflow_id = uuid4()

        step = MagicMock(spec=ApprovalStep)
        step.required_user_id = None
        step.required_role = "reviewer"
        step.workflow_id = workflow_id

        mock_workflow = MagicMock(spec=ApprovalWorkflow)
        mock_workflow.project_id = project_id

        with patch.object(workflow_service, "get_workflow", return_value=mock_workflow):
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None  # No member found
            mock_session.execute.return_value = mock_result

            result = await workflow_service._check_step_permission(step, user_id)

            assert result is False

    @pytest.mark.asyncio
    async def test_permission_denied_when_workflow_not_found(
        self, workflow_service, mock_session
    ):
        """Test permission denied when workflow doesn't exist."""
        user_id = uuid4()
        workflow_id = uuid4()

        step = MagicMock(spec=ApprovalStep)
        step.required_user_id = None
        step.required_role = "reviewer"
        step.workflow_id = workflow_id

        with patch.object(workflow_service, "get_workflow", return_value=None):
            result = await workflow_service._check_step_permission(step, user_id)

            assert result is False

    @pytest.mark.asyncio
    async def test_permission_granted_when_no_requirements(self, workflow_service):
        """Test permission granted when no specific user or role required."""
        user_id = uuid4()
        step = MagicMock(spec=ApprovalStep)
        step.required_user_id = None
        step.required_role = None

        result = await workflow_service._check_step_permission(step, user_id)

        assert result is True


class TestApproveStep:
    """Test WorkflowService.approve_step with permission checking."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def workflow_service(self, mock_session):
        """Create WorkflowService instance with mock session."""
        from app.services.team.workflow_service import WorkflowService

        return WorkflowService(mock_session)

    @pytest.mark.asyncio
    async def test_approve_step_raises_permission_error(
        self, workflow_service, mock_session
    ):
        """Test approve_step raises PermissionError when user lacks permission."""
        step_id = uuid4()
        user_id = uuid4()
        other_user_id = uuid4()

        # Mock step in review status with different required user
        mock_step = MagicMock(spec=ApprovalStep)
        mock_step.id = step_id
        mock_step.status = StepStatus.IN_REVIEW
        mock_step.required_user_id = other_user_id  # Different user required
        mock_step.required_role = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_step
        mock_session.execute.return_value = mock_result

        with pytest.raises(PermissionError) as exc_info:
            await workflow_service.approve_step(step_id, user_id)

        assert "does not have permission" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_approve_step_raises_value_error_not_in_review(
        self, workflow_service, mock_session
    ):
        """Test approve_step raises ValueError when step not in review."""
        step_id = uuid4()
        user_id = uuid4()

        mock_step = MagicMock(spec=ApprovalStep)
        mock_step.id = step_id
        mock_step.status = StepStatus.PENDING  # Not in review

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_step
        mock_session.execute.return_value = mock_result

        with pytest.raises(ValueError) as exc_info:
            await workflow_service.approve_step(step_id, user_id)

        assert "not in review" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_approve_step_raises_value_error_not_found(
        self, workflow_service, mock_session
    ):
        """Test approve_step raises ValueError when step not found."""
        step_id = uuid4()
        user_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(ValueError) as exc_info:
            await workflow_service.approve_step(step_id, user_id)

        assert "not found" in str(exc_info.value)


class TestCreateWorkflow:
    """Test WorkflowService.create_workflow."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def workflow_service(self, mock_session):
        """Create WorkflowService instance with mock session."""
        from app.services.team.workflow_service import WorkflowService

        return WorkflowService(mock_session)

    @pytest.mark.asyncio
    async def test_create_workflow_creates_workflow_and_steps(
        self, workflow_service, mock_session
    ):
        """Test create_workflow creates workflow with steps."""
        project_id = uuid4()
        created_by_id = uuid4()

        steps_data = [
            {"name": "Initial Review", "required_role": "reviewer"},
            {"name": "Final Approval", "required_user_id": str(uuid4())},
        ]

        # Mock workflow gets an ID after flush
        added_items: list[Any] = []

        def capture_add(item):
            if hasattr(item, "id") and item.id is None:
                item.id = uuid4()
            added_items.append(item)

        mock_session.add.side_effect = capture_add
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        await workflow_service.create_workflow(
            project_id=project_id,
            title="Test Workflow",
            workflow_type="approval",
            created_by_id=created_by_id,
            steps_data=steps_data,
            description="Test description",
        )

        # Verify workflow was added
        assert mock_session.add.call_count >= 3  # 1 workflow + 2 steps
        assert mock_session.commit.called
        assert mock_session.refresh.called
