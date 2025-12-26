"""Comprehensive tests for Entitlements models.

Tests cover:
- All entitlements enums (5 categories)
- EntAuthority, EntApprovalType, EntRoadmapItem, EntStudy, EntEngagement, EntLegalInstrument
- Status transitions
- Date handling
- JSON/metadata fields
"""

from __future__ import annotations

from datetime import date


from app.models.entitlements import (
    EntApprovalCategory,
    EntApprovalType,
    EntAuthority,
    EntEngagement,
    EntEngagementStatus,
    EntEngagementType,
    EntLegalInstrument,
    EntLegalInstrumentStatus,
    EntLegalInstrumentType,
    EntRoadmapItem,
    EntRoadmapStatus,
    EntStudy,
    EntStudyStatus,
    EntStudyType,
)


class TestEntApprovalCategoryEnum:
    """Tests for EntApprovalCategory enum."""

    def test_all_categories_defined(self) -> None:
        """All expected categories should be defined."""
        expected = ["PLANNING", "BUILDING", "ENVIRONMENTAL", "TRANSPORT", "UTILITIES"]
        actual = [c.name for c in EntApprovalCategory]
        assert sorted(actual) == sorted(expected)

    def test_category_values(self) -> None:
        """Category values should be lowercase."""
        assert EntApprovalCategory.PLANNING.value == "planning"
        assert EntApprovalCategory.BUILDING.value == "building"
        assert EntApprovalCategory.ENVIRONMENTAL.value == "environmental"


class TestEntRoadmapStatusEnum:
    """Tests for EntRoadmapStatus enum."""

    def test_all_statuses_defined(self) -> None:
        """All expected statuses should be defined."""
        expected = [
            "PLANNED",
            "IN_PROGRESS",
            "SUBMITTED",
            "APPROVED",
            "REJECTED",
            "BLOCKED",
            "COMPLETE",
        ]
        actual = [s.name for s in EntRoadmapStatus]
        assert sorted(actual) == sorted(expected)

    def test_status_values(self) -> None:
        """Status values should be lowercase with underscores."""
        assert EntRoadmapStatus.PLANNED.value == "planned"
        assert EntRoadmapStatus.IN_PROGRESS.value == "in_progress"
        assert EntRoadmapStatus.COMPLETE.value == "complete"


class TestEntStudyTypeEnum:
    """Tests for EntStudyType enum."""

    def test_all_types_defined(self) -> None:
        """All expected study types should be defined."""
        expected = ["TRAFFIC", "ENVIRONMENTAL", "HERITAGE", "UTILITIES", "COMMUNITY"]
        actual = [t.name for t in EntStudyType]
        assert sorted(actual) == sorted(expected)


class TestEntStudyStatusEnum:
    """Tests for EntStudyStatus enum."""

    def test_all_statuses_defined(self) -> None:
        """All expected statuses should be defined."""
        expected = [
            "DRAFT",
            "SCOPE_DEFINED",
            "IN_PROGRESS",
            "SUBMITTED",
            "ACCEPTED",
            "REJECTED",
        ]
        actual = [s.name for s in EntStudyStatus]
        assert sorted(actual) == sorted(expected)


class TestEntEngagementTypeEnum:
    """Tests for EntEngagementType enum."""

    def test_all_types_defined(self) -> None:
        """All expected engagement types should be defined."""
        expected = ["AGENCY", "COMMUNITY", "POLITICAL", "PRIVATE_PARTNER", "REGULATOR"]
        actual = [t.name for t in EntEngagementType]
        assert sorted(actual) == sorted(expected)


class TestEntEngagementStatusEnum:
    """Tests for EntEngagementStatus enum."""

    def test_all_statuses_defined(self) -> None:
        """All expected statuses should be defined."""
        expected = ["PLANNED", "ACTIVE", "COMPLETED", "BLOCKED"]
        actual = [s.name for s in EntEngagementStatus]
        assert sorted(actual) == sorted(expected)


class TestEntLegalInstrumentTypeEnum:
    """Tests for EntLegalInstrumentType enum."""

    def test_all_types_defined(self) -> None:
        """All expected instrument types should be defined."""
        expected = ["AGREEMENT", "LICENCE", "MEMORANDUM", "WAIVER", "VARIATION"]
        actual = [t.name for t in EntLegalInstrumentType]
        assert sorted(actual) == sorted(expected)


