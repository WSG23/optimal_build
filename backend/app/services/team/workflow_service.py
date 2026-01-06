"""Service for managing approval workflows."""

from uuid import UUID

from backend._compat.datetime import utcnow

from app.models.team import TeamMember
from app.models.workflow import (
    ApprovalStep,
    ApprovalWorkflow,
    StepStatus,
    WorkflowStatus,
)

from sqlalchemy import select
from sqlalchemy.orm import joinedload


class WorkflowService:
    """Service for managing approval workflows."""

    def __init__(self, db_session):
        self.db = db_session

    async def _check_step_permission(self, step: ApprovalStep, user_id: UUID) -> bool:
        """Check if user has permission to approve/reject a step.

        Permission is granted if:
        1. The step requires a specific user and user_id matches, OR
        2. The step requires a role and the user has that role in the project, OR
        3. No specific user or role is required (any team member can approve)

        Args:
            step: The approval step to check
            user_id: The ID of the user attempting to approve

        Returns:
            True if user has permission, False otherwise
        """
        # If step requires a specific user, check for exact match
        if step.required_user_id is not None:
            return step.required_user_id == user_id

        # If step requires a specific role, check user's role in the project
        if step.required_role is not None:
            # Get the workflow to find the project_id
            workflow = await self.get_workflow(step.workflow_id)
            if not workflow:
                return False

            # Check if user is a team member with the required role
            query = select(TeamMember).where(
                TeamMember.project_id == workflow.project_id,
                TeamMember.user_id == user_id,
                TeamMember.is_active.is_(True),
            )
            result = await self.db.execute(query)
            member = result.scalar_one_or_none()

            if not member:
                return False

            # Check if member's role matches required role
            # Handle both enum and string comparisons
            member_role = (
                member.role.value if hasattr(member.role, "value") else member.role
            )
            required_role = (
                step.required_role.value
                if hasattr(step.required_role, "value")
                else step.required_role
            )
            return member_role == required_role

        # No specific user or role required - any authenticated user can approve
        return True

    async def create_workflow(
        self,
        project_id: UUID,
        title: str,
        workflow_type: str,
        created_by_id: UUID,
        steps_data: list[dict],
        description: str = None,
    ) -> ApprovalWorkflow:
        """Create a new approval workflow with steps."""

        workflow = ApprovalWorkflow(
            project_id=project_id,
            title=title,
            description=description,
            workflow_type=workflow_type,
            created_by_id=created_by_id,
            status=WorkflowStatus.IN_PROGRESS,  # Auto-start?
        )
        self.db.add(workflow)
        await self.db.flush()  # Get ID

        for idx, step_data in enumerate(steps_data):
            step = ApprovalStep(
                workflow_id=workflow.id,
                name=step_data["name"],
                sequence_order=idx + 1,
                required_role=step_data.get("required_role"),
                required_user_id=step_data.get("required_user_id"),
                status=(
                    StepStatus.PENDING if idx > 0 else StepStatus.IN_REVIEW
                ),  # Activate first step
            )
            self.db.add(step)

        await self.db.commit()
        await self.db.refresh(workflow)
        return workflow

    async def get_workflow(self, workflow_id: UUID) -> ApprovalWorkflow:
        """Get workflow with steps."""
        query = (
            select(ApprovalWorkflow)
            .options(joinedload(ApprovalWorkflow.steps))
            .where(ApprovalWorkflow.id == workflow_id)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def approve_step(
        self, step_id: UUID, user_id: UUID, comments: str = None
    ) -> ApprovalStep:
        """Approve a specific step."""

        query = select(ApprovalStep).where(ApprovalStep.id == step_id)
        result = await self.db.execute(query)
        step = result.scalar_one_or_none()

        if not step:
            raise ValueError("Step not found")

        if step.status != StepStatus.IN_REVIEW:
            raise ValueError("Step is not in review")

        # Check permission (user_id matches required_user_id or has required role)
        has_permission = await self._check_step_permission(step, user_id)
        if not has_permission:
            raise PermissionError(
                "User does not have permission to approve this step. "
                "Required: specific user or role assignment."
            )

        step.status = StepStatus.APPROVED
        step.approved_by_id = user_id
        step.decision_at = utcnow()
        step.comments = comments

        self.db.add(step)

        # Advance workflow
        await self._advance_workflow(step.workflow_id)

        await self.db.commit()
        await self.db.refresh(step)
        return step

    async def _advance_workflow(self, workflow_id: UUID) -> None:
        """Check workflow state and activate next step or complete workflow."""
        workflow = await self.get_workflow(workflow_id)

        all_steps_approved = True
        next_step_found = False

        steps = sorted(workflow.steps, key=lambda s: s.sequence_order)

        for step in steps:
            if step.status == StepStatus.APPROVED:
                continue
            elif step.status == StepStatus.PENDING:
                if not next_step_found:
                    step.status = StepStatus.IN_REVIEW
                    self.db.add(step)
                    next_step_found = True
                    all_steps_approved = False
                else:
                    all_steps_approved = False
            elif step.status in [StepStatus.IN_REVIEW, StepStatus.REJECTED]:
                all_steps_approved = False
                next_step_found = True  # Current active step

        if all_steps_approved:
            workflow.status = WorkflowStatus.APPROVED
            workflow.completed_at = utcnow()
            self.db.add(workflow)
