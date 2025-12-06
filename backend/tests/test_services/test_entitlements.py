"""Integration tests for the EntitlementsService."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest
from backend._compat.datetime import UTC

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
from app.services.entitlements import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    EntitlementsService,
    PageResult,
    _normalise_limit,
    _normalise_offset,
)
from sqlalchemy.ext.asyncio import AsyncSession

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _make_authority(**overrides) -> EntAuthority:
    """Create a minimal EntAuthority for testing."""
    defaults = dict(
        jurisdiction="SG",
        name="Urban Redevelopment Authority",
        slug="ura-sg",
        website="https://www.ura.gov.sg",
        contact_email="ura@example.com",
        metadata={},
    )
    defaults.update(overrides)
    return EntAuthority(**defaults)


def _make_approval_type(authority_id: int, **overrides) -> EntApprovalType:
    """Create a minimal EntApprovalType for testing."""
    defaults = dict(
        authority_id=authority_id,
        code="PP",
        name="Planning Permission",
        category=EntApprovalCategory.PLANNING,
        description="Standard planning permission",
        requirements={},
        processing_time_days=90,
        is_mandatory=True,
        metadata={},
    )
    defaults.update(overrides)
    return EntApprovalType(**defaults)


def _make_roadmap_item(project_id: int, **overrides) -> EntRoadmapItem:
    """Create a minimal EntRoadmapItem for testing."""
    defaults = dict(
        project_id=project_id,
        approval_type_id=None,
        sequence_order=1,
        status=EntRoadmapStatus.PLANNED,
        status_changed_at=None,
        target_submission_date=None,
        target_decision_date=None,
        actual_submission_date=None,
        actual_decision_date=None,
        notes=None,
        metadata={},
    )
    defaults.update(overrides)
    return EntRoadmapItem(**defaults)


def _make_study(project_id: int, **overrides) -> EntStudy:
    """Create a minimal EntStudy for testing."""
    defaults = dict(
        project_id=project_id,
        name="Traffic Impact Assessment",
        study_type=EntStudyType.TRAFFIC,
        status=EntStudyStatus.DRAFT,
        summary="Traffic study for development",
        consultant=None,
        due_date=None,
        completed_at=None,
        attachments=[],
        metadata={},
    )
    defaults.update(overrides)
    return EntStudy(**defaults)


def _make_engagement(project_id: int, **overrides) -> EntEngagement:
    """Create a minimal EntEngagement for testing."""
    defaults = dict(
        project_id=project_id,
        name="Community Consultation",
        organisation="Local Residents Association",
        engagement_type=EntEngagementType.COMMUNITY,
        status=EntEngagementStatus.PLANNED,
        contact_email=None,
        contact_phone=None,
        meetings=[],
        notes=None,
        metadata={},
    )
    defaults.update(overrides)
    return EntEngagement(**defaults)


def _make_legal_instrument(project_id: int, **overrides) -> EntLegalInstrument:
    """Create a minimal EntLegalInstrument for testing."""
    defaults = dict(
        project_id=project_id,
        name="Development Agreement",
        instrument_type=EntLegalInstrumentType.AGREEMENT,
        status=EntLegalInstrumentStatus.DRAFT,
        reference_code=None,
        effective_date=None,
        expiry_date=None,
        attachments=[],
        metadata={},
    )
    defaults.update(overrides)
    return EntLegalInstrument(**defaults)


# ============================================================================
# PAGINATION HELPER TESTS
# ============================================================================


def test_normalise_limit_none():
    """Test _normalise_limit returns default when limit is None."""
    assert _normalise_limit(None) == DEFAULT_PAGE_SIZE


def test_normalise_limit_zero():
    """Test _normalise_limit returns default when limit is zero."""
    assert _normalise_limit(0) == DEFAULT_PAGE_SIZE


def test_normalise_limit_negative():
    """Test _normalise_limit returns default when limit is negative."""
    assert _normalise_limit(-10) == DEFAULT_PAGE_SIZE


def test_normalise_limit_normal():
    """Test _normalise_limit accepts valid positive limit."""
    assert _normalise_limit(25) == 25


def test_normalise_limit_exceeds_max():
    """Test _normalise_limit clamps to maximum when limit exceeds MAX_PAGE_SIZE."""
    assert _normalise_limit(300) == MAX_PAGE_SIZE


def test_normalise_offset_none():
    """Test _normalise_offset returns 0 when offset is None."""
    assert _normalise_offset(None) == 0


def test_normalise_offset_negative():
    """Test _normalise_offset returns 0 when offset is negative."""
    assert _normalise_offset(-5) == 0


def test_normalise_offset_zero():
    """Test _normalise_offset accepts zero offset."""
    assert _normalise_offset(0) == 0


def test_normalise_offset_positive():
    """Test _normalise_offset accepts valid positive offset."""
    assert _normalise_offset(100) == 100


# ============================================================================
# AUTHORITY TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_list_authorities_empty(db_session: AsyncSession):
    """Test list_authorities returns empty list when no authorities exist."""
    service = EntitlementsService(db_session)
    authorities = await service.list_authorities()
    assert authorities == []


@pytest.mark.asyncio
async def test_list_authorities_success(db_session: AsyncSession):
    """Test list_authorities returns all authorities ordered by name."""
    # Create multiple authorities
    auth1 = _make_authority(name="Building Control Authority", slug="bca-sg")
    auth2 = _make_authority(name="Urban Redevelopment Authority", slug="ura-sg")
    auth3 = _make_authority(name="Land Transport Authority", slug="lta-sg")

    db_session.add_all([auth1, auth2, auth3])
    await db_session.flush()

    service = EntitlementsService(db_session)
    authorities = await service.list_authorities()

    # Should be ordered by name
    assert len(authorities) == 3
    assert authorities[0].name == "Building Control Authority"
    assert authorities[1].name == "Land Transport Authority"
    assert authorities[2].name == "Urban Redevelopment Authority"


@pytest.mark.asyncio
async def test_list_authorities_filtered_by_jurisdiction(db_session: AsyncSession):
    """Test list_authorities filters by jurisdiction when provided."""
    # Create authorities in different jurisdictions
    auth_sg = _make_authority(jurisdiction="SG", slug="ura-sg")
    auth_au = _make_authority(
        jurisdiction="AU", name="Victorian Planning Authority", slug="vpa-au"
    )

    db_session.add_all([auth_sg, auth_au])
    await db_session.flush()

    service = EntitlementsService(db_session)
    authorities = await service.list_authorities(jurisdiction="SG")

    assert len(authorities) == 1
    assert authorities[0].jurisdiction == "SG"


@pytest.mark.asyncio
async def test_get_authority_by_slug_success(db_session: AsyncSession):
    """Test get_authority_by_slug returns authority when found."""
    authority = _make_authority(slug="ura-sg")
    db_session.add(authority)
    await db_session.flush()

    service = EntitlementsService(db_session)
    result = await service.get_authority_by_slug("ura-sg")

    assert result is not None
    assert result.slug == "ura-sg"
    assert result.name == "Urban Redevelopment Authority"


@pytest.mark.asyncio
async def test_get_authority_by_slug_not_found(db_session: AsyncSession):
    """Test get_authority_by_slug returns None when not found."""
    service = EntitlementsService(db_session)
    result = await service.get_authority_by_slug("non-existent")
    assert result is None


@pytest.mark.asyncio
async def test_upsert_authority_create_new(db_session: AsyncSession):
    """Test upsert_authority creates new authority when slug doesn't exist."""
    service = EntitlementsService(db_session)
    authority = await service.upsert_authority(
        jurisdiction="SG",
        name="Building Control Authority",
        slug="bca-sg",
        website="https://www.bca.gov.sg",
        contact_email="bca@example.com",
        metadata={"region": "southeast-asia"},
    )

    assert authority.id is not None
    assert authority.jurisdiction == "SG"
    assert authority.name == "Building Control Authority"
    assert authority.slug == "bca-sg"
    assert authority.website == "https://www.bca.gov.sg"
    assert authority.contact_email == "bca@example.com"
    assert authority.metadata == {"region": "southeast-asia"}


