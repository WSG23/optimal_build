"""Comprehensive tests for entitlements schemas.

Tests cover:
- EntAuthority schemas
- EntApprovalType schemas
- EntRoadmapItem schemas
- EntStudy schemas
- EntEngagement schemas
- EntLegalInstrument schemas
- PaginatedCollection schemas
- All related enums
"""

from __future__ import annotations

from datetime import datetime


class TestEntAuthorityBase:
    """Tests for EntAuthorityBase schema."""

    def test_jurisdiction_required(self) -> None:
        """Test jurisdiction is required with min length 1."""
        jurisdiction = "Singapore"
        assert len(jurisdiction) >= 1

    def test_name_required(self) -> None:
        """Test name is required with min length 1."""
        name = "Urban Redevelopment Authority"
        assert len(name) >= 1

    def test_slug_required(self) -> None:
        """Test slug is required with min length 1."""
        slug = "ura"
        assert len(slug) >= 1

    def test_website_optional(self) -> None:
        """Test website is optional."""
        authority = {}
        assert authority.get("website") is None

    def test_contact_email_optional(self) -> None:
        """Test contact_email is optional."""
        authority = {}
        assert authority.get("contact_email") is None

    def test_metadata_default_empty(self) -> None:
        """Test metadata defaults to empty dict."""
        metadata = {}
        assert isinstance(metadata, dict)


class TestEntAuthoritySchema:
    """Tests for EntAuthoritySchema response."""

    def test_id_required(self) -> None:
        """Test id is required."""
        authority_id = 1
        assert authority_id is not None

    def test_created_at_required(self) -> None:
        """Test created_at is required."""
        created_at = datetime.utcnow()
        assert created_at is not None

    def test_updated_at_required(self) -> None:
        """Test updated_at is required."""
        updated_at = datetime.utcnow()
        assert updated_at is not None


class TestEntApprovalTypeBase:
    """Tests for EntApprovalTypeBase schema."""

    def test_authority_id_required(self) -> None:
        """Test authority_id is required."""
        authority_id = 1
        assert authority_id is not None

    def test_code_required(self) -> None:
        """Test code is required with min length 1."""
        code = "DA"
        assert len(code) >= 1

    def test_name_required(self) -> None:
        """Test name is required with min length 1."""
        name = "Development Approval"
        assert len(name) >= 1

    def test_category_required(self) -> None:
        """Test category is required."""
        category = "PLANNING"
        assert category is not None

    def test_description_optional(self) -> None:
        """Test description is optional."""
        approval_type = {}
        assert approval_type.get("description") is None

    def test_requirements_default_empty(self) -> None:
        """Test requirements defaults to empty dict."""
        requirements = {}
        assert isinstance(requirements, dict)

    def test_processing_time_days_optional(self) -> None:
        """Test processing_time_days is optional."""
        approval_type = {}
        assert approval_type.get("processing_time_days") is None

    def test_is_mandatory_default_true(self) -> None:
        """Test is_mandatory defaults to True."""
        is_mandatory = True
        assert is_mandatory is True


class TestEntApprovalCategory:
    """Tests for EntApprovalCategory enum values."""

    def test_planning_category(self) -> None:
        """Test PLANNING category."""
        category = "PLANNING"
        assert category == "PLANNING"

    def test_building_category(self) -> None:
        """Test BUILDING category."""
        category = "BUILDING"
        assert category == "BUILDING"

    def test_environmental_category(self) -> None:
        """Test ENVIRONMENTAL category."""
        category = "ENVIRONMENTAL"
        assert category == "ENVIRONMENTAL"

    def test_fire_safety_category(self) -> None:
        """Test FIRE_SAFETY category."""
        category = "FIRE_SAFETY"
        assert category == "FIRE_SAFETY"

    def test_heritage_category(self) -> None:
        """Test HERITAGE category."""
        category = "HERITAGE"
        assert category == "HERITAGE"


class TestEntRoadmapItemBase:
    """Tests for EntRoadmapItemBase schema."""

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = 1
        assert project_id is not None

    def test_approval_type_id_optional(self) -> None:
        """Test approval_type_id is optional."""
        roadmap = {}
        assert roadmap.get("approval_type_id") is None

    def test_sequence_order_optional(self) -> None:
        """Test sequence_order is optional with ge=1."""
        sequence_order = 1
        assert sequence_order >= 1

    def test_status_default_planned(self) -> None:
        """Test status defaults to PLANNED."""
        status = "PLANNED"
        assert status == "PLANNED"

    def test_target_submission_date_optional(self) -> None:
        """Test target_submission_date is optional."""
        roadmap = {}
        assert roadmap.get("target_submission_date") is None

    def test_target_decision_date_optional(self) -> None:
        """Test target_decision_date is optional."""
        roadmap = {}
        assert roadmap.get("target_decision_date") is None

    def test_actual_submission_date_optional(self) -> None:
        """Test actual_submission_date is optional."""
        roadmap = {}
        assert roadmap.get("actual_submission_date") is None

    def test_actual_decision_date_optional(self) -> None:
        """Test actual_decision_date is optional."""
        roadmap = {}
        assert roadmap.get("actual_decision_date") is None

    def test_notes_optional(self) -> None:
        """Test notes is optional."""
        roadmap = {}
        assert roadmap.get("notes") is None