class TestEntLegalInstrumentStatusEnum:
    """Tests for EntLegalInstrumentStatus enum."""

    def test_all_statuses_defined(self) -> None:
        """All expected statuses should be defined."""
        expected = ["DRAFT", "IN_REVIEW", "EXECUTED", "EXPIRED"]
        actual = [s.name for s in EntLegalInstrumentStatus]
        assert sorted(actual) == sorted(expected)


class TestEntAuthority:
    """Tests for EntAuthority model."""

    def test_create_authority(self) -> None:
        """Authority with required fields should be valid."""
        authority = EntAuthority(
            jurisdiction="SG",
            name="Urban Redevelopment Authority",
            slug="ura-sg",
        )
        assert authority.jurisdiction == "SG"
        assert authority.name == "Urban Redevelopment Authority"
        assert authority.slug == "ura-sg"

    def test_authority_with_contact(self) -> None:
        """Authority with contact info."""
        authority = EntAuthority(
            jurisdiction="SG",
            name="BCA",
            slug="bca-sg",
            website="https://www.bca.gov.sg",
            contact_email="info@bca.gov.sg",
        )
        assert authority.website == "https://www.bca.gov.sg"
        assert authority.contact_email == "info@bca.gov.sg"

    def test_authority_metadata(self) -> None:
        """Authority with metadata JSON."""
        authority = EntAuthority(
            jurisdiction="SG",
            name="Test",
            slug="test",
            metadata_json={"region": "central", "priority": "high"},
        )
        assert authority.metadata_json["region"] == "central"


class TestEntApprovalType:
    """Tests for EntApprovalType model."""

    def test_create_approval_type(self) -> None:
        """ApprovalType with required fields."""
        approval_type = EntApprovalType(
            authority_id=1,
            code="PP",
            name="Planning Permission",
            category=EntApprovalCategory.PLANNING,
        )
        assert approval_type.code == "PP"
        assert approval_type.category == EntApprovalCategory.PLANNING

    def test_approval_type_with_details(self) -> None:
        """ApprovalType with all details."""
        approval_type = EntApprovalType(
            authority_id=1,
            code="BP",
            name="Building Plan",
            category=EntApprovalCategory.BUILDING,
            description="Building plan approval for new construction",
            requirements={"documents": ["floor_plan", "elevation"]},
            processing_time_days=30,
            is_mandatory=True,
        )
        assert approval_type.processing_time_days == 30
        assert approval_type.is_mandatory is True
        assert "floor_plan" in approval_type.requirements["documents"]


class TestEntRoadmapItem:
    """Tests for EntRoadmapItem model."""

    def test_create_roadmap_item(self) -> None:
        """RoadmapItem with required fields."""
        item = EntRoadmapItem(
            project_id=1,
            sequence_order=1,
            status=EntRoadmapStatus.PLANNED,
        )
        assert item.project_id == 1
        assert item.sequence_order == 1
        assert item.status == EntRoadmapStatus.PLANNED

    def test_roadmap_item_with_dates(self) -> None:
        """RoadmapItem with target and actual dates."""
        item = EntRoadmapItem(
            project_id=1,
            sequence_order=2,
            status=EntRoadmapStatus.SUBMITTED,
            target_submission_date=date(2024, 3, 1),
            target_decision_date=date(2024, 4, 15),
            actual_submission_date=date(2024, 3, 5),
            actual_decision_date=None,
        )
        assert item.target_submission_date == date(2024, 3, 1)
        assert item.actual_submission_date == date(2024, 3, 5)
        assert item.actual_decision_date is None

    def test_roadmap_item_with_notes(self) -> None:
        """RoadmapItem with notes."""
        item = EntRoadmapItem(
            project_id=1,
            sequence_order=1,
            status=EntRoadmapStatus.IN_PROGRESS,
            notes="Awaiting environmental study completion",
        )
        assert "environmental" in item.notes

    def test_roadmap_status_transitions(self) -> None:
        """Test various status values."""
        statuses = [
            EntRoadmapStatus.PLANNED,
            EntRoadmapStatus.IN_PROGRESS,
            EntRoadmapStatus.SUBMITTED,
            EntRoadmapStatus.APPROVED,
            EntRoadmapStatus.REJECTED,
            EntRoadmapStatus.BLOCKED,
            EntRoadmapStatus.COMPLETE,
        ]
        for status in statuses:
            item = EntRoadmapItem(
                project_id=1,
                sequence_order=1,
                status=status,
            )
            assert item.status == status


