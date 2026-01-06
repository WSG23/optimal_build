from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api import deps
from app.schemas.workflow import (
    ApprovalStepUpdate,
    ApprovalWorkflowCreate,
    ApprovalWorkflowRead,
)
from app.services.team.workflow_service import WorkflowService

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.post("/", response_model=ApprovalWorkflowRead)
async def create_workflow(
    project_id: UUID,
    workflow_in: ApprovalWorkflowCreate,
    db=Depends(deps.get_db),
    identity: deps.RequestIdentity = Depends(deps.require_reviewer),
) -> ApprovalWorkflowRead:
    """
    Create a new approval workflow (e.g. for a design phase).
    """
    service = WorkflowService(db)
    steps_data = [
        {"name": step.name, "required_role": step.approver_role}
        for step in workflow_in.steps
    ]
    workflow = await service.create_workflow(
        project_id=project_id,
        title=workflow_in.name,
        workflow_type=workflow_in.workflow_type,
        created_by_id=UUID(identity.user_id),
        steps_data=steps_data,
        description=workflow_in.description,
    )
    # Reload workflow with steps eagerly loaded
    workflow = await service.get_workflow(workflow.id)
    return ApprovalWorkflowRead.from_orm_workflow(workflow)


@router.get("/{workflow_id}", response_model=ApprovalWorkflowRead)
async def get_workflow(
    workflow_id: UUID,
    db=Depends(deps.get_db),
    identity: deps.RequestIdentity = Depends(deps.require_viewer),
) -> ApprovalWorkflowRead:
    """
    Get workflow details including steps and status.
    """
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return ApprovalWorkflowRead.from_orm_workflow(workflow)


@router.post("/steps/{step_id}/approve", response_model=ApprovalWorkflowRead)
async def approve_step(
    step_id: UUID,
    approval_in: ApprovalStepUpdate,
    db=Depends(deps.get_db),
    identity: deps.RequestIdentity = Depends(deps.get_identity),
) -> ApprovalWorkflowRead:
    """
    Approve (or reject) a specific step in the workflow.
    Validates if the current user has the required role.
    """
    service = WorkflowService(db)
    try:
        step = await service.approve_step(
            step_id=step_id,
            user_id=UUID(identity.user_id),
            comments=approval_in.comments,
        )
        # Return the updated workflow
        workflow = await service.get_workflow(step.workflow_id)
        if not workflow:
            raise HTTPException(status_code=400, detail="Unable to approve step")
        return ApprovalWorkflowRead.from_orm_workflow(workflow)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