@pytest.mark.asyncio
async def test_upsert_authority_update_existing(db_session: AsyncSession):
    """Test upsert_authority updates existing authority when slug exists."""
    # Create initial authority
    authority = _make_authority(slug="ura-sg", website="https://old.ura.gov.sg")
    db_session.add(authority)
    await db_session.flush()
    authority_id = authority.id

    # Update authority
    service = EntitlementsService(db_session)
    updated = await service.upsert_authority(
        jurisdiction="SG",
        name="Urban Redevelopment Authority (Updated)",
        slug="ura-sg",
        website="https://new.ura.gov.sg",
        contact_email="new@ura.gov.sg",
        metadata={"updated": True},
    )

    assert updated.id == authority_id  # Same ID
    assert updated.name == "Urban Redevelopment Authority (Updated)"
    assert updated.website == "https://new.ura.gov.sg"
    assert updated.contact_email == "new@ura.gov.sg"
    assert updated.metadata == {"updated": True}


@pytest.mark.asyncio
async def test_upsert_authority_metadata_null_preserves_existing(
    db_session: AsyncSession,
):
    """Test upsert_authority preserves metadata when not provided on update."""
    # Create authority with metadata
    authority = _make_authority(slug="ura-sg", metadata={"existing": "data"})
    db_session.add(authority)
    await db_session.flush()

    # Update without metadata parameter
    service = EntitlementsService(db_session)
    updated = await service.upsert_authority(
        jurisdiction="SG",
        name="Urban Redevelopment Authority",
        slug="ura-sg",
    )

    # Metadata should be preserved
    assert updated.metadata == {"existing": "data"}


# ============================================================================
# APPROVAL TYPE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_get_approval_type_success(db_session: AsyncSession):
    """Test get_approval_type returns approval type when found."""
    authority = _make_authority()
    db_session.add(authority)
    await db_session.flush()

    approval_type = _make_approval_type(authority.id, code="PP")
    db_session.add(approval_type)
    await db_session.flush()

    service = EntitlementsService(db_session)
    result = await service.get_approval_type(authority_id=authority.id, code="PP")

    assert result is not None
    assert result.code == "PP"
    assert result.name == "Planning Permission"


@pytest.mark.asyncio
async def test_get_approval_type_not_found(db_session: AsyncSession):
    """Test get_approval_type returns None when not found."""
    service = EntitlementsService(db_session)
    result = await service.get_approval_type(authority_id=999, code="XX")
    assert result is None


@pytest.mark.asyncio
async def test_list_approval_types_empty(db_session: AsyncSession):
    """Test list_approval_types returns empty list when no types exist."""
    service = EntitlementsService(db_session)
    approval_types = await service.list_approval_types(authority_id=999)
    assert approval_types == []


