from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

pytest.importorskip("sqlalchemy")

from httpx import AsyncClient
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import listings as listings_api
from app.core.jwt_auth import create_tokens
from app.models.analytics_capture import (
    DataCaptureEvent,
    ExternalAPICall,
    StatusTransition,
)
from app.models.listing_integration import ListingPublication, ListingPublicationStatus
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
    connect_body = connect_response.json()
    assert connect_body["provider_status"]["state"] == "mock"

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
    assert body["provider_status"]["state"] == "mock"
    assert body["provider_status"]["synthetic"] is True

    async with async_session_factory() as session:
        publication_count = await session.scalar(
            select(func.count()).select_from(ListingPublication)
        )
        external_call_count = await session.scalar(
            select(func.count())
            .select_from(ExternalAPICall)
            .where(ExternalAPICall.provider == provider)
        )
        transition_count = await session.scalar(
            select(func.count())
            .select_from(StatusTransition)
            .where(StatusTransition.entity_type == "listing_publication")
        )
    assert publication_count == 1
    assert external_call_count == 2
    assert transition_count == 1

    accounts_response = await app_client.get(
        "/api/v1/integrations/listings/accounts",
        headers=headers,
    )
    assert accounts_response.status_code == 200
    accounts = accounts_response.json()
    assert len(accounts) == 1
    assert accounts[0]["provider"] == provider
    assert accounts[0]["provider_status"]["state"] == "mock"
    assert accounts[0]["provider_status"]["synthetic"] is True

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
    assert body["provider_status"]["state"] == "mock"


@pytest.mark.asyncio
async def test_publish_failure_persists_failed_publication_and_capture(
    app_client: AsyncClient,
    async_session_factory,
    market_demo_data,
    monkeypatch,
) -> None:
    user_id = uuid4()
    async with async_session_factory() as session:
        session.add(
            User(
                id=str(user_id),
                email="failure@example.com",
                username="failure_user",
                full_name="Failure User",
                hashed_password="dummy",
            )
        )
        await session.commit()
        property_id = await _fetch_demo_property_id(session)

    tokens = create_tokens(
        {
            "id": str(user_id),
            "email": "failure@example.com",
            "username": "failure_user",
        }
    )
    headers = {
        "Authorization": f"Bearer {tokens.access_token}",
        "X-Role": "admin",
        "X-Request-ID": "listing-failure-test",
    }

    connect_response = await app_client.post(
        "/api/v1/integrations/listings/propertyguru/connect",
        json={"code": "mock-code", "redirect_uri": "http://localhost/callback"},
        headers=headers,
    )
    assert connect_response.status_code == 200, connect_response.text

    failing_client = SimpleNamespace(
        publish_listing=AsyncMock(side_effect=RuntimeError("provider down")),
        source_metadata=lambda: SimpleNamespace(
            model_dump=lambda mode="json": {"state": "mock", "synthetic": True}
        ),
    )
    monkeypatch.setitem(
        listings_api.CLIENTS,
        listings_api.ListingProvider.PROPERTYGURU,
        failing_client,
    )

    response = await app_client.post(
        "/api/v1/integrations/listings/propertyguru/publish",
        json={
            "property_id": str(property_id),
            "external_id": "failing-listing",
            "title": "Failing Listing",
        },
        headers=headers,
    )
    assert response.status_code == 502

    async with async_session_factory() as session:
        publication = (
            (await session.execute(select(ListingPublication))).scalars().first()
        )
        external_call = (
            (
                await session.execute(
                    select(ExternalAPICall).where(
                        ExternalAPICall.provider == "propertyguru",
                        ExternalAPICall.outcome == "failure",
                    )
                )
            )
            .scalars()
            .first()
        )
        failure_capture = (
            (
                await session.execute(
                    select(DataCaptureEvent).where(
                        DataCaptureEvent.source == "listings.publish",
                        DataCaptureEvent.outcome == "rejected",
                    )
                )
            )
            .scalars()
            .first()
        )
        transition = (
            (
                await session.execute(
                    select(StatusTransition).where(
                        StatusTransition.entity_type == "listing_publication",
                        StatusTransition.to_status
                        == ListingPublicationStatus.FAILED.value,
                    )
                )
            )
            .scalars()
            .first()
        )

    assert publication is not None
    assert publication.status == ListingPublicationStatus.FAILED
    assert publication.last_error == "provider down"
    assert external_call is not None
    assert transition is not None
    assert failure_capture is not None


async def _fetch_demo_property_id(session: AsyncSession) -> str:
    result = await session.execute(
        select(Property.id).where(Property.name == "Market Demo Tower")
    )
    property_id = result.scalar_one()
    return str(property_id if isinstance(property_id, UUID) else property_id)
