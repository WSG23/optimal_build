"""Development phase management service.

Phase 2D: Multi-Phase Development Management
- Gantt chart timeline generation
- Critical path analysis
- Heritage preservation tracking
- Tenant coordination workflows
- Mixed-use orchestration
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import structlog

from app.models.development_phase import (
    DependencyType,
    DevelopmentPhase,
    HeritageClassification,
    MilestoneType,
    PhaseMilestone,
    PhaseStatus,
    PhaseType,
    TenantRelocation,
)

logger = structlog.get_logger()


@dataclass
class GanttTask:
    """A task in the Gantt chart representation."""

    id: int
    code: str
    name: str
    phase_type: str
    start_date: date
    end_date: date
    duration_days: int
    completion_pct: float
    status: str
    is_critical: bool
    is_milestone: bool
    dependencies: List[int]  # List of predecessor task IDs
    heritage_classification: Optional[str] = None
    occupancy_status: Optional[str] = None
    color: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class GanttChart:
    """Complete Gantt chart data for a project."""

    project_id: int
    project_name: str
    tasks: List[GanttTask]
    milestones: List[Dict[str, Any]]
    critical_path: List[int]  # Task IDs on critical path
    project_start: date
    project_end: date
    total_duration_days: int
    completion_pct: float
    phases_summary: Dict[str, int]  # Phase type counts
    warnings: List[str]


@dataclass
class CriticalPathResult:
    """Result of critical path analysis."""

    critical_path: List[int]  # Phase IDs in critical path order
    total_duration_days: int
    earliest_start: Dict[int, date]  # Phase ID -> earliest start date
    earliest_finish: Dict[int, date]
    latest_start: Dict[int, date]
    latest_finish: Dict[int, date]
    float_days: Dict[int, int]  # Phase ID -> total float


@dataclass
class HeritageTracker:
    """Heritage preservation tracking summary."""

    project_id: int
    total_heritage_phases: int
    classifications: Dict[str, int]  # Classification -> count
    phases: List[Dict[str, Any]]
    pending_approvals: List[Dict[str, Any]]
    approved_conditions: List[str]
    risk_items: List[str]


@dataclass
class TenantCoordinationSummary:
    """Tenant coordination summary for occupied renovations."""

    project_id: int
    total_tenants: int
    relocation_required: int
    relocated: int
    returned: int
    pending_notification: int
    agreements_signed: int
    total_relocation_cost: Decimal
    tenants: List[Dict[str, Any]]
    timeline: List[Dict[str, Any]]
    warnings: List[str]


class PhaseManagerService:
    """Service for managing multi-phase development projects."""

    # Color coding for phase types in Gantt charts
    PHASE_COLORS = {
        PhaseType.DEMOLITION: "#e74c3c",  # Red
        PhaseType.SITE_PREPARATION: "#f39c12",  # Orange
        PhaseType.FOUNDATION: "#8b4513",  # Brown
        PhaseType.STRUCTURE: "#3498db",  # Blue
        PhaseType.ENVELOPE: "#9b59b6",  # Purple
        PhaseType.MEP_ROUGH_IN: "#1abc9c",  # Teal
        PhaseType.INTERIOR_FIT_OUT: "#2ecc71",  # Green
        PhaseType.FACADE: "#e67e22",  # Dark Orange
        PhaseType.LANDSCAPING: "#27ae60",  # Dark Green
        PhaseType.COMMISSIONING: "#16a085",  # Dark Teal
        PhaseType.HANDOVER: "#2c3e50",  # Dark Blue
        # Heritage
        PhaseType.HERITAGE_ASSESSMENT: "#c0392b",  # Dark Red
        PhaseType.HERITAGE_RESTORATION: "#d35400",  # Pumpkin
        PhaseType.HERITAGE_INTEGRATION: "#a04000",  # Rust
        # Renovation
        PhaseType.TENANT_RELOCATION: "#7f8c8d",  # Gray
        PhaseType.SOFT_STRIP: "#95a5a6",  # Light Gray
        PhaseType.REFURBISHMENT: "#34495e",  # Dark Gray
        PhaseType.TENANT_FIT_OUT: "#5dade2",  # Light Blue
        # Mixed-use
        PhaseType.RETAIL_PODIUM: "#f1c40f",  # Yellow
        PhaseType.OFFICE_FLOORS: "#3498db",  # Blue
        PhaseType.RESIDENTIAL_TOWER: "#9b59b6",  # Purple
        PhaseType.AMENITY_LEVEL: "#1abc9c",  # Teal
    }

    def generate_gantt_chart(
        self,
        project_id: int,
        project_name: str,
        phases: List[DevelopmentPhase],
        milestones: Optional[List[PhaseMilestone]] = None,
    ) -> GanttChart:
        """Generate Gantt chart data from development phases."""
        logger.info("gantt.generate", project_id=project_id, phase_count=len(phases))

        if not phases:
            return GanttChart(
                project_id=project_id,
                project_name=project_name,
                tasks=[],
                milestones=[],
                critical_path=[],
                project_start=date.today(),
                project_end=date.today(),
                total_duration_days=0,
                completion_pct=0.0,
                phases_summary={},
                warnings=["No phases defined"],
            )

        # Build dependency map
        dependency_map: Dict[int, List[int]] = {}
        for phase in phases:
            predecessor_ids = []
            if phase.dependencies:
                for dep in phase.dependencies:
                    predecessor_ids.append(dep.predecessor_phase_id)
            dependency_map[phase.id] = predecessor_ids

        # Convert phases to Gantt tasks
        tasks: List[GanttTask] = []
        phases_summary: Dict[str, int] = {}

        for phase in phases:
            phase_type_value = phase.phase_type.value if phase.phase_type else "unknown"
            phases_summary[phase_type_value] = (
                phases_summary.get(phase_type_value, 0) + 1
            )

            start = phase.actual_start_date or phase.planned_start_date or date.today()
            end = (
                phase.actual_end_date
                or phase.planned_end_date
                or start + timedelta(days=30)
            )
            duration = (end - start).days

            tasks.append(
                GanttTask(
                    id=phase.id,
                    code=phase.phase_code,
                    name=phase.phase_name,
                    phase_type=phase_type_value,
                    start_date=start,
                    end_date=end,
                    duration_days=duration,
                    completion_pct=float(phase.completion_percentage or 0),
                    status=(
                        phase.status.value
                        if phase.status
                        else PhaseStatus.NOT_STARTED.value
                    ),
                    is_critical=phase.is_critical_path or False,
                    is_milestone=False,
                    dependencies=dependency_map.get(phase.id, []),
                    heritage_classification=(
                        phase.heritage_classification.value
                        if phase.heritage_classification
                        else None
                    ),
                    occupancy_status=(
                        phase.occupancy_status.value if phase.occupancy_status else None
                    ),
                    color=self.PHASE_COLORS.get(phase.phase_type, "#95a5a6"),
                    notes=phase.notes,
                )
            )

        # Add milestones
        milestone_data: List[Dict[str, Any]] = []
        if milestones:
            for ms in milestones:
                milestone_data.append(
                    {
                        "id": ms.id,
                        "phase_id": ms.phase_id,
                        "name": ms.milestone_name,
                        "type": ms.milestone_type.value if ms.milestone_type else None,
                        "planned_date": (
                            ms.planned_date.isoformat() if ms.planned_date else None
                        ),
                        "actual_date": (
                            ms.actual_date.isoformat() if ms.actual_date else None
                        ),
                        "is_achieved": ms.is_achieved,
                        "is_overdue": ms.is_overdue,
                        "requires_approval": ms.requires_approval,
                        "approval_status": ms.approval_status,
                    }
                )

        # Calculate project dates
        project_start = min(t.start_date for t in tasks)
        project_end = max(t.end_date for t in tasks)
        total_duration = (project_end - project_start).days

        # Calculate overall completion
        total_weighted_completion = sum(
            t.completion_pct * t.duration_days for t in tasks
        )
        total_duration_sum = sum(t.duration_days for t in tasks)
        overall_completion = (
            total_weighted_completion / total_duration_sum
            if total_duration_sum > 0
            else 0.0
        )

        # Identify critical path
        critical_path = [t.id for t in tasks if t.is_critical]

        # Generate warnings
        warnings: List[str] = []
        for task in tasks:
            if task.status == PhaseStatus.DELAYED.value:
                warnings.append(f"Phase '{task.code}' is delayed")
            if (
                task.heritage_classification
                and task.heritage_classification != HeritageClassification.NONE.value
            ):
                if not any(
                    ms.get("type") == MilestoneType.HERITAGE_CLEARANCE.value
                    for ms in milestone_data
                ):
                    warnings.append(
                        f"Heritage phase '{task.code}' missing heritage clearance milestone"
                    )

        return GanttChart(
            project_id=project_id,
            project_name=project_name,
            tasks=tasks,
            milestones=milestone_data,
            critical_path=critical_path,
            project_start=project_start,
            project_end=project_end,
            total_duration_days=total_duration,
            completion_pct=overall_completion,
            phases_summary=phases_summary,
            warnings=warnings,
        )

    def calculate_critical_path(
        self,
        phases: List[DevelopmentPhase],
        project_start: date,
    ) -> CriticalPathResult:
        """Calculate critical path using forward and backward pass."""
        logger.info("critical_path.calculate", phase_count=len(phases))

        if not phases:
            return CriticalPathResult(
                critical_path=[],
                total_duration_days=0,
                earliest_start={},
                earliest_finish={},
                latest_start={},
                latest_finish={},
                float_days={},
            )

        # Build phase lookup and dependency graph
        phase_map = {p.id: p for p in phases}
        predecessors: Dict[int, List[Tuple[int, DependencyType, int]]] = (
            {}
        )  # successor -> [(pred, type, lag)]
        successors: Dict[int, List[int]] = {}  # predecessor -> [successors]

        for phase in phases:
            predecessors[phase.id] = []
            successors[phase.id] = []

        for phase in phases:
            if phase.dependencies:
                for dep in phase.dependencies:
                    pred_id = dep.predecessor_phase_id
                    lag = dep.lag_days or 0
                    dep_type = dep.dependency_type or DependencyType.FINISH_TO_START
                    predecessors[phase.id].append((pred_id, dep_type, lag))
                    if pred_id in successors:
                        successors[pred_id].append(phase.id)

        # Forward pass: calculate earliest start/finish
        earliest_start: Dict[int, date] = {}
        earliest_finish: Dict[int, date] = {}

        # Topological sort for forward pass
        processed = set()
        sorted_phases: List[int] = []

        def visit(phase_id: int) -> None:
            if phase_id in processed:
                return
            processed.add(phase_id)
            for pred_id, _, _ in predecessors.get(phase_id, []):
                if pred_id in phase_map:
                    visit(pred_id)
            sorted_phases.append(phase_id)

        for phase in phases:
            visit(phase.id)

        # Forward pass
        for phase_id in sorted_phases:
            phase = phase_map[phase_id]
            duration = phase.duration_days or 30

            if not predecessors[phase_id]:
                earliest_start[phase_id] = project_start
            else:
                max_start = project_start
                for pred_id, dep_type, lag in predecessors[phase_id]:
                    if pred_id not in earliest_finish:
                        continue
                    pred_phase = phase_map.get(pred_id)
                    if not pred_phase:
                        continue

                    if dep_type == DependencyType.FINISH_TO_START:
                        start = earliest_finish[pred_id] + timedelta(days=lag)
                    elif dep_type == DependencyType.START_TO_START:
                        start = earliest_start[pred_id] + timedelta(days=lag)
                    else:
                        start = earliest_finish[pred_id] + timedelta(days=lag)

                    if start > max_start:
                        max_start = start

                earliest_start[phase_id] = max_start

            earliest_finish[phase_id] = earliest_start[phase_id] + timedelta(
                days=duration
            )

        # Backward pass: calculate latest start/finish
        project_end = (
            max(earliest_finish.values()) if earliest_finish else project_start
        )
        latest_start: Dict[int, date] = {}
        latest_finish: Dict[int, date] = {}

        # Initialize end phases
        for phase_id in reversed(sorted_phases):
            if not successors[phase_id]:
                latest_finish[phase_id] = project_end

        # Backward pass
        for phase_id in reversed(sorted_phases):
            phase = phase_map[phase_id]
            duration = phase.duration_days or 30

            if phase_id not in latest_finish:
                min_finish = project_end
                for succ_id in successors[phase_id]:
                    if succ_id in latest_start:
                        if latest_start[succ_id] < min_finish:
                            min_finish = latest_start[succ_id]
                latest_finish[phase_id] = min_finish

            latest_start[phase_id] = latest_finish[phase_id] - timedelta(days=duration)

        # Calculate float
        float_days: Dict[int, int] = {}
        for phase_id in sorted_phases:
            es = earliest_start.get(phase_id, project_start)
            ls = latest_start.get(phase_id, project_start)
            float_days[phase_id] = (ls - es).days

        # Critical path: phases with zero float
        critical_path = [pid for pid in sorted_phases if float_days.get(pid, 0) == 0]

        total_duration = (project_end - project_start).days

        return CriticalPathResult(
            critical_path=critical_path,
            total_duration_days=total_duration,
            earliest_start=earliest_start,
            earliest_finish=earliest_finish,
            latest_start=latest_start,
            latest_finish=latest_finish,
            float_days=float_days,
        )

    def track_heritage_preservation(
        self,
        project_id: int,
        phases: List[DevelopmentPhase],
        milestones: Optional[List[PhaseMilestone]] = None,
    ) -> HeritageTracker:
        """Track heritage preservation requirements across phases."""
        logger.info("heritage.track", project_id=project_id)

        heritage_phases = [
            p
            for p in phases
            if p.heritage_classification
            and p.heritage_classification != HeritageClassification.NONE
        ]

        classifications: Dict[str, int] = {}
        phase_details: List[Dict[str, Any]] = []
        pending_approvals: List[Dict[str, Any]] = []
        approved_conditions: List[str] = []
        risk_items: List[str] = []

        for phase in heritage_phases:
            classification = phase.heritage_classification.value
            classifications[classification] = classifications.get(classification, 0) + 1

            phase_details.append(
                {
                    "id": phase.id,
                    "code": phase.phase_code,
                    "name": phase.phase_name,
                    "classification": classification,
                    "constraints": phase.heritage_constraints or [],
                    "approval_required": phase.heritage_approval_required,
                    "approval_date": (
                        phase.heritage_approval_date.isoformat()
                        if phase.heritage_approval_date
                        else None
                    ),
                    "conditions": phase.heritage_conditions,
                    "status": phase.status.value if phase.status else None,
                }
            )

            if phase.heritage_approval_required and not phase.heritage_approval_date:
                pending_approvals.append(
                    {
                        "phase_id": phase.id,
                        "phase_code": phase.phase_code,
                        "classification": classification,
                    }
                )

            if phase.heritage_conditions:
                approved_conditions.append(
                    f"[{phase.phase_code}] {phase.heritage_conditions}"
                )

            # Identify risks
            if (
                phase.status == PhaseStatus.IN_PROGRESS
                and not phase.heritage_approval_date
            ):
                risk_items.append(
                    f"Phase '{phase.phase_code}' in progress without heritage approval"
                )

        # Check milestones for heritage clearance
        if milestones:
            for ms in milestones:
                if ms.milestone_type == MilestoneType.HERITAGE_CLEARANCE:
                    if ms.is_overdue and not ms.is_achieved:
                        risk_items.append(
                            f"Heritage clearance milestone '{ms.milestone_name}' is overdue"
                        )

        return HeritageTracker(
            project_id=project_id,
            total_heritage_phases=len(heritage_phases),
            classifications=classifications,
            phases=phase_details,
            pending_approvals=pending_approvals,
            approved_conditions=approved_conditions,
            risk_items=risk_items,
        )

    def coordinate_tenant_relocation(
        self,
        project_id: int,
        relocations: List[TenantRelocation],
        phases: Optional[List[DevelopmentPhase]] = None,
    ) -> TenantCoordinationSummary:
        """Coordinate tenant relocations for occupied building renovations."""
        logger.info(
            "tenant.coordinate", project_id=project_id, tenant_count=len(relocations)
        )

        tenant_details: List[Dict[str, Any]] = []
        timeline: List[Dict[str, Any]] = []
        warnings: List[str] = []

        relocation_required = 0
        relocated = 0
        returned = 0
        pending_notification = 0
        agreements_signed = 0
        total_cost = Decimal("0")

        for rel in relocations:
            if rel.relocation_required:
                relocation_required += 1

            if rel.status == "relocated":
                relocated += 1
            elif rel.status == "returned":
                returned += 1
            elif rel.status == "planned" and not rel.notification_date:
                pending_notification += 1

            if rel.agreement_signed:
                agreements_signed += 1

            if rel.relocation_allowance:
                total_cost += rel.relocation_allowance
            if rel.fit_out_contribution:
                total_cost += rel.fit_out_contribution

            tenant_details.append(
                {
                    "id": rel.id,
                    "name": rel.tenant_name,
                    "current_unit": rel.current_unit,
                    "leased_area_sqm": (
                        float(rel.leased_area_sqm) if rel.leased_area_sqm else None
                    ),
                    "lease_expiry": (
                        rel.lease_expiry_date.isoformat()
                        if rel.lease_expiry_date
                        else None
                    ),
                    "status": rel.status,
                    "temporary_location": rel.temporary_location,
                    "relocation_start": (
                        rel.relocation_start_date.isoformat()
                        if rel.relocation_start_date
                        else None
                    ),
                    "relocation_end": (
                        rel.relocation_end_date.isoformat()
                        if rel.relocation_end_date
                        else None
                    ),
                    "return_unit": rel.return_unit,
                    "agreement_signed": rel.agreement_signed,
                    "contact_name": rel.contact_name,
                }
            )

            # Build timeline events
            if rel.relocation_start_date:
                timeline.append(
                    {
                        "date": rel.relocation_start_date.isoformat(),
                        "event": "relocation_start",
                        "tenant": rel.tenant_name,
                        "details": f"Relocate to {rel.temporary_location}",
                    }
                )
            if rel.relocation_end_date:
                timeline.append(
                    {
                        "date": rel.relocation_end_date.isoformat(),
                        "event": "relocation_end",
                        "tenant": rel.tenant_name,
                        "details": f"Return to {rel.return_unit or rel.current_unit}",
                    }
                )

            # Warnings
            if rel.relocation_required and not rel.agreement_signed:
                if rel.relocation_start_date:
                    days_until = (rel.relocation_start_date - date.today()).days
                    if days_until < 30:
                        warnings.append(
                            f"Tenant '{rel.tenant_name}' relocation in {days_until} days but agreement not signed"
                        )

            if rel.lease_expiry_date and rel.relocation_end_date:
                if rel.relocation_end_date > rel.lease_expiry_date:
                    warnings.append(
                        f"Tenant '{rel.tenant_name}' relocation extends beyond lease expiry"
                    )

        # Sort timeline by date
        timeline.sort(key=lambda x: x["date"])

        return TenantCoordinationSummary(
            project_id=project_id,
            total_tenants=len(relocations),
            relocation_required=relocation_required,
            relocated=relocated,
            returned=returned,
            pending_notification=pending_notification,
            agreements_signed=agreements_signed,
            total_relocation_cost=total_cost,
            tenants=tenant_details,
            timeline=timeline,
            warnings=warnings,
        )

    def validate_phase_sequence(
        self,
        phases: List[DevelopmentPhase],
    ) -> Tuple[bool, List[str]]:
        """Validate that phase dependencies form a valid sequence."""
        errors: List[str] = []

        phase_ids = {p.id for p in phases}

        for phase in phases:
            if phase.dependencies:
                for dep in phase.dependencies:
                    if dep.predecessor_phase_id not in phase_ids:
                        errors.append(
                            f"Phase '{phase.phase_code}' depends on non-existent phase ID {dep.predecessor_phase_id}"
                        )

        # Check for circular dependencies
        visited = set()
        rec_stack = set()

        def has_cycle(phase_id: int, pred_map: Dict[int, List[int]]) -> bool:
            visited.add(phase_id)
            rec_stack.add(phase_id)

            for pred_id in pred_map.get(phase_id, []):
                if pred_id not in visited:
                    if has_cycle(pred_id, pred_map):
                        return True
                elif pred_id in rec_stack:
                    return True

            rec_stack.remove(phase_id)
            return False

        pred_map: Dict[int, List[int]] = {}
        for phase in phases:
            if phase.dependencies:
                pred_map[phase.id] = [
                    d.predecessor_phase_id for d in phase.dependencies
                ]
            else:
                pred_map[phase.id] = []

        for phase in phases:
            if phase.id not in visited:
                if has_cycle(phase.id, pred_map):
                    errors.append("Circular dependency detected in phase sequence")
                    break

        return len(errors) == 0, errors


# Singleton instance
_phase_manager: Optional[PhaseManagerService] = None


def get_phase_manager_service() -> PhaseManagerService:
    """Get the phase manager service singleton."""
    global _phase_manager
    if _phase_manager is None:
        _phase_manager = PhaseManagerService()
    return _phase_manager


__all__ = [
    "PhaseManagerService",
    "GanttChart",
    "GanttTask",
    "CriticalPathResult",
    "HeritageTracker",
    "TenantCoordinationSummary",
    "get_phase_manager_service",
]
