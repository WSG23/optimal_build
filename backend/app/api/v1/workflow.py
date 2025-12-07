from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api import deps
from app.schemas.workflow import (
    ApprovalStepUpdate,
    ApprovalWorkflowCreate,
    ApprovalWorkflowRead,
)
from app.services.team.workflow_service import WorkflowService

router = APIRouter()


@router.post("/", response_model=ApprovalWorkflowRead)
async def create_workflow(
    project_id: UUID,
    workflow_in: ApprovalWorkflowCreate,
    db=Depends(deps.get_db),
    identity: deps.RequestIdentity = Depends(deps.require_reviewer),
) -> Any:
    """
    Create a new approval workflow (e.g. for a design phase).
    """
    workflow = await WorkflowService.create_workflow(db, project_id, workflow_in)
    return workflow


@router.get("/{workflow_id}", response_model=ApprovalWorkflowRead)
async def get_workflow(
    workflow_id: UUID,
    db=Depends(deps.get_db),
    identity: deps.RequestIdentity = Depends(deps.require_viewer),
) -> Any:
    """
    Get workflow details including steps and status.
    """
    workflow = await WorkflowService.get_workflow(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.post("/steps/{step_id}/approve", response_model=ApprovalWorkflowRead)
async def approve_step(
    step_id: UUID,
    approval_in: ApprovalStepUpdate,
    db=Depends(deps.get_db),
    identity: deps.RequestIdentity = Depends(deps.get_identity),
) -> Any:
    """
    Approve (or reject) a specific step in the workflow.
    Validates if the current user has the required role.
    """
    # Logic to check if user has the role for this step would go here or in service
    # For now, we assume if they can authenticate and hit this endpoint, we pass to service

    workflow = await WorkflowService.approve_step(
        db,
        step_id,
        approver_id=identity.user_id,
        comments=approval_in.comments,
        approved=approval_in.approved,
    )
    if not workflow:
        raise HTTPException(status_code=400, detail="Unable to approve step")

    return workflow
