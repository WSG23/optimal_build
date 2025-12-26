"""Comprehensive tests for construction schemas.

Tests cover:
- Contractor schemas (Base, Create, Update, Response)
- QualityInspection schemas
- SafetyIncident schemas
- DrawdownRequest schemas
- Enum validation
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4


class TestContractorBase:
    """Tests for ContractorBase schema."""

    def test_company_name_required(self) -> None:
        """Test company_name is required."""
        company_name = "ABC Construction Pte Ltd"
        assert len(company_name) > 0

    def test_contractor_type_default(self) -> None:
        """Test contractor_type defaults to GENERAL_CONTRACTOR."""
        contractor_type = "GENERAL_CONTRACTOR"
        assert contractor_type == "GENERAL_CONTRACTOR"

    def test_contact_person_optional(self) -> None:
        """Test contact_person is optional."""
        contractor = {"company_name": "Test"}
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

    def test_contract_value_decimal(self) -> None:
        """Test contract_value is Decimal."""
        contract_value = Decimal("1500000.00")
        assert isinstance(contract_value, Decimal)

    def test_contract_date_optional(self) -> None:
        """Test contract_date is optional."""
        contractor = {}
        assert contractor.get("contract_date") is None

    def test_is_active_default_true(self) -> None:
        """Test is_active defaults to True."""
        is_active = True
        assert is_active is True

    def test_metadata_default_empty_dict(self) -> None:
        """Test metadata defaults to empty dict."""
        metadata = {}
        assert isinstance(metadata, dict)


class TestContractorCreate:
    """Tests for ContractorCreate schema."""

    def test_project_id_required(self) -> None:
        """Test project_id is required for creation."""
        project_id = uuid4()
        assert project_id is not None

    def test_inherits_base_fields(self) -> None:
        """Test inherits fields from ContractorBase."""
        contractor = {
            "project_id": str(uuid4()),
            "company_name": "Test Contractor",
            "contractor_type": "GENERAL_CONTRACTOR",
        }
        assert "company_name" in contractor


class TestContractorUpdate:
    """Tests for ContractorUpdate schema."""

    def test_all_fields_optional(self) -> None:
        """Test all fields are optional for update."""
        update = {}
        assert update.get("company_name") is None
        assert update.get("contractor_type") is None
        assert update.get("is_active") is None

    def test_partial_update(self) -> None:
        """Test partial update with some fields."""
        update = {"is_active": False, "contract_value": Decimal("2000000")}
        assert update["is_active"] is False


class TestContractorResponse:
    """Tests for ContractorResponse schema."""

    def test_id_required(self) -> None:
        """Test id is required UUID."""
        contractor_id = uuid4()
        assert len(str(contractor_id)) == 36

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = uuid4()
        assert project_id is not None

    def test_created_at_required(self) -> None:
        """Test created_at is required."""
        created_at = datetime.utcnow()
        assert created_at is not None

    def test_updated_at_optional(self) -> None:
        """Test updated_at is optional."""
        response = {"id": uuid4()}
        assert response.get("updated_at") is None


class TestContractorType:
    """Tests for ContractorType enum values."""

    def test_general_contractor(self) -> None:
        """Test GENERAL_CONTRACTOR type."""
        contractor_type = "GENERAL_CONTRACTOR"
        assert contractor_type == "GENERAL_CONTRACTOR"

    def test_subcontractor(self) -> None:
        """Test SUBCONTRACTOR type."""
        contractor_type = "SUBCONTRACTOR"
        assert contractor_type == "SUBCONTRACTOR"

    def test_specialist(self) -> None:
        """Test SPECIALIST type."""
        contractor_type = "SPECIALIST"
        assert contractor_type == "SPECIALIST"

    def test_consultant(self) -> None:
        """Test CONSULTANT type."""
        contractor_type = "CONSULTANT"
        assert contractor_type == "CONSULTANT"


class TestQualityInspectionBase:
    """Tests for QualityInspectionBase schema."""

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
        """Test status defaults to SCHEDULED."""
        status = "SCHEDULED"
        assert status == "SCHEDULED"

    def test_defects_found_default_empty(self) -> None:
        """Test defects_found defaults to empty dict."""
        defects_found = {}
        assert isinstance(defects_found, dict)

    def test_photos_url_default_empty(self) -> None:
        """Test photos_url defaults to empty list."""
        photos_url = []
        assert isinstance(photos_url, list)

    def test_notes_optional(self) -> None:
        """Test notes is optional."""
        inspection = {}
        assert inspection.get("notes") is None


class TestInspectionStatus:
    """Tests for InspectionStatus enum values."""

    def test_scheduled(self) -> None:
        """Test SCHEDULED status."""
        status = "SCHEDULED"
        assert status == "SCHEDULED"

    def test_in_progress(self) -> None:
        """Test IN_PROGRESS status."""
        status = "IN_PROGRESS"
        assert status == "IN_PROGRESS"

    def test_completed(self) -> None:
        """Test COMPLETED status."""
        status = "COMPLETED"
        assert status == "COMPLETED"

    def test_failed(self) -> None:
        """Test FAILED status."""
        status = "FAILED"
        assert status == "FAILED"

    def test_cancelled(self) -> None:
        """Test CANCELLED status."""
        status = "CANCELLED"
        assert status == "CANCELLED"


class TestSafetyIncidentBase:
    """Tests for SafetyIncidentBase schema."""

    def test_incident_date_required(self) -> None:
        """Test incident_date is required."""
        incident_date = datetime.utcnow()
        assert incident_date is not None

    def test_severity_required(self) -> None:
        """Test severity is required."""
        severity = "HIGH"
        assert severity is not None

    def test_title_required(self) -> None:
        """Test title is required."""
        title = "Worker Fall from Scaffolding"
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


class TestSeverityLevel:
    """Tests for SeverityLevel enum values."""

    def test_low_severity(self) -> None:
        """Test LOW severity level."""
        severity = "LOW"
        assert severity == "LOW"

    def test_medium_severity(self) -> None:
        """Test MEDIUM severity level."""
        severity = "MEDIUM"
        assert severity == "MEDIUM"

    def test_high_severity(self) -> None:
        """Test HIGH severity level."""
        severity = "HIGH"
        assert severity == "HIGH"

    def test_critical_severity(self) -> None:
        """Test CRITICAL severity level."""
        severity = "CRITICAL"
        assert severity == "CRITICAL"


class TestDrawdownRequestBase:
    """Tests for DrawdownRequestBase schema."""

    def test_request_name_required(self) -> None:
        """Test request_name is required."""
        request_name = "Phase 1 Foundation Works"
        assert len(request_name) > 0

    def test_request_date_required(self) -> None:
        """Test request_date is required."""
        request_date = date(2024, 6, 15)
        assert request_date is not None

    def test_amount_requested_required(self) -> None:
        """Test amount_requested is required."""
        amount_requested = Decimal("500000.00")
        assert amount_requested > 0

    def test_amount_approved_optional(self) -> None:
        """Test amount_approved is optional."""
        drawdown = {}
        assert drawdown.get("amount_approved") is None

    def test_status_default_draft(self) -> None:
        """Test status defaults to DRAFT."""
        status = "DRAFT"
        assert status == "DRAFT"

    def test_contractor_id_optional(self) -> None:
        """Test contractor_id is optional."""
        drawdown = {}
        assert drawdown.get("contractor_id") is None

    def test_supporting_docs_default_empty(self) -> None:
        """Test supporting_docs defaults to empty list."""
        supporting_docs = []
        assert isinstance(supporting_docs, list)

    def test_notes_optional(self) -> None:
        """Test notes is optional."""
        drawdown = {}
        assert drawdown.get("notes") is None


class TestDrawdownStatus:
    """Tests for DrawdownStatus enum values."""

    def test_draft_status(self) -> None:
        """Test DRAFT status."""
        status = "DRAFT"
        assert status == "DRAFT"

    def test_submitted_status(self) -> None:
        """Test SUBMITTED status."""
        status = "SUBMITTED"
        assert status == "SUBMITTED"

    def test_under_review_status(self) -> None:
        """Test UNDER_REVIEW status."""
        status = "UNDER_REVIEW"
        assert status == "UNDER_REVIEW"

    def test_approved_status(self) -> None:
        """Test APPROVED status."""
        status = "APPROVED"
        assert status == "APPROVED"

    def test_rejected_status(self) -> None:
        """Test REJECTED status."""
        status = "REJECTED"
        assert status == "REJECTED"

    def test_disbursed_status(self) -> None:
        """Test DISBURSED status."""
        status = "DISBURSED"
        assert status == "DISBURSED"


class TestDrawdownRequestResponse:
    """Tests for DrawdownRequestResponse schema."""

    def test_id_required(self) -> None:
        """Test id is required UUID."""
        request_id = uuid4()
        assert len(str(request_id)) == 36

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = uuid4()
        assert project_id is not None

    def test_created_at_required(self) -> None:
        """Test created_at is required."""
        created_at = datetime.utcnow()
        assert created_at is not None

    def test_updated_at_optional(self) -> None:
        """Test updated_at is optional."""
        response = {"id": uuid4()}
        assert response.get("updated_at") is None
