"""Comprehensive tests for development_phases API.

Tests cover:
- GanttTaskResponse model
- GanttMilestoneResponse model
- GanttChartResponse model
- CriticalPhaseResponse model
- NonCriticalPhaseResponse model
- CriticalPathResponse model
- HeritagePhaseResponse model
- HeritageTrackerResponse model
- TenantRelocationResponse model
- TimelineEventResponse model
- TenantCoordinationResponse model
"""

from __future__ import annotations

from typing import List

import pytest

from app.api.v1.development_phases import (
    GanttTaskResponse,
    GanttMilestoneResponse,
    GanttChartResponse,
    CriticalPhaseResponse,
    NonCriticalPhaseResponse,
    CriticalPathResponse,
    HeritagePhaseResponse,
    HeritageTrackerResponse,
    TenantRelocationResponse,
    TimelineEventResponse,
    TenantCoordinationResponse,
)

# Mark all tests in this module as not requiring database
pytestmark = pytest.mark.no_db


class TestGanttTaskResponse:
    """Tests for GanttTaskResponse model."""

    def test_required_fields(self) -> None:
        """Test required fields."""
        task = GanttTaskResponse(
            id=1,
            code="PH-001",
            name="Site Preparation",
            phase_type="construction",
            start_date="2024-01-01",
            end_date="2024-03-01",
            duration=60,
            progress=0.5,
            status="in_progress",
            is_critical=True,
            is_milestone=False,
            dependencies=[],
        )
        assert task.id == 1
        assert task.code == "PH-001"
        assert task.is_critical is True

    def test_with_dependencies(self) -> None:
        """Test task with dependencies."""
        task = GanttTaskResponse(
            id=2,
            code="PH-002",
            name="Foundation Work",
            phase_type="construction",
            start_date="2024-03-01",
            end_date="2024-05-01",
            duration=61,
            progress=0.0,
            status="pending",
            is_critical=True,
            is_milestone=False,
            dependencies=[1],
        )
        assert task.dependencies == [1]

    def test_heritage_task(self) -> None:
        """Test heritage-related task."""
        task = GanttTaskResponse(
            id=3,
            code="HE-001",
            name="Heritage Restoration",
            phase_type="restoration",
            start_date="2024-04-01",
            end_date="2024-08-01",
            duration=122,
            progress=0.25,
            status="in_progress",
            is_critical=False,
            is_milestone=False,
            dependencies=[],
            is_heritage=True,
            color="#D4A574",
            notes="Listed building restoration",
        )
        assert task.is_heritage is True
        assert task.color == "#D4A574"

    def test_tenant_coordination_task(self) -> None:
        """Test tenant coordination task."""
        task = GanttTaskResponse(
            id=4,
            code="TC-001",
            name="Tenant Relocation",
            phase_type="coordination",
            start_date="2024-02-01",
            end_date="2024-02-28",
            duration=27,
            progress=0.75,
            status="in_progress",
            is_critical=False,
            is_milestone=False,
            dependencies=[],
            has_tenant_coordination=True,
        )
        assert task.has_tenant_coordination is True

    def test_with_budget(self) -> None:
        """Test task with budget information."""
        task = GanttTaskResponse(
            id=5,
            code="PH-003",
            name="Structural Work",
            phase_type="construction",
            start_date="2024-05-01",
            end_date="2024-08-01",
            duration=92,
            progress=0.0,
            status="pending",
            is_critical=True,
            is_milestone=False,
            dependencies=[2],
            budget_amount=5000000.0,
            actual_cost_amount=0.0,
        )
        assert task.budget_amount == 5000000.0


