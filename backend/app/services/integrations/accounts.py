"""Service helpers for managing listing integration accounts."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing_integration import (
    ListingAccountStatus,
    ListingIntegrationAccount,
    ListingProvider,
)


class ListingIntegrationAccountService:
    """Persist and retrieve external listing integration accounts."""

    async def list_accounts(
        self, *, user_id: UUID, session: AsyncSession
    ) -> list[ListingIntegrationAccount]:
        stmt = (
            select(ListingIntegrationAccount)
            .where(ListingIntegrationAccount.user_id == str(user_id))
            .order_by(ListingIntegrationAccount.provider)
        )
        result = await session.execute(stmt)
        return [row[0] for row in result.all()]

    async def get_account(
        self,
        *,
        user_id: UUID,
        provider: ListingProvider,
        session: AsyncSession,
    ) -> Optional[ListingIntegrationAccount]:
        stmt = select(ListingIntegrationAccount).where(
            ListingIntegrationAccount.user_id == str(user_id),
            ListingIntegrationAccount.provider == provider,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_account(
        self,
        *,
        user_id: UUID,
        provider: ListingProvider,
        access_token: str | None,
        refresh_token: str | None,
        expires_at: datetime | None,
        metadata: Optional[dict],
        session: AsyncSession,
    ) -> ListingIntegrationAccount:
        account = await self.get_account(
            user_id=user_id, provider=provider, session=session
        )
        if account is None:
            account = ListingIntegrationAccount(
                user_id=str(user_id),
                provider=provider,
                status=ListingAccountStatus.CONNECTED,
            )
            session.add(account)

        account.access_token = access_token
        account.refresh_token = refresh_token
        account.expires_at = expires_at
        if metadata is not None:
            account.metadata_json = metadata
        account.status = ListingAccountStatus.CONNECTED
        await session.commit()
        await session.refresh(account)
        return account

    async def revoke_account(
        self,
        *,
        account: ListingIntegrationAccount,
        session: AsyncSession,
    ) -> ListingIntegrationAccount:
        account.status = ListingAccountStatus.REVOKED
        account.access_token = None
        account.refresh_token = None
        account.expires_at = None
        await session.commit()
        await session.refresh(account)
        return account

    async def mark_disconnected(
        self,
        *,
        account: ListingIntegrationAccount,
        session: AsyncSession,
    ) -> ListingIntegrationAccount:
        account.status = ListingAccountStatus.DISCONNECTED
        await session.commit()
        await session.refresh(account)
        return account

    async def ensure_account_for_providers(
        self,
        *,
        user_id: UUID,
        providers: Iterable[ListingProvider],
        session: AsyncSession,
    ) -> dict[ListingProvider, ListingIntegrationAccount]:
        accounts = {}
        for provider in providers:
            record = await self.get_account(
                user_id=user_id, provider=provider, session=session
            )
            if record:
                accounts[provider] = record
        return accounts
