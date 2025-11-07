from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest
from unittest.mock import AsyncMock

from app.api.v1 import agents as agents_api
from app.services.agents.gps_property_logger import PropertyLogResult
from app.services.geocoding import Address


def _sample_result():
    return PropertyLogResult(
        property_id=uuid4(),
        address=Address(
            full_address="1 Sample Way",
            street_name="Sample Way",
            building_name="Sample Tower",
            block_number="01",
            postal_code="010101",
            district="D01",
        ),
        coordinates=(1.3, 103.8),
        ura_zoning={"zone_code": "C1"},
        existing_use="Office",
        property_info={"gfa": 1000},
        nearby_amenities={"coffee": 3},
        quick_analysis={
            "generated_at": datetime.utcnow().isoformat(),
            "scenarios": [],
        },
        timestamp=datetime.utcnow(),
    )


@pytest.mark.asyncio
async def test_log_property_by_gps_success(client, monkeypatch):
    result = _sample_result()
    monkeypatch.setattr(
        agents_api.gps_logger,
        "log_property_from_gps",
        AsyncMock(return_value=result),
    )

    response = await client.post(
        "/api/v1/agents/commercial-property/properties/log-gps",
        json={"latitude": 1.3, "longitude": 103.8},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["property_id"] == str(result.property_id)
    agents_api.gps_logger.log_property_from_gps.assert_awaited_once()  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_log_property_by_gps_fallback(client, monkeypatch):
    monkeypatch.setattr(
        agents_api.gps_logger,
        "log_property_from_gps",
        AsyncMock(side_effect=RuntimeError("gps offline")),
    )
    ensure_seeded = AsyncMock(return_value=None)
    auto_populate = AsyncMock(return_value=None)
    monkeypatch.setattr(
        agents_api.DeveloperChecklistService,
        "ensure_templates_seeded",
        ensure_seeded,
    )
    monkeypatch.setattr(
        agents_api.DeveloperChecklistService,
        "auto_populate_checklist",
        auto_populate,
    )

    response = await client.post(
        "/api/v1/agents/commercial-property/properties/log-gps",
        json={"latitude": 1.31, "longitude": 103.82},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ura_zoning"]["zone_code"] == "MU"
    ensure_seeded.assert_awaited()
    auto_populate.assert_awaited()
