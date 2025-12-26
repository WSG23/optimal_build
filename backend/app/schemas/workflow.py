from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, computed_field
from app.models.workflow import WorkflowStatus, StepStatus


class ApprovalStepBase(BaseModel):
    name: str
    order: int = Field(default=0, alias="sequence_order")
    approver_role: str = Field(default="", alias="required_role")

    model_config = {"populate_by_name": True}


class ApprovalStepRead(BaseModel):
    id: UUID
    name: str
    status: StepStatus
    approved_by_id: Optional[UUID] = None
    approved_at: Optional[datetime] = Field(
        default=None, validation_alias="decision_at"
    )
    comments: Optional[str] = None
    # Map from model fields
    order: int = Field(default=0, validation_alias="sequence_order")
    approver_role: Optional[str] = Field(default=None, validation_alias="required_role")

    model_config = {"from_attributes": True}


class ApprovalStepUpdate(BaseModel):
    approved: bool
    comments: Optional[str] = None


class ApprovalWorkflowBase(BaseModel):
    name: str = Field(validation_alias="title")
    description: Optional[str] = None
    workflow_type: str

    model_config = {"from_attributes": True}


class ApprovalWorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    workflow_type: str
    steps: List[ApprovalStepBase]


class ApprovalWorkflowRead(BaseModel):
    id: UUID
    project_id: UUID
    name: str = Field(validation_alias="title")
    description: Optional[str] = None
    workflow_type: str
    status: WorkflowStatus
    created_at: datetime
    updated_at: datetime
    steps: List[ApprovalStepRead]

    @computed_field
    @property
    def current_step_order(self) -> int:
        """Compute the current step order from the steps list."""
        for step in self.steps:
            if step.status in (StepStatus.PENDING, StepStatus.IN_REVIEW):
                return step.order
        return len(self.steps)

    model_config = {"from_attributes": True}
