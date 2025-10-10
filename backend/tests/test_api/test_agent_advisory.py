from __future__ import annotations

from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.property import Property
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_advisory_summary_returns_sections(
    app_client: AsyncClient,
    async_session_factory,
    market_demo_data,
) -> None:
    async with async_session_factory() as session:  # type: AsyncSession
        property_id = await _fetch_demo_property_id(session)

    response = await app_client.get(
        f"/api/v1/agents/commercial-property/properties/{property_id}/advisory"
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["asset_mix"]["property_id"] == property_id
    assert payload["market_positioning"]["target_segments"]
    assert payload["absorption_forecast"]["expected_months_to_stabilize"] >= 6


@pytest.mark.asyncio
async def test_submit_and_list_feedback(
    app_client: AsyncClient,
    async_session_factory,
    market_demo_data,
) -> None:
    async with async_session_factory() as session:  # type: AsyncSession
        property_id = await _fetch_demo_property_id(session)

    post_response = await app_client.post(
        f"/api/v1/agents/commercial-property/properties/{property_id}/advisory/feedback",
        json={
            "sentiment": "positive",
            "notes": "Investors responded well to premium positioning.",
            "channel": "call",
        },
    )

    assert post_response.status_code == 201, post_response.text
    recorded = post_response.json()
    assert recorded["property_id"] == property_id
    assert recorded["sentiment"] == "positive"

    list_response = await app_client.get(
        f"/api/v1/agents/commercial-property/properties/{property_id}/advisory/feedback"
    )
    assert list_response.status_code == 200
    items = list_response.json()
    assert any(item["id"] == recorded["id"] for item in items)


async def _fetch_demo_property_id(session: AsyncSession) -> str:
    result = await session.execute(
        select(Property.id).where(Property.name == "Market Demo Tower")
    )
    property_id = result.scalar_one()
    return str(property_id if isinstance(property_id, UUID) else property_id)
