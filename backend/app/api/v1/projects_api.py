"""Projects API with CRUD operations using PostgreSQL."""

import uuid
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.database import get_session
from app.models.projects import Project, ProjectPhase, ProjectType

router = APIRouter(prefix="/projects", tags=["Projects"])


# Pydantic models
class ProjectCreate(BaseModel):
    """Project creation model."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    location: Optional[str] = Field(None, max_length=200)
    project_type: str = Field(default="new_development")
    status: str = Field(default="planning")
    budget: Optional[float] = Field(None, gt=0)


class ProjectUpdate(BaseModel):
    """Project update model."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    location: Optional[str] = Field(None, max_length=200)
    project_type: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = Field(None, gt=0)


class ProjectResponse(BaseModel):
    """Project response model."""

    id: str
    name: str
    description: Optional[str]
    location: Optional[str]
    project_type: Optional[str]
    status: str
    budget: Optional[float]
    owner_email: Optional[str]
    created_at: str
    updated_at: str
    is_active: bool

    model_config = {"from_attributes": True}


def _project_to_response(project: Project) -> ProjectResponse:
    """Convert Project model to response."""
    return ProjectResponse(
        id=str(project.id),
        name=project.project_name,
        description=project.description,
        location=None,  # Location stored in related properties
        project_type=project.project_type.value if project.project_type else None,
        status=project.current_phase.value if project.current_phase else "planning",
        budget=(
            float(project.estimated_cost_sgd) if project.estimated_cost_sgd else None
        ),
        owner_email=project.owner_email,
        created_at=project.created_at.isoformat() if project.created_at else "",
        updated_at=project.updated_at.isoformat() if project.updated_at else "",
        is_active=project.is_active if project.is_active is not None else True,
    )


def _generate_project_code() -> str:
    """Generate a unique project code."""
    return f"PROJ-{uuid.uuid4().hex[:8].upper()}"


@router.post(
    "/create", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED
)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_session),
    identity: deps.RequestIdentity = Depends(deps.require_reviewer),
) -> ProjectResponse:
    """Create a new project for the authenticated user."""
    # Map project_type string to enum
    try:
        project_type_enum = ProjectType(project_data.project_type)
    except ValueError:
        project_type_enum = ProjectType.NEW_DEVELOPMENT

    # Map status to phase enum
    status_to_phase = {
        "planning": ProjectPhase.CONCEPT,
        "approval": ProjectPhase.APPROVAL,
        "construction": ProjectPhase.CONSTRUCTION,
        "completed": ProjectPhase.OPERATION,
    }
    phase = status_to_phase.get(project_data.status, ProjectPhase.CONCEPT)

    # Create new project
    db_project = Project(
        id=uuid.uuid4(),
        project_name=project_data.name,
        project_code=_generate_project_code(),
        description=project_data.description,
        project_type=project_type_enum,
        current_phase=phase,
        estimated_cost_sgd=project_data.budget,
        owner_email=identity.email,
        is_active=True,
    )

    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)

    return _project_to_response(db_project)


@router.get("/list", response_model=List[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_session),
    identity: deps.RequestIdentity = Depends(deps.require_viewer),
    skip: int = 0,
    limit: int = 100,
) -> List[ProjectResponse]:
    """List all active projects (filtered by user access in future)."""
    result = await db.execute(
        select(Project)
        .where(Project.is_active == True)  # noqa: E712
        .offset(skip)
        .limit(limit)
        .order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()

    return [_project_to_response(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_session),
    identity: deps.RequestIdentity = Depends(deps.require_viewer),
) -> ProjectResponse:
    """Get a specific project by ID."""
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project ID format. Expected UUID.",
        ) from e

    result = await db.execute(
        select(Project).where(
            Project.id == project_uuid,
            Project.is_active == True,  # noqa: E712
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    return _project_to_response(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    db: AsyncSession = Depends(get_session),
    identity: deps.RequestIdentity = Depends(deps.require_reviewer),
) -> ProjectResponse:
    """Update a project (must have reviewer role)."""
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project ID format. Expected UUID.",
        ) from e

    result = await db.execute(
        select(Project).where(
            Project.id == project_uuid,
            Project.is_active == True,  # noqa: E712
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Update fields
    update_data = project_update.model_dump(exclude_unset=True)

    if "name" in update_data:
        project.project_name = update_data["name"]
    if "description" in update_data:
        project.description = update_data["description"]
    if "project_type" in update_data and update_data["project_type"]:
        try:
            project.project_type = ProjectType(update_data["project_type"])
        except ValueError:
            pass  # Keep existing type if invalid
    if "status" in update_data:
        status_to_phase = {
            "planning": ProjectPhase.CONCEPT,
            "approval": ProjectPhase.APPROVAL,
            "construction": ProjectPhase.CONSTRUCTION,
            "completed": ProjectPhase.OPERATION,
        }
        if update_data["status"] in status_to_phase:
            project.current_phase = status_to_phase[update_data["status"]]
    if "budget" in update_data:
        project.estimated_cost_sgd = update_data["budget"]

    await db.commit()
    await db.refresh(project)

    return _project_to_response(project)


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_session),
    identity: deps.RequestIdentity = Depends(deps.require_reviewer),
) -> dict[str, str]:
    """Soft delete a project (marks as inactive) - must have reviewer role."""
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project ID format. Expected UUID.",
        ) from e

    result = await db.execute(
        select(Project).where(
            Project.id == project_uuid,
            Project.is_active == True,  # noqa: E712
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    project.is_active = False
    await db.commit()

    return {"message": "Project deleted successfully", "project_id": project_id}


@router.get("/stats/summary")
async def get_project_stats(
    db: AsyncSession = Depends(get_session),
    identity: deps.RequestIdentity = Depends(deps.require_viewer),
) -> dict[str, Any]:
    """Get project statistics."""
    result = await db.execute(select(Project).where(Project.is_active.is_(True)))
    projects = result.scalars().all()

    total_budget = sum(
        float(p.estimated_cost_sgd) for p in projects if p.estimated_cost_sgd
    )

    phase_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}

    for project in projects:
        phase = project.current_phase.value if project.current_phase else "concept"
        phase_counts[phase] = phase_counts.get(phase, 0) + 1

        if project.project_type:
            ptype = project.project_type.value
            type_counts[ptype] = type_counts.get(ptype, 0) + 1

    # Count active projects (not in operation/completed phase)
    active_phases = {
        "concept",
        "feasibility",
        "design",
        "approval",
        "tender",
        "construction",
    }
    active_count = sum(
        1
        for p in projects
        if p.current_phase and p.current_phase.value in active_phases
    )

    completed_count = sum(
        1 for p in projects if p.current_phase and p.current_phase.value == "operation"
    )

    return {
        "total_projects": len(projects),
        "total_budget": total_budget,
        "active_projects": active_count,
        "completed_projects": completed_count,
        "status_breakdown": phase_counts,
        "type_breakdown": type_counts,
        "recent_projects": [
            {
                "id": str(p.id),
                "name": p.project_name,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in sorted(
                projects,
                key=lambda x: x.created_at if x.created_at else "",
                reverse=True,
            )[:5]
        ],
    }
