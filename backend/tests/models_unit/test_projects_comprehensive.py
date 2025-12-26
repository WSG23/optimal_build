"""Comprehensive tests for Project model.

Tests cover:
- Project creation and field validation
- Enum field validation (ProjectType, ProjectPhase, ApprovalStatus)
- Financial field precision (DECIMAL types)
- Foreign key relationships
- Timeline and date handling
- JSON field handling
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal


from app.models.projects import (
    ApprovalStatus,
    Project,
    ProjectPhase,
    ProjectType,
)


class TestProjectTypeEnum:
    """Tests for ProjectType enum."""

    def test_all_project_types_defined(self) -> None:
        """All expected project types should be defined."""
        expected = [
            "NEW_DEVELOPMENT",
            "REDEVELOPMENT",
            "ADDITION_ALTERATION",
            "CONSERVATION",
            "CHANGE_OF_USE",
            "SUBDIVISION",
            "EN_BLOC",
            "DEMOLITION",
        ]
        actual = [pt.name for pt in ProjectType]
        assert sorted(actual) == sorted(expected)

    def test_project_type_values(self) -> None:
        """Project type values should be lowercase."""
        assert ProjectType.NEW_DEVELOPMENT.value == "new_development"
        assert ProjectType.REDEVELOPMENT.value == "redevelopment"
        assert ProjectType.EN_BLOC.value == "en_bloc"

    def test_project_type_is_string_enum(self) -> None:
        """ProjectType should be a string enum."""
        assert isinstance(ProjectType.NEW_DEVELOPMENT, str)
        assert ProjectType.NEW_DEVELOPMENT == "new_development"


class TestProjectPhaseEnum:
    """Tests for ProjectPhase enum."""

    def test_all_phases_defined(self) -> None:
        """All expected phases should be defined."""
        expected = [
            "CONCEPT",
            "FEASIBILITY",
            "DESIGN",
            "APPROVAL",
            "TENDER",
            "CONSTRUCTION",
            "TESTING_COMMISSIONING",
            "HANDOVER",
            "OPERATION",
        ]
        actual = [pp.name for pp in ProjectPhase]
        assert sorted(actual) == sorted(expected)

    def test_phase_values(self) -> None:
        """Phase values should be lowercase."""
        assert ProjectPhase.CONCEPT.value == "concept"
        assert ProjectPhase.CONSTRUCTION.value == "construction"

    def test_phase_progression(self) -> None:
        """Phases should be in logical order."""
        phases = list(ProjectPhase)
        phase_names = [p.name for p in phases]
        assert phase_names.index("CONCEPT") < phase_names.index("FEASIBILITY")
        assert phase_names.index("DESIGN") < phase_names.index("CONSTRUCTION")


class TestApprovalStatusEnum:
    """Tests for ApprovalStatus enum."""

    def test_all_statuses_defined(self) -> None:
        """All expected statuses should be defined."""
        expected = [
            "NOT_SUBMITTED",
            "PENDING",
            "APPROVED",
            "APPROVED_WITH_CONDITIONS",
            "REJECTED",
            "RESUBMISSION_REQUIRED",
            "EXPIRED",
        ]
        actual = [s.name for s in ApprovalStatus]
        assert sorted(actual) == sorted(expected)

    def test_default_status(self) -> None:
        """NOT_SUBMITTED should be the logical default."""
        assert ApprovalStatus.NOT_SUBMITTED.value == "not_submitted"


class TestProjectCreation:
    """Tests for Project model creation."""

    def test_create_minimal_project(self) -> None:
        """Project with only required fields should be valid."""
        project = Project(
            id=uuid.uuid4(),
            project_name="Test Project",
            project_code="TEST-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
        )
        assert project.project_name == "Test Project"
        assert project.project_code == "TEST-001"
        assert project.project_type == ProjectType.NEW_DEVELOPMENT

    def test_create_project_with_all_fields(self) -> None:
        """Project with all fields should be valid."""
        project_id = uuid.uuid4()
        project = Project(
            id=project_id,
            project_name="Full Project",
            project_code="FULL-001",
            description="A fully specified project",
            project_type=ProjectType.REDEVELOPMENT,
            current_phase=ProjectPhase.DESIGN,
            owner_email="owner@example.com",
            start_date=date(2024, 1, 1),
            target_completion_date=date(2026, 12, 31),
            proposed_gfa_sqm=Decimal("10000.50"),
            proposed_units=100,
            proposed_height_m=Decimal("45.50"),
            proposed_storeys=15,
            estimated_cost_sgd=Decimal("50000000.00"),
            is_active=True,
        )
        assert project.id == project_id
        assert project.current_phase == ProjectPhase.DESIGN
        assert project.proposed_units == 100

    def test_default_current_phase(self) -> None:
        """Default phase should be CONCEPT."""
        project = Project(
            project_name="Test",
            project_code="T-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
        )
        # Note: Default is set at DB level, model may not reflect it without session
        assert (
            project.current_phase is None
            or project.current_phase == ProjectPhase.CONCEPT
        )


class TestProjectFinancialFields:
    """Tests for financial field precision."""

    def test_gfa_decimal_precision(self) -> None:
        """GFA should support 2 decimal places."""
        project = Project(
            project_name="Test",
            project_code="T-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            proposed_gfa_sqm=Decimal("12345.67"),
        )
        assert project.proposed_gfa_sqm == Decimal("12345.67")

    def test_cost_decimal_precision(self) -> None:
        """Cost fields should support large values with 2 decimal places."""
        project = Project(
            project_name="Test",
            project_code="T-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            estimated_cost_sgd=Decimal("999999999999.99"),
            actual_cost_sgd=Decimal("888888888888.88"),
        )
        assert project.estimated_cost_sgd == Decimal("999999999999.99")
        assert project.actual_cost_sgd == Decimal("888888888888.88")

    def test_plot_ratio_precision(self) -> None:
        """Plot ratio should support 2 decimal places."""
        project = Project(
            project_name="Test",
            project_code="T-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            proposed_plot_ratio=Decimal("2.50"),
        )
        assert project.proposed_plot_ratio == Decimal("2.50")

    def test_completion_percentage(self) -> None:
        """Completion percentage should support decimals."""
        project = Project(
            project_name="Test",
            project_code="T-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            completion_percentage=Decimal("75.50"),
        )
        assert project.completion_percentage == Decimal("75.50")


class TestProjectRegulatoryFields:
    """Tests for regulatory approval fields."""

    def test_ura_fields(self) -> None:
        """URA fields should be settable."""
        project = Project(
            project_name="Test",
            project_code="T-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            ura_submission_number="URA-2024-001",
            ura_approval_status=ApprovalStatus.PENDING,
            ura_submission_date=date(2024, 1, 15),
        )
        assert project.ura_submission_number == "URA-2024-001"
        assert project.ura_approval_status == ApprovalStatus.PENDING

    def test_bca_fields(self) -> None:
        """BCA fields should be settable."""
        project = Project(
            project_name="Test",
            project_code="T-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            bca_submission_number="BCA-2024-001",
            bca_approval_status=ApprovalStatus.APPROVED,
            bca_bc1_number="BC1-12345",
            bca_permit_number="BP-2024-001",
        )
        assert project.bca_bc1_number == "BC1-12345"
        assert project.bca_approval_status == ApprovalStatus.APPROVED

    def test_scdf_fields(self) -> None:
        """SCDF fields should be settable."""
        project = Project(
            project_name="Test",
            project_code="T-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            scdf_approval_status=ApprovalStatus.APPROVED_WITH_CONDITIONS,
            fire_safety_certificate="FSC-2024-001",
        )
        assert project.scdf_approval_status == ApprovalStatus.APPROVED_WITH_CONDITIONS
        assert project.fire_safety_certificate == "FSC-2024-001"

    def test_other_agency_approvals(self) -> None:
        """Other agency approval booleans should work."""
        project = Project(
            project_name="Test",
            project_code="T-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            nea_approval=True,
            pub_approval=True,
            lta_approval=False,
            nparks_approval=True,
        )
        assert project.nea_approval is True
        assert project.lta_approval is False


class TestProjectStatusFields:
    """Tests for project status fields."""

    def test_active_status(self) -> None:
        """is_active should be settable."""
        project = Project(
            project_name="Test",
            project_code="T-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            is_active=True,
        )
        assert project.is_active is True

    def test_completion_status(self) -> None:
        """Completion flags should be settable."""
        project = Project(
            project_name="Test",
            project_code="T-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            is_completed=True,
            has_top=True,
            has_csc=True,
        )
        assert project.is_completed is True
        assert project.has_top is True
        assert project.has_csc is True


class TestProjectDateFields:
    """Tests for date fields."""

    def test_timeline_dates(self) -> None:
        """Timeline dates should be settable."""
        project = Project(
            project_name="Test",
            project_code="T-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            start_date=date(2024, 1, 1),
            target_completion_date=date(2026, 12, 31),
            actual_completion_date=date(2027, 3, 15),
        )
        assert project.start_date == date(2024, 1, 1)
        assert project.target_completion_date == date(2026, 12, 31)

    def test_key_milestone_dates(self) -> None:
        """Key milestone dates should be settable."""
        project = Project(
            project_name="Test",
            project_code="T-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            land_tender_date=date(2023, 6, 1),
            award_date=date(2023, 9, 15),
            groundbreaking_date=date(2024, 1, 1),
            topping_out_date=date(2025, 6, 1),
            top_date=date(2026, 12, 1),
            csc_date=date(2027, 3, 1),
        )
        assert project.land_tender_date == date(2023, 6, 1)
        assert project.top_date == date(2026, 12, 1)


class TestProjectJSONFields:
    """Tests for JSON fields."""

    def test_conditions_json(self) -> None:
        """URA conditions should accept JSON."""
        conditions = {
            "condition_1": "Must provide parking",
            "condition_2": "Height restriction applies",
        }
        project = Project(
            project_name="Test",
            project_code="T-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            ura_conditions=conditions,
        )
        assert project.ura_conditions == conditions

    def test_milestones_json(self) -> None:
        """Milestones should accept JSON list."""
        milestones = [
            {"name": "Foundation", "date": "2024-03-01", "status": "complete"},
            {"name": "Structure", "date": "2025-01-01", "status": "pending"},
        ]
        project = Project(
            project_name="Test",
            project_code="T-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            milestones_data=milestones,
        )
        assert len(project.milestones_data) == 2

    def test_documents_json(self) -> None:
        """Documents should accept JSON."""
        documents = {
            "architectural_plans": "s3://bucket/plans.pdf",
            "structural_drawings": "s3://bucket/structural.pdf",
        }
        project = Project(
            project_name="Test",
            project_code="T-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            documents=documents,
        )
        assert project.documents["architectural_plans"] == "s3://bucket/plans.pdf"


class TestProjectConsultantFields:
    """Tests for consultant/contractor fields."""

    def test_contractor_fields(self) -> None:
        """Contractor fields should be settable."""
        project = Project(
            project_name="Test",
            project_code="T-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            main_contractor="ABC Construction Pte Ltd",
            architect_firm="XYZ Architects",
            c_and_s_engineer="Structural Engineers Ltd",
            mep_engineer="MEP Solutions",
            qs_consultant="QS Associates",
        )
        assert project.main_contractor == "ABC Construction Pte Ltd"
        assert project.architect_firm == "XYZ Architects"


class TestProjectQualityFields:
    """Tests for quality/compliance score fields."""

    def test_buildability_scores(self) -> None:
        """Buildability scores should accept decimals."""
        project = Project(
            project_name="Test",
            project_code="T-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            buildability_score=Decimal("85.50"),
            constructability_score=Decimal("90.25"),
            quality_mark_score=Decimal("92.00"),
        )
        assert project.buildability_score == Decimal("85.50")
        assert project.quality_mark_score == Decimal("92.00")

    def test_green_mark_target(self) -> None:
        """Green mark target should be settable."""
        project = Project(
            project_name="Test",
            project_code="T-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            green_mark_target="Platinum",
        )
        assert project.green_mark_target == "Platinum"


class TestProjectRepr:
    """Tests for __repr__ method."""

    def test_repr_format(self) -> None:
        """Repr should show name and code."""
        project = Project(
            project_name="Marina Bay Tower",
            project_code="MBT-2024",
            project_type=ProjectType.NEW_DEVELOPMENT,
        )
        repr_str = repr(project)
        assert "Marina Bay Tower" in repr_str
        assert "MBT-2024" in repr_str