@pytest.mark.asyncio
async def test_list_approval_types_success(db_session: AsyncSession):
    """Test list_approval_types returns all types for authority ordered by name."""
    authority = _make_authority()
    db_session.add(authority)
    await db_session.flush()

    # Create multiple approval types
    type1 = _make_approval_type(authority.id, code="BP", name="Building Permit")
    type2 = _make_approval_type(authority.id, code="PP", name="Planning Permission")
    type3 = _make_approval_type(
        authority.id, code="DP", name="Demolition Permit", is_mandatory=False
    )

    db_session.add_all([type1, type2, type3])
    await db_session.flush()

    service = EntitlementsService(db_session)
    approval_types = await service.list_approval_types(authority_id=authority.id)

    # Should be ordered by name
    assert len(approval_types) == 3
    assert approval_types[0].name == "Building Permit"
    assert approval_types[1].name == "Demolition Permit"
    assert approval_types[2].name == "Planning Permission"


@pytest.mark.asyncio
async def test_upsert_approval_type_create_new_with_enum(db_session: AsyncSession):
    """Test upsert_approval_type creates new type with enum category."""
    authority = _make_authority()
    db_session.add(authority)
    await db_session.flush()

    service = EntitlementsService(db_session)
    approval_type = await service.upsert_approval_type(
        authority=authority,
        code="ENV01",
        name="Environmental Impact Assessment",
        category=EntApprovalCategory.ENVIRONMENTAL,
        description="Required for large projects",
        requirements={"min_site_area": 5000},
        processing_time_days=120,
        is_mandatory=True,
        metadata={"category": "environmental"},
    )

    assert approval_type.id is not None
    assert approval_type.authority_id == authority.id
    assert approval_type.code == "ENV01"
    assert approval_type.name == "Environmental Impact Assessment"
    assert approval_type.category == "environmental"
    assert approval_type.description == "Required for large projects"
    assert approval_type.requirements == {"min_site_area": 5000}
    assert approval_type.processing_time_days == 120
    assert approval_type.is_mandatory is True


@pytest.mark.asyncio
async def test_upsert_approval_type_create_new_with_string(db_session: AsyncSession):
    """Test upsert_approval_type creates new type with string category."""
    authority = _make_authority()
    db_session.add(authority)
    await db_session.flush()

    service = EntitlementsService(db_session)
    approval_type = await service.upsert_approval_type(
        authority=authority,
        code="BLD01",
        name="Building Permit",
        category="building",  # String instead of enum
        is_mandatory=False,
    )

    assert approval_type.category == "building"
    assert approval_type.is_mandatory is False


@pytest.mark.asyncio
async def test_upsert_approval_type_invalid_category(db_session: AsyncSession):
    """Test upsert_approval_type raises error for invalid category type."""
    authority = _make_authority()
    db_session.add(authority)
    await db_session.flush()

    service = EntitlementsService(db_session)
    with pytest.raises(
        ValueError, match="category must be EntApprovalCategory or string"
    ):
        await service.upsert_approval_type(
            authority=authority,
            code="TEST",
            name="Test Approval",
            category=123,  # Invalid type
        )


@pytest.mark.asyncio
async def test_upsert_approval_type_update_existing(db_session: AsyncSession):
    """Test upsert_approval_type updates existing type when authority+code exists."""
    authority = _make_authority()
    db_session.add(authority)
    await db_session.flush()

    # Create initial approval type
    approval_type = _make_approval_type(
        authority.id, code="PP", processing_time_days=90
    )
    db_session.add(approval_type)
    await db_session.flush()
    approval_type_id = approval_type.id

    # Update approval type
    service = EntitlementsService(db_session)
    updated = await service.upsert_approval_type(
        authority=authority,
        code="PP",
        name="Planning Permission (Updated)",
        category=EntApprovalCategory.PLANNING,
        description="Updated description",
        processing_time_days=60,
        is_mandatory=False,
        requirements={"new": "requirements"},
        metadata={"updated": True},
    )

    assert updated.id == approval_type_id  # Same ID
    assert updated.name == "Planning Permission (Updated)"
    assert updated.description == "Updated description"
    assert updated.processing_time_days == 60
    assert updated.is_mandatory is False
    assert updated.requirements == {"new": "requirements"}
    assert updated.metadata == {"updated": True}


@pytest.mark.asyncio
async def test_upsert_approval_type_preserves_optional_fields(
    db_session: AsyncSession,
):
    """Test upsert_approval_type preserves optional fields when not provided."""
    authority = _make_authority()
    db_session.add(authority)
    await db_session.flush()

    # Create with metadata and requirements
    approval_type = _make_approval_type(
        authority.id,
        code="PP",
        metadata={"existing": "meta"},
        requirements={"existing": "req"},
    )
    db_session.add(approval_type)
    await db_session.flush()

    # Update without metadata/requirements
    service = EntitlementsService(db_session)
    updated = await service.upsert_approval_type(
        authority=authority,
        code="PP",
        name="Planning Permission",
        category=EntApprovalCategory.PLANNING,
    )

    # Should preserve existing values
    assert updated.metadata == {"existing": "meta"}
    assert updated.requirements == {"existing": "req"}


# ============================================================================
# ROADMAP ITEM TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_list_roadmap_items_empty(db_session: AsyncSession):
    """Test list_roadmap_items returns empty result for project with no items."""
    service = EntitlementsService(db_session)
    result = await service.list_roadmap_items(project_id=1)

    assert isinstance(result, PageResult)
    assert result.items == []
    assert result.total == 0