class TestGanttMilestoneResponse:
    """Tests for GanttMilestoneResponse model."""

    def test_basic_milestone(self) -> None:
        """Test basic milestone."""
        milestone = GanttMilestoneResponse(
            id=1,
            phase_id=2,
            name="Foundation Complete",
        )
        assert milestone.id == 1
        assert milestone.name == "Foundation Complete"

    def test_achieved_milestone(self) -> None:
        """Test achieved milestone."""
        milestone = GanttMilestoneResponse(
            id=2,
            phase_id=3,
            name="TOP Achieved",
            type="regulatory",
            planned_date="2024-12-01",
            actual_date="2024-11-28",
            is_achieved=True,
            is_overdue=False,
        )
        assert milestone.is_achieved is True
        assert milestone.actual_date == "2024-11-28"

    def test_overdue_milestone(self) -> None:
        """Test overdue milestone."""
        milestone = GanttMilestoneResponse(
            id=3,
            phase_id=4,
            name="Permit Approval",
            type="approval",
            planned_date="2024-06-01",
            is_achieved=False,
            is_overdue=True,
            requires_approval=True,
            approval_status="pending",
        )
        assert milestone.is_overdue is True
        assert milestone.requires_approval is True


class TestGanttChartResponse:
    """Tests for GanttChartResponse model."""

    def test_empty_chart(self) -> None:
        """Test empty chart."""
        chart = GanttChartResponse(
            project_id=1,
            project_name="Test Project",
            generated_at="2024-01-01T00:00:00Z",
            tasks=[],
        )
        assert chart.project_id == 1
        assert chart.tasks == []

    def test_full_chart(self) -> None:
        """Test full chart with all data."""
        task = GanttTaskResponse(
            id=1,
            code="PH-001",
            name="Site Prep",
            phase_type="construction",
            start_date="2024-01-01",
            end_date="2024-02-01",
            duration=31,
            progress=1.0,
            status="completed",
            is_critical=True,
            is_milestone=False,
            dependencies=[],
        )
        milestone = GanttMilestoneResponse(
            id=1,
            phase_id=1,
            name="Site Ready",
            is_achieved=True,
        )
        chart = GanttChartResponse(
            project_id=1,
            project_name="Tower Development",
            generated_at="2024-03-01T10:00:00Z",
            tasks=[task],
            milestones=[milestone],
            critical_path=[1],
            project_start_date="2024-01-01",
            project_end_date="2024-12-31",
            total_duration=365,
            critical_path_duration=180,
            completion_pct=25.0,
            phases_summary={"construction": 3, "fit_out": 2},
            warnings=["Permit approval pending"],
        )
        assert chart.total_duration == 365
        assert chart.completion_pct == 25.0
        assert len(chart.warnings) == 1


class TestCriticalPhaseResponse:
    """Tests for CriticalPhaseResponse model."""

    def test_critical_phase(self) -> None:
        """Test critical phase data."""
        phase = CriticalPhaseResponse(
            phase_id=1,
            name="Foundation Work",
            early_start=0,
            early_finish=60,
            late_start=0,
            late_finish=60,
            float=0,
        )
        assert phase.float == 0
        assert phase.early_finish == 60


class TestNonCriticalPhaseResponse:
    """Tests for NonCriticalPhaseResponse model."""

    def test_non_critical_phase(self) -> None:
        """Test non-critical phase with float."""
        phase = NonCriticalPhaseResponse(
            phase_id=5,
            name="Landscaping",
            float=30,
        )
        assert phase.float == 30
        assert phase.name == "Landscaping"


class TestCriticalPathResponse:
    """Tests for CriticalPathResponse model."""

    def test_critical_path(self) -> None:
        """Test critical path analysis."""
        critical = CriticalPhaseResponse(
            phase_id=1,
            name="Structure",
            early_start=0,
            early_finish=90,
            late_start=0,
            late_finish=90,
            float=0,
        )
        non_critical = NonCriticalPhaseResponse(
            phase_id=2,
            name="Interior",
            float=15,
        )
        response = CriticalPathResponse(
            project_id=1,
            critical_path=[1, 3, 4],
            total_duration=180,
            critical_phases=[critical],
            non_critical_phases=[non_critical],
        )
        assert response.total_duration == 180
        assert len(response.critical_path) == 3