class TestEntStudy:
    """Tests for EntStudy model."""

    def test_create_study(self) -> None:
        """Study with required fields."""
        study = EntStudy(
            project_id=1,
            name="Traffic Impact Assessment",
            study_type=EntStudyType.TRAFFIC,
            status=EntStudyStatus.DRAFT,
        )
        assert study.name == "Traffic Impact Assessment"
        assert study.study_type == EntStudyType.TRAFFIC
        assert study.status == EntStudyStatus.DRAFT

    def test_study_with_consultant(self) -> None:
        """Study with consultant info."""
        study = EntStudy(
            project_id=1,
            name="Environmental Study",
            study_type=EntStudyType.ENVIRONMENTAL,
            status=EntStudyStatus.IN_PROGRESS,
            consultant="Green Consultants Pte Ltd",
            due_date=date(2024, 6, 30),
        )
        assert study.consultant == "Green Consultants Pte Ltd"
        assert study.due_date == date(2024, 6, 30)

    def test_study_with_attachments(self) -> None:
        """Study with attachments JSON."""
        study = EntStudy(
            project_id=1,
            name="Heritage Assessment",
            study_type=EntStudyType.HERITAGE,
            status=EntStudyStatus.SUBMITTED,
            attachments=[
                {"name": "report.pdf", "url": "s3://bucket/report.pdf"},
                {"name": "photos.zip", "url": "s3://bucket/photos.zip"},
            ],
        )
        assert len(study.attachments) == 2

    def test_study_status_transitions(self) -> None:
        """Test various study statuses."""
        statuses = [
            EntStudyStatus.DRAFT,
            EntStudyStatus.SCOPE_DEFINED,
            EntStudyStatus.IN_PROGRESS,
            EntStudyStatus.SUBMITTED,
            EntStudyStatus.ACCEPTED,
            EntStudyStatus.REJECTED,
        ]
        for status in statuses:
            study = EntStudy(
                project_id=1,
                name="Test",
                study_type=EntStudyType.TRAFFIC,
                status=status,
            )
            assert study.status == status


class TestEntEngagement:
    """Tests for EntEngagement model."""

    def test_create_engagement(self) -> None:
        """Engagement with required fields."""
        engagement = EntEngagement(
            project_id=1,
            name="Community Consultation",
            engagement_type=EntEngagementType.COMMUNITY,
            status=EntEngagementStatus.PLANNED,
        )
        assert engagement.name == "Community Consultation"
        assert engagement.engagement_type == EntEngagementType.COMMUNITY

    def test_engagement_with_organisation(self) -> None:
        """Engagement with organisation details."""
        engagement = EntEngagement(
            project_id=1,
            name="Agency Meeting",
            organisation="Urban Redevelopment Authority",
            engagement_type=EntEngagementType.AGENCY,
            status=EntEngagementStatus.ACTIVE,
            contact_email="contact@ura.gov.sg",
            contact_phone="+65 6223 4811",
        )
        assert engagement.organisation == "Urban Redevelopment Authority"
        assert engagement.contact_email == "contact@ura.gov.sg"

    def test_engagement_with_meetings(self) -> None:
        """Engagement with meetings JSON."""
        engagement = EntEngagement(
            project_id=1,
            name="Regulator Meetings",
            engagement_type=EntEngagementType.REGULATOR,
            status=EntEngagementStatus.ACTIVE,
            meetings=[
                {"date": "2024-01-15", "outcome": "positive", "attendees": 5},
                {"date": "2024-02-20", "outcome": "pending", "attendees": 8},
            ],
        )
        assert len(engagement.meetings) == 2
        assert engagement.meetings[0]["outcome"] == "positive"

    def test_engagement_types(self) -> None:
        """Test all engagement types."""
        types = [
            EntEngagementType.AGENCY,
            EntEngagementType.COMMUNITY,
            EntEngagementType.POLITICAL,
            EntEngagementType.PRIVATE_PARTNER,
            EntEngagementType.REGULATOR,
        ]
        for etype in types:
            engagement = EntEngagement(
                project_id=1,
                name="Test",
                engagement_type=etype,
                status=EntEngagementStatus.PLANNED,
            )
            assert engagement.engagement_type == etype