@pytest.mark.asyncio
async def test_list_roadmap_items_success(db_session: AsyncSession):
    """Test list_roadmap_items returns all items ordered by sequence."""
    project_id = 1

    # Create multiple roadmap items
    item1 = _make_roadmap_item(project_id, sequence_order=1)
    item2 = _make_roadmap_item(project_id, sequence_order=2)
    item3 = _make_roadmap_item(project_id, sequence_order=3)

    db_session.add_all([item1, item2, item3])
    await db_session.flush()

    service = EntitlementsService(db_session)
    result = await service.list_roadmap_items(project_id=project_id)

    assert result.total == 3
    assert len(result.items) == 3
    assert result.items[0].sequence_order == 1
    assert result.items[1].sequence_order == 2
    assert result.items[2].sequence_order == 3


@pytest.mark.asyncio
async def test_list_roadmap_items_pagination(db_session: AsyncSession):
    """Test list_roadmap_items respects limit and offset."""
    project_id = 1

    # Create 10 roadmap items
    for i in range(1, 11):
        item = _make_roadmap_item(project_id, sequence_order=i)
        db_session.add(item)
    await db_session.flush()

    service = EntitlementsService(db_session)

    # Get page 2 with limit 3
    result = await service.list_roadmap_items(project_id=project_id, limit=3, offset=3)

    assert result.total == 10
    assert len(result.items) == 3
    assert result.items[0].sequence_order == 4
    assert result.items[1].sequence_order == 5
    assert result.items[2].sequence_order == 6


@pytest.mark.asyncio
async def test_list_roadmap_items_default_pagination(db_session: AsyncSession):
    """Test list_roadmap_items uses default pagination when not specified."""
    project_id = 1

    # Create DEFAULT_PAGE_SIZE + 10 items
    for i in range(1, DEFAULT_PAGE_SIZE + 11):
        item = _make_roadmap_item(project_id, sequence_order=i)
        db_session.add(item)
    await db_session.flush()

    service = EntitlementsService(db_session)
    result = await service.list_roadmap_items(project_id=project_id)

    # Should return only DEFAULT_PAGE_SIZE items
    assert result.total == DEFAULT_PAGE_SIZE + 10
    assert len(result.items) == DEFAULT_PAGE_SIZE


@pytest.mark.asyncio
async def test_all_roadmap_items(db_session: AsyncSession):
    """Test all_roadmap_items returns complete roadmap without pagination."""
    project_id = 1

    # Create 10 items
    for i in range(1, 11):
        item = _make_roadmap_item(project_id, sequence_order=i)
        db_session.add(item)
    await db_session.flush()

    service = EntitlementsService(db_session)
    items = await service.all_roadmap_items(project_id)

    # Should return all items
    assert len(items) == 10


@pytest.mark.asyncio
async def test_create_roadmap_item_at_end(db_session: AsyncSession):
    """Test create_roadmap_item adds item at end when no sequence specified."""
    project_id = 1

    # Create existing items
    item1 = _make_roadmap_item(project_id, sequence_order=1)
    item2 = _make_roadmap_item(project_id, sequence_order=2)
    db_session.add_all([item1, item2])
    await db_session.flush()

    service = EntitlementsService(db_session)
    new_item = await service.create_roadmap_item(
        project_id=project_id,
        approval_type_id=None,
        sequence_order=None,
        status=EntRoadmapStatus.PLANNED,
        status_changed_at=None,
        target_submission_date=None,
        target_decision_date=None,
        actual_submission_date=None,
        actual_decision_date=None,
        notes="New item",
        metadata={"key": "value"},
    )

    assert new_item.sequence_order == 3
    assert new_item.notes == "New item"


@pytest.mark.asyncio
async def test_create_roadmap_item_at_beginning(db_session: AsyncSession):
    """Test create_roadmap_item inserts at beginning and reindexes."""
    project_id = 1

    # Create existing items
    item1 = _make_roadmap_item(project_id, sequence_order=1)
    item2 = _make_roadmap_item(project_id, sequence_order=2)
    db_session.add_all([item1, item2])
    await db_session.flush()

    service = EntitlementsService(db_session)
    new_item = await service.create_roadmap_item(
        project_id=project_id,
        approval_type_id=None,
        sequence_order=1,
        status=EntRoadmapStatus.PLANNED,
        status_changed_at=None,
        target_submission_date=None,
        target_decision_date=None,
        actual_submission_date=None,
        actual_decision_date=None,
        notes="First item",
        metadata={},
    )

    # Flush to persist all changes
    await db_session.flush()

    # Refresh items to get updated sequence_order
    await db_session.refresh(item1)
    await db_session.refresh(item2)
    await db_session.refresh(new_item)

    assert new_item.sequence_order == 1
    assert item1.sequence_order == 2
    assert item2.sequence_order == 3


@pytest.mark.asyncio
async def test_create_roadmap_item_in_middle(db_session: AsyncSession):
    """Test create_roadmap_item inserts in middle and reindexes."""
    project_id = 1

    # Create existing items
    item1 = _make_roadmap_item(project_id, sequence_order=1)
    item2 = _make_roadmap_item(project_id, sequence_order=2)
    item3 = _make_roadmap_item(project_id, sequence_order=3)
    db_session.add_all([item1, item2, item3])
    await db_session.flush()

    service = EntitlementsService(db_session)
    new_item = await service.create_roadmap_item(
        project_id=project_id,
        approval_type_id=None,
        sequence_order=2,
        status=EntRoadmapStatus.PLANNED,
        status_changed_at=None,
        target_submission_date=None,
        target_decision_date=None,
        actual_submission_date=None,
        actual_decision_date=None,
        notes="Middle item",
        metadata={},
    )

    # Flush to persist all changes
    await db_session.flush()

    # Refresh to get updated sequence_order
    await db_session.refresh(item1)
    await db_session.refresh(item2)
    await db_session.refresh(item3)
    await db_session.refresh(new_item)

    assert item1.sequence_order == 1
    assert new_item.sequence_order == 2
    assert item2.sequence_order == 3
    assert item3.sequence_order == 4


