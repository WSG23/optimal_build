"""Service for managing approval workflows."""

from uuid import UUID

from backend._compat.datetime import utcnow

from app.models.team import TeamMember
from app.models.users import User, UserRole
from app.models.workflow import (
    ApprovalStep,
    ApprovalWorkflow,
    StepStatus,
    WorkflowStatus,
)
from app.services.notification import NotificationService

# from app.services.base import BaseService # Removed
from sqlalchemy import and_, select
from sqlalchemy.orm import joinedload


class WorkflowService:
    """Service for managing approval workflows."""

    def __init__(self, db_session):
        self.db = db_session
        self.notifications = NotificationService(db_session)

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
        workflow_with_steps = await self.get_workflow(workflow.id)
        if not workflow_with_steps:
            raise ValueError("Workflow not found")

        first_step = next(
            (
                step
                for step in sorted(
                    workflow_with_steps.steps, key=lambda step: step.sequence_order
                )
                if step.status == StepStatus.IN_REVIEW
            ),
            None,
        )
        if first_step:
            await self._notify_step_approvers(workflow_with_steps, first_step)

        return workflow_with_steps

    async def get_workflow(self, workflow_id: UUID) -> ApprovalWorkflow:
        """Get workflow with steps."""
        query = (
            select(ApprovalWorkflow)
            .options(joinedload(ApprovalWorkflow.steps))
            .where(ApprovalWorkflow.id == workflow_id)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_workflows(
        self,
        project_id: UUID,
        *,
        status: WorkflowStatus | None = None,
    ) -> list[ApprovalWorkflow]:
        """List workflows for a project (including steps)."""

        query = (
            select(ApprovalWorkflow)
            .options(joinedload(ApprovalWorkflow.steps))
            .where(ApprovalWorkflow.project_id == project_id)
            .order_by(ApprovalWorkflow.created_at.desc())
        )
        if status is not None:
            query = query.where(ApprovalWorkflow.status == status)

        result = await self.db.execute(query)
        return list(result.unique().scalars().all())

    async def decide_step(
        self,
        step_id: UUID,
        user_id: UUID,
        *,
        approved: bool,
        comments: str | None = None,
    ) -> ApprovalStep:
        """Approve or reject a specific step."""

        query = select(ApprovalStep).where(ApprovalStep.id == step_id)
        result = await self.db.execute(query)
        step = result.scalar_one_or_none()

        if not step:
            raise ValueError("Step not found")

        if step.status != StepStatus.IN_REVIEW:
            raise ValueError("Step is not in review")

        workflow = await self.get_workflow(step.workflow_id)
        if not workflow:
            raise ValueError("Workflow not found")

        await self._ensure_user_can_decide_step(step, workflow, user_id)

        user = await self._get_user(user_id)

        step.status = StepStatus.APPROVED if approved else StepStatus.REJECTED
        step.approved_by_id = user_id
        step.decision_at = utcnow()
        step.comments = comments

        self.db.add(step)

        # Advance workflow
        next_step, completed_status = await self._advance_workflow(workflow)

        await self.db.commit()
        await self.db.refresh(step)

        # Notifications after commit so list endpoints can see the updated state.
        if completed_status == WorkflowStatus.APPROVED:
            await self.notifications.notify_workflow_approved(
                user_id=workflow.created_by_id,
                workflow_title=workflow.title,
                approver_name=user.full_name,
                workflow_id=workflow.id,
                project_id=workflow.project_id,
            )
        elif completed_status == WorkflowStatus.REJECTED:
            await self.notifications.notify_workflow_rejected(
                user_id=workflow.created_by_id,
                workflow_title=workflow.title,
                rejector_name=user.full_name,
                reason=comments,
                workflow_id=workflow.id,
                project_id=workflow.project_id,
            )
        elif next_step:
            await self._notify_step_approvers(workflow, next_step)
        return step

    async def _get_user(self, user_id: UUID) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")
        return user

    async def _ensure_user_can_decide_step(
        self, step: ApprovalStep, workflow: ApprovalWorkflow, user_id: UUID
    ) -> None:
        # Admins can always decide.
        user = await self._get_user(user_id)
        if user.role == UserRole.ADMIN:
            return

        if step.required_user_id and step.required_user_id != user_id:
            raise PermissionError("User is not the required approver for this step")

        member_query = select(TeamMember).where(
            and_(
                TeamMember.project_id == workflow.project_id,
                TeamMember.user_id == user_id,
                TeamMember.is_active.is_(True),
            )
        )
        member_result = await self.db.execute(member_query)
        membership = member_result.scalar_one_or_none()
        if not membership:
            raise PermissionError("User is not a member of this project team")

        required_role = step.required_role
        if required_role is None:
            return

        required_role_value = (
            required_role.value
            if hasattr(required_role, "value")
            else str(required_role)
        )
        membership_role_value = (
            membership.role.value
            if hasattr(membership.role, "value")
            else str(membership.role)
        )
        if membership_role_value != required_role_value:
            raise PermissionError("User does not have the required role for this step")

    async def _notify_step_approvers(
        self,
        workflow: ApprovalWorkflow,
        step: ApprovalStep,
    ) -> None:
        if step.required_user_id:
            await self.notifications.notify_workflow_approval_pending(
                user_id=step.required_user_id,
                workflow_title=workflow.title,
                step_name=step.name,
                workflow_id=workflow.id,
                project_id=workflow.project_id,
            )
            return

        if step.required_role is None:
            return

        required_role_value = (
            step.required_role.value
            if hasattr(step.required_role, "value")
            else str(step.required_role)
        )
        query = select(TeamMember).where(
            and_(
                TeamMember.project_id == workflow.project_id,
                TeamMember.is_active.is_(True),
                TeamMember.role == required_role_value,
            )
        )
        result = await self.db.execute(query)
        members = list(result.scalars().all())
        for member in members:
            await self.notifications.notify_workflow_approval_pending(
                user_id=member.user_id,
                workflow_title=workflow.title,
                step_name=step.name,
                workflow_id=workflow.id,
                project_id=workflow.project_id,
            )

    async def _advance_workflow(
        self, workflow: ApprovalWorkflow
    ) -> tuple[ApprovalStep | None, WorkflowStatus | None]:
        """Check workflow state and activate next step or complete workflow.

        Returns:
          (next_step_activated, completed_status)
        """

        all_steps_approved = True
        next_step_found = False
        next_step_activated: ApprovalStep | None = None
        completed_status: WorkflowStatus | None = None

        steps = sorted(workflow.steps, key=lambda s: s.sequence_order)

        for step in steps:
            if step.status == StepStatus.APPROVED:
                continue
            if step.status == StepStatus.REJECTED:
                all_steps_approved = False
                completed_status = WorkflowStatus.REJECTED
                next_step_found = True
                break
            elif step.status == StepStatus.PENDING:
                if not next_step_found:
                    step.status = StepStatus.IN_REVIEW
                    self.db.add(step)
                    next_step_found = True
                    all_steps_approved = False
                    next_step_activated = step
                else:
                    all_steps_approved = False
            elif step.status in [StepStatus.IN_REVIEW, StepStatus.REJECTED]:
                all_steps_approved = False
                next_step_found = True  # Current active step

        if completed_status == WorkflowStatus.REJECTED:
            workflow.status = WorkflowStatus.REJECTED
            workflow.completed_at = utcnow()
            self.db.add(workflow)
            return next_step_activated, WorkflowStatus.REJECTED

        if all_steps_approved:
            workflow.status = WorkflowStatus.APPROVED
            workflow.completed_at = utcnow()
            self.db.add(workflow)
            completed_status = WorkflowStatus.APPROVED

        return next_step_activated, completed_status
