"""Development phases API for multi-phase project management.

Phase 2D: Multi-Phase Development Management
- Gantt chart generation
- Critical path analysis
- Heritage preservation tracking
- Tenant coordination workflows
"""

from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.development_phase import (
    DevelopmentPhase,
    PhaseMilestone,
    TenantRelocation,
)
from app.models.projects import Project
from app.services.development.phase_manager import (
    get_phase_manager_service,
)
from app.core.database import get_session

router = APIRouter(prefix="/projects", tags=["Development Phases"])


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------


class GanttTaskResponse(BaseModel):
    """A task in the Gantt chart."""

    id: int
    code: str
    name: str
    phase_type: str
    start_date: str
    end_date: str
    duration: int
    progress: float
    status: str
    is_critical: bool
    is_milestone: bool
    dependencies: List[int]
    is_heritage: bool = False
    has_tenant_coordination: bool = False
    color: Optional[str] = None
    notes: Optional[str] = None
    budget_amount: Optional[float] = None
    actual_cost_amount: Optional[float] = None


class GanttMilestoneResponse(BaseModel):
    """A milestone in the Gantt chart."""

    id: int
    phase_id: int
    name: str
    type: Optional[str] = None
    planned_date: Optional[str] = None
    actual_date: Optional[str] = None
    is_achieved: bool = False
    is_overdue: bool = False
    requires_approval: bool = False
    approval_status: Optional[str] = None


class GanttChartResponse(BaseModel):
    """Complete Gantt chart data."""

    project_id: int
    project_name: str
    generated_at: str
    tasks: List[GanttTaskResponse]
    milestones: List[GanttMilestoneResponse] = []
    critical_path: List[int] = []
    project_start_date: Optional[str] = None
    project_end_date: Optional[str] = None
    total_duration: int = 0
    critical_path_duration: int = 0
    completion_pct: float = 0.0
    phases_summary: Dict[str, int] = {}
    warnings: List[str] = []


class CriticalPhaseResponse(BaseModel):
    """A phase on the critical path."""

    phase_id: int
    name: str
    early_start: int
    early_finish: int
    late_start: int
    late_finish: int
    float: int


class NonCriticalPhaseResponse(BaseModel):
    """A phase not on the critical path."""

    phase_id: int
    name: str
    float: int


class CriticalPathResponse(BaseModel):
    """Critical path analysis result."""

    project_id: int
    critical_path: List[int]
    total_duration: int
    critical_phases: List[CriticalPhaseResponse] = []
    non_critical_phases: List[NonCriticalPhaseResponse] = []


class HeritagePhaseResponse(BaseModel):
    """A heritage-classified phase."""

    phase_id: int
    code: str
    name: str
    heritage_classification: str
    approval_required: bool = False
    approval_status: Optional[str] = None
    special_considerations: List[str] = []


class HeritageTrackerResponse(BaseModel):
    """Heritage preservation tracking summary."""

    project_id: int
    heritage_classification: str = "none"
    overall_approval_status: str = "not_required"
    total_heritage_phases: int = 0
    classifications: Dict[str, int] = {}
    phases: List[HeritagePhaseResponse] = []
    required_approvals: List[str] = []
    pending_approvals: List[Dict[str, Any]] = []
    preservation_risks: List[str] = []
    recommendations: List[str] = []


class TenantRelocationResponse(BaseModel):
    """Tenant relocation details."""

    id: int
    phase_id: int
    tenant_name: str
    current_unit: str
    relocation_type: str = ""
    status: str
    notification_date: Optional[str] = None
    planned_move_date: Optional[str] = None
    actual_move_date: Optional[str] = None
    temporary_location: Optional[str] = None
    compensation_amount: Optional[float] = None
    notes: Optional[str] = None


class TimelineEventResponse(BaseModel):
    """A timeline event for tenant coordination."""

    date: str
    event: str
    tenant_name: str
    status: str = ""
    details: Optional[str] = None


class TenantCoordinationResponse(BaseModel):
    """Tenant coordination summary."""

    project_id: int
    total_tenants: int = 0
    relocation_required: int = 0
    relocated: int = 0
    returned: int = 0
    pending_notification: int = 0
    agreements_signed: int = 0
    total_relocation_cost: float = 0.0
    status_breakdown: Dict[str, int] = {}
    relocations: List[TenantRelocationResponse] = []
    upcoming_moves: List[TenantRelocationResponse] = []
    overdue_notifications: List[TenantRelocationResponse] = []
    timeline: List[TimelineEventResponse] = []
    warnings: List[str] = []


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