@pytest.mark.asyncio
async def test_create_roadmap_item_with_dates(db_session: AsyncSession):
    """Test create_roadmap_item properly stores date fields."""
    project_id = 1
    today = date.today()
    target_submission = today + timedelta(days=30)
    target_decision = today + timedelta(days=60)

    service = EntitlementsService(db_session)
    item = await service.create_roadmap_item(
        project_id=project_id,
        approval_type_id=None,
        sequence_order=None,
        status=EntRoadmapStatus.PLANNED,
        status_changed_at=None,
        target_submission_date=target_submission,
        target_decision_date=target_decision,
        actual_submission_date=None,
        actual_decision_date=None,
        notes=None,
        metadata={},
    )

    assert item.target_submission_date == target_submission
    assert item.target_decision_date == target_decision


@pytest.mark.asyncio
async def test_update_roadmap_item_basic_fields(db_session: AsyncSession):
    """Test update_roadmap_item updates basic fields."""
    project_id = 1
    item = _make_roadmap_item(project_id, notes="Original notes")
    db_session.add(item)
    await db_session.flush()
    item_id = item.id

    service = EntitlementsService(db_session)
    updated = await service.update_roadmap_item(
        item_id=item_id,
        project_id=project_id,
        notes="Updated notes",
        metadata={"updated": True},
    )

    assert updated.id == item_id
    assert updated.notes == "Updated notes"
    assert updated.metadata == {"updated": True}


@pytest.mark.asyncio
async def test_update_roadmap_item_dates(db_session: AsyncSession):
    """Test update_roadmap_item updates date fields."""
    project_id = 1
    item = _make_roadmap_item(project_id)
    db_session.add(item)
    await db_session.flush()

    today = date.today()
    submission_date = today + timedelta(days=10)
    decision_date = today + timedelta(days=20)

    service = EntitlementsService(db_session)
    updated = await service.update_roadmap_item(
        item_id=item.id,
        project_id=project_id,
        target_submission_date=submission_date,
        target_decision_date=decision_date,
    )

    assert updated.target_submission_date == submission_date
    assert updated.target_decision_date == decision_date


@pytest.mark.asyncio
async def test_update_roadmap_item_status_updates_timestamp(db_session: AsyncSession):
    """Test update_roadmap_item updates status_changed_at when status changes."""
    project_id = 1
    item = _make_roadmap_item(
        project_id, status=EntRoadmapStatus.PLANNED, status_changed_at=None
    )
    db_session.add(item)
    await db_session.flush()

    service = EntitlementsService(db_session)
    updated = await service.update_roadmap_item(
        item_id=item.id,
        project_id=project_id,
        status=EntRoadmapStatus.IN_PROGRESS,
    )

    assert updated.status == EntRoadmapStatus.IN_PROGRESS
    assert updated.status_changed_at is not None
    assert isinstance(updated.status_changed_at, datetime)


@pytest.mark.asyncio
async def test_update_roadmap_item_same_status_preserves_timestamp(
    db_session: AsyncSession,
):
    """Test update_roadmap_item preserves timestamp when status unchanged."""
    project_id = 1
    original_timestamp = datetime.now(UTC) - timedelta(days=1)
    item = _make_roadmap_item(
        project_id,
        status=EntRoadmapStatus.IN_PROGRESS,
        status_changed_at=original_timestamp,
    )
    db_session.add(item)
    await db_session.flush()

    service = EntitlementsService(db_session)
    updated = await service.update_roadmap_item(
        item_id=item.id,
        project_id=project_id,
        status=EntRoadmapStatus.IN_PROGRESS,  # Same status
        notes="Updated notes",
    )

    # Timestamp should not change
    assert updated.status_changed_at == original_timestamp


@pytest.mark.asyncio
async def test_update_roadmap_item_reorder_to_beginning(db_session: AsyncSession):
    """Test update_roadmap_item reorders item to beginning."""
    project_id = 1

    # Create items in order
    item1 = _make_roadmap_item(project_id, sequence_order=1)
    item2 = _make_roadmap_item(project_id, sequence_order=2)
    item3 = _make_roadmap_item(project_id, sequence_order=3)
    db_session.add_all([item1, item2, item3])
    await db_session.flush()

    # Move item3 to beginning
    service = EntitlementsService(db_session)
    await service.update_roadmap_item(
        item_id=item3.id,
        project_id=project_id,
        sequence_order=1,
    )

    # Flush to persist all changes
    await db_session.flush()

    # Refresh all items
    await db_session.refresh(item1)
    await db_session.refresh(item2)
    await db_session.refresh(item3)

    assert item3.sequence_order == 1
    assert item1.sequence_order == 2
    assert item2.sequence_order == 3


