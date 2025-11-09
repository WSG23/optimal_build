from __future__ import annotations

import uuid

import pytest

from app.services.developer_checklist_service import (
    DEFAULT_TEMPLATE_DEFINITIONS,
    DeveloperChecklistService,
)
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@pytest.mark.asyncio
async def test_list_templates_seeded(
    app_client: AsyncClient,
) -> None:
    resp = await app_client.get("/api/v1/developers/checklists/templates")
    assert resp.status_code == 200, resp.text

    payload = resp.json()
    assert isinstance(payload, list)
    assert len(payload) >= len(DEFAULT_TEMPLATE_DEFINITIONS)

    first = payload[0]
    assert "id" in first
    assert "developmentScenario" in first
    assert "category" in first
    assert "priority" in first


@pytest.mark.asyncio
async def test_create_update_delete_template(
    app_client: AsyncClient,
) -> None:
    base_payload = {
        "developmentScenario": "unit_test_demo",
        "category": "title_verification",
        "itemTitle": "Verify land ownership records",
        "itemDescription": "Fetch SLA title report and confirm there are no caveats.",
        "priority": "high",
        "typicalDurationDays": 3,
        "requiresProfessional": True,
        "professionalType": "Conveyancing lawyer",
    }

    create_resp = await app_client.post(
        "/api/v1/developers/checklists/templates", json=base_payload
    )
    assert create_resp.status_code == 201, create_resp.text
    created = create_resp.json()
    template_id = created["id"]
    assert created["developmentScenario"] == "unit_test_demo"
    assert created["priority"] == "high"
    assert created["requiresProfessional"] is True

    update_payload = {
        "itemTitle": "Verify and document land ownership",
        "priority": "medium",
        "requiresProfessional": False,
        "professionalType": None,
        "displayOrder": 55,
    }

    update_resp = await app_client.put(
        f"/api/v1/developers/checklists/templates/{template_id}",
        json=update_payload,
    )
    assert update_resp.status_code == 200, update_resp.text
    updated = update_resp.json()
    assert updated["itemTitle"] == "Verify and document land ownership"
    assert updated["priority"] == "medium"
    assert updated["requiresProfessional"] is False
    assert updated["professionalType"] is None
    assert updated["displayOrder"] == 55

    delete_resp = await app_client.delete(
        f"/api/v1/developers/checklists/templates/{template_id}"
    )
    assert delete_resp.status_code == 204, delete_resp.text

    delete_again_resp = await app_client.delete(
        f"/api/v1/developers/checklists/templates/{template_id}"
    )
    assert delete_again_resp.status_code == 404


@pytest.mark.asyncio
async def test_bulk_import_replace_existing(
    app_client: AsyncClient,
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    scenario_key = f"bulk_{uuid.uuid4().hex[:8]}"

    # Seed one template via service to ensure replace_existing removes it.
    async with async_session_factory() as session:
        await DeveloperChecklistService.create_template(
            session,
            {
                "development_scenario": scenario_key,
                "category": "title_verification",
                "item_title": "Initial placeholder",
                "priority": "high",
                "requires_professional": False,
                "display_order": 10,
            },
        )
        await session.commit()

    import_payload = {
        "replaceExisting": True,
        "templates": [
            {
                "developmentScenario": scenario_key,
                "category": "zoning_compliance",
                "itemTitle": "Confirm masterplan alignment",
                "itemDescription": "Cross-check plot ratio and allowable uses.",
                "priority": "critical",
                "typicalDurationDays": 2,
                "requiresProfessional": False,
                "displayOrder": 30,
            }
        ],
    }

    import_resp = await app_client.post(
        "/api/v1/developers/checklists/templates/import", json=import_payload
    )
    assert import_resp.status_code == 200, import_resp.text
    result = import_resp.json()
    assert result == {"created": 1, "updated": 0, "deleted": 1}

    # Validate that only the new template remains for the scenario.
    list_resp = await app_client.get(
        "/api/v1/developers/checklists/templates",
        params={"developmentScenario": scenario_key},
    )
    assert list_resp.status_code == 200, list_resp.text
    items = list_resp.json()
    assert len(items) == 1
    assert items[0]["itemTitle"] == "Confirm masterplan alignment"
