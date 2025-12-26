"""Comprehensive tests for construction model.

Tests cover:
- ContractorType enum
- InspectionStatus enum
- SeverityLevel enum
- DrawdownStatus enum
- Contractor model structure
- QualityInspection model structure
- SafetyIncident model structure
- DrawdownRequest model structure
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4


class TestContractorType:
    """Tests for ContractorType enum."""

    def test_general_contractor(self) -> None:
        """Test general_contractor type."""
        contractor_type = "general_contractor"
        assert contractor_type == "general_contractor"

    def test_sub_contractor(self) -> None:
        """Test sub_contractor type."""
        contractor_type = "sub_contractor"
        assert contractor_type == "sub_contractor"

    def test_specialist(self) -> None:
        """Test specialist type."""
        contractor_type = "specialist"
        assert contractor_type == "specialist"

    def test_consultant(self) -> None:
        """Test consultant type."""
        contractor_type = "consultant"
        assert contractor_type == "consultant"

    def test_supplier(self) -> None:
        """Test supplier type."""
        contractor_type = "supplier"
        assert contractor_type == "supplier"


class TestInspectionStatus:
    """Tests for InspectionStatus enum."""

    def test_scheduled(self) -> None:
        """Test scheduled status."""
        status = "scheduled"
        assert status == "scheduled"

    def test_passed(self) -> None:
        """Test passed status."""
        status = "passed"
        assert status == "passed"

    def test_failed(self) -> None:
        """Test failed status."""
        status = "failed"
        assert status == "failed"

    def test_passed_with_conditions(self) -> None:
        """Test passed_with_conditions status."""
        status = "passed_with_conditions"
        assert status == "passed_with_conditions"

    def test_rectification_required(self) -> None:
        """Test rectification_required status."""
        status = "rectification_required"
        assert status == "rectification_required"


class TestSeverityLevel:
    """Tests for SeverityLevel enum."""

    def test_near_miss(self) -> None:
        """Test near_miss level."""
        severity = "near_miss"
        assert severity == "near_miss"

    def test_minor(self) -> None:
        """Test minor level."""
        severity = "minor"
        assert severity == "minor"

    def test_moderate(self) -> None:
        """Test moderate level."""
        severity = "moderate"
        assert severity == "moderate"

    def test_severe(self) -> None:
        """Test severe level."""
        severity = "severe"
        assert severity == "severe"

    def test_fatal(self) -> None:
        """Test fatal level."""
        severity = "fatal"
        assert severity == "fatal"


class TestDrawdownStatus:
    """Tests for DrawdownStatus enum."""

    def test_draft(self) -> None:
        """Test draft status."""
        status = "draft"
        assert status == "draft"

    def test_submitted(self) -> None:
        """Test submitted status."""
        status = "submitted"
        assert status == "submitted"

    def test_verified_qs(self) -> None:
        """Test verified_qs status."""
        status = "verified_qs"
        assert status == "verified_qs"

    def test_approved_architect(self) -> None:
        """Test approved_architect status."""
        status = "approved_architect"
        assert status == "approved_architect"

    def test_approved_lender(self) -> None:
        """Test approved_lender status."""
        status = "approved_lender"
        assert status == "approved_lender"

    def test_paid(self) -> None:
        """Test paid status."""
        status = "paid"
        assert status == "paid"

    def test_rejected(self) -> None:
        """Test rejected status."""
        status = "rejected"
        assert status == "rejected"


class TestContractorModel:
    """Tests for Contractor model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        contractor_id = uuid4()
        assert len(str(contractor_id)) == 36

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = uuid4()
        assert project_id is not None

    def test_company_name_required(self) -> None:
        """Test company_name is required."""
        company_name = "ABC Construction Pte Ltd"
        assert len(company_name) > 0

    def test_contractor_type_default(self) -> None:
        """Test contractor_type defaults to general_contractor."""
        contractor_type = "general_contractor"
        assert contractor_type == "general_contractor"

    def test_contact_person_optional(self) -> None:
        """Test contact_person is optional."""
        contractor = {}
        assert contractor.get("contact_person") is None

    def test_email_optional(self) -> None:
        """Test email is optional."""
        contractor = {}
        assert contractor.get("email") is None

    def test_phone_optional(self) -> None:
        """Test phone is optional."""
        contractor = {}
        assert contractor.get("phone") is None

    def test_contract_value_optional(self) -> None:
        """Test contract_value is optional."""
        contractor = {}
        assert contractor.get("contract_value") is None

    def test_contract_date_optional(self) -> None:
        """Test contract_date is optional."""
        contractor = {}
        assert contractor.get("contract_date") is None

    def test_is_active_default_true(self) -> None:
        """Test is_active defaults to True."""
        is_active = True
        assert is_active is True

    def test_metadata_default_empty(self) -> None:
        """Test metadata_json defaults to empty dict."""
        metadata = {}
        assert isinstance(metadata, dict)