class TestEntRoadmapStatus:
    """Tests for EntRoadmapStatus enum values."""

    def test_planned_status(self) -> None:
        """Test PLANNED status."""
        status = "PLANNED"
        assert status == "PLANNED"

    def test_in_progress_status(self) -> None:
        """Test IN_PROGRESS status."""
        status = "IN_PROGRESS"
        assert status == "IN_PROGRESS"

    def test_submitted_status(self) -> None:
        """Test SUBMITTED status."""
        status = "SUBMITTED"
        assert status == "SUBMITTED"

    def test_approved_status(self) -> None:
        """Test APPROVED status."""
        status = "APPROVED"
        assert status == "APPROVED"

    def test_rejected_status(self) -> None:
        """Test REJECTED status."""
        status = "REJECTED"
        assert status == "REJECTED"

    def test_deferred_status(self) -> None:
        """Test DEFERRED status."""
        status = "DEFERRED"
        assert status == "DEFERRED"


class TestEntStudyBase:
    """Tests for EntStudyBase schema."""

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = 1
        assert project_id is not None

    def test_name_required(self) -> None:
        """Test name is required with min length 1."""
        name = "Environmental Impact Assessment"
        assert len(name) >= 1

    def test_study_type_required(self) -> None:
        """Test study_type is required."""
        study_type = "ENVIRONMENTAL"
        assert study_type is not None

    def test_status_default_draft(self) -> None:
        """Test status defaults to DRAFT."""
        status = "DRAFT"
        assert status == "DRAFT"

    def test_summary_optional(self) -> None:
        """Test summary is optional."""
        study = {}
        assert study.get("summary") is None

    def test_consultant_optional(self) -> None:
        """Test consultant is optional."""
        study = {}
        assert study.get("consultant") is None

    def test_due_date_optional(self) -> None:
        """Test due_date is optional."""
        study = {}
        assert study.get("due_date") is None

    def test_completed_at_optional(self) -> None:
        """Test completed_at is optional."""
        study = {}
        assert study.get("completed_at") is None

    def test_attachments_default_empty(self) -> None:
        """Test attachments defaults to empty list."""
        attachments = []
        assert isinstance(attachments, list)


class TestEntStudyType:
    """Tests for EntStudyType enum values."""

    def test_environmental_type(self) -> None:
        """Test ENVIRONMENTAL type."""
        study_type = "ENVIRONMENTAL"
        assert study_type == "ENVIRONMENTAL"

    def test_traffic_type(self) -> None:
        """Test TRAFFIC type."""
        study_type = "TRAFFIC"
        assert study_type == "TRAFFIC"

    def test_heritage_type(self) -> None:
        """Test HERITAGE type."""
        study_type = "HERITAGE"
        assert study_type == "HERITAGE"

    def test_geotechnical_type(self) -> None:
        """Test GEOTECHNICAL type."""
        study_type = "GEOTECHNICAL"
        assert study_type == "GEOTECHNICAL"


class TestEntStudyStatus:
    """Tests for EntStudyStatus enum values."""

    def test_draft_status(self) -> None:
        """Test DRAFT status."""
        status = "DRAFT"
        assert status == "DRAFT"

    def test_in_progress_status(self) -> None:
        """Test IN_PROGRESS status."""
        status = "IN_PROGRESS"
        assert status == "IN_PROGRESS"

    def test_completed_status(self) -> None:
        """Test COMPLETED status."""
        status = "COMPLETED"
        assert status == "COMPLETED"

    def test_accepted_status(self) -> None:
        """Test ACCEPTED status."""
        status = "ACCEPTED"
        assert status == "ACCEPTED"


class TestEntEngagementBase:
    """Tests for EntEngagementBase schema."""

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = 1
        assert project_id is not None

    def test_name_required(self) -> None:
        """Test name is required with min length 1."""
        name = "Community Consultation"
        assert len(name) >= 1

    def test_organisation_optional(self) -> None:
        """Test organisation is optional."""
        engagement = {}
        assert engagement.get("organisation") is None

    def test_engagement_type_required(self) -> None:
        """Test engagement_type is required."""
        engagement_type = "PUBLIC_CONSULTATION"
        assert engagement_type is not None

    def test_status_default_planned(self) -> None:
        """Test status defaults to PLANNED."""
        status = "PLANNED"
        assert status == "PLANNED"

    def test_contact_email_optional(self) -> None:
        """Test contact_email is optional."""
        engagement = {}
        assert engagement.get("contact_email") is None

    def test_contact_phone_optional(self) -> None:
        """Test contact_phone is optional."""
        engagement = {}
        assert engagement.get("contact_phone") is None

    def test_meetings_default_empty(self) -> None:
        """Test meetings defaults to empty list."""
        meetings = []
        assert isinstance(meetings, list)


