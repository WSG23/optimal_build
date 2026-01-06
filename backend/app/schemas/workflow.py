from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.workflow import StepStatus, WorkflowStatus


class ApprovalStepBase(BaseModel):
    name: str
    order: int
    approver_role: str  # e.g. "architect", "engineer"


class ApprovalStepRead(BaseModel):
    """Response model for approval step - maps from ORM ApprovalStep model."""

    id: UUID
    name: str
    order: int  # Aliased from sequence_order
    status: StepStatus
    approver_role: Optional[str] = None  # Aliased from required_role
    approved_by_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None  # Aliased from decision_at
    comments: Optional[str] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_step(cls, step) -> "ApprovalStepRead":
        """Create from ORM ApprovalStep model."""
        approver_role = None
        if step.required_role:
            approver_role = (
                step.required_role.value
                if hasattr(step.required_role, "value")
                else step.required_role
            )
        return cls(
            id=step.id,
            name=step.name,
            order=step.sequence_order,
            status=step.status,
            approver_role=approver_role,
            approved_by_id=step.approved_by_id,
            approved_at=step.decision_at,
            comments=step.comments,
        )


class ApprovalStepUpdate(BaseModel):
    approved: bool
    comments: Optional[str] = None


class ApprovalWorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    workflow_type: str


class ApprovalWorkflowCreate(ApprovalWorkflowBase):
    steps: List[ApprovalStepBase]


class ApprovalWorkflowRead(BaseModel):
    """Response model for workflow - maps from ORM ApprovalWorkflow model."""

    id: UUID
    project_id: UUID
    name: str  # Aliased from title
    description: Optional[str] = None
    workflow_type: str
    status: WorkflowStatus
    current_step_order: int
    created_at: datetime
    updated_at: datetime
    steps: List[ApprovalStepRead]

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_workflow(cls, workflow) -> "ApprovalWorkflowRead":
        """Create from ORM ApprovalWorkflow model."""
        # Calculate current_step_order from steps
        current_step_order = 0
        if workflow.steps:
            for step in workflow.steps:
                if step.status.value in ("pending", "in_review"):
                    current_step_order = step.sequence_order
                    break
            else:
                # All steps done - use last step order
                current_step_order = max(s.sequence_order for s in workflow.steps)

        return cls(
            id=workflow.id,
            project_id=workflow.project_id,
            name=workflow.title,
            description=workflow.description,
            workflow_type=workflow.workflow_type,
            status=workflow.status,
            current_step_order=current_step_order,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at,
            steps=[ApprovalStepRead.from_orm_step(s) for s in workflow.steps],
        )