class TestEntLegalInstrument:
    """Tests for EntLegalInstrument model."""

    def test_create_legal_instrument(self) -> None:
        """LegalInstrument with required fields."""
        instrument = EntLegalInstrument(
            project_id=1,
            name="Development Agreement",
            instrument_type=EntLegalInstrumentType.AGREEMENT,
            status=EntLegalInstrumentStatus.DRAFT,
        )
        assert instrument.name == "Development Agreement"
        assert instrument.instrument_type == EntLegalInstrumentType.AGREEMENT

    def test_legal_instrument_with_dates(self) -> None:
        """LegalInstrument with dates."""
        instrument = EntLegalInstrument(
            project_id=1,
            name="Building Licence",
            instrument_type=EntLegalInstrumentType.LICENCE,
            status=EntLegalInstrumentStatus.EXECUTED,
            reference_code="LIC-2024-001",
            effective_date=date(2024, 1, 1),
            expiry_date=date(2026, 12, 31),
        )
        assert instrument.reference_code == "LIC-2024-001"
        assert instrument.effective_date == date(2024, 1, 1)
        assert instrument.expiry_date == date(2026, 12, 31)

    def test_legal_instrument_with_attachments(self) -> None:
        """LegalInstrument with attachments."""
        instrument = EntLegalInstrument(
            project_id=1,
            name="MOU",
            instrument_type=EntLegalInstrumentType.MEMORANDUM,
            status=EntLegalInstrumentStatus.EXECUTED,
            attachments=[
                {"name": "signed_mou.pdf", "url": "s3://bucket/mou.pdf"},
            ],
        )
        assert len(instrument.attachments) == 1

    def test_legal_instrument_types(self) -> None:
        """Test all instrument types."""
        types = [
            EntLegalInstrumentType.AGREEMENT,
            EntLegalInstrumentType.LICENCE,
            EntLegalInstrumentType.MEMORANDUM,
            EntLegalInstrumentType.WAIVER,
            EntLegalInstrumentType.VARIATION,
        ]
        for itype in types:
            instrument = EntLegalInstrument(
                project_id=1,
                name="Test",
                instrument_type=itype,
                status=EntLegalInstrumentStatus.DRAFT,
            )
            assert instrument.instrument_type == itype

    def test_legal_instrument_statuses(self) -> None:
        """Test all instrument statuses."""
        statuses = [
            EntLegalInstrumentStatus.DRAFT,
            EntLegalInstrumentStatus.IN_REVIEW,
            EntLegalInstrumentStatus.EXECUTED,
            EntLegalInstrumentStatus.EXPIRED,
        ]
        for status in statuses:
            instrument = EntLegalInstrument(
                project_id=1,
                name="Test",
                instrument_type=EntLegalInstrumentType.AGREEMENT,
                status=status,
            )
            assert instrument.status == status


class TestEntitlementRelationships:
    """Tests for entitlement model relationships."""

    def test_authority_has_approval_types(self) -> None:
        """Authority should have approval_types relationship."""
        authority = EntAuthority(
            jurisdiction="SG",
            name="Test",
            slug="test",
        )
        assert hasattr(authority, "approval_types")

    def test_approval_type_has_authority(self) -> None:
        """ApprovalType should have authority relationship."""
        approval_type = EntApprovalType(
            authority_id=1,
            code="PP",
            name="Test",
            category=EntApprovalCategory.PLANNING,
        )
        assert hasattr(approval_type, "authority")

    def test_approval_type_has_roadmap_items(self) -> None:
        """ApprovalType should have roadmap_items relationship."""
        approval_type = EntApprovalType(
            authority_id=1,
            code="PP",
            name="Test",
            category=EntApprovalCategory.PLANNING,
        )
        assert hasattr(approval_type, "roadmap_items")

    def test_roadmap_item_has_approval_type(self) -> None:
        """RoadmapItem should have approval_type relationship."""
        item = EntRoadmapItem(
            project_id=1,
            sequence_order=1,
            status=EntRoadmapStatus.PLANNED,
        )
        assert hasattr(item, "approval_type")
