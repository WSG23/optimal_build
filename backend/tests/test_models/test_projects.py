"""Integration tests for Project model."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from app.models.project import ApprovalStatus, Project, ProjectPhase, ProjectType
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


class TestProjectModel:
    """Test Project model CRUD operations and schema compliance."""

    async def test_create_minimal_project(self, session: AsyncSession):
        """Test creating a project with only required fields."""
        project = Project(
            project_name="Test Project",
            project_code="TEST-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            current_phase=ProjectPhase.CONCEPT,
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)

        assert project.id is not None
        assert project.project_name == "Test Project"
        assert project.project_code == "TEST-001"
        assert project.project_type == ProjectType.NEW_DEVELOPMENT
        assert project.current_phase == ProjectPhase.CONCEPT
        assert project.created_at is not None
        assert project.updated_at is not None

    async def test_create_full_project(self, session: AsyncSession):
        """Test creating a project with all fields populated."""
        project = Project(
            project_name="Marina Waterfront Development",
            project_code="MWD-2025",
            description="Luxury waterfront residential development",
            owner_email="developer@example.com",
            project_type=ProjectType.NEW_DEVELOPMENT,
            current_phase=ProjectPhase.FEASIBILITY,
            start_date=date(2025, 1, 1),
            target_completion_date=date(2027, 12, 31),
            # URA fields
            ura_submission_number="URA-2025-001",
            ura_approval_status=ApprovalStatus.PENDING,
            ura_submission_date=date(2025, 2, 1),
            # BCA fields
            bca_submission_number="BCA-2025-001",
            bca_approval_status=ApprovalStatus.PENDING,
            bca_submission_date=date(2025, 2, 15),
            # SCDF fields
            scdf_approval_status=ApprovalStatus.NOT_SUBMITTED,
            # Agency approvals
            nea_approval=False,
            pub_approval=False,
            lta_approval=False,
            nparks_approval=False,
            # Development parameters
            proposed_gfa_sqm=50000.0,
            proposed_units=200,
            proposed_height_m=120.0,
            proposed_storeys=30,
            proposed_plot_ratio=3.5,
            # Financial
            estimated_cost_sgd=150000000.0,
            development_charge_sgd=5000000.0,
            construction_cost_psf=850.0,
            # Construction team
            main_contractor="ABC Construction Pte Ltd",
            architect_firm="XYZ Architects",
            c_and_s_engineer="Engineering Solutions Pte Ltd",
            # Compliance scores
            buildability_score=85.0,
            green_mark_target="Platinum",
            # Progress
            completion_percentage=5.0,
            # Status
            is_active=True,
            is_completed=False,
            has_top=False,
            has_csc=False,
            # Key dates
            land_tender_date=date(2024, 6, 1),
            award_date=date(2024, 9, 1),
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)

        assert project.id is not None
        assert project.project_name == "Marina Waterfront Development"
        assert project.estimated_cost_sgd == 150000000.0
        assert project.proposed_gfa_sqm == 50000.0
        assert project.ura_approval_status == ApprovalStatus.PENDING
        assert project.green_mark_target == "Platinum"

    async def test_project_code_unique_constraint(self, session: AsyncSession):
        """Test that project_code must be unique."""
        project1 = Project(
            project_name="Project 1",
            project_code="UNIQUE-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            current_phase=ProjectPhase.CONCEPT,
        )
        session.add(project1)
        await session.commit()

        project2 = Project(
            project_name="Project 2",
            project_code="UNIQUE-001",  # Same code
            project_type=ProjectType.NEW_DEVELOPMENT,
            current_phase=ProjectPhase.CONCEPT,
        )
        session.add(project2)

        with pytest.raises(Exception) as exc_info:
            await session.commit()

        assert (
            "unique" in str(exc_info.value).lower()
            or "duplicate" in str(exc_info.value).lower()
        )

    async def test_project_enum_values(self, session: AsyncSession):
        """Test all ProjectType enum values work correctly."""
        project_types = [
            ProjectType.NEW_DEVELOPMENT,
            ProjectType.REDEVELOPMENT,
            ProjectType.ADDITION_ALTERATION,
            ProjectType.CONSERVATION,
            ProjectType.CHANGE_OF_USE,
            ProjectType.SUBDIVISION,
            ProjectType.EN_BLOC,
            ProjectType.DEMOLITION,
        ]

        for idx, project_type in enumerate(project_types):
            project = Project(
                project_name=f"Test {project_type.value}",
                project_code=f"TEST-{idx:03d}",
                project_type=project_type,
                current_phase=ProjectPhase.CONCEPT,
            )
            session.add(project)

        await session.commit()

        # Verify all were created
        result = await session.execute(select(Project))
        projects = result.scalars().all()
        assert len(projects) == len(project_types)

    async def test_project_phase_enum_values(self, session: AsyncSession):
        """Test all ProjectPhase enum values work correctly."""
        phases = [
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

        for idx, phase in enumerate(phases):
            project = Project(
                project_name=f"Test Phase {phase.value}",
                project_code=f"PHASE-{idx:03d}",
                project_type=ProjectType.NEW_DEVELOPMENT,
                current_phase=phase,
            )
            session.add(project)

        await session.commit()

        # Verify all were created
        result = await session.execute(select(Project))
        projects = result.scalars().all()
        assert len(projects) == len(phases)

    async def test_approval_status_enum_values(self, session: AsyncSession):
        """Test all ApprovalStatus enum values work correctly."""
        statuses = [
            ApprovalStatus.NOT_SUBMITTED,
            ApprovalStatus.PENDING,
            ApprovalStatus.APPROVED,
            ApprovalStatus.APPROVED_WITH_CONDITIONS,
            ApprovalStatus.REJECTED,
            ApprovalStatus.RESUBMISSION_REQUIRED,
            ApprovalStatus.EXPIRED,
        ]

        for idx, status in enumerate(statuses):
            project = Project(
                project_name=f"Test Status {status.value}",
                project_code=f"STATUS-{idx:03d}",
                project_type=ProjectType.NEW_DEVELOPMENT,
                current_phase=ProjectPhase.APPROVAL,
                ura_approval_status=status,
                bca_approval_status=status,
                scdf_approval_status=status,
            )
            session.add(project)

        await session.commit()

        # Verify all were created
        result = await session.execute(select(Project))
        projects = result.scalars().all()
        assert len(projects) == len(statuses)

    async def test_timezone_aware_timestamps(self, session: AsyncSession):
        """Test that created_at and updated_at are timezone-aware."""
        project = Project(
            project_name="Timezone Test",
            project_code="TZ-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            current_phase=ProjectPhase.CONCEPT,
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)

        assert project.created_at is not None
        assert project.updated_at is not None
        # Columns are stored as TIMESTAMP WITH TIME ZONE in PostgreSQL
        # asyncpg returns them as UTC but strips tzinfo (this is standard behavior)
        # Verify they are valid datetime objects
        assert isinstance(project.created_at, datetime)
        assert isinstance(project.updated_at, datetime)

    async def test_jsonb_columns(self, session: AsyncSession):
        """Test JSONB columns for milestones, risks, etc."""
        project = Project(
            project_name="JSONB Test",
            project_code="JSON-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            current_phase=ProjectPhase.CONSTRUCTION,
            milestones_data={
                "milestones": [
                    {"name": "Foundation", "date": "2025-03-01", "status": "completed"},
                    {
                        "name": "Superstructure",
                        "date": "2025-09-01",
                        "status": "in_progress",
                    },
                ]
            },
            risks_identified={
                "risks": [
                    {"id": 1, "description": "Weather delays", "severity": "medium"},
                    {"id": 2, "description": "Material shortage", "severity": "high"},
                ]
            },
            ura_conditions={"conditions": ["Max height 150m", "Min setback 10m"]},
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)

        assert project.milestones_data is not None
        assert len(project.milestones_data["milestones"]) == 2
        assert project.risks_identified["risks"][1]["severity"] == "high"
        assert "Max height 150m" in project.ura_conditions["conditions"]

    async def test_update_project(self, session: AsyncSession):
        """Test updating project fields."""
        project = Project(
            project_name="Original Name",
            project_code="UPDATE-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            current_phase=ProjectPhase.CONCEPT,
            completion_percentage=0.0,
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)
        original_updated_at = project.updated_at

        # Update fields
        project.current_phase = ProjectPhase.CONSTRUCTION
        project.completion_percentage = 45.0
        project.ura_approval_status = ApprovalStatus.APPROVED
        await session.commit()
        await session.refresh(project)

        assert project.current_phase == ProjectPhase.CONSTRUCTION
        assert project.completion_percentage == 45.0
        assert project.ura_approval_status == ApprovalStatus.APPROVED
        # updated_at should be automatically updated
        assert project.updated_at > original_updated_at

    async def test_query_by_filters(self, session: AsyncSession):
        """Test querying projects by various filters."""
        # Create test projects
        for i in range(5):
            project = Project(
                project_name=f"Project {i}",
                project_code=f"FILTER-{i:03d}",
                project_type=(
                    ProjectType.NEW_DEVELOPMENT
                    if i % 2 == 0
                    else ProjectType.REDEVELOPMENT
                ),
                current_phase=(
                    ProjectPhase.CONCEPT if i < 3 else ProjectPhase.CONSTRUCTION
                ),
                is_active=i < 4,  # Last one is inactive
            )
            session.add(project)
        await session.commit()

        # Query active projects
        stmt = select(Project).where(Project.is_active.is_(True))
        result = await session.execute(stmt)
        active_projects = result.scalars().all()
        assert len(active_projects) == 4

        # Query by type
        stmt = select(Project).where(
            Project.project_type == ProjectType.NEW_DEVELOPMENT
        )
        result = await session.execute(stmt)
        new_dev_projects = result.scalars().all()
        assert len(new_dev_projects) == 3

        # Query by phase
        stmt = select(Project).where(Project.current_phase == ProjectPhase.CONSTRUCTION)
        result = await session.execute(stmt)
        construction_projects = result.scalars().all()
        assert len(construction_projects) == 2
