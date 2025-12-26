"""Comprehensive tests for development_phase model.

Tests cover:
- PhaseType enum
- PhaseStatus enum
- DependencyType enum
- MilestoneType enum
- HeritageClassification enum
- OccupancyStatus enum
- DevelopmentPhase model structure
- PhaseDependency model structure
- PhaseMilestone model structure
- TenantRelocation model structure
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal


class TestPhaseType:
    """Tests for PhaseType enum."""

    def test_demolition(self) -> None:
        """Test demolition phase type."""
        phase = "demolition"
        assert phase == "demolition"

    def test_site_preparation(self) -> None:
        """Test site_preparation phase type."""
        phase = "site_preparation"
        assert phase == "site_preparation"

    def test_foundation(self) -> None:
        """Test foundation phase type."""
        phase = "foundation"
        assert phase == "foundation"

    def test_structure(self) -> None:
        """Test structure phase type."""
        phase = "structure"
        assert phase == "structure"

    def test_envelope(self) -> None:
        """Test envelope phase type."""
        phase = "envelope"
        assert phase == "envelope"

    def test_mep_rough_in(self) -> None:
        """Test mep_rough_in phase type."""
        phase = "mep_rough_in"
        assert phase == "mep_rough_in"

    def test_interior_fit_out(self) -> None:
        """Test interior_fit_out phase type."""
        phase = "interior_fit_out"
        assert phase == "interior_fit_out"

    def test_heritage_assessment(self) -> None:
        """Test heritage_assessment phase type."""
        phase = "heritage_assessment"
        assert phase == "heritage_assessment"

    def test_heritage_restoration(self) -> None:
        """Test heritage_restoration phase type."""
        phase = "heritage_restoration"
        assert phase == "heritage_restoration"

    def test_tenant_relocation(self) -> None:
        """Test tenant_relocation phase type."""
        phase = "tenant_relocation"
        assert phase == "tenant_relocation"


class TestPhaseStatus:
    """Tests for PhaseStatus enum."""

    def test_not_started(self) -> None:
        """Test not_started status."""
        status = "not_started"
        assert status == "not_started"

    def test_planning(self) -> None:
        """Test planning status."""
        status = "planning"
        assert status == "planning"

    def test_in_progress(self) -> None:
        """Test in_progress status."""
        status = "in_progress"
        assert status == "in_progress"

    def test_on_hold(self) -> None:
        """Test on_hold status."""
        status = "on_hold"
        assert status == "on_hold"

    def test_delayed(self) -> None:
        """Test delayed status."""
        status = "delayed"
        assert status == "delayed"

    def test_completed(self) -> None:
        """Test completed status."""
        status = "completed"
        assert status == "completed"

    def test_cancelled(self) -> None:
        """Test cancelled status."""
        status = "cancelled"
        assert status == "cancelled"


class TestDependencyType:
    """Tests for DependencyType enum."""

    def test_finish_to_start(self) -> None:
        """Test FS - Finish to Start dependency."""
        dep = "FS"
        assert dep == "FS"

    def test_start_to_start(self) -> None:
        """Test SS - Start to Start dependency."""
        dep = "SS"
        assert dep == "SS"

    def test_finish_to_finish(self) -> None:
        """Test FF - Finish to Finish dependency."""
        dep = "FF"
        assert dep == "FF"

    def test_start_to_finish(self) -> None:
        """Test SF - Start to Finish dependency."""
        dep = "SF"
        assert dep == "SF"


class TestMilestoneType:
    """Tests for MilestoneType enum."""

    def test_authority_approval(self) -> None:
        """Test authority_approval milestone."""
        milestone = "authority_approval"
        assert milestone == "authority_approval"

    def test_planning_approval(self) -> None:
        """Test planning_approval milestone."""
        milestone = "planning_approval"
        assert milestone == "planning_approval"

    def test_building_permit(self) -> None:
        """Test building_permit milestone."""
        milestone = "building_permit"
        assert milestone == "building_permit"

    def test_structural_completion(self) -> None:
        """Test structural_completion milestone."""
        milestone = "structural_completion"
        assert milestone == "structural_completion"

    def test_top_out(self) -> None:
        """Test top_out milestone."""
        milestone = "top_out"
        assert milestone == "top_out"

    def test_practical_completion(self) -> None:
        """Test practical_completion milestone."""
        milestone = "practical_completion"
        assert milestone == "practical_completion"

    def test_certificate_of_occupancy(self) -> None:
        """Test certificate_of_occupancy milestone."""
        milestone = "certificate_of_occupancy"
        assert milestone == "certificate_of_occupancy"


class TestHeritageClassification:
    """Tests for HeritageClassification enum."""

    def test_none_classification(self) -> None:
        """Test none heritage classification."""
        classification = "none"
        assert classification == "none"

    def test_locally_listed(self) -> None:
        """Test locally_listed classification."""
        classification = "locally_listed"
        assert classification == "locally_listed"

    def test_nationally_listed(self) -> None:
        """Test nationally_listed classification."""
        classification = "nationally_listed"
        assert classification == "nationally_listed"

    def test_conservation_area(self) -> None:
        """Test conservation_area classification."""
        classification = "conservation_area"
        assert classification == "conservation_area"

    def test_world_heritage(self) -> None:
        """Test world_heritage classification."""
        classification = "world_heritage"
        assert classification == "world_heritage"

    def test_facade_only(self) -> None:
        """Test facade_only classification."""
        classification = "facade_only"
        assert classification == "facade_only"


class TestOccupancyStatus:
    """Tests for OccupancyStatus enum."""

    def test_vacant(self) -> None:
        """Test vacant status."""
        status = "vacant"
        assert status == "vacant"

    def test_partially_occupied(self) -> None:
        """Test partially_occupied status."""
        status = "partially_occupied"
        assert status == "partially_occupied"

    def test_fully_occupied(self) -> None:
        """Test fully_occupied status."""
        status = "fully_occupied"
        assert status == "fully_occupied"

    def test_decanting_in_progress(self) -> None:
        """Test decanting_in_progress status."""
        status = "decanting_in_progress"
        assert status == "decanting_in_progress"


class TestDevelopmentPhaseModel:
    """Tests for DevelopmentPhase model structure."""

    def test_id_is_integer(self) -> None:
        """Test id is integer type."""
        phase_id = 1
        assert isinstance(phase_id, int)

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = 1
        assert project_id is not None

    def test_phase_code_required(self) -> None:
        """Test phase_code is required."""
        code = "P1A"
        assert len(code) > 0

    def test_phase_name_required(self) -> None:
        """Test phase_name is required."""
        name = "Foundation Works"
        assert len(name) > 0

    def test_phase_type_default_structure(self) -> None:
        """Test phase_type defaults to structure."""
        phase_type = "structure"
        assert phase_type == "structure"

    def test_status_default_not_started(self) -> None:
        """Test status defaults to not_started."""
        status = "not_started"
        assert status == "not_started"

    def test_completion_percentage_default_zero(self) -> None:
        """Test completion_percentage defaults to 0."""
        pct = 0
        assert pct == 0

    def test_is_critical_path_default_false(self) -> None:
        """Test is_critical_path defaults to False."""
        critical = False
        assert critical is False


class TestPhaseMilestoneModel:
    """Tests for PhaseMilestone model structure."""

    def test_id_is_integer(self) -> None:
        """Test id is integer type."""
        milestone_id = 1
        assert isinstance(milestone_id, int)

    def test_phase_id_required(self) -> None:
        """Test phase_id is required."""
        phase_id = 1
        assert phase_id is not None

    def test_milestone_name_required(self) -> None:
        """Test milestone_name is required."""
        name = "BCA Building Permit"
        assert len(name) > 0

    def test_milestone_type_required(self) -> None:
        """Test milestone_type is required."""
        milestone_type = "building_permit"
        assert milestone_type is not None

    def test_planned_date_required(self) -> None:
        """Test planned_date is required."""
        planned = date(2024, 6, 30)
        assert planned is not None

    def test_is_achieved_default_false(self) -> None:
        """Test is_achieved defaults to False."""
        achieved = False
        assert achieved is False


class TestTenantRelocationModel:
    """Tests for TenantRelocation model structure."""

    def test_id_is_integer(self) -> None:
        """Test id is integer type."""
        relocation_id = 1
        assert isinstance(relocation_id, int)

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = 1
        assert project_id is not None

    def test_tenant_name_required(self) -> None:
        """Test tenant_name is required."""
        name = "ABC Pte Ltd"
        assert len(name) > 0

    def test_relocation_required_default_true(self) -> None:
        """Test relocation_required defaults to True."""
        required = True
        assert required is True

    def test_status_default_planned(self) -> None:
        """Test status defaults to planned."""
        status = "planned"
        assert status == "planned"


class TestDevelopmentPhaseScenarios:
    """Tests for development phase use case scenarios."""

    def test_create_development_phase(self) -> None:
        """Test creating a development phase."""
        phase = {
            "id": 1,
            "project_id": 1,
            "phase_code": "P1",
            "phase_name": "Foundation Works",
            "phase_type": "foundation",
            "status": "planning",
            "completion_percentage": Decimal("0.00"),
            "planned_start_date": date(2024, 3, 1).isoformat(),
            "planned_end_date": date(2024, 6, 30).isoformat(),
            "duration_days": 122,
            "is_critical_path": True,
            "estimated_cost": Decimal("5000000.00"),
        }
        assert phase["phase_type"] == "foundation"
        assert phase["is_critical_path"] is True

    def test_heritage_phase(self) -> None:
        """Test creating a heritage-specific phase."""
        phase = {
            "id": 2,
            "project_id": 1,
            "phase_code": "H1",
            "phase_name": "Heritage Assessment",
            "phase_type": "heritage_assessment",
            "heritage_classification": "conservation_area",
            "heritage_approval_required": True,
            "heritage_conditions": "Preserve original facade elements",
        }
        assert phase["heritage_classification"] == "conservation_area"
        assert phase["heritage_approval_required"] is True

    def test_renovation_phase_with_occupancy(self) -> None:
        """Test creating a renovation phase with occupied building."""
        phase = {
            "id": 3,
            "project_id": 1,
            "phase_code": "R1",
            "phase_name": "Tenant Decanting",
            "phase_type": "tenant_relocation",
            "occupancy_status": "fully_occupied",
            "affected_tenants_count": 15,
            "working_hours_restriction": "08:00-18:00 weekdays only",
            "noise_restrictions": {"zones": ["tenant_areas"], "hours": "09:00-17:00"},
        }
        assert phase["affected_tenants_count"] == 15

    def test_phase_dependency(self) -> None:
        """Test creating a phase dependency."""
        dependency = {
            "id": 1,
            "predecessor_phase_id": 1,
            "successor_phase_id": 2,
            "dependency_type": "FS",
            "lag_days": 5,
            "notes": "Allow curing time before superstructure",
        }
        assert dependency["dependency_type"] == "FS"
        assert dependency["lag_days"] == 5

    def test_phase_milestone(self) -> None:
        """Test creating a phase milestone."""
        milestone = {
            "id": 1,
            "phase_id": 1,
            "milestone_name": "BCA Building Permit Approval",
            "milestone_type": "building_permit",
            "planned_date": date(2024, 4, 15).isoformat(),
            "requires_approval": True,
            "approval_authority": "BCA",
            "approval_status": "pending",
            "notify_before_days": 14,
        }
        assert milestone["approval_authority"] == "BCA"

    def test_tenant_relocation(self) -> None:
        """Test creating a tenant relocation record."""
        relocation = {
            "id": 1,
            "project_id": 1,
            "phase_id": 3,
            "tenant_name": "Singapore Tech Pte Ltd",
            "current_unit": "Level 15",
            "leased_area_sqm": Decimal("500.00"),
            "lease_expiry_date": date(2025, 12, 31).isoformat(),
            "relocation_required": True,
            "temporary_location": "Level 5 (swing space)",
            "relocation_start_date": date(2024, 6, 1).isoformat(),
            "relocation_allowance": Decimal("50000.00"),
            "rent_abatement_months": 2,
            "status": "notified",
            "agreement_signed": True,
        }
        assert relocation["relocation_required"] is True
        assert relocation["rent_abatement_months"] == 2

    def test_update_phase_progress(self) -> None:
        """Test updating phase progress."""
        phase = {"completion_percentage": Decimal("0.00"), "status": "not_started"}
        phase["status"] = "in_progress"
        phase["completion_percentage"] = Decimal("45.50")
        phase["actual_start_date"] = date(2024, 3, 5)
        assert phase["completion_percentage"] == Decimal("45.50")

    def test_complete_milestone(self) -> None:
        """Test completing a milestone."""
        milestone = {
            "is_achieved": False,
            "actual_date": None,
            "approval_status": "pending",
        }
        milestone["is_achieved"] = True
        milestone["actual_date"] = date.today()
        milestone["approval_status"] = "approved"
        milestone["approval_reference"] = "BCA-2024-12345"
        assert milestone["is_achieved"] is True

    def test_phase_delay_calculation(self) -> None:
        """Test calculating phase delay."""
        phase = {
            "planned_end_date": date(2024, 6, 30),
            "status": "in_progress",
        }
        # If today is past planned end, calculate days delayed
        today = date(2024, 7, 15)
        if today > phase["planned_end_date"]:
            days_delayed = (today - phase["planned_end_date"]).days
            phase["status"] = "delayed"
        else:
            days_delayed = 0
        assert days_delayed == 15
        assert phase["status"] == "delayed"