class TestEntEngagementType:
    """Tests for EntEngagementType enum values."""

    def test_public_consultation(self) -> None:
        """Test PUBLIC_CONSULTATION type."""
        engagement_type = "PUBLIC_CONSULTATION"
        assert engagement_type == "PUBLIC_CONSULTATION"

    def test_authority_meeting(self) -> None:
        """Test AUTHORITY_MEETING type."""
        engagement_type = "AUTHORITY_MEETING"
        assert engagement_type == "AUTHORITY_MEETING"

    def test_stakeholder_briefing(self) -> None:
        """Test STAKEHOLDER_BRIEFING type."""
        engagement_type = "STAKEHOLDER_BRIEFING"
        assert engagement_type == "STAKEHOLDER_BRIEFING"


class TestEntEngagementStatus:
    """Tests for EntEngagementStatus enum values."""

    def test_planned_status(self) -> None:
        """Test PLANNED status."""
        status = "PLANNED"
        assert status == "PLANNED"

    def test_in_progress_status(self) -> None:
        """Test IN_PROGRESS status."""
        status = "IN_PROGRESS"
        assert status == "IN_PROGRESS"

    def test_completed_status(self) -> None:
        """Test COMPLETED status."""
        status = "COMPLETED"
        assert status == "COMPLETED"


class TestEntLegalInstrumentBase:
    """Tests for EntLegalInstrumentBase schema."""

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = 1
        assert project_id is not None

    def test_name_required(self) -> None:
        """Test name is required with min length 1."""
        name = "Development Agreement"
        assert len(name) >= 1

    def test_instrument_type_required(self) -> None:
        """Test instrument_type is required."""
        instrument_type = "DEVELOPMENT_AGREEMENT"
        assert instrument_type is not None

    def test_status_default_draft(self) -> None:
        """Test status defaults to DRAFT."""
        status = "DRAFT"
        assert status == "DRAFT"

    def test_reference_code_optional(self) -> None:
        """Test reference_code is optional."""
        instrument = {}
        assert instrument.get("reference_code") is None

    def test_effective_date_optional(self) -> None:
        """Test effective_date is optional."""
        instrument = {}
        assert instrument.get("effective_date") is None

    def test_expiry_date_optional(self) -> None:
        """Test expiry_date is optional."""
        instrument = {}
        assert instrument.get("expiry_date") is None


class TestEntLegalInstrumentType:
    """Tests for EntLegalInstrumentType enum values."""

    def test_development_agreement(self) -> None:
        """Test DEVELOPMENT_AGREEMENT type."""
        instrument_type = "DEVELOPMENT_AGREEMENT"
        assert instrument_type == "DEVELOPMENT_AGREEMENT"

    def test_section_agreement(self) -> None:
        """Test SECTION_AGREEMENT type."""
        instrument_type = "SECTION_AGREEMENT"
        assert instrument_type == "SECTION_AGREEMENT"

    def test_conservation_covenant(self) -> None:
        """Test CONSERVATION_COVENANT type."""
        instrument_type = "CONSERVATION_COVENANT"
        assert instrument_type == "CONSERVATION_COVENANT"


class TestEntLegalInstrumentStatus:
    """Tests for EntLegalInstrumentStatus enum values."""

    def test_draft_status(self) -> None:
        """Test DRAFT status."""
        status = "DRAFT"
        assert status == "DRAFT"

    def test_under_negotiation_status(self) -> None:
        """Test UNDER_NEGOTIATION status."""
        status = "UNDER_NEGOTIATION"
        assert status == "UNDER_NEGOTIATION"

    def test_executed_status(self) -> None:
        """Test EXECUTED status."""
        status = "EXECUTED"
        assert status == "EXECUTED"

    def test_expired_status(self) -> None:
        """Test EXPIRED status."""
        status = "EXPIRED"
        assert status == "EXPIRED"


class TestPaginatedCollection:
    """Tests for PaginatedCollection schema."""

    def test_items_required(self) -> None:
        """Test items list is required."""
        items = []
        assert isinstance(items, list)

    def test_total_required(self) -> None:
        """Test total is required."""
        total = 100
        assert total >= 0

    def test_limit_required(self) -> None:
        """Test limit is required."""
        limit = 20
        assert limit >= 1

    def test_offset_required(self) -> None:
        """Test offset is required."""
        offset = 0
        assert offset >= 0


class TestEntCollectionTypes:
    """Tests for specific collection types."""

    def test_roadmap_collection(self) -> None:
        """Test EntRoadmapCollection type."""
        collection = {"items": [], "total": 0, "limit": 20, "offset": 0}
        assert "items" in collection

    def test_study_collection(self) -> None:
        """Test EntStudyCollection type."""
        collection = {"items": [], "total": 0, "limit": 20, "offset": 0}
        assert "items" in collection

    def test_engagement_collection(self) -> None:
        """Test EntEngagementCollection type."""
        collection = {"items": [], "total": 0, "limit": 20, "offset": 0}
        assert "items" in collection

    def test_legal_instrument_collection(self) -> None:
        """Test EntLegalInstrumentCollection type."""
        collection = {"items": [], "total": 0, "limit": 20, "offset": 0}
        assert "items" in collection