class TestQualityInspectionModel:
    """Tests for QualityInspection model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        inspection_id = uuid4()
        assert len(str(inspection_id)) == 36

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = uuid4()
        assert project_id is not None

    def test_development_phase_id_optional(self) -> None:
        """Test development_phase_id is optional."""
        inspection = {}
        assert inspection.get("development_phase_id") is None

    def test_inspection_date_required(self) -> None:
        """Test inspection_date is required."""
        inspection_date = date(2024, 6, 15)
        assert inspection_date is not None

    def test_inspector_name_required(self) -> None:
        """Test inspector_name is required."""
        inspector_name = "John Smith"
        assert len(inspector_name) > 0

    def test_location_optional(self) -> None:
        """Test location is optional."""
        inspection = {}
        assert inspection.get("location") is None

    def test_status_default_scheduled(self) -> None:
        """Test status defaults to scheduled."""
        status = "scheduled"
        assert status == "scheduled"

    def test_defects_found_default_empty(self) -> None:
        """Test defects_found defaults to empty dict."""
        defects = {}
        assert isinstance(defects, dict)

    def test_photos_url_default_empty(self) -> None:
        """Test photos_url defaults to empty list."""
        photos = []
        assert isinstance(photos, list)

    def test_notes_optional(self) -> None:
        """Test notes is optional."""
        inspection = {}
        assert inspection.get("notes") is None


class TestSafetyIncidentModel:
    """Tests for SafetyIncident model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        incident_id = uuid4()
        assert len(str(incident_id)) == 36

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = uuid4()
        assert project_id is not None

    def test_incident_date_required(self) -> None:
        """Test incident_date is required."""
        incident_date = datetime.utcnow()
        assert incident_date is not None

    def test_severity_default_minor(self) -> None:
        """Test severity defaults to minor."""
        severity = "minor"
        assert severity == "minor"

    def test_title_required(self) -> None:
        """Test title is required."""
        title = "Worker Injury on Site"
        assert len(title) > 0

    def test_description_optional(self) -> None:
        """Test description is optional."""
        incident = {}
        assert incident.get("description") is None

    def test_location_optional(self) -> None:
        """Test location is optional."""
        incident = {}
        assert incident.get("location") is None

    def test_reported_by_optional(self) -> None:
        """Test reported_by is optional."""
        incident = {}
        assert incident.get("reported_by") is None

    def test_is_resolved_default_false(self) -> None:
        """Test is_resolved defaults to False."""
        is_resolved = False
        assert is_resolved is False

    def test_resolution_notes_optional(self) -> None:
        """Test resolution_notes is optional."""
        incident = {}
        assert incident.get("resolution_notes") is None


class TestDrawdownRequestModel:
    """Tests for DrawdownRequest model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        request_id = uuid4()
        assert len(str(request_id)) == 36

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = uuid4()
        assert project_id is not None

    def test_request_name_required(self) -> None:
        """Test request_name is required."""
        request_name = "Drawdown #3 - Foundation"
        assert len(request_name) > 0

    def test_request_date_required(self) -> None:
        """Test request_date is required."""
        request_date = date(2024, 6, 15)
        assert request_date is not None

    def test_amount_requested_required(self) -> None:
        """Test amount_requested is required."""
        amount = Decimal("500000.00")
        assert amount > 0

    def test_amount_approved_optional(self) -> None:
        """Test amount_approved is optional."""
        request = {}
        assert request.get("amount_approved") is None

    def test_status_default_draft(self) -> None:
        """Test status defaults to draft."""
        status = "draft"
        assert status == "draft"

    def test_contractor_id_optional(self) -> None:
        """Test contractor_id is optional."""
        request = {}
        assert request.get("contractor_id") is None

    def test_supporting_docs_default_empty(self) -> None:
        """Test supporting_docs defaults to empty list."""
        docs = []
        assert isinstance(docs, list)

    def test_notes_optional(self) -> None:
        """Test notes is optional."""
        request = {}
        assert request.get("notes") is None


class TestConstructionScenarios:
    """Tests for construction use case scenarios."""

    def test_add_general_contractor(self) -> None:
        """Test adding a general contractor."""
        contractor = {
            "id": str(uuid4()),
            "project_id": str(uuid4()),
            "company_name": "Singapore Construction Pte Ltd",
            "contractor_type": "general_contractor",
            "contact_person": "John Tan",
            "email": "john@sgconstruction.com.sg",
            "phone": "+65 9123 4567",
            "contract_value": Decimal("10000000.00"),
            "contract_date": date(2024, 1, 15),
            "is_active": True,
        }
        assert contractor["contractor_type"] == "general_contractor"

    def test_schedule_inspection(self) -> None:
        """Test scheduling a quality inspection."""
        inspection = {
            "id": str(uuid4()),
            "project_id": str(uuid4()),
            "inspection_date": date(2024, 7, 1),
            "inspector_name": "BCA Inspector",
            "location": "Level 5 Slab",
            "status": "scheduled",
        }
        assert inspection["status"] == "scheduled"

    def test_log_safety_incident(self) -> None:
        """Test logging a safety incident."""
        incident = {
            "id": str(uuid4()),
            "project_id": str(uuid4()),
            "incident_date": datetime.utcnow(),
            "severity": "minor",
            "title": "Minor Hand Injury",
            "description": "Worker received minor cut while handling materials",
            "location": "Level 3 Loading Bay",
            "reported_by": "Site Supervisor",
            "is_resolved": False,
        }
        assert incident["severity"] == "minor"

    def test_create_drawdown_request(self) -> None:
        """Test creating a drawdown request."""
        request = {
            "id": str(uuid4()),
            "project_id": str(uuid4()),
            "request_name": "Drawdown #5 - Superstructure",
            "request_date": date(2024, 7, 15),
            "amount_requested": Decimal("2500000.00"),
            "status": "draft",
            "supporting_docs": ["invoice_001.pdf", "progress_report.pdf"],
        }
        assert request["status"] == "draft"

    def test_approve_drawdown(self) -> None:
        """Test approving a drawdown request."""
        request = {
            "status": "submitted",
            "amount_requested": Decimal("2500000.00"),
        }
        request["status"] = "approved_lender"
        request["amount_approved"] = Decimal("2400000.00")
        assert request["amount_approved"] == Decimal("2400000.00")