@pytest.mark.asyncio
async def test_update_roadmap_item_reorder_to_end(db_session: AsyncSession):
    """Test update_roadmap_item reorders item to end."""
    project_id = 1

    # Create items
    item1 = _make_roadmap_item(project_id, sequence_order=1)
    item2 = _make_roadmap_item(project_id, sequence_order=2)
    item3 = _make_roadmap_item(project_id, sequence_order=3)
    db_session.add_all([item1, item2, item3])
    await db_session.flush()

    # Move item1 to end
    service = EntitlementsService(db_session)
    await service.update_roadmap_item(
        item_id=item1.id,
        project_id=project_id,
        sequence_order=3,
    )

    # Flush to persist all changes
    await db_session.flush()

    # Refresh all
    await db_session.refresh(item1)
    await db_session.refresh(item2)
    await db_session.refresh(item3)

    assert item2.sequence_order == 1
    assert item3.sequence_order == 2
    assert item1.sequence_order == 3


@pytest.mark.asyncio
async def test_update_roadmap_item_not_found(db_session: AsyncSession):
    """Test update_roadmap_item raises error when item not found."""
    service = EntitlementsService(db_session)

    with pytest.raises(ValueError, match="Roadmap item 999 not found for project 1"):
        await service.update_roadmap_item(
            item_id=999,
            project_id=1,
            notes="Won't work",
        )


@pytest.mark.asyncio
async def test_delete_roadmap_item_success(db_session: AsyncSession):
    """Test delete_roadmap_item removes item and reindexes."""
    project_id = 1

    # Create items
    item1 = _make_roadmap_item(project_id, sequence_order=1)
    item2 = _make_roadmap_item(project_id, sequence_order=2)
    item3 = _make_roadmap_item(project_id, sequence_order=3)
    db_session.add_all([item1, item2, item3])
    await db_session.flush()

    # Delete middle item
    service = EntitlementsService(db_session)
    await service.delete_roadmap_item(item_id=item2.id, project_id=project_id)

    # Refresh remaining items
    await db_session.refresh(item1)
    await db_session.refresh(item3)

    # Check reindexing
    assert item1.sequence_order == 1
    assert item3.sequence_order == 2

    # Verify item2 is gone
    all_items = await service.all_roadmap_items(project_id)
    assert len(all_items) == 2


@pytest.mark.asyncio
async def test_delete_roadmap_item_not_found(db_session: AsyncSession):
    """Test delete_roadmap_item silently succeeds when item not found."""
    service = EntitlementsService(db_session)
    # Should not raise error
    await service.delete_roadmap_item(item_id=999, project_id=1)


# ============================================================================
# STUDY TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_list_studies_empty(db_session: AsyncSession):
    """Test list_studies returns empty result when no studies exist."""
    service = EntitlementsService(db_session)
    result = await service.list_studies(project_id=1)

    assert isinstance(result, PageResult)
    assert result.items == []
    assert result.total == 0


@pytest.mark.asyncio
async def test_list_studies_success(db_session: AsyncSession):
    """Test list_studies returns all studies ordered by created_at desc."""
    project_id = 1

    # Create multiple studies
    study1 = _make_study(project_id, name="Study 1")
    study2 = _make_study(project_id, name="Study 2")
    study3 = _make_study(project_id, name="Study 3")

    db_session.add_all([study1, study2, study3])
    await db_session.flush()

    service = EntitlementsService(db_session)
    result = await service.list_studies(project_id=project_id)

    assert result.total == 3
    assert len(result.items) == 3
    # Should be ordered by created_at desc (newest first)


@pytest.mark.asyncio
async def test_list_studies_pagination(db_session: AsyncSession):
    """Test list_studies respects limit and offset."""
    project_id = 1

    # Create 10 studies
    for i in range(10):
        study = _make_study(project_id, name=f"Study {i}")
        db_session.add(study)
    await db_session.flush()

    service = EntitlementsService(db_session)
    result = await service.list_studies(project_id=project_id, limit=3, offset=2)

    assert result.total == 10
    assert len(result.items) == 3


@pytest.mark.asyncio
async def test_create_study_success(db_session: AsyncSession):
    """Test create_study creates new study with all fields."""
    project_id = 1
    due = date.today() + timedelta(days=60)

    service = EntitlementsService(db_session)
    study = await service.create_study(
        project_id=project_id,
        name="Environmental Impact Study",
        study_type=EntStudyType.ENVIRONMENTAL,
        status=EntStudyStatus.SCOPE_DEFINED,
        summary="Full EIS for project",
        consultant="Environmental Consultants Ltd",
        due_date=due,
        attachments=[{"file": "eis_scope.pdf"}],
        metadata={"budget": 50000},
    )

    assert study.id is not None
    assert study.project_id == project_id
    assert study.name == "Environmental Impact Study"
    assert study.study_type == EntStudyType.ENVIRONMENTAL
    assert study.status == EntStudyStatus.SCOPE_DEFINED
    assert study.consultant == "Environmental Consultants Ltd"
    assert study.due_date == due
    assert study.attachments == [{"file": "eis_scope.pdf"}]
    assert study.metadata == {"budget": 50000}


@pytest.mark.asyncio
async def test_update_study_success(db_session: AsyncSession):
    """Test update_study updates study fields."""
    project_id = 1
    study = _make_study(project_id, status=EntStudyStatus.DRAFT)
    db_session.add(study)
    await db_session.flush()

    service = EntitlementsService(db_session)
    updated = await service.update_study(
        study_id=study.id,
        project_id=project_id,
        status=EntStudyStatus.IN_PROGRESS,
        consultant="New Consultant",
        summary="Updated summary",
    )

    assert updated.status == EntStudyStatus.IN_PROGRESS
    assert updated.consultant == "New Consultant"
    assert updated.summary == "Updated summary"


