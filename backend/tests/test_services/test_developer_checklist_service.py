from __future__ import annotations

from uuid import uuid4

import pytest
from app.models.developer_checklists import (
    ChecklistStatus,
    DeveloperChecklistTemplate,
    DeveloperPropertyChecklist,
)
from app.services.developer_checklist_service import (
    DEFAULT_TEMPLATE_DEFINITIONS,
    DeveloperChecklistService,
)
from sqlalchemy import func, select


def _count_templates_for_scenario(scenario: str) -> int:
    return sum(
        1
        for definition in DEFAULT_TEMPLATE_DEFINITIONS
        if definition["development_scenario"] == scenario
    )


@pytest.mark.asyncio
async def test_seed_templates_is_idempotent(async_session_factory) -> None:
    async with async_session_factory() as session:
        seeded = await DeveloperChecklistService.ensure_templates_seeded(session)
        await session.commit()
        assert seeded is True

        total = await session.scalar(select(func.count(DeveloperChecklistTemplate.id)))
        assert total == len(DEFAULT_TEMPLATE_DEFINITIONS)

        seeded_again = await DeveloperChecklistService.ensure_templates_seeded(session)
        await session.commit()
        assert seeded_again is False


@pytest.mark.asyncio
async def test_auto_populate_creates_checklist_items(async_session_factory) -> None:
    async with async_session_factory() as session:
        await DeveloperChecklistService.ensure_templates_seeded(session)
        property_id = uuid4()

        created_items = await DeveloperChecklistService.auto_populate_checklist(
            session=session,
            property_id=property_id,
            development_scenarios=["raw_land"],
        )
        await session.commit()

        expected_count = _count_templates_for_scenario("raw_land")
        assert len(created_items) == expected_count

        stored_items = await session.execute(
            select(DeveloperPropertyChecklist).where(
                DeveloperPropertyChecklist.property_id == property_id
            )
        )
        stored_list = list(stored_items.scalars().all())
        assert len(stored_list) == expected_count

        # Calling auto populate again should not duplicate items
        duplicate_items = await DeveloperChecklistService.auto_populate_checklist(
            session=session,
            property_id=property_id,
            development_scenarios=["raw_land"],
        )
        await session.commit()
        assert duplicate_items == []


@pytest.mark.asyncio
async def test_get_checklist_summary_counts_statuses(async_session_factory) -> None:
    async with async_session_factory() as session:
        await DeveloperChecklistService.ensure_templates_seeded(session)
        property_id = uuid4()

        items = await DeveloperChecklistService.auto_populate_checklist(
            session=session,
            property_id=property_id,
            development_scenarios=["raw_land"],
        )

        # Update statuses to cover different buckets
        if items:
            items[0].status = ChecklistStatus.COMPLETED
        if len(items) > 1:
            items[1].status = ChecklistStatus.IN_PROGRESS
        await session.flush()

        summary = await DeveloperChecklistService.get_checklist_summary(
            session, property_id
        )

        expected_total = _count_templates_for_scenario("raw_land")
        assert summary["total"] == expected_total
        assert summary["completed"] == (1 if items else 0)
        assert summary["in_progress"] == (1 if len(items) > 1 else 0)
        assert (
            summary["pending"]
            == expected_total - summary["completed"] - summary["in_progress"]
        )
        assert summary["property_id"] == str(property_id)
        for item in items:
            category_key = item.category.value
            breakdown = summary["by_category_status"].get(category_key)
            assert breakdown is not None
            assert breakdown["total"] >= 1


@pytest.mark.asyncio
async def test_get_property_checklist_respects_filters(async_session_factory) -> None:
    async with async_session_factory() as session:
        await DeveloperChecklistService.ensure_templates_seeded(session)
        property_id = uuid4()

        await DeveloperChecklistService.auto_populate_checklist(
            session=session,
            property_id=property_id,
            development_scenarios=["existing_building", "raw_land"],
        )

        all_items = await DeveloperChecklistService.get_property_checklist(
            session=session,
            property_id=property_id,
        )
        assert all_items

        scenarios = [item.development_scenario for item in all_items]
        assert scenarios == sorted(scenarios)

        order_tracker: dict[str, int] = {}
        for payload in DeveloperChecklistService.format_property_checklist_items(
            all_items
        ):
            scenario = payload["development_scenario"]
            display_order = payload.get("display_order") or 0
            assert display_order >= order_tracker.get(scenario, 0)
            order_tracker[scenario] = display_order

        filtered = await DeveloperChecklistService.get_property_checklist(
            session=session,
            property_id=property_id,
            development_scenario="raw_land",
        )
        assert filtered
        assert all(item.development_scenario == "raw_land" for item in filtered)


@pytest.mark.asyncio
async def test_format_property_checklist_items_merges_metadata(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        await DeveloperChecklistService.ensure_templates_seeded(session)
        property_id = uuid4()

        await DeveloperChecklistService.auto_populate_checklist(
            session=session,
            property_id=property_id,
            development_scenarios=["raw_land"],
        )
        await session.commit()

        items = await DeveloperChecklistService.get_property_checklist(
            session=session,
            property_id=property_id,
        )

        target_record = next(
            item
            for item in items
            if item.template is not None and item.template.requires_professional
        )

        target_record.metadata = {}
        await session.commit()
        items_after_reset = await DeveloperChecklistService.get_property_checklist(
            session=session,
            property_id=property_id,
        )
        fallback_payload = next(
            item
            for item in DeveloperChecklistService.format_property_checklist_items(
                items_after_reset
            )
            if item["id"] == str(target_record.id)
        )
        assert fallback_payload["requires_professional"] is True
        assert (
            fallback_payload["professional_type"]
            == target_record.template.professional_type
        )

        target_record.metadata = {
            "requires_professional": False,
            "professional_type": "Custom",
            "display_order": target_record.template.display_order,
        }
        await session.commit()
        items_after_override = await DeveloperChecklistService.get_property_checklist(
            session=session,
            property_id=property_id,
        )
        override_payload = next(
            item
            for item in DeveloperChecklistService.format_property_checklist_items(
                items_after_override
            )
            if item["id"] == str(target_record.id)
        )
        assert override_payload["requires_professional"] is False
        assert override_payload["professional_type"] is None