async def get_project_or_404(db: AsyncSession, project_id: int) -> Project:
    """Get a project by ID or raise 404."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


async def get_project_phases(
    db: AsyncSession, project_id: int
) -> List[DevelopmentPhase]:
    """Get all phases for a project with dependencies loaded."""
    result = await db.execute(
        select(DevelopmentPhase)
        .where(DevelopmentPhase.project_id == project_id)
        .options(selectinload(DevelopmentPhase.dependencies))
        .order_by(DevelopmentPhase.sequence_order)
    )
    return list(result.scalars().all())


async def get_project_milestones(
    db: AsyncSession, project_id: int
) -> List[PhaseMilestone]:
    """Get all milestones for phases in a project."""
    # Get phase IDs for the project
    phase_result = await db.execute(
        select(DevelopmentPhase.id).where(DevelopmentPhase.project_id == project_id)
    )
    phase_ids = [row[0] for row in phase_result.fetchall()]

    if not phase_ids:
        return []

    result = await db.execute(
        select(PhaseMilestone).where(PhaseMilestone.phase_id.in_(phase_ids))
    )
    return list(result.scalars().all())


async def get_project_tenant_relocations(
    db: AsyncSession, project_id: int
) -> List[TenantRelocation]:
    """Get all tenant relocations for phases in a project."""
    # Get phase IDs for the project
    phase_result = await db.execute(
        select(DevelopmentPhase.id).where(DevelopmentPhase.project_id == project_id)
    )
    phase_ids = [row[0] for row in phase_result.fetchall()]

    if not phase_ids:
        return []

    result = await db.execute(
        select(TenantRelocation).where(TenantRelocation.phase_id.in_(phase_ids))
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------


@router.get("/{project_id}/gantt", response_model=GanttChartResponse)
async def get_gantt_chart(
    project_id: int,
    db: AsyncSession = Depends(get_session),
) -> GanttChartResponse:
    """Generate Gantt chart data for a project.

    Returns a complete Gantt chart with:
    - All development phases as tasks
    - Critical path highlighting
    - Milestone markers
    - Heritage and tenant coordination indicators

    Args:
        project_id: The project ID to generate the Gantt chart for.
        db: Database session.

    Returns:
        GanttChartResponse with tasks, milestones, and metadata.

    Raises:
        HTTPException 404: If project not found.
    """
    project = await get_project_or_404(db, project_id)
    phases = await get_project_phases(db, project_id)
    milestones = await get_project_milestones(db, project_id)

    service = get_phase_manager_service()
    gantt = service.generate_gantt_chart(
        project_id=project_id,
        project_name=project.name,
        phases=phases,
        milestones=milestones if milestones else None,
    )

    # Convert dataclass to response model
    from datetime import datetime

    tasks = [
        GanttTaskResponse(
            id=t.id,
            code=t.code,
            name=t.name,
            phase_type=t.phase_type,
            start_date=(
                t.start_date.isoformat()
                if isinstance(t.start_date, date)
                else str(t.start_date)
            ),
            end_date=(
                t.end_date.isoformat()
                if isinstance(t.end_date, date)
                else str(t.end_date)
            ),
            duration=t.duration_days,
            progress=t.completion_pct,
            status=t.status,
            is_critical=t.is_critical,
            is_milestone=t.is_milestone,
            dependencies=t.dependencies,
            is_heritage=t.heritage_classification is not None
            and t.heritage_classification != "none",
            has_tenant_coordination=t.occupancy_status is not None
            and t.occupancy_status not in ("vacant", None),
            color=t.color,
            notes=t.notes,
        )
        for t in gantt.tasks
    ]

    milestone_responses = [
        GanttMilestoneResponse(
            id=m.get("id", 0),
            phase_id=m.get("phase_id", 0),
            name=m.get("name", ""),
            type=m.get("type"),
            planned_date=m.get("planned_date"),
            actual_date=m.get("actual_date"),
            is_achieved=m.get("is_achieved", False),
            is_overdue=m.get("is_overdue", False),
            requires_approval=m.get("requires_approval", False),
            approval_status=m.get("approval_status"),
        )
        for m in gantt.milestones
    ]

    # Calculate critical path duration
    critical_duration = sum(t.duration for t in tasks if t.id in gantt.critical_path)

    return GanttChartResponse(
        project_id=gantt.project_id,
        project_name=gantt.project_name,
        generated_at=datetime.now().isoformat(),
        tasks=tasks,
        milestones=milestone_responses,
        critical_path=gantt.critical_path,
        project_start_date=(
            gantt.project_start.isoformat() if gantt.project_start else None
        ),
        project_end_date=gantt.project_end.isoformat() if gantt.project_end else None,
        total_duration=gantt.total_duration_days,
        critical_path_duration=critical_duration,
        completion_pct=gantt.completion_pct,
        phases_summary=gantt.phases_summary,
        warnings=gantt.warnings,
    )


@router.get("/{project_id}/critical-path", response_model=CriticalPathResponse)
async def get_critical_path(
    project_id: int,
    db: AsyncSession = Depends(get_session),
) -> CriticalPathResponse:
    """Calculate critical path for a project.

    Performs forward and backward pass analysis to determine:
    - Critical path (sequence of tasks with zero float)
    - Early/late start and finish dates for each phase
    - Total float for each phase

    Args:
        project_id: The project ID to analyze.
        db: Database session.

    Returns:
        CriticalPathResponse with critical and non-critical phases.

    Raises:
        HTTPException 404: If project not found.
    """
    await get_project_or_404(db, project_id)
    phases = await get_project_phases(db, project_id)

    service = get_phase_manager_service()

    # Determine project start date
    project_start = date.today()
    if phases:
        starts = [
            p.planned_start_date or p.actual_start_date
            for p in phases
            if p.planned_start_date or p.actual_start_date
        ]
        if starts:
            project_start = min(starts)

    result = service.calculate_critical_path(phases, project_start)

    # Build phase lookup for names
    phase_map = {p.id: p for p in phases}

    # Convert to response format
    critical_phases = []
    non_critical_phases = []

    for phase_id in result.critical_path:
        phase = phase_map.get(phase_id)
        if phase:
            es = result.earliest_start.get(phase_id, project_start)
            ef = result.earliest_finish.get(phase_id, project_start)
            ls = result.latest_start.get(phase_id, project_start)
            lf = result.latest_finish.get(phase_id, project_start)
            float_days = result.float_days.get(phase_id, 0)

            critical_phases.append(
                CriticalPhaseResponse(
                    phase_id=phase_id,
                    name=phase.phase_name,
                    early_start=(es - project_start).days,
                    early_finish=(ef - project_start).days,
                    late_start=(ls - project_start).days,
                    late_finish=(lf - project_start).days,
                    float=float_days,
                )
            )

    for phase in phases:
        if phase.id not in result.critical_path:
            float_days = result.float_days.get(phase.id, 0)
            non_critical_phases.append(
                NonCriticalPhaseResponse(
                    phase_id=phase.id,
                    name=phase.phase_name,
                    float=float_days,
                )
            )

    return CriticalPathResponse(
        project_id=project_id,
        critical_path=result.critical_path,
        total_duration=result.total_duration_days,
        critical_phases=critical_phases,
        non_critical_phases=non_critical_phases,
    )


@router.get("/{project_id}/heritage", response_model=HeritageTrackerResponse)
async def get_heritage_tracker(
    project_id: int,
    db: AsyncSession = Depends(get_session),
) -> HeritageTrackerResponse:
    """Get heritage preservation tracking for a project.

    Returns heritage classification details, approval status,
    and preservation risks for heritage-classified phases.

    Args:
        project_id: The project ID to track heritage for.
        db: Database session.

    Returns:
        HeritageTrackerResponse with heritage phase details.

    Raises:
        HTTPException 404: If project not found.
    """
    await get_project_or_404(db, project_id)
    phases = await get_project_phases(db, project_id)
    milestones = await get_project_milestones(db, project_id)

    service = get_phase_manager_service()
    tracker = service.track_heritage_preservation(
        project_id=project_id,
        phases=phases,
        milestones=milestones if milestones else None,
    )

    # Convert to response format
    heritage_phases = [
        HeritagePhaseResponse(
            phase_id=p.get("id", 0),
            code=p.get("code", ""),
            name=p.get("name", ""),
            heritage_classification=p.get("classification", "none"),
            approval_required=p.get("approval_required", False),
            approval_status=p.get("approval_date") if p.get("approval_date") else None,
            special_considerations=p.get("constraints", []),
        )
        for p in tracker.phases
    ]

    # Determine overall classification (highest level)
    overall_classification = "none"
    classification_priority = [
        "world_heritage",
        "nationally_listed",
        "locally_listed",
        "interior_protected",
        "facade_only",
        "conservation_area",
        "none",
    ]
    for cls in classification_priority:
        if tracker.classifications.get(cls, 0) > 0:
            overall_classification = cls
            break

    # Determine overall approval status
    overall_status = "not_required"
    if tracker.pending_approvals:
        overall_status = "pending"
    elif tracker.total_heritage_phases > 0 and not tracker.pending_approvals:
        overall_status = "approved"

    return HeritageTrackerResponse(
        project_id=tracker.project_id,
        heritage_classification=overall_classification,
        overall_approval_status=overall_status,
        total_heritage_phases=tracker.total_heritage_phases,
        classifications=tracker.classifications,
        phases=heritage_phases,
        required_approvals=[
            f"Heritage approval for {a.get('phase_code', 'unknown')}"
            for a in tracker.pending_approvals
        ],
        pending_approvals=tracker.pending_approvals,
        preservation_risks=tracker.risk_items,
        recommendations=tracker.approved_conditions,
    )


@router.get(
    "/{project_id}/tenant-coordination", response_model=TenantCoordinationResponse
)
async def get_tenant_coordination(
    project_id: int,
    db: AsyncSession = Depends(get_session),
) -> TenantCoordinationResponse:
    """Get tenant coordination summary for a project.

    Returns tenant relocation status, timeline, and warnings
    for occupied building renovations.

    Args:
        project_id: The project ID to get tenant coordination for.
        db: Database session.

    Returns:
        TenantCoordinationResponse with tenant details and timeline.

    Raises:
        HTTPException 404: If project not found.
    """
    await get_project_or_404(db, project_id)
    phases = await get_project_phases(db, project_id)
    relocations = await get_project_tenant_relocations(db, project_id)

    service = get_phase_manager_service()
    summary = service.coordinate_tenant_relocation(
        project_id=project_id,
        relocations=relocations,
        phases=phases if phases else None,
    )

    # Convert to response format
    all_relocations = [
        TenantRelocationResponse(
            id=t.get("id", 0),
            phase_id=0,  # Not directly available in tenant dict
            tenant_name=t.get("name", ""),
            current_unit=t.get("current_unit", ""),
            relocation_type="temporary" if t.get("temporary_location") else "permanent",
            status=t.get("status", ""),
            notification_date=None,  # Not in current dict structure
            planned_move_date=t.get("relocation_start"),
            actual_move_date=(
                t.get("relocation_start") if t.get("status") == "relocated" else None
            ),
            temporary_location=t.get("temporary_location"),
            compensation_amount=None,  # Not directly available
            notes=None,
        )
        for t in summary.tenants
    ]

    # Filter for upcoming moves (planned but not yet moved)
    upcoming = [
        r for r in all_relocations if r.status == "planned" and r.planned_move_date
    ]

    # Filter for overdue notifications
    overdue = [
        r for r in all_relocations if r.status == "planned" and not r.notification_date
    ]

    # Build status breakdown
    status_breakdown: Dict[str, int] = {}
    for t in summary.tenants:
        status = t.get("status", "unknown")
        status_breakdown[status] = status_breakdown.get(status, 0) + 1

    timeline_events = [
        TimelineEventResponse(
            date=e.get("date", ""),
            event=e.get("event", ""),
            tenant_name=e.get("tenant", ""),
            status="",
            details=e.get("details"),
        )
        for e in summary.timeline
    ]

    return TenantCoordinationResponse(
        project_id=summary.project_id,
        total_tenants=summary.total_tenants,
        relocation_required=summary.relocation_required,
        relocated=summary.relocated,
        returned=summary.returned,
        pending_notification=summary.pending_notification,
        agreements_signed=summary.agreements_signed,
        total_relocation_cost=float(summary.total_relocation_cost),
        status_breakdown=status_breakdown,
        relocations=all_relocations,
        upcoming_moves=upcoming,
        overdue_notifications=overdue,
        timeline=timeline_events,
        warnings=summary.warnings,
    )