class TestHeritagePhaseResponse:
    """Tests for HeritagePhaseResponse model."""

    def test_heritage_phase(self) -> None:
        """Test heritage phase."""
        phase = HeritagePhaseResponse(
            phase_id=1,
            code="HE-001",
            name="Facade Restoration",
            heritage_classification="grade_ii",
            approval_required=True,
            special_considerations=[
                "Original materials only",
                "Heritage specialist required",
            ],
        )
        assert phase.heritage_classification == "grade_ii"
        assert phase.approval_required is True
        assert len(phase.special_considerations) == 2


class TestHeritageTrackerResponse:
    """Tests for HeritageTrackerResponse model."""

    def test_no_heritage(self) -> None:
        """Test project with no heritage."""
        tracker = HeritageTrackerResponse(
            project_id=1,
        )
        assert tracker.heritage_classification == "none"
        assert tracker.total_heritage_phases == 0

    def test_with_heritage(self) -> None:
        """Test project with heritage phases."""
        phase = HeritagePhaseResponse(
            phase_id=1,
            code="HE-001",
            name="Conservation Work",
            heritage_classification="locally_listed",
            approval_required=True,
        )
        tracker = HeritageTrackerResponse(
            project_id=1,
            heritage_classification="locally_listed",
            overall_approval_status="pending",
            total_heritage_phases=2,
            classifications={"locally_listed": 2},
            phases=[phase],
            required_approvals=["Heritage Board"],
            pending_approvals=[{"phase_code": "HE-001", "authority": "Heritage Board"}],
            preservation_risks=["Material deterioration"],
            recommendations=["Use lime mortar only"],
        )
        assert tracker.total_heritage_phases == 2
        assert len(tracker.pending_approvals) == 1


class TestTenantRelocationResponse:
    """Tests for TenantRelocationResponse model."""

    def test_planned_relocation(self) -> None:
        """Test planned relocation."""
        relocation = TenantRelocationResponse(
            id=1,
            phase_id=2,
            tenant_name="ABC Corp",
            current_unit="Unit 5A",
            status="planned",
            planned_move_date="2024-06-01",
        )
        assert relocation.tenant_name == "ABC Corp"
        assert relocation.status == "planned"

    def test_temporary_relocation(self) -> None:
        """Test temporary relocation."""
        relocation = TenantRelocationResponse(
            id=2,
            phase_id=3,
            tenant_name="XYZ Ltd",
            current_unit="Unit 10B",
            relocation_type="temporary",
            status="relocated",
            notification_date="2024-01-15",
            planned_move_date="2024-02-01",
            actual_move_date="2024-02-03",
            temporary_location="Unit 2A (temp)",
            compensation_amount=5000.0,
            notes="Returning after renovation",
        )
        assert relocation.relocation_type == "temporary"
        assert relocation.temporary_location is not None


class TestTimelineEventResponse:
    """Tests for TimelineEventResponse model."""

    def test_timeline_event(self) -> None:
        """Test timeline event."""
        event = TimelineEventResponse(
            date="2024-03-15",
            event="Move-out",
            tenant_name="ABC Corp",
            status="completed",
            details="Completed ahead of schedule",
        )
        assert event.event == "Move-out"
        assert event.status == "completed"


class TestTenantCoordinationResponse:
    """Tests for TenantCoordinationResponse model."""

    def test_empty_coordination(self) -> None:
        """Test empty tenant coordination."""
        coordination = TenantCoordinationResponse(
            project_id=1,
        )
        assert coordination.total_tenants == 0
        assert coordination.relocations == []

    def test_full_coordination(self) -> None:
        """Test full tenant coordination."""
        relocation = TenantRelocationResponse(
            id=1,
            phase_id=1,
            tenant_name="Test Tenant",
            current_unit="Unit 1",
            status="planned",
        )
        event = TimelineEventResponse(
            date="2024-04-01",
            event="Notification",
            tenant_name="Test Tenant",
        )
        coordination = TenantCoordinationResponse(
            project_id=1,
            total_tenants=10,
            relocation_required=5,
            relocated=2,
            returned=1,
            pending_notification=2,
            agreements_signed=3,
            total_relocation_cost=50000.0,
            status_breakdown={"planned": 2, "relocated": 2, "returned": 1},
            relocations=[relocation],
            upcoming_moves=[relocation],
            overdue_notifications=[],
            timeline=[event],
            warnings=["2 tenants pending notification"],
        )
        assert coordination.total_tenants == 10
        assert coordination.total_relocation_cost == 50000.0