@pytest.mark.asyncio
async def test_update_study_not_found(db_session: AsyncSession):
    """Test update_study raises error when study not found."""
    service = EntitlementsService(db_session)

    with pytest.raises(ValueError, match="Study 999 not found for project 1"):
        await service.update_study(
            study_id=999,
            project_id=1,
            summary="Won't work",
        )


@pytest.mark.asyncio
async def test_delete_study_success(db_session: AsyncSession):
    """Test delete_study removes study."""
    project_id = 1
    study = _make_study(project_id)
    db_session.add(study)
    await db_session.flush()
    study_id = study.id

    service = EntitlementsService(db_session)
    await service.delete_study(study_id=study_id, project_id=project_id)

    # Verify it's gone
    result = await service.list_studies(project_id=project_id)
    assert result.total == 0


@pytest.mark.asyncio
async def test_delete_study_not_found(db_session: AsyncSession):
    """Test delete_study silently succeeds when study not found."""
    service = EntitlementsService(db_session)
    # Should not raise error
    await service.delete_study(study_id=999, project_id=1)


# ============================================================================
# ENGAGEMENT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_list_engagements_empty(db_session: AsyncSession):
    """Test list_engagements returns empty result when no engagements exist."""
    service = EntitlementsService(db_session)
    result = await service.list_engagements(project_id=1)

    assert isinstance(result, PageResult)
    assert result.items == []
    assert result.total == 0


@pytest.mark.asyncio
async def test_list_engagements_success(db_session: AsyncSession):
    """Test list_engagements returns all engagements ordered by created_at desc."""
    project_id = 1

    # Create multiple engagements
    eng1 = _make_engagement(project_id, name="Engagement 1")
    eng2 = _make_engagement(project_id, name="Engagement 2")
    eng3 = _make_engagement(project_id, name="Engagement 3")

    db_session.add_all([eng1, eng2, eng3])
    await db_session.flush()

    service = EntitlementsService(db_session)
    result = await service.list_engagements(project_id=project_id)

    assert result.total == 3
    assert len(result.items) == 3


@pytest.mark.asyncio
async def test_list_engagements_pagination(db_session: AsyncSession):
    """Test list_engagements respects limit and offset."""
    project_id = 1

    # Create 10 engagements
    for i in range(10):
        eng = _make_engagement(project_id, name=f"Engagement {i}")
        db_session.add(eng)
    await db_session.flush()

    service = EntitlementsService(db_session)
    result = await service.list_engagements(project_id=project_id, limit=5, offset=3)

    assert result.total == 10
    assert len(result.items) == 5


@pytest.mark.asyncio
async def test_create_engagement_success(db_session: AsyncSession):
    """Test create_engagement creates new engagement with all fields."""
    project_id = 1

    service = EntitlementsService(db_session)
    engagement = await service.create_engagement(
        project_id=project_id,
        name="Public Hearing",
        organisation="City Council",
        engagement_type=EntEngagementType.POLITICAL,
        status=EntEngagementStatus.PLANNED,
        contact_email="council@city.gov",
        contact_phone="+65 6123 4567",
        meetings=[{"date": "2025-11-01", "location": "City Hall"}],
        notes="Quarterly public consultation",
        metadata={"priority": "high"},
    )

    assert engagement.id is not None
    assert engagement.project_id == project_id
    assert engagement.name == "Public Hearing"
    assert engagement.engagement_type == EntEngagementType.POLITICAL
    assert engagement.status == EntEngagementStatus.PLANNED
    assert engagement.contact_email == "council@city.gov"
    assert engagement.meetings == [{"date": "2025-11-01", "location": "City Hall"}]


@pytest.mark.asyncio
async def test_create_engagement_active_status_initializes_meetings(
    db_session: AsyncSession,
):
    """Test create_engagement initializes empty meetings array for ACTIVE status."""
    project_id = 1

    service = EntitlementsService(db_session)
    engagement = await service.create_engagement(
        project_id=project_id,
        name="Active Engagement",
        engagement_type=EntEngagementType.AGENCY,
        status=EntEngagementStatus.ACTIVE,
    )

    # Should initialize meetings to empty array
    assert engagement.meetings == []


@pytest.mark.asyncio
async def test_update_engagement_success(db_session: AsyncSession):
    """Test update_engagement updates engagement fields."""
    project_id = 1
    engagement = _make_engagement(project_id, status=EntEngagementStatus.PLANNED)
    db_session.add(engagement)
    await db_session.flush()

    service = EntitlementsService(db_session)
    updated = await service.update_engagement(
        engagement_id=engagement.id,
        project_id=project_id,
        status=EntEngagementStatus.ACTIVE,
        notes="Updated notes",
        meetings=[{"date": "2025-11-15"}],
    )

    assert updated.status == EntEngagementStatus.ACTIVE
    assert updated.notes == "Updated notes"
    assert updated.meetings == [{"date": "2025-11-15"}]


@pytest.mark.asyncio
async def test_update_engagement_not_found(db_session: AsyncSession):
    """Test update_engagement raises error when engagement not found."""
    service = EntitlementsService(db_session)

    with pytest.raises(ValueError, match="Engagement 999 not found for project 1"):
        await service.update_engagement(
            engagement_id=999,
            project_id=1,
            notes="Won't work",
        )


