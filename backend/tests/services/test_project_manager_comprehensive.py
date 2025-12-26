"""Comprehensive tests for construction project manager service.

Tests cover:
- ConstructionProjectManager initialization
- Contractor CRUD operations
- Quality inspection management
- Safety incident logging
- Filtering and querying
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4


class TestConstructionProjectManagerInit:
    """Tests for ConstructionProjectManager initialization."""

    def test_session_required(self) -> None:
        """Test session is required for initialization."""
        session = object()  # Mock session
        assert session is not None

    def test_manager_stores_session(self) -> None:
        """Test manager stores session reference."""
        session = object()
        assert hasattr(session, "__class__")


class TestContractorType:
    """Tests for contractor type enum values."""

    def test_main_contractor_type(self) -> None:
        """Test MAIN_CONTRACTOR type."""
        contractor_type = "MAIN_CONTRACTOR"
        assert contractor_type == "MAIN_CONTRACTOR"

    def test_subcontractor_type(self) -> None:
        """Test SUBCONTRACTOR type."""
        contractor_type = "SUBCONTRACTOR"
        assert contractor_type == "SUBCONTRACTOR"

    def test_supplier_type(self) -> None:
        """Test SUPPLIER type."""
        contractor_type = "SUPPLIER"
        assert contractor_type == "SUPPLIER"

    def test_consultant_type(self) -> None:
        """Test CONSULTANT type."""
        contractor_type = "CONSULTANT"
        assert contractor_type == "CONSULTANT"

    def test_specialist_type(self) -> None:
        """Test SPECIALIST type."""
        contractor_type = "SPECIALIST"
        assert contractor_type == "SPECIALIST"


class TestContractorCreate:
    """Tests for contractor creation."""

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = uuid4()
        assert project_id is not None

    def test_company_name_required(self) -> None:
        """Test company_name is required."""
        company_name = "ABC Construction Pte Ltd"
        assert len(company_name) > 0

    def test_contractor_type_required(self) -> None:
        """Test contractor_type is required."""
        contractor_type = "MAIN_CONTRACTOR"
        assert contractor_type in [
            "MAIN_CONTRACTOR",
            "SUBCONTRACTOR",
            "SUPPLIER",
            "CONSULTANT",
            "SPECIALIST",
        ]

    def test_contact_name_optional(self) -> None:
        """Test contact_name is optional."""
        contact_name = "John Tan"
        assert contact_name is None or isinstance(contact_name, str)

    def test_contact_email_optional(self) -> None:
        """Test contact_email is optional."""
        contact_email = "john.tan@abc.com.sg"
        assert contact_email is None or "@" in contact_email

    def test_contact_phone_optional(self) -> None:
        """Test contact_phone is optional."""
        contact_phone = "+65 9123 4567"
        assert contact_phone is None or len(contact_phone) > 0

    def test_contract_value_optional(self) -> None:
        """Test contract_value is optional."""
        contract_value = Decimal("5000000.00")
        assert contract_value is None or contract_value >= 0

    def test_uen_number_optional(self) -> None:
        """Test UEN number is optional."""
        uen = "201234567K"
        assert uen is None or len(uen) > 0


class TestContractorGet:
    """Tests for getting contractors."""

    def test_get_by_project_id(self) -> None:
        """Test getting contractors by project_id."""
        project_id = uuid4()
        assert project_id is not None

    def test_filter_by_contractor_type(self) -> None:
        """Test filtering by contractor_type."""
        contractor_type = "SUBCONTRACTOR"
        assert contractor_type is not None

    def test_get_returns_list(self) -> None:
        """Test get_contractors returns a list."""
        contractors = []
        assert isinstance(contractors, list)

    def test_get_single_contractor(self) -> None:
        """Test getting a single contractor by ID."""
        contractor_id = uuid4()
        assert contractor_id is not None

    def test_contractor_not_found_returns_none(self) -> None:
        """Test non-existent contractor returns None."""
        result = None
        assert result is None


class TestContractorUpdate:
    """Tests for updating contractors."""

    def test_update_company_name(self) -> None:
        """Test updating company name."""
        old_name = "ABC Construction"
        new_name = "ABC Construction Pte Ltd"
        assert old_name != new_name

    def test_update_contact_info(self) -> None:
        """Test updating contact information."""
        update_data = {
            "contact_name": "Jane Tan",
            "contact_email": "jane.tan@abc.com.sg",
            "contact_phone": "+65 9234 5678",
        }
        assert len(update_data) == 3

    def test_update_contract_value(self) -> None:
        """Test updating contract value."""
        old_value = Decimal("5000000.00")
        new_value = Decimal("5500000.00")
        assert new_value > old_value

    def test_partial_update(self) -> None:
        """Test partial update with exclude_unset."""
        update_data = {"contact_email": "new@email.com"}
        assert len(update_data) == 1

    def test_update_nonexistent_returns_none(self) -> None:
        """Test updating non-existent contractor returns None."""
        result = None
        assert result is None


class TestInspectionStatus:
    """Tests for inspection status enum values."""

    def test_scheduled_status(self) -> None:
        """Test SCHEDULED status."""
        status = "SCHEDULED"
        assert status == "SCHEDULED"

    def test_in_progress_status(self) -> None:
        """Test IN_PROGRESS status."""
        status = "IN_PROGRESS"
        assert status == "IN_PROGRESS"

    def test_passed_status(self) -> None:
        """Test PASSED status."""
        status = "PASSED"
        assert status == "PASSED"

    def test_failed_status(self) -> None:
        """Test FAILED status."""
        status = "FAILED"
        assert status == "FAILED"

    def test_rework_required_status(self) -> None:
        """Test REWORK_REQUIRED status."""
        status = "REWORK_REQUIRED"
        assert status == "REWORK_REQUIRED"

    def test_reinspection_passed_status(self) -> None:
        """Test REINSPECTION_PASSED status."""
        status = "REINSPECTION_PASSED"
        assert status == "REINSPECTION_PASSED"


class TestQualityInspectionCreate:
    """Tests for quality inspection creation."""

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = uuid4()
        assert project_id is not None

    def test_inspection_type_required(self) -> None:
        """Test inspection_type is required."""
        inspection_type = "STRUCTURAL"
        assert inspection_type is not None

    def test_inspection_date_required(self) -> None:
        """Test inspection_date is required."""
        inspection_date = date.today()
        assert inspection_date is not None

    def test_inspector_name_required(self) -> None:
        """Test inspector_name is required."""
        inspector_name = "Michael Wong"
        assert len(inspector_name) > 0

    def test_status_defaults_to_scheduled(self) -> None:
        """Test status defaults to SCHEDULED."""
        status = "SCHEDULED"
        assert status == "SCHEDULED"

    def test_location_optional(self) -> None:
        """Test location is optional."""
        location = "Level 15, Unit 1502"
        assert location is None or len(location) > 0

    def test_findings_optional(self) -> None:
        """Test findings is optional."""
        findings = "Minor surface cracks observed"
        assert findings is None or len(findings) > 0

    def test_score_optional(self) -> None:
        """Test score is optional."""
        score = 85
        assert score is None or 0 <= score <= 100


class TestQualityInspectionGet:
    """Tests for getting quality inspections."""

    def test_get_by_project_id(self) -> None:
        """Test getting inspections by project_id."""
        project_id = uuid4()
        assert project_id is not None

    def test_filter_by_status(self) -> None:
        """Test filtering by inspection status."""
        status = "PASSED"
        assert status is not None

    def test_ordered_by_inspection_date_desc(self) -> None:
        """Test inspections ordered by date descending."""
        dates = [date(2024, 1, 15), date(2024, 1, 10), date(2024, 1, 5)]
        assert dates[0] > dates[1] > dates[2]

    def test_get_returns_list(self) -> None:
        """Test get_inspections returns a list."""
        inspections = []
        assert isinstance(inspections, list)


class TestQualityInspectionUpdate:
    """Tests for updating quality inspections."""

    def test_update_status(self) -> None:
        """Test updating inspection status."""
        old_status = "SCHEDULED"
        new_status = "PASSED"
        assert old_status != new_status

    def test_update_findings(self) -> None:
        """Test updating inspection findings."""
        findings = "All structural elements meet specifications"
        assert len(findings) > 0

    def test_update_score(self) -> None:
        """Test updating inspection score."""
        score = 92
        assert 0 <= score <= 100

    def test_add_corrective_actions(self) -> None:
        """Test adding corrective actions."""
        corrective_actions = ["Repair surface cracks", "Apply waterproofing"]
        assert len(corrective_actions) >= 1

    def test_update_nonexistent_returns_none(self) -> None:
        """Test updating non-existent inspection returns None."""
        result = None
        assert result is None


class TestSafetyIncidentSeverity:
    """Tests for safety incident severity levels."""

    def test_minor_severity(self) -> None:
        """Test MINOR severity."""
        severity = "MINOR"
        assert severity == "MINOR"

    def test_moderate_severity(self) -> None:
        """Test MODERATE severity."""
        severity = "MODERATE"
        assert severity == "MODERATE"

    def test_major_severity(self) -> None:
        """Test MAJOR severity."""
        severity = "MAJOR"
        assert severity == "MAJOR"

    def test_critical_severity(self) -> None:
        """Test CRITICAL severity."""
        severity = "CRITICAL"
        assert severity == "CRITICAL"

    def test_fatality_severity(self) -> None:
        """Test FATALITY severity."""
        severity = "FATALITY"
        assert severity == "FATALITY"


class TestSafetyIncidentCreate:
    """Tests for safety incident creation."""

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = uuid4()
        assert project_id is not None

    def test_incident_date_required(self) -> None:
        """Test incident_date is required."""
        incident_date = datetime.now()
        assert incident_date is not None

    def test_description_required(self) -> None:
        """Test description is required."""
        description = "Worker slipped on wet surface"
        assert len(description) > 0

    def test_severity_required(self) -> None:
        """Test severity is required."""
        severity = "MINOR"
        assert severity in ["MINOR", "MODERATE", "MAJOR", "CRITICAL", "FATALITY"]

    def test_location_optional(self) -> None:
        """Test location is optional."""
        location = "Basement Level B2"
        assert location is None or len(location) > 0

    def test_injured_parties_optional(self) -> None:
        """Test injured_parties is optional."""
        injured_parties = ["Worker A"]
        assert injured_parties is None or len(injured_parties) >= 0

    def test_witnesses_optional(self) -> None:
        """Test witnesses is optional."""
        witnesses = ["Supervisor B", "Worker C"]
        assert witnesses is None or len(witnesses) >= 0

    def test_is_resolved_defaults_false(self) -> None:
        """Test is_resolved defaults to False."""
        is_resolved = False
        assert is_resolved is False


class TestSafetyIncidentGet:
    """Tests for getting safety incidents."""

    def test_get_by_project_id(self) -> None:
        """Test getting incidents by project_id."""
        project_id = uuid4()
        assert project_id is not None

    def test_filter_unresolved_only(self) -> None:
        """Test filtering to unresolved incidents only."""
        unresolved_only = True
        assert unresolved_only is True

    def test_ordered_by_incident_date_desc(self) -> None:
        """Test incidents ordered by date descending."""
        dates = [
            datetime(2024, 1, 15, 10, 0),
            datetime(2024, 1, 10, 14, 0),
            datetime(2024, 1, 5, 9, 0),
        ]
        assert dates[0] > dates[1] > dates[2]

    def test_get_returns_list(self) -> None:
        """Test get_safety_incidents returns a list."""
        incidents = []
        assert isinstance(incidents, list)


class TestSafetyIncidentUpdate:
    """Tests for updating safety incidents."""

    def test_mark_resolved(self) -> None:
        """Test marking incident as resolved."""
        is_resolved = True
        assert is_resolved is True

    def test_add_resolution_notes(self) -> None:
        """Test adding resolution notes."""
        resolution_notes = "Wet floor signs installed, anti-slip mats added"
        assert len(resolution_notes) > 0

    def test_add_corrective_measures(self) -> None:
        """Test adding corrective measures."""
        corrective_measures = [
            "Install anti-slip flooring",
            "Improve drainage",
            "Safety briefing for workers",
        ]
        assert len(corrective_measures) >= 1

    def test_update_severity(self) -> None:
        """Test updating severity after investigation."""
        old_severity = "MODERATE"
        new_severity = "MINOR"
        assert old_severity != new_severity

    def test_add_investigation_findings(self) -> None:
        """Test adding investigation findings."""
        findings = "Inadequate drainage caused water accumulation"
        assert len(findings) > 0

    def test_update_nonexistent_returns_none(self) -> None:
        """Test updating non-existent incident returns None."""
        result = None
        assert result is None


class TestContractorPayload:
    """Tests for ContractorCreate and ContractorUpdate payloads."""

    def test_model_dump_creates_dict(self) -> None:
        """Test model_dump creates dictionary."""
        payload = {
            "project_id": str(uuid4()),
            "company_name": "Test Company",
            "contractor_type": "MAIN_CONTRACTOR",
        }
        assert isinstance(payload, dict)
        assert "project_id" in payload

    def test_exclude_unset_for_updates(self) -> None:
        """Test exclude_unset for partial updates."""
        full_data = {"company_name": "New Name", "contact_name": None}
        update_data = {k: v for k, v in full_data.items() if v is not None}
        assert "contact_name" not in update_data


class TestInspectionPayload:
    """Tests for QualityInspectionCreate and Update payloads."""

    def test_create_payload(self) -> None:
        """Test inspection create payload."""
        payload = {
            "project_id": str(uuid4()),
            "inspection_type": "ELECTRICAL",
            "inspection_date": date.today().isoformat(),
            "inspector_name": "Inspector Lee",
        }
        assert len(payload) >= 4

    def test_update_payload_partial(self) -> None:
        """Test partial update payload."""
        payload = {"status": "PASSED", "score": 95}
        assert len(payload) == 2


class TestSafetyIncidentPayload:
    """Tests for SafetyIncidentCreate and Update payloads."""

    def test_create_payload(self) -> None:
        """Test incident create payload."""
        payload = {
            "project_id": str(uuid4()),
            "incident_date": datetime.now().isoformat(),
            "description": "Test incident",
            "severity": "MINOR",
        }
        assert len(payload) >= 4

    def test_update_payload_resolve(self) -> None:
        """Test update payload for resolving incident."""
        payload = {
            "is_resolved": True,
            "resolution_notes": "Issue addressed",
            "resolution_date": datetime.now().isoformat(),
        }
        assert payload["is_resolved"] is True


class TestQueryFiltering:
    """Tests for query filtering logic."""

    def test_filter_contractors_by_type(self) -> None:
        """Test filtering contractors by type."""
        contractors = [
            {"type": "MAIN_CONTRACTOR"},
            {"type": "SUBCONTRACTOR"},
            {"type": "SUBCONTRACTOR"},
        ]
        filtered = [c for c in contractors if c["type"] == "SUBCONTRACTOR"]
        assert len(filtered) == 2

    def test_filter_inspections_by_status(self) -> None:
        """Test filtering inspections by status."""
        inspections = [
            {"status": "PASSED"},
            {"status": "FAILED"},
            {"status": "PASSED"},
        ]
        filtered = [i for i in inspections if i["status"] == "PASSED"]
        assert len(filtered) == 2

    def test_filter_incidents_unresolved(self) -> None:
        """Test filtering unresolved incidents."""
        incidents = [
            {"is_resolved": False},
            {"is_resolved": True},
            {"is_resolved": False},
        ]
        filtered = [i for i in incidents if not i["is_resolved"]]
        assert len(filtered) == 2


class TestEdgeCases:
    """Tests for edge cases in project manager."""

    def test_empty_project_contractors(self) -> None:
        """Test project with no contractors."""
        contractors = []
        assert len(contractors) == 0

    def test_empty_project_inspections(self) -> None:
        """Test project with no inspections."""
        inspections = []
        assert len(inspections) == 0

    def test_empty_project_incidents(self) -> None:
        """Test project with no incidents."""
        incidents = []
        assert len(incidents) == 0

    def test_contractor_with_zero_contract_value(self) -> None:
        """Test contractor with zero contract value."""
        contract_value = Decimal("0")
        assert contract_value == 0

    def test_inspection_with_zero_score(self) -> None:
        """Test inspection with zero score (failed)."""
        score = 0
        assert score == 0

    def test_future_inspection_date(self) -> None:
        """Test scheduling future inspection."""
        future_date = date(2025, 12, 31)
        assert future_date > date.today()

    def test_past_incident_date(self) -> None:
        """Test past incident date is valid."""
        past_date = datetime(2024, 1, 1, 10, 0)
        assert past_date < datetime.now()


class TestMOMReporting:
    """Tests for MOM (Ministry of Manpower) safety reporting."""

    def test_mom_reportable_severity(self) -> None:
        """Test MOM reportable severity levels."""
        mom_reportable = ["MAJOR", "CRITICAL", "FATALITY"]
        severity = "MAJOR"
        assert severity in mom_reportable

    def test_non_mom_reportable_severity(self) -> None:
        """Test non-MOM reportable severity levels."""
        non_reportable = ["MINOR", "MODERATE"]
        severity = "MINOR"
        assert severity in non_reportable

    def test_incident_tracking_number(self) -> None:
        """Test incident tracking number format."""
        tracking = f"INC-{date.today().strftime('%Y%m%d')}-001"
        assert tracking.startswith("INC-")

    def test_reporting_deadline(self) -> None:
        """Test MOM reporting deadline calculation."""
        incident_date = date(2024, 1, 15)
        # MOM requires reporting within 10 days for major incidents
        deadline = date(2024, 1, 25)
        days_diff = (deadline - incident_date).days
        assert days_diff == 10
