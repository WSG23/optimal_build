"""Service for managing approval workflows."""

from uuid import UUID

from backend._compat.datetime import utcnow
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.team import TeamMember
from app.models.workflow import (
    ApprovalStep,
    ApprovalWorkflow,
    StepStatus,
    WorkflowStatus,
)
from app.services.analytics_capture import (
    capture_lifecycle_event,
    capture_status_transition,
    capture_success,
)


class WorkflowService:
    """Service for managing approval workflows."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session

    @staticmethod
    def _enum_value(value: object) -> object:
        return value.value if hasattr(value, "value") else value

    def _workflow_payload(self, workflow: ApprovalWorkflow) -> dict[str, object]:
        return {
            "id": str(workflow.id),
            "project_id": str(workflow.project_id),
            "title": workflow.title,
            "description": workflow.description,
            "workflow_type": workflow.workflow_type,
            "created_by_id": str(workflow.created_by_id),
            "status": self._enum_value(workflow.status),
            "completed_at": (
                workflow.completed_at.isoformat() if workflow.completed_at else None
            ),
        }

    def _step_payload(self, step: ApprovalStep) -> dict[str, object]:
        return {
            "id": str(step.id),
            "workflow_id": str(step.workflow_id),
            "name": step.name,
            "sequence_order": step.sequence_order,
            "required_role": self._enum_value(step.required_role),
            "required_user_id": (
                str(step.required_user_id) if step.required_user_id else None
            ),
            "status": self._enum_value(step.status),
            "approved_by_id": str(step.approved_by_id) if step.approved_by_id else None,
            "decision_at": step.decision_at.isoformat() if step.decision_at else None,
            "comments": step.comments,
        }

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
        description: str | None = None,
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

        created_steps: list[ApprovalStep] = []
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
            created_steps.append(step)

        await self.db.flush()
        await capture_lifecycle_event(
            self.db,
            entity_type="approval_workflow",
            entity_id=str(workflow.id),
            action="create",
            after_payload={
                **self._workflow_payload(workflow),
                "steps": [self._step_payload(step) for step in created_steps],
            },
            metadata={"project_id": str(project_id)},
        )
        await capture_status_transition(
            self.db,
            entity_type="approval_workflow",
            entity_id=str(workflow.id),
            status_field="status",
            from_status=None,
            to_status=WorkflowStatus.IN_PROGRESS.value,
            reason="workflow_created",
            metadata={"project_id": str(project_id)},
        )
        for step in created_steps:
            await capture_status_transition(
                self.db,
                entity_type="approval_step",
                entity_id=str(step.id),
                status_field="status",
                from_status=None,
                to_status=str(self._enum_value(step.status)),
                reason="workflow_created",
                metadata={"workflow_id": str(workflow.id)},
            )
        await capture_success(
            self.db,
            source="workflow.create",
            operation="create",
            entity_type="approval_workflow",
            entity_id=str(workflow.id),
            raw_payload={
                **self._workflow_payload(workflow),
                "steps": [self._step_payload(step) for step in created_steps],
            },
        )

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

    async def list_workflows(self, project_id: UUID) -> list[ApprovalWorkflow]:
        """List all workflows for a project with their steps.

        Args:
            project_id: The project ID to filter workflows by

        Returns:
            List of workflows with steps eagerly loaded
        """
        query = (
            select(ApprovalWorkflow)
            .options(joinedload(ApprovalWorkflow.steps))
            .where(ApprovalWorkflow.project_id == project_id)
            .order_by(ApprovalWorkflow.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().unique().all()

    async def approve_step(
        self, step_id: UUID, user_id: UUID, comments: str | None = None
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
        await capture_status_transition(
            self.db,
            entity_type="approval_step",
            entity_id=str(step.id),
            status_field="status",
            from_status=StepStatus.IN_REVIEW.value,
            to_status=StepStatus.APPROVED.value,
            reason="approve_step",
            metadata={"workflow_id": str(step.workflow_id), "user_id": str(user_id)},
        )
        await capture_lifecycle_event(
            self.db,
            entity_type="approval_step",
            entity_id=str(step.id),
            action="update",
            after_payload=self._step_payload(step),
            metadata={"updated_fields": ["status", "approved_by_id", "decision_at"]},
        )

        # Advance workflow
        await self._advance_workflow(step.workflow_id)

        await self.db.commit()
        await self.db.refresh(step)
        return step

    async def reject_step(
        self, step_id: UUID, user_id: UUID, comments: str | None = None
    ) -> ApprovalStep:
        """Reject a specific step, blocking workflow progression."""

        query = select(ApprovalStep).where(ApprovalStep.id == step_id)
        result = await self.db.execute(query)
        step = result.scalar_one_or_none()

        if not step:
            raise ValueError("Step not found")

        if step.status != StepStatus.IN_REVIEW:
            raise ValueError("Step is not in review")

        has_permission = await self._check_step_permission(step, user_id)
        if not has_permission:
            raise PermissionError(
                "User does not have permission to reject this step. "
                "Required: specific user or role assignment."
            )

        step.status = StepStatus.REJECTED
        step.approved_by_id = user_id
        step.decision_at = utcnow()
        step.comments = comments

        self.db.add(step)
        await capture_status_transition(
            self.db,
            entity_type="approval_step",
            entity_id=str(step.id),
            status_field="status",
            from_status=StepStatus.IN_REVIEW.value,
            to_status=StepStatus.REJECTED.value,
            reason="reject_step",
            metadata={"workflow_id": str(step.workflow_id), "user_id": str(user_id)},
        )
        await capture_lifecycle_event(
            self.db,
            entity_type="approval_step",
            entity_id=str(step.id),
            action="update",
            after_payload=self._step_payload(step),
            metadata={"updated_fields": ["status", "approved_by_id", "decision_at"]},
        )

        # Mark workflow as rejected
        workflow = await self.get_workflow(step.workflow_id)
        if workflow:
            previous_status = workflow.status
            workflow.status = WorkflowStatus.REJECTED
            workflow.completed_at = utcnow()
            self.db.add(workflow)
            await capture_status_transition(
                self.db,
                entity_type="approval_workflow",
                entity_id=str(workflow.id),
                status_field="status",
                from_status=str(self._enum_value(previous_status)),
                to_status=WorkflowStatus.REJECTED.value,
                reason="reject_step",
                metadata={"step_id": str(step.id), "user_id": str(user_id)},
            )
            await capture_lifecycle_event(
                self.db,
                entity_type="approval_workflow",
                entity_id=str(workflow.id),
                action="update",
                after_payload=self._workflow_payload(workflow),
                metadata={"updated_fields": ["status", "completed_at"]},
            )

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
                    previous_status = step.status
                    step.status = StepStatus.IN_REVIEW
                    self.db.add(step)
                    await capture_status_transition(
                        self.db,
                        entity_type="approval_step",
                        entity_id=str(step.id),
                        status_field="status",
                        from_status=str(self._enum_value(previous_status)),
                        to_status=StepStatus.IN_REVIEW.value,
                        reason="advance_workflow",
                        metadata={"workflow_id": str(workflow_id)},
                    )
                    next_step_found = True
                    all_steps_approved = False
                else:
                    all_steps_approved = False
            elif step.status in [StepStatus.IN_REVIEW, StepStatus.REJECTED]:
                all_steps_approved = False
                next_step_found = True  # Current active step

        if all_steps_approved:
            previous_status = workflow.status
            workflow.status = WorkflowStatus.APPROVED
            workflow.completed_at = utcnow()
            self.db.add(workflow)
            await capture_status_transition(
                self.db,
                entity_type="approval_workflow",
                entity_id=str(workflow.id),
                status_field="status",
                from_status=str(self._enum_value(previous_status)),
                to_status=WorkflowStatus.APPROVED.value,
                reason="advance_workflow_complete",
            )
            await capture_lifecycle_event(
                self.db,
                entity_type="approval_workflow",
                entity_id=str(workflow.id),
                action="update",
                after_payload=self._workflow_payload(workflow),
                metadata={"updated_fields": ["status", "completed_at"]},
            )
