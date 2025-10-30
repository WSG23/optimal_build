"""Tests for listing integration account service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.core.config import settings
from app.models.listing_integration import (
    ListingAccountStatus,
    ListingProvider,
)
from app.models.users import User
from app.services.integrations.accounts import ListingIntegrationAccountService


@pytest.mark.asyncio
async def test_account_lifecycle(monkeypatch, db_session) -> None:
    monkeypatch.setattr(settings, "LISTING_TOKEN_SECRET", "integration-secret")
    service = ListingIntegrationAccountService()

    user = User(
        id=uuid4(),
        email="user@example.com",
        username="user",
        full_name="Integration User",
        hashed_password="hashed",
    )
    db_session.add(user)
    await db_session.commit()

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

    account = await service.upsert_account(
        user_id=user.id,
        provider=ListingProvider.PROPERTYGURU,
        access_token="access-token-1",
        refresh_token="refresh-token-1",
        expires_at=expires_at,
        metadata={"scope": "basic"},
        session=db_session,
    )

    assert account.status == ListingAccountStatus.CONNECTED
    assert service.access_token(account) == "access-token-1"
    assert service.refresh_token(account) == "refresh-token-1"

    fetched = await service.get_account(
        user_id=user.id,
        provider=ListingProvider.PROPERTYGURU,
        session=db_session,
    )
    assert fetched is not None
    assert fetched.id == account.id

    listed = await service.list_accounts(user_id=user.id, session=db_session)
    assert [acc.provider for acc in listed] == [ListingProvider.PROPERTYGURU]

    assert service.is_token_valid(account, now=datetime.now(timezone.utc)) is True
    assert (
        service.needs_refresh(
            account,
            now=datetime.now(timezone.utc) + timedelta(minutes=25),
        )
        is True
    )

    # Update tokens
    new_expiry = datetime.now(timezone.utc) + timedelta(minutes=60)
    account = await service.store_tokens(
        account=account,
        access_token="access-token-2",
        refresh_token="refresh-token-2",
        expires_at=new_expiry,
        session=db_session,
    )
    assert service.access_token(account) == "access-token-2"
    stored_expiry = account.expires_at
    if stored_expiry.tzinfo is None:
        stored_expiry = stored_expiry.replace(tzinfo=timezone.utc)
    assert stored_expiry == new_expiry

    # Add second provider to exercise ensure_account_for_providers
    await service.upsert_account(
        user_id=user.id,
        provider=ListingProvider.EDGEPROP,
        access_token="edge-access",
        refresh_token="edge-refresh",
        expires_at=new_expiry,
        metadata=None,
        session=db_session,
    )

    accounts_map = await service.ensure_account_for_providers(
        user_id=user.id,
        providers=[ListingProvider.PROPERTYGURU, ListingProvider.EDGEPROP],
        session=db_session,
    )
    assert set(accounts_map) == {
        ListingProvider.PROPERTYGURU,
        ListingProvider.EDGEPROP,
    }

    # Revoke / disconnect flows
    account = await service.revoke_account(account=account, session=db_session)
    assert account.status == ListingAccountStatus.REVOKED
    assert account.access_token is None

    account = await service.mark_disconnected(account=account, session=db_session)
    assert account.status == ListingAccountStatus.DISCONNECTED
