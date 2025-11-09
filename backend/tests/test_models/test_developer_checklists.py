"""Test developer checklist models can be created in SQLite fixture."""

from __future__ import annotations

from uuid import uuid4

import pytest

pytest.importorskip("sqlalchemy")

from app.models.developer_checklists import (
    ChecklistCategory,
    ChecklistPriority,
    ChecklistStatus,
    DeveloperChecklistTemplate,
    DeveloperPropertyChecklist,
)
from sqlalchemy import select


@pytest.mark.asyncio
async def test_developer_checklist_template_create(db_session):
    """Test creating a checklist template with portable UUID."""
    template = DeveloperChecklistTemplate(
        id=uuid4(),
        development_scenario="raw_land",
        category=ChecklistCategory.TITLE_VERIFICATION,
        item_title="Verify land title",
        item_description="Confirm clear title",
        priority=ChecklistPriority.CRITICAL,
        typical_duration_days=14,
        requires_professional=True,
        professional_type="Lawyer",
        display_order=1,
    )

    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    # Verify it was created
    result = await db_session.execute(
        select(DeveloperChecklistTemplate).where(
            DeveloperChecklistTemplate.id == template.id
        )
    )
    fetched = result.scalar_one()

    assert fetched.id == template.id
    assert fetched.item_title == "Verify land title"
    assert fetched.category == ChecklistCategory.TITLE_VERIFICATION
    assert fetched.priority == ChecklistPriority.CRITICAL


@pytest.mark.asyncio
async def test_developer_property_checklist_create(db_session):
    """Test creating a property checklist item with portable UUID and MetadataProxy."""
    property_id = uuid4()

    checklist_item = DeveloperPropertyChecklist(
        id=uuid4(),
        property_id=property_id,
        development_scenario="existing_building",
        category=ChecklistCategory.ZONING_COMPLIANCE,
        item_title="Check zoning regulations",
        priority=ChecklistPriority.HIGH,
        status=ChecklistStatus.PENDING,
        requires_professional=False,
    )

    # Test MetadataProxy
    checklist_item.metadata = {"notes": "test", "custom_field": 123}

    db_session.add(checklist_item)
    await db_session.commit()
    await db_session.refresh(checklist_item)

    # Verify it was created
    result = await db_session.execute(
        select(DeveloperPropertyChecklist).where(
            DeveloperPropertyChecklist.id == checklist_item.id
        )
    )
    fetched = result.scalar_one()

    assert fetched.id == checklist_item.id
    assert fetched.property_id == property_id
    assert fetched.status == ChecklistStatus.PENDING
    assert fetched.category == ChecklistCategory.ZONING_COMPLIANCE
    # Test MetadataProxy access
    assert fetched.metadata == {"notes": "test", "custom_field": 123}
    assert fetched.metadata_json == {"notes": "test", "custom_field": 123}


@pytest.mark.asyncio
async def test_checklist_item_to_dict(db_session):
    """Test to_dict() serialization method."""
    property_id = uuid4()

    checklist_item = DeveloperPropertyChecklist(
        id=uuid4(),
        property_id=property_id,
        development_scenario="heritage_property",
        category=ChecklistCategory.HERITAGE_CONSTRAINTS,
        item_title="Heritage approval required",
        priority=ChecklistPriority.CRITICAL,
        status=ChecklistStatus.IN_PROGRESS,
        requires_professional=True,
        professional_type="Heritage Consultant",
    )

    db_session.add(checklist_item)
    await db_session.commit()
    await db_session.refresh(checklist_item)

    # Test serialization
    data = checklist_item.to_dict()

    assert data["id"] == str(checklist_item.id)
    assert data["property_id"] == str(property_id)
    assert data["category"] == "heritage_constraints"
    assert data["status"] == "in_progress"
    assert data["priority"] == "critical"
    assert data["requires_professional"] is True
    assert data["professional_type"] == "Heritage Consultant"
    assert "created_at" in data
    assert "updated_at" in data
