from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel
from app.models.workflow import WorkflowStatus, StepStatus


class ApprovalStepBase(BaseModel):
    name: str
    order: int
    approver_role: str  # e.g. "architect", "engineer"


class ApprovalStepRead(ApprovalStepBase):
    id: UUID
    status: StepStatus
    approved_by_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    comments: Optional[str] = None

    class Config:
        from_attributes = True


class ApprovalStepUpdate(BaseModel):
    approved: bool
    comments: Optional[str] = None


class ApprovalWorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    workflow_type: str


class ApprovalWorkflowCreate(ApprovalWorkflowBase):
    steps: List[ApprovalStepBase]


class ApprovalWorkflowRead(ApprovalWorkflowBase):
    id: UUID
    project_id: UUID
    status: WorkflowStatus
    current_step_order: int
    created_at: datetime
    updated_at: datetime
    steps: List[ApprovalStepRead]

    class Config:
        from_attributes = True