@pytest.mark.asyncio
async def test_delete_engagement_success(db_session: AsyncSession):
    """Test delete_engagement removes engagement."""
    project_id = 1
    engagement = _make_engagement(project_id)
    db_session.add(engagement)
    await db_session.flush()
    engagement_id = engagement.id

    service = EntitlementsService(db_session)
    await service.delete_engagement(engagement_id=engagement_id, project_id=project_id)

    # Verify it's gone
    result = await service.list_engagements(project_id=project_id)
    assert result.total == 0


@pytest.mark.asyncio
async def test_delete_engagement_not_found(db_session: AsyncSession):
    """Test delete_engagement silently succeeds when engagement not found."""
    service = EntitlementsService(db_session)
    # Should not raise error
    await service.delete_engagement(engagement_id=999, project_id=1)


# ============================================================================
# LEGAL INSTRUMENT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_list_legal_instruments_empty(db_session: AsyncSession):
    """Test list_legal_instruments returns empty result when no instruments exist."""
    service = EntitlementsService(db_session)
    result = await service.list_legal_instruments(project_id=1)

    assert isinstance(result, PageResult)
    assert result.items == []
    assert result.total == 0


@pytest.mark.asyncio
async def test_list_legal_instruments_success(db_session: AsyncSession):
    """Test list_legal_instruments returns all instruments ordered by created_at desc."""
    project_id = 1

    # Create multiple instruments
    inst1 = _make_legal_instrument(project_id, name="Instrument 1")
    inst2 = _make_legal_instrument(project_id, name="Instrument 2")
    inst3 = _make_legal_instrument(project_id, name="Instrument 3")

    db_session.add_all([inst1, inst2, inst3])
    await db_session.flush()

    service = EntitlementsService(db_session)
    result = await service.list_legal_instruments(project_id=project_id)

    assert result.total == 3
    assert len(result.items) == 3


@pytest.mark.asyncio
async def test_list_legal_instruments_pagination(db_session: AsyncSession):
    """Test list_legal_instruments respects limit and offset."""
    project_id = 1

    # Create 10 instruments
    for i in range(10):
        inst = _make_legal_instrument(project_id, name=f"Instrument {i}")
        db_session.add(inst)
    await db_session.flush()

    service = EntitlementsService(db_session)
    result = await service.list_legal_instruments(
        project_id=project_id, limit=4, offset=2
    )

    assert result.total == 10
    assert len(result.items) == 4


@pytest.mark.asyncio
async def test_create_legal_instrument_success(db_session: AsyncSession):
    """Test create_legal_instrument creates new instrument with all fields."""
    project_id = 1
    effective = date.today()
    expiry = effective + timedelta(days=365)

    service = EntitlementsService(db_session)
    instrument = await service.create_legal_instrument(
        project_id=project_id,
        name="Development Licence Agreement",
        instrument_type=EntLegalInstrumentType.LICENCE,
        status=EntLegalInstrumentStatus.DRAFT,
        reference_code="DLA-2025-001",
        effective_date=effective,
        expiry_date=expiry,
        attachments=[{"file": "licence_draft.pdf"}],
        metadata={"value": 1000000},
    )

    assert instrument.id is not None
    assert instrument.project_id == project_id
    assert instrument.name == "Development Licence Agreement"
    assert instrument.instrument_type == EntLegalInstrumentType.LICENCE
    assert instrument.status == EntLegalInstrumentStatus.DRAFT
    assert instrument.reference_code == "DLA-2025-001"
    assert instrument.effective_date == effective
    assert instrument.expiry_date == expiry
    assert instrument.attachments == [{"file": "licence_draft.pdf"}]


@pytest.mark.asyncio
async def test_update_legal_instrument_success(db_session: AsyncSession):
    """Test update_legal_instrument updates instrument fields."""
    project_id = 1
    instrument = _make_legal_instrument(
        project_id, status=EntLegalInstrumentStatus.DRAFT
    )
    db_session.add(instrument)
    await db_session.flush()

    service = EntitlementsService(db_session)
    updated = await service.update_legal_instrument(
        instrument_id=instrument.id,
        project_id=project_id,
        status=EntLegalInstrumentStatus.IN_REVIEW,
        reference_code="UPD-2025-001",
    )

    assert updated.status == EntLegalInstrumentStatus.IN_REVIEW
    assert updated.reference_code == "UPD-2025-001"


@pytest.mark.asyncio
async def test_update_legal_instrument_not_found(db_session: AsyncSession):
    """Test update_legal_instrument raises error when instrument not found."""
    service = EntitlementsService(db_session)

    with pytest.raises(
        ValueError, match="Legal instrument 999 not found for project 1"
    ):
        await service.update_legal_instrument(
            instrument_id=999,
            project_id=1,
            reference_code="Won't work",
        )


@pytest.mark.asyncio
async def test_delete_legal_instrument_success(db_session: AsyncSession):
    """Test delete_legal_instrument removes instrument."""
    project_id = 1
    instrument = _make_legal_instrument(project_id)
    db_session.add(instrument)
    await db_session.flush()
    instrument_id = instrument.id

    service = EntitlementsService(db_session)
    await service.delete_legal_instrument(
        instrument_id=instrument_id, project_id=project_id
    )

    # Verify it's gone
    result = await service.list_legal_instruments(project_id=project_id)
    assert result.total == 0


@pytest.mark.asyncio
async def test_delete_legal_instrument_not_found(db_session: AsyncSession):
    """Test delete_legal_instrument silently succeeds when instrument not found."""
    service = EntitlementsService(db_session)
    # Should not raise error
    await service.delete_legal_instrument(instrument_id=999, project_id=1)
