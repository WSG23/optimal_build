from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt_auth import create_tokens
from app.models.property import Property
from app.models.users import User


@pytest.mark.parametrize("provider", ["propertyguru", "edgeprop", "zoho_crm"])
@pytest.mark.asyncio
async def test_mock_flow(
    provider: str,
    app_client: AsyncClient,
    async_session_factory,
    market_demo_data,
) -> None:
    user_id = uuid4()
    async with async_session_factory() as session:  # type: AsyncSession
        session.add(
            User(
                id=str(user_id),
                email="integration@example.com",
                username="integration_user",
                full_name="Integration User",
                hashed_password="dummy",
            )
        )
        await session.commit()
        property_id = await _fetch_demo_property_id(session)

    tokens = create_tokens(
        {
            "id": str(user_id),
            "email": "integration@example.com",
            "username": "integration_user",
        }
    )
    headers = {
        "Authorization": f"Bearer {tokens.access_token}",
        "X-Role": "admin",
    }

    connect_response = await app_client.post(
        f"/api/v1/integrations/listings/{provider}/connect",
        json={"code": "mock-code", "redirect_uri": "http://localhost/callback"},
        headers=headers,
    )
    assert connect_response.status_code == 200, connect_response.text

    publish_response = await app_client.post(
        f"/api/v1/integrations/listings/{provider}/publish",
        json={
            "property_id": str(property_id),
            "external_id": "mock-listing-1",
            "title": "Demo Listing",
        },
        headers=headers,
    )
    assert publish_response.status_code == 200, publish_response.text
    body = publish_response.json()
    assert body["listing_id"] == "mock-listing-1"

    accounts_response = await app_client.get(
        "/api/v1/integrations/listings/accounts",
        headers=headers,
    )
    assert accounts_response.status_code == 200
    accounts = accounts_response.json()
    assert len(accounts) == 1
    assert accounts[0]["provider"] == provider

    async with async_session_factory() as session:
        await session.execute(
            text(
                "UPDATE listing_integration_accounts SET expires_at = "
                "datetime('now', '-10 minutes')"
            )
        )
        await session.commit()

    expired_response = await app_client.post(
        f"/api/v1/integrations/listings/{provider}/publish",
        json={
            "property_id": str(property_id),
            "external_id": "mock-listing-2",
            "title": "Expired Listing",
        },
        headers=headers,
    )
    assert expired_response.status_code == 401
    assert "expired" in expired_response.json()["detail"].lower()

    disconnect_response = await app_client.post(
        f"/api/v1/integrations/listings/{provider}/disconnect",
        headers=headers,
    )
    assert disconnect_response.status_code == 200
    body = disconnect_response.json()
    assert body["status"] == "disconnected"
    assert body["provider"] == provider


async def _fetch_demo_property_id(session: AsyncSession) -> str:
    result = await session.execute(
        select(Property.id).where(Property.name == "Market Demo Tower")
    )
    property_id = result.scalar_one()
    return str(property_id if isinstance(property_id, UUID) else property_id)
