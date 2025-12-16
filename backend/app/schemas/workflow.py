"""Pydantic schemas for Phase 2E approval workflows."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.workflow import StepStatus, WorkflowStatus


class ApprovalStepCreate(BaseModel):
    """Create a workflow step."""

    name: str
    required_role: str | None = None
    required_user_id: UUID | None = None


class ApprovalStepRead(BaseModel):
    """Read a workflow step."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workflow_id: UUID
    name: str
    sequence_order: int
    required_role: str | None = None
    required_user_id: UUID | None = None
    status: StepStatus
    approved_by_id: UUID | None = None
    decision_at: datetime | None = None
    comments: str | None = None


class ApprovalStepUpdate(BaseModel):
    approved: bool
    comments: str | None = None


class ApprovalWorkflowCreate(BaseModel):
    title: str
    description: str | None = None
    workflow_type: str
    steps: list[ApprovalStepCreate] = Field(default_factory=list)


class ApprovalWorkflowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    title: str
    description: str | None = None
    workflow_type: str
    status: WorkflowStatus
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    steps: list[ApprovalStepRead]
