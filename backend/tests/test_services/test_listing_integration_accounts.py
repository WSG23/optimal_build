from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

pytest.importorskip("sqlalchemy")

from app.models.listing_integration import ListingProvider
from app.models.user import User
from app.services.integrations.accounts import ListingIntegrationAccountService


@pytest.mark.asyncio
async def test_upsert_and_list_accounts(async_session_factory):
    service = ListingIntegrationAccountService()
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

        account = await service.upsert_account(
            user_id=user_id,
            provider=ListingProvider.PROPERTYGURU,
            access_token="token",
            refresh_token="refresh",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            metadata={"scope": "listing"},
            session=session,
        )
        assert account.provider == ListingProvider.PROPERTYGURU
        assert account.status.value == "connected"
        assert account.metadata_json.get("scope") == "listing"

        accounts = await service.list_accounts(user_id=user_id, session=session)
        assert len(accounts) == 1
        assert accounts[0].provider == ListingProvider.PROPERTYGURU
        assert service.is_token_valid(accounts[0])
        assert not service.needs_refresh(accounts[0])
        assert service.access_token(accounts[0]) == "token"
        assert service.refresh_token(accounts[0]) == "refresh"


@pytest.mark.asyncio
async def test_is_token_valid_handles_expiry(async_session_factory):
    service = ListingIntegrationAccountService()
    user_id = uuid4()

    async with async_session_factory() as session:  # type: AsyncSession
        session.add(
            User(
                id=str(user_id),
                email="integration-expired@example.com",
                username="integration_expired",
                full_name="Integration Expired",
                hashed_password="dummy",
            )
        )
        await session.commit()

        account = await service.upsert_account(
            user_id=user_id,
            provider=ListingProvider.PROPERTYGURU,
            access_token="token",
            refresh_token="refresh",
            expires_at=datetime.utcnow() - timedelta(minutes=1),
            metadata={"scope": "listing"},
            session=session,
        )
        assert not service.is_token_valid(account)

        account.expires_at = datetime.utcnow() + timedelta(minutes=3)
        await session.commit()
        assert service.needs_refresh(account)