class TestDevelopmentPhaseScenarios:
    """Tests for development phase use case scenarios."""

    def test_multi_phase_project(self) -> None:
        """Test multi-phase development project."""
        tasks: List[GanttTaskResponse] = [
            GanttTaskResponse(
                id=i,
                code=f"PH-{i:03d}",
                name=name,
                phase_type=phase_type,
                start_date=f"2024-{month:02d}-01",
                end_date=f"2024-{month+2:02d}-01",
                duration=60,
                progress=0.0,
                status="pending",
                is_critical=i in [1, 2, 4],
                is_milestone=False,
                dependencies=deps,
            )
            for i, (name, phase_type, month, deps) in enumerate(
                [
                    ("Site Preparation", "construction", 1, []),
                    ("Foundation", "construction", 3, [0]),
                    ("Parking Structure", "construction", 3, [0]),
                    ("Tower Structure", "construction", 5, [1]),
                    ("MEP Install", "construction", 7, [3]),
                    ("Fit-Out", "fit_out", 9, [4]),
                ],
                start=1,
            )
        ]
        chart = GanttChartResponse(
            project_id=1,
            project_name="Mixed-Use Tower",
            generated_at="2024-01-01T00:00:00Z",
            tasks=tasks,
            critical_path=[1, 2, 4, 5],
            total_duration=330,
            completion_pct=0.0,
        )
        assert len(chart.tasks) == 6
        assert len(chart.critical_path) == 4

    def test_heritage_renovation_project(self) -> None:
        """Test heritage renovation project."""
        heritage_task = GanttTaskResponse(
            id=1,
            code="HE-001",
            name="Facade Restoration",
            phase_type="heritage",
            start_date="2024-01-01",
            end_date="2024-06-01",
            duration=152,
            progress=0.0,
            status="pending",
            is_critical=True,
            is_milestone=False,
            dependencies=[],
            is_heritage=True,
            notes="Grade II listed building",
        )
        heritage_phase = HeritagePhaseResponse(
            phase_id=1,
            code="HE-001",
            name="Facade Restoration",
            heritage_classification="grade_ii",
            approval_required=True,
            special_considerations=[
                "Original stonework preservation",
                "Window pattern must match",
                "Heritage approved materials only",
            ],
        )
        tracker = HeritageTrackerResponse(
            project_id=1,
            heritage_classification="grade_ii",
            overall_approval_status="approved",
            total_heritage_phases=3,
            phases=[heritage_phase],
            recommendations=["Engage specialist mason"],
        )
        assert heritage_task.is_heritage is True
        assert tracker.heritage_classification == "grade_ii"

    def test_tenant_relocation_project(self) -> None:
        """Test tenant relocation for occupied building."""
        tenants = [
            TenantRelocationResponse(
                id=i,
                phase_id=1,
                tenant_name=f"Tenant {i}",
                current_unit=f"Unit {i}",
                relocation_type="temporary",
                status=status,
            )
            for i, status in enumerate(
                ["notified", "agreement_signed", "relocated", "returned", "planned"],
                start=1,
            )
        ]
        coordination = TenantCoordinationResponse(
            project_id=1,
            total_tenants=5,
            relocation_required=5,
            relocated=2,
            returned=1,
            pending_notification=1,
            agreements_signed=3,
            total_relocation_cost=100000.0,
            status_breakdown={
                "notified": 1,
                "agreement_signed": 1,
                "relocated": 1,
                "returned": 1,
                "planned": 1,
            },
            relocations=tenants,
            warnings=[
                "1 tenant pending notification",
                "Relocation deadline in 30 days",
            ],
        )
        assert coordination.total_tenants == 5
        assert len(coordination.warnings) == 2
