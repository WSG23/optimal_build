from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api import deps
from app.models.workflow import WorkflowStatus
from app.schemas.workflow import (
    ApprovalStepUpdate,
    ApprovalWorkflowCreate,
    ApprovalWorkflowRead,
)
from app.services.team.workflow_service import WorkflowService

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.get("/", response_model=list[ApprovalWorkflowRead])
async def list_workflows(
    project_id: UUID,
    status: WorkflowStatus | None = None,
    db=Depends(deps.get_db),
    identity: deps.RequestIdentity = Depends(deps.require_viewer),
) -> Any:
    """
    List workflows for a project (including steps).
    """
    service = WorkflowService(db)
    workflows = await service.list_workflows(project_id=project_id, status=status)
    return workflows


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
    if not identity.user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    service = WorkflowService(db)
    steps_data = [
        {
            "name": step.name,
            "required_role": step.required_role,
            "required_user_id": step.required_user_id,
        }
        for step in workflow_in.steps
    ]
    workflow = await service.create_workflow(
        project_id=project_id,
        title=workflow_in.title,
        workflow_type=workflow_in.workflow_type,
        created_by_id=UUID(identity.user_id),
        steps_data=steps_data,
        description=workflow_in.description,
    )
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
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id)
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
    if not identity.user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    service = WorkflowService(db)
    try:
        step = await service.decide_step(
            step_id=step_id,
            user_id=UUID(identity.user_id),
            approved=approval_in.approved,
            comments=approval_in.comments,
        )
        # Return the updated workflow
        workflow = await service.get_workflow(step.workflow_id)
        if not workflow:
            raise HTTPException(status_code=400, detail="Unable to approve step")
        return workflow
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
