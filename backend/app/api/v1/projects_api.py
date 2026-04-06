"""Projects API with CRUD operations using PostgreSQL."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api import deps
from app.core.database import get_session
from app.models.projects import Project, ProjectPhase, ProjectType
from app.schemas._typing import dump_model

if TYPE_CHECKING:
    from app.models.development_phase import PhaseStatus

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

    model_config = ConfigDict(from_attributes=True)


class ProgressProject(BaseModel):
    id: str
    name: str
    current_phase: Optional[str] = None


class ProgressPhase(BaseModel):
    id: str
    name: str
    progress: float
    status: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    source: str


class PendingApprovalItem(BaseModel):
    id: str
    title: str
    workflow_name: str
    required_by: str
    status: str


class TeamActivityItem(BaseModel):
    id: str
    name: str
    email: str
    role: str
    last_active_at: Optional[str]
    pending_tasks: int
    completed_tasks: int


class WorkflowSummary(BaseModel):
    total_steps: int
    approved_steps: int
    pending_steps: int


class ProjectProgressResponse(BaseModel):
    project: ProgressProject
    phases: List[ProgressPhase]
    workflow_summary: WorkflowSummary
    pending_approvals: List[PendingApprovalItem]
    team_activity: List[TeamActivityItem]


class DashboardKPI(BaseModel):
    label: str
    value: str
    raw_value: float | None = None
    sub_value: Optional[str] = None
    trend: dict[str, str] | None = None
    trend_direction: Optional[str] = None  # up, down, neutral


class DashboardModule(BaseModel):
    key: str
    label: str
    path: str
    enabled: bool
    description: Optional[str] = None


class ProjectDashboardResponse(BaseModel):
    project_id: str
    project_name: str
    status: str
    kpis: List[DashboardKPI]
    modules: List[DashboardModule]


def _format_currency(value: float | int | None) -> str:
    """Format large currency values for dashboard display."""

    if value is None:
        return "—"

    numeric = float(value)
    sign = "-" if numeric < 0 else ""
    absolute = abs(numeric)
    for divisor, suffix in (
        (1_000_000_000, "B"),
        (1_000_000, "M"),
        (1_000, "K"),
    ):
        if absolute >= divisor:
            formatted = f"{absolute / divisor:.1f}".rstrip("0").rstrip(".")
            return f"{sign}${formatted}{suffix}"

    if absolute.is_integer():
        return f"{sign}${absolute:,.0f}"
    formatted = f"{absolute:.2f}".rstrip("0").rstrip(".")
    return f"{sign}${formatted}"


def _format_area(value: float | int | None) -> str:
    """Format square metre values for dashboard display."""

    if value is None:
        return "—"
    numeric = float(value)
    if numeric.is_integer():
        return f"{numeric:,.0f} m²"
    formatted = f"{numeric:,.1f}".rstrip("0").rstrip(".")
    return f"{formatted} m²"


def _format_percentage(value: float | int | None) -> str:
    """Format percentage values for dashboard display."""

    if value is None:
        return "—"
    numeric = float(value)
    return f"{numeric:.1f}".rstrip("0").rstrip(".") + "%"


def _kpi(label: str, raw_value: float | int | None, formatter: Any) -> DashboardKPI:
    if raw_value is None:
        return DashboardKPI(label=label, value="—", raw_value=None)
    numeric = float(raw_value)
    return DashboardKPI(label=label, value=formatter(numeric), raw_value=numeric)


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


def _phase_display_name(phase: ProjectPhase) -> str:
    return str(phase.value).replace("_", " ").title()


def _phase_status_from_development(status: PhaseStatus | None) -> str:
    if status is None:
        return "not_started"
    normalized = str(getattr(status, "value", status)).lower()
    mapping = {
        "not_started": "not_started",
        "planning": "not_started",
        "in_progress": "in_progress",
        "on_hold": "delayed",
        "delayed": "delayed",
        "completed": "completed",
        "cancelled": "delayed",
    }
    return mapping.get(normalized, "not_started")


def _workflow_step_status(status: str | None) -> str:
    if not status:
        return "pending"
    return status.lower()


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
    update_data = dump_model(project_update, exclude_unset=True)

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


@router.get("/{project_id}/progress", response_model=ProjectProgressResponse)
async def get_project_progress(
    project_id: str,
    db: AsyncSession = Depends(get_session),
    identity: deps.RequestIdentity = Depends(deps.require_viewer),
) -> ProjectProgressResponse:
    """Get progress details for a project."""
    from app.api.v1.finance_common import normalise_project_id
    from app.models.development_phase import DevelopmentPhase
    from app.models.workflow import ApprovalStep, ApprovalWorkflow
    from app.services.team.team_service import TeamService

    project_uuid = normalise_project_id(project_id)
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

    phases_result = await db.execute(
        select(DevelopmentPhase)
        .where(DevelopmentPhase.project_id == project_uuid)
        .order_by(DevelopmentPhase.planned_start_date.asc().nulls_last())
    )
    development_phases = list(phases_result.scalars().all())

    phases: list[ProgressPhase] = []
    if development_phases:
        for phase in development_phases:
            progress_value = (
                float(phase.completion_percentage)
                if phase.completion_percentage is not None
                else 0.0
            )
            phases.append(
                ProgressPhase(
                    id=str(phase.id),
                    name=phase.phase_name,
                    progress=progress_value,
                    status=_phase_status_from_development(phase.status),
                    start_date=(
                        phase.planned_start_date.isoformat()
                        if phase.planned_start_date
                        else None
                    ),
                    end_date=(
                        phase.planned_end_date.isoformat()
                        if phase.planned_end_date
                        else None
                    ),
                    source="development_phase",
                )
            )
    else:
        phase_order = [
            ProjectPhase.CONCEPT,
            ProjectPhase.FEASIBILITY,
            ProjectPhase.DESIGN,
            ProjectPhase.APPROVAL,
            ProjectPhase.TENDER,
            ProjectPhase.CONSTRUCTION,
            ProjectPhase.TESTING_COMMISSIONING,
            ProjectPhase.HANDOVER,
            ProjectPhase.OPERATION,
        ]
        current_phase = project.current_phase or ProjectPhase.CONCEPT
        try:
            current_index = phase_order.index(current_phase)
        except ValueError:
            current_index = 0
        for idx, phase in enumerate(phase_order):
            if idx < current_index:
                status_label = "completed"
                progress_value = 100.0
            elif idx == current_index:
                status_label = "in_progress"
                progress_value = 50.0
            else:
                status_label = "not_started"
                progress_value = 0.0
            phases.append(
                ProgressPhase(
                    id=phase.value,
                    name=_phase_display_name(phase),
                    progress=progress_value,
                    status=status_label,
                    source="project_phase",
                )
            )

    workflow_result = await db.execute(
        select(ApprovalWorkflow)
        .where(ApprovalWorkflow.project_id == project_uuid)
        .options(
            selectinload(ApprovalWorkflow.steps).selectinload(
                ApprovalStep.required_user
            )
        )
    )
    workflows = list(workflow_result.scalars().unique().all())
    total_steps = 0
    approved_steps = 0
    pending_steps = 0
    pending_approvals: list[PendingApprovalItem] = []

    for workflow in workflows:
        for step in workflow.steps:
            total_steps += 1
            status_value = _workflow_step_status(step.status)
            if status_value == "approved":
                approved_steps += 1
            if status_value in ("pending", "in_review"):
                pending_steps += 1
                required_by = "Any team member"
                if step.required_user and step.required_user.full_name:
                    required_by = step.required_user.full_name
                elif step.required_role:
                    required_by = step.required_role
                pending_approvals.append(
                    PendingApprovalItem(
                        id=str(step.id),
                        title=step.name,
                        workflow_name=workflow.title,
                        required_by=required_by,
                        status=status_value,
                    )
                )

    workflow_summary = WorkflowSummary(
        total_steps=total_steps,
        approved_steps=approved_steps,
        pending_steps=pending_steps,
    )

    team_service = TeamService(db)
    activity_stats = await team_service.get_team_activity(project_uuid)
    team_activity: list[TeamActivityItem] = []
    for member in activity_stats.get("members", []):
        last_active = member.get("last_active_at")
        team_activity.append(
            TeamActivityItem(
                id=str(member.get("id")),
                name=str(member.get("name") or ""),
                email=str(member.get("email") or ""),
                role=str(member.get("role") or ""),
                last_active_at=(
                    last_active.isoformat()
                    if hasattr(last_active, "isoformat")
                    else None
                ),
                pending_tasks=int(member.get("pending_tasks") or 0),
                completed_tasks=int(member.get("completed_tasks") or 0),
            )
        )

    return ProjectProgressResponse(
        project=ProgressProject(
            id=str(project.id),
            name=project.project_name,
            current_phase=(
                project.current_phase.value if project.current_phase else None
            ),
        ),
        phases=phases,
        workflow_summary=workflow_summary,
        pending_approvals=pending_approvals,
        team_activity=team_activity,
    )


@router.get("/{project_id}/dashboard", response_model=ProjectDashboardResponse)
async def get_project_dashboard(
    project_id: str,
    db: AsyncSession = Depends(get_session),
    identity: deps.RequestIdentity = Depends(deps.require_viewer),
) -> ProjectDashboardResponse:
    """Get dashboard data including KPIs and available modules."""
    from app.api.v1.finance_common import normalise_project_id
    from app.models.finance import FinProject, FinScenario

    try:
        project_uuid = normalise_project_id(project_id)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid project ID format. Expected UUID.",
            ) from exc
        raise

    # Fetch Project with Financial Data
    stmt = select(Project).where(
        Project.id == project_uuid, Project.is_active.is_(True)
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Fetch Primary Financial Scenario
    fin_stmt = (
        select(FinScenario)
        .join(FinProject, FinScenario.fin_project_id == FinProject.id)
        .where(
            FinProject.project_id == project_uuid,
            FinScenario.is_primary.is_(True),
        )
        .options(selectinload(FinScenario.results))
    )
    fin_result = await db.execute(fin_stmt)
    primary_scenario = fin_result.scalars().first()

    results = list(primary_scenario.results) if primary_scenario else []

    def _result_value(*names: str) -> float | None:
        lowered = {name.lower() for name in names}
        for result_entry in results:
            result_name = (result_entry.name or "").lower()
            if result_name in lowered or any(name in result_name for name in lowered):
                if result_entry.value is None:
                    return None
                return float(result_entry.value)
        return None

    projected_revenue = _result_value("projected_revenue", "total_revenue", "revenue")
    irr_value = _result_value("irr")

    kpis: List[DashboardKPI] = [
        _kpi("Total GFA", project.proposed_gfa_sqm, _format_area),
        _kpi("Development Cost", project.estimated_cost_sgd, _format_currency),
        _kpi("Projected Revenue", projected_revenue, _format_currency),
        _kpi("IRR", irr_value, _format_percentage),
    ]

    # Modules
    base_path = f"/projects/{project_id}"
    modules = [
        DashboardModule(
            key="capture",
            label="Capture Results",
            path=f"{base_path}/capture",
            enabled=True,
            description="Site analysis and capture data",
        ),
        DashboardModule(
            key="feasibility",
            label="Feasibility",
            path=f"{base_path}/feasibility",
            enabled=True,
            description="Financial modeling and feasibility",
        ),
        DashboardModule(
            key="finance",
            label="Finance",
            path=f"{base_path}/finance",
            enabled=True,
            description="Detailed financial control",
        ),
        DashboardModule(
            key="phases",
            label="Phase Management",
            path=f"{base_path}/phases",
            enabled=True,
            description="Manage project phases",
        ),
        DashboardModule(
            key="team",
            label="Team",
            path=f"{base_path}/team",
            enabled=True,
            description="Team members and roles",
        ),
        DashboardModule(
            key="regulatory",
            label="Regulatory",
            path=f"{base_path}/regulatory",
            enabled=True,
            description="Regulatory submissions and approvals",
        ),
    ]

    return ProjectDashboardResponse(
        project_id=str(project.id),
        project_name=project.project_name,
        status=project.current_phase.value if project.current_phase else "planning",
        kpis=kpis,
        modules=modules,
    )
