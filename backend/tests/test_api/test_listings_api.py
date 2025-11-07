from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock

from app.api.v1 import listings as listings_api
from app.core.jwt_auth import TokenData
from app.models.listing_integration import ListingProvider, ListingAccountStatus


class _StubSession:
    async def execute(self, *_args, **_kwargs):
        return SimpleNamespace()


def _token(user_id: str | None) -> TokenData | None:
    if user_id is None:
        return None
    return TokenData(email="tester@example.com", username="tester", user_id=user_id)


def test_ensure_user_requires_token():
    with pytest.raises(HTTPException):
        listings_api._ensure_user(None)

    user_id = uuid4()
    assert listings_api._ensure_user(_token(str(user_id))) == user_id


def test_resolve_provider_and_client_lookup(monkeypatch):
    with pytest.raises(HTTPException):
        listings_api._resolve_provider("unknown")

    provider = listings_api._resolve_provider("propertyguru")
    assert provider is ListingProvider.PROPERTYGURU

    monkeypatch.setitem(listings_api.CLIENTS, provider, None)
    with pytest.raises(HTTPException):
        listings_api._client_for(provider)


@pytest.mark.asyncio
async def test_list_listing_accounts_returns_serialised(monkeypatch):
    user_id = uuid4()
    account = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        provider=ListingProvider.PROPERTYGURU,
        status=ListingAccountStatus.CONNECTED,
        created_at=datetime(2024, 1, 1),
        updated_at=None,
        metadata={"mode": "mock"},
        expires_at=datetime.utcnow() + timedelta(days=30),
    )
    monkeypatch.setattr(
        listings_api.account_service,
        "list_accounts",
        AsyncMock(return_value=[account]),
    )

    response = await listings_api.list_listing_accounts(
        session=_StubSession(),
        role="viewer",
        token=_token(str(user_id)),
    )
    assert response[0]["provider"] == "propertyguru"


@pytest.mark.asyncio
async def test_connect_account_missing_code(monkeypatch):
    monkeypatch.setattr(listings_api.account_service, "upsert_account", AsyncMock())
    with pytest.raises(HTTPException) as exc:
        await listings_api.connect_account(
            provider="propertyguru",
            payload={},
            session=_StubSession(),
            role="viewer",
            token=_token(str(uuid4())),
        )
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_publish_listing_requires_linked_account(monkeypatch):
    monkeypatch.setattr(
        listings_api.account_service,
        "get_account",
        AsyncMock(return_value=None),
    )
    with pytest.raises(HTTPException) as exc:
        await listings_api.publish_listing(
            provider="propertyguru",
            payload={},
            session=_StubSession(),
            role="viewer",
            token=_token(str(uuid4())),
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_disconnect_account_when_missing(monkeypatch):
    monkeypatch.setattr(
        listings_api.account_service,
        "get_account",
        AsyncMock(return_value=None),
    )
    with pytest.raises(HTTPException) as exc:
        await listings_api.disconnect_account(
            provider="propertyguru",
            session=_StubSession(),
            role="viewer",
            token=_token(str(uuid4())),
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_connect_account_success(monkeypatch):
    provider = ListingProvider.PROPERTYGURU
    user_id = uuid4()
    tokens = SimpleNamespace(
        access_token="access",
        refresh_token="refresh",
        expires_at=datetime.utcnow() + timedelta(days=1),
    )
    client = SimpleNamespace(exchange_authorization_code=AsyncMock(return_value=tokens))
    monkeypatch.setitem(listings_api.CLIENTS, provider, client)
    monkeypatch.setattr(
        listings_api.account_service,
        "upsert_account",
        AsyncMock(
            return_value=SimpleNamespace(
                id=uuid4(),
                user_id=user_id,
                provider=provider,
                status=ListingAccountStatus.CONNECTED,
                metadata={},
                created_at=datetime.utcnow(),
                updated_at=None,
                expires_at=tokens.expires_at,
            )
        ),
    )

    response = await listings_api.connect_account(
        provider=provider.value,
        payload={"code": "demo", "redirect_uri": "https://example.com"},
        session=_StubSession(),
        role="viewer",
        token=_token(str(user_id)),
    )
    assert response["provider"] == provider.value


@pytest.mark.asyncio
async def test_publish_listing_success(monkeypatch):
    provider = ListingProvider.PROPERTYGURU
    user_id = uuid4()
    account = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        provider=provider,
    )
    monkeypatch.setattr(
        listings_api.account_service,
        "get_account",
        AsyncMock(return_value=account),
    )
    monkeypatch.setattr(
        listings_api.account_service,
        "is_token_valid",
        lambda account: True,
    )
    monkeypatch.setattr(
        listings_api.account_service,
        "needs_refresh",
        lambda account: False,
    )
    client = SimpleNamespace(
        publish_listing=AsyncMock(return_value=("listing-1", {"ok": True}))
    )
    monkeypatch.setitem(listings_api.CLIENTS, provider, client)

    payload = {"title": "New listing"}
    response = await listings_api.publish_listing(
        provider=provider.value,
        payload=payload,
        session=_StubSession(),
        role="viewer",
        token=_token(str(user_id)),
    )
    assert response["listing_id"] == "listing-1"
    listings_api.account_service.get_account.assert_awaited()


@pytest.mark.asyncio
async def test_disconnect_account_success(monkeypatch):
    provider = ListingProvider.PROPERTYGURU
    account = SimpleNamespace(
        id=uuid4(),
        user_id=uuid4(),
        provider=provider,
    )
    monkeypatch.setattr(
        listings_api.account_service,
        "get_account",
        AsyncMock(return_value=account),
    )
    monkeypatch.setattr(
        listings_api.account_service,
        "revoke_account",
        AsyncMock(),
    )

    response = await listings_api.disconnect_account(
        provider=provider.value,
        session=_StubSession(),
        role="viewer",
        token=_token(str(account.user_id)),
    )
    assert response["status"] == "disconnected"
    listings_api.account_service.revoke_account.assert_awaited_once()
