"""Tests for developer checklist service."""

from __future__ import annotations

from uuid import uuid4

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.developer_checklists import (
    ChecklistCategory,
    ChecklistPriority,
    ChecklistStatus,
)
from app.services.developer_checklist_service import (
    DeveloperChecklistService,
)


class TestTemplateManagement:
    """Tests for template CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_template_success(self, session: AsyncSession) -> None:
        """Test successful creation of a new checklist template."""
        payload = {
            "development_scenario": "raw_land",
            "category": "title_verification",
            "item_title": "Custom Title Check",
            "item_description": "Verify ownership details",
            "priority": "critical",
            "typical_duration_days": 5,
            "requires_professional": True,
            "professional_type": "Lawyer",
            "display_order": 100,
        }

        result = await DeveloperChecklistService.create_template(session, payload)
        await session.commit()

        assert result.id is not None
        assert result.development_scenario == "raw_land"
        assert result.category == ChecklistCategory.TITLE_VERIFICATION
        assert result.item_title == "Custom Title Check"
        assert result.priority == ChecklistPriority.CRITICAL
        assert result.requires_professional is True
        assert result.professional_type == "Lawyer"

    @pytest.mark.asyncio
    async def test_create_template_without_required_scenario_raises_error(
        self, session: AsyncSession
    ) -> None:
        """Test that creating template without scenario raises ValueError."""
        payload = {
            "category": "title_verification",
            "item_title": "Test Item",
            "priority": "critical",
        }

        with pytest.raises(ValueError, match="development_scenario is required"):
            await DeveloperChecklistService.create_template(session, payload)

    @pytest.mark.asyncio
    async def test_create_template_without_item_title_raises_error(
        self, session: AsyncSession
    ) -> None:
        """Test that creating template without item_title raises ValueError."""
        payload = {
            "development_scenario": "raw_land",
            "category": "title_verification",
            "priority": "critical",
        }

        with pytest.raises(ValueError, match="item_title is required"):
            await DeveloperChecklistService.create_template(session, payload)

    @pytest.mark.asyncio
    async def test_create_duplicate_template_raises_error(
        self, session: AsyncSession
    ) -> None:
        """Test that creating duplicate template raises ValueError."""
        payload = {
            "development_scenario": "raw_land",
            "category": "title_verification",
            "item_title": "Unique Title",
            "priority": "critical",
        }

        await DeveloperChecklistService.create_template(session, payload)
        await session.flush()

        with pytest.raises(ValueError, match="already exists"):
            await DeveloperChecklistService.create_template(session, payload)

    @pytest.mark.asyncio
    async def test_create_template_assigns_auto_display_order(
        self, session: AsyncSession
    ) -> None:
        """Test that display_order is auto-assigned when not provided."""
        payload1 = {
            "development_scenario": "raw_land",
            "category": "title_verification",
            "item_title": "First Item",
            "priority": "critical",
        }
        payload2 = {
            "development_scenario": "raw_land",
            "category": "zoning_compliance",
            "item_title": "Second Item",
            "priority": "high",
        }

        result1 = await DeveloperChecklistService.create_template(session, payload1)
        await session.flush()
        result2 = await DeveloperChecklistService.create_template(session, payload2)
        await session.flush()

        assert result1.display_order == 10
        assert result2.display_order == 20

    @pytest.mark.asyncio
    async def test_list_templates_all(self, session: AsyncSession) -> None:
        """Test listing all templates."""
        payload1 = {
            "development_scenario": "raw_land",
            "category": "title_verification",
            "item_title": "Item 1",
            "priority": "critical",
        }
        payload2 = {
            "development_scenario": "existing_building",
            "category": "structural_survey",
            "item_title": "Item 2",
            "priority": "high",
        }

        await DeveloperChecklistService.create_template(session, payload1)
        await DeveloperChecklistService.create_template(session, payload2)
        await session.flush()

        results = await DeveloperChecklistService.list_templates(session)

        assert len(results) == 2
        assert results[0].item_title == "Item 1"
        assert results[1].item_title == "Item 2"

    @pytest.mark.asyncio
    async def test_list_templates_filtered_by_scenario(
        self, session: AsyncSession
    ) -> None:
        """Test listing templates filtered by development scenario."""
        payload1 = {
            "development_scenario": "raw_land",
            "category": "title_verification",
            "item_title": "Raw Land Item",
            "priority": "critical",
        }
        payload2 = {
            "development_scenario": "existing_building",
            "category": "structural_survey",
            "item_title": "Existing Item",
            "priority": "high",
        }

        await DeveloperChecklistService.create_template(session, payload1)
        await DeveloperChecklistService.create_template(session, payload2)
        await session.flush()

        results = await DeveloperChecklistService.list_templates(
            session, development_scenario="raw_land"
        )

        assert len(results) == 1
        assert results[0].item_title == "Raw Land Item"

    @pytest.mark.asyncio
    async def test_update_template_success(self, session: AsyncSession) -> None:
        """Test successful template update."""
        payload = {
            "development_scenario": "raw_land",
            "category": "title_verification",
            "item_title": "Original Title",
            "priority": "critical",
        }

        template = await DeveloperChecklistService.create_template(session, payload)
        template_id = template.id
        await session.flush()

        update_payload = {
            "item_title": "Updated Title",
            "priority": "high",
            "typical_duration_days": 10,
        }

        result = await DeveloperChecklistService.update_template(
            session, template_id, update_payload
        )

        assert result is not None
        assert result.item_title == "Updated Title"
        assert result.priority == ChecklistPriority.HIGH
        assert result.typical_duration_days == 10

    @pytest.mark.asyncio
    async def test_update_nonexistent_template_returns_none(
        self, session: AsyncSession
    ) -> None:
        """Test that updating non-existent template returns None."""
        fake_id = uuid4()
        payload = {"item_title": "Updated Title"}

        result = await DeveloperChecklistService.update_template(
            session, fake_id, payload
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_template_success(self, session: AsyncSession) -> None:
        """Test successful template deletion."""
        payload = {
            "development_scenario": "raw_land",
            "category": "title_verification",
            "item_title": "Template to Delete",
            "priority": "critical",
        }

        template = await DeveloperChecklistService.create_template(session, payload)
        template_id = template.id
        await session.flush()

        result = await DeveloperChecklistService.delete_template(session, template_id)

        assert result is True

        # Verify template was deleted
        templates = await DeveloperChecklistService.list_templates(session)
        assert len(templates) == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_template_returns_false(
        self, session: AsyncSession
    ) -> None:
        """Test that deleting non-existent template returns False."""
        fake_id = uuid4()

        result = await DeveloperChecklistService.delete_template(session, fake_id)

        assert result is False


class TestBulkOperations:
    """Tests for bulk upsert and seeding operations."""

    @pytest.mark.asyncio
    async def test_bulk_upsert_templates_creates_new(
        self, session: AsyncSession
    ) -> None:
        """Test bulk upsert creates new templates."""
        definitions = [
            {
                "development_scenario": "raw_land",
                "category": "title_verification",
                "item_title": "Title Item 1",
                "priority": "critical",
            },
            {
                "development_scenario": "raw_land",
                "category": "zoning_compliance",
                "item_title": "Zoning Item 1",
                "priority": "high",
            },
        ]

        result = await DeveloperChecklistService.bulk_upsert_templates(
            session, definitions
        )
        await session.flush()

        assert result["created"] == 2
        assert result["updated"] == 0
        assert result["deleted"] == 0

    @pytest.mark.asyncio
    async def test_bulk_upsert_templates_updates_existing(
        self, session: AsyncSession
    ) -> None:
        """Test bulk upsert updates existing templates."""
        initial = [
            {
                "development_scenario": "raw_land",
                "category": "title_verification",
                "item_title": "Title Check",
                "priority": "critical",
                "typical_duration_days": 5,
            }
        ]

        await DeveloperChecklistService.bulk_upsert_templates(session, initial)
        await session.flush()

        updated = [
            {
                "development_scenario": "raw_land",
                "category": "title_verification",
                "item_title": "Title Check",
                "priority": "high",
                "typical_duration_days": 10,
            }
        ]

        result = await DeveloperChecklistService.bulk_upsert_templates(session, updated)

        assert result["created"] == 0
        assert result["updated"] == 1
        assert result["deleted"] == 0

    @pytest.mark.asyncio
    async def test_bulk_upsert_with_replace_existing_deletes_old(
        self, session: AsyncSession
    ) -> None:
        """Test bulk upsert with replace_existing=True deletes templates not in new list."""
        initial = [
            {
                "development_scenario": "raw_land",
                "category": "title_verification",
                "item_title": "Item 1",
                "priority": "critical",
            },
            {
                "development_scenario": "raw_land",
                "category": "zoning_compliance",
                "item_title": "Item 2",
                "priority": "high",
            },
        ]

        await DeveloperChecklistService.bulk_upsert_templates(session, initial)
        await session.flush()

        updated = [
            {
                "development_scenario": "raw_land",
                "category": "title_verification",
                "item_title": "Item 1",
                "priority": "critical",
            }
        ]

        result = await DeveloperChecklistService.bulk_upsert_templates(
            session, updated, replace_existing=True
        )

        assert result["created"] == 0
        assert result["updated"] == 0
        assert result["deleted"] == 1

        templates = await DeveloperChecklistService.list_templates(session)
        assert len(templates) == 1

    @pytest.mark.asyncio
    async def test_ensure_templates_seeded(self, session: AsyncSession) -> None:
        """Test seeding default templates."""
        result = await DeveloperChecklistService.ensure_templates_seeded(session)

        assert result is True

        templates = await DeveloperChecklistService.list_templates(session)
        assert len(templates) > 0


class TestPropertyChecklists:
    """Tests for property-level checklist operations."""

    @pytest.mark.asyncio
    async def test_auto_populate_checklist(self, session: AsyncSession) -> None:
        """Test auto-population of checklists from templates."""
        await DeveloperChecklistService.ensure_templates_seeded(session)
        await session.flush()

        property_id = uuid4()
        scenarios = ["raw_land"]

        items = await DeveloperChecklistService.auto_populate_checklist(
            session, property_id, scenarios
        )
        await session.flush()

        assert len(items) > 0
        assert all(item.property_id == property_id for item in items)
        assert all(item.development_scenario == "raw_land" for item in items)
        assert all(item.status == ChecklistStatus.PENDING for item in items)

    @pytest.mark.asyncio
    async def test_auto_populate_with_assigned_to(self, session: AsyncSession) -> None:
        """Test auto-population with assigned_to user."""
        await DeveloperChecklistService.ensure_templates_seeded(session)
        await session.flush()

        property_id = uuid4()
        assigned_user = uuid4()
        scenarios = ["raw_land"]

        items = await DeveloperChecklistService.auto_populate_checklist(
            session, property_id, scenarios, assigned_to=assigned_user
        )
        await session.flush()

        assert all(item.assigned_to == assigned_user for item in items)

    @pytest.mark.asyncio
    async def test_auto_populate_prevents_duplicates(
        self, session: AsyncSession
    ) -> None:
        """Test that auto-population prevents duplicate items."""
        await DeveloperChecklistService.ensure_templates_seeded(session)
        await session.flush()

        property_id = uuid4()
        scenarios = ["raw_land"]

        _ = await DeveloperChecklistService.auto_populate_checklist(
            session, property_id, scenarios
        )
        await session.flush()

        items2 = await DeveloperChecklistService.auto_populate_checklist(
            session, property_id, scenarios
        )
        await session.flush()

        assert len(items2) == 0

    @pytest.mark.asyncio
    async def test_get_property_checklist(self, session: AsyncSession) -> None:
        """Test retrieving property checklists."""
        await DeveloperChecklistService.ensure_templates_seeded(session)
        await session.flush()

        property_id = uuid4()
        scenarios = ["raw_land", "existing_building"]

        await DeveloperChecklistService.auto_populate_checklist(
            session, property_id, scenarios
        )
        await session.flush()

        items = await DeveloperChecklistService.get_property_checklist(
            session, property_id
        )

        assert len(items) > 0
        assert all(item.property_id == property_id for item in items)

    @pytest.mark.asyncio
    async def test_get_property_checklist_filtered_by_scenario(
        self, session: AsyncSession
    ) -> None:
        """Test retrieving property checklists filtered by scenario."""
        await DeveloperChecklistService.ensure_templates_seeded(session)
        await session.flush()

        property_id = uuid4()
        scenarios = ["raw_land", "existing_building"]

        await DeveloperChecklistService.auto_populate_checklist(
            session, property_id, scenarios
        )
        await session.flush()

        items = await DeveloperChecklistService.get_property_checklist(
            session, property_id, development_scenario="raw_land"
        )

        assert all(item.development_scenario == "raw_land" for item in items)

    @pytest.mark.asyncio
    async def test_get_property_checklist_filtered_by_status(
        self, session: AsyncSession
    ) -> None:
        """Test retrieving property checklists filtered by status."""
        await DeveloperChecklistService.ensure_templates_seeded(session)
        await session.flush()

        property_id = uuid4()
        scenarios = ["raw_land"]

        items = await DeveloperChecklistService.auto_populate_checklist(
            session, property_id, scenarios
        )
        await session.flush()

        # Update one item to completed
        if items:
            await DeveloperChecklistService.update_checklist_status(
                session, items[0].id, ChecklistStatus.COMPLETED
            )
            await session.flush()

        pending = await DeveloperChecklistService.get_property_checklist(
            session, property_id, status=ChecklistStatus.PENDING
        )
        completed = await DeveloperChecklistService.get_property_checklist(
            session, property_id, status=ChecklistStatus.COMPLETED
        )

        assert len(pending) > 0
        assert len(completed) == 1


class TestStatusUpdates:
    """Tests for checklist status management."""

    @pytest.mark.asyncio
    async def test_update_checklist_status_to_completed(
        self, session: AsyncSession
    ) -> None:
        """Test updating checklist item to completed status."""
        await DeveloperChecklistService.ensure_templates_seeded(session)
        await session.flush()

        property_id = uuid4()
        completed_by = uuid4()

        items = await DeveloperChecklistService.auto_populate_checklist(
            session, property_id, ["raw_land"]
        )
        await session.flush()

        item = items[0]
        result = await DeveloperChecklistService.update_checklist_status(
            session,
            item.id,
            ChecklistStatus.COMPLETED,
            completed_by=completed_by,
            notes="Work completed successfully",
        )
        await session.flush()

        assert result is not None
        assert result.status == ChecklistStatus.COMPLETED
        assert result.completed_by == completed_by
        assert result.completed_date is not None
        assert result.notes == "Work completed successfully"

    @pytest.mark.asyncio
    async def test_update_checklist_status_to_in_progress(
        self, session: AsyncSession
    ) -> None:
        """Test updating checklist item to in_progress status."""
        await DeveloperChecklistService.ensure_templates_seeded(session)
        await session.flush()

        property_id = uuid4()
        items = await DeveloperChecklistService.auto_populate_checklist(
            session, property_id, ["raw_land"]
        )
        await session.flush()

        result = await DeveloperChecklistService.update_checklist_status(
            session, items[0].id, ChecklistStatus.IN_PROGRESS
        )
        await session.flush()

        assert result is not None
        assert result.status == ChecklistStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_update_checklist_status_not_applicable(
        self, session: AsyncSession
    ) -> None:
        """Test updating checklist item to not_applicable status."""
        await DeveloperChecklistService.ensure_templates_seeded(session)
        await session.flush()

        property_id = uuid4()
        items = await DeveloperChecklistService.auto_populate_checklist(
            session, property_id, ["raw_land"]
        )
        await session.flush()

        result = await DeveloperChecklistService.update_checklist_status(
            session, items[0].id, ChecklistStatus.NOT_APPLICABLE, notes="Not required"
        )
        await session.flush()

        assert result is not None
        assert result.status == ChecklistStatus.NOT_APPLICABLE
        assert result.notes == "Not required"

    @pytest.mark.asyncio
    async def test_update_nonexistent_checklist_returns_none(
        self, session: AsyncSession
    ) -> None:
        """Test updating non-existent checklist returns None."""
        fake_id = uuid4()

        result = await DeveloperChecklistService.update_checklist_status(
            session, fake_id, ChecklistStatus.COMPLETED
        )

        assert result is None


class TestSummaryReports:
    """Tests for checklist summary and reporting."""

    @pytest.mark.asyncio
    async def test_get_checklist_summary_empty(self, session: AsyncSession) -> None:
        """Test summary for property with no checklists."""
        property_id = uuid4()

        summary = await DeveloperChecklistService.get_checklist_summary(
            session, property_id
        )

        assert summary["total"] == 0
        assert summary["completed"] == 0
        assert summary["pending"] == 0
        assert summary["completion_percentage"] == 0

    @pytest.mark.asyncio
    async def test_get_checklist_summary_with_items(
        self, session: AsyncSession
    ) -> None:
        """Test summary calculation with multiple items."""
        await DeveloperChecklistService.ensure_templates_seeded(session)
        await session.flush()

        property_id = uuid4()
        scenarios = ["raw_land"]

        items = await DeveloperChecklistService.auto_populate_checklist(
            session, property_id, scenarios
        )
        await session.flush()

        # Mark some as completed
        for i, item in enumerate(items):
            if i < len(items) // 2:
                await DeveloperChecklistService.update_checklist_status(
                    session, item.id, ChecklistStatus.COMPLETED
                )
            else:
                await DeveloperChecklistService.update_checklist_status(
                    session, item.id, ChecklistStatus.IN_PROGRESS
                )
        await session.flush()

        summary = await DeveloperChecklistService.get_checklist_summary(
            session, property_id
        )

        assert summary["total"] == len(items)
        assert summary["completed"] == len(items) // 2
        assert summary["in_progress"] == len(items) - (len(items) // 2)
        assert summary["pending"] == 0

    @pytest.mark.asyncio
    async def test_get_checklist_summary_by_category(
        self, session: AsyncSession
    ) -> None:
        """Test summary includes category breakdown."""
        await DeveloperChecklistService.ensure_templates_seeded(session)
        await session.flush()

        property_id = uuid4()
        scenarios = ["raw_land"]

        await DeveloperChecklistService.auto_populate_checklist(
            session, property_id, scenarios
        )
        await session.flush()

        summary = await DeveloperChecklistService.get_checklist_summary(
            session, property_id
        )

        assert "by_category_status" in summary
        assert len(summary["by_category_status"]) > 0

    @pytest.mark.asyncio
    async def test_completion_percentage_calculation(
        self, session: AsyncSession
    ) -> None:
        """Test completion percentage is calculated correctly."""
        await DeveloperChecklistService.ensure_templates_seeded(session)
        await session.flush()

        property_id = uuid4()
        scenarios = ["raw_land"]

        items = await DeveloperChecklistService.auto_populate_checklist(
            session, property_id, scenarios
        )
        await session.flush()

        # Complete all items
        for item in items:
            await DeveloperChecklistService.update_checklist_status(
                session, item.id, ChecklistStatus.COMPLETED
            )
        await session.flush()

        summary = await DeveloperChecklistService.get_checklist_summary(
            session, property_id
        )

        assert summary["completion_percentage"] == 100

    @pytest.mark.asyncio
    async def test_format_property_checklist_items(self, session: AsyncSession) -> None:
        """Test formatting checklist items for API response."""
        await DeveloperChecklistService.ensure_templates_seeded(session)
        await session.flush()

        property_id = uuid4()
        items = await DeveloperChecklistService.auto_populate_checklist(
            session, property_id, ["raw_land"]
        )
        await session.flush()

        formatted = DeveloperChecklistService.format_property_checklist_items(items)

        assert len(formatted) == len(items)
        for item_dict in formatted:
            assert "id" in item_dict
            assert "property_id" in item_dict
            assert "status" in item_dict
            assert "priority" in item_dict
            assert "requires_professional" in item_dict

    @pytest.mark.asyncio
    async def test_get_templates_for_scenario(self, session: AsyncSession) -> None:
        """Test retrieving templates for a specific scenario."""
        await DeveloperChecklistService.ensure_templates_seeded(session)
        await session.flush()

        templates = await DeveloperChecklistService.get_templates_for_scenario(
            session, "raw_land"
        )

        assert len(templates) > 0
        assert all(t.development_scenario == "raw_land" for t in templates)
