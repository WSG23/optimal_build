"""Service helpers for managing listing integration accounts."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional
from uuid import UUID

from app.core.config import settings
from app.models.listing_integration import (
    ListingAccountStatus,
    ListingIntegrationAccount,
    ListingProvider,
)
from app.utils.encryption import TokenCipher
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class ListingIntegrationAccountService:
    """Persist and retrieve external listing integration accounts."""

    refresh_threshold: timedelta = timedelta(minutes=5)

    def __init__(self) -> None:
        self._cipher = TokenCipher(settings.LISTING_TOKEN_SECRET)

    async def list_accounts(
        self, *, user_id: UUID, session: AsyncSession
    ) -> list[ListingIntegrationAccount]:
        stmt = (
            select(ListingIntegrationAccount)
            .where(ListingIntegrationAccount.user_id == str(user_id))
            .order_by(ListingIntegrationAccount.provider)
        )
        result = await session.execute(stmt)
        accounts: list[ListingIntegrationAccount] = []
        for row in result.all():
            if isinstance(row, ListingIntegrationAccount):
                accounts.append(row)
                continue
            if isinstance(row, tuple | list):  # type: ignore[arg-type]
                if row:
                    candidate = row[0]
                    if isinstance(candidate, ListingIntegrationAccount):
                        accounts.append(candidate)
                continue
            candidate = getattr(row, "_mapping", None)
            if candidate:
                first = next(iter(candidate.values()), None)
                if isinstance(first, ListingIntegrationAccount):
                    accounts.append(first)
        return accounts

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

        account.access_token = self._cipher.encrypt(access_token)
        account.refresh_token = self._cipher.encrypt(refresh_token)
        account.expires_at = expires_at
        if metadata is not None:
            account.metadata = metadata
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

    def is_token_valid(
        self,
        account: ListingIntegrationAccount,
        *,
        now: datetime | None = None,
    ) -> bool:
        """Return ``True`` when the stored token is present and not expired."""

        if not account.access_token:
            return False
        if account.expires_at is None:
            return True
        now = now or datetime.now(timezone.utc)
        expires_at = account.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at > now

    def needs_refresh(
        self,
        account: ListingIntegrationAccount,
        *,
        now: datetime | None = None,
    ) -> bool:
        """Return ``True`` when the token is close to expiring."""

        if account.refresh_token is None:
            return False
        if account.expires_at is None:
            return False
        now = now or datetime.now(timezone.utc)
        expires_at = account.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at <= now + self.refresh_threshold

    def access_token(self, account: ListingIntegrationAccount) -> Optional[str]:
        return self._cipher.decrypt(account.access_token)

    def refresh_token(self, account: ListingIntegrationAccount) -> Optional[str]:
        return self._cipher.decrypt(account.refresh_token)

    async def store_tokens(
        self,
        *,
        account: ListingIntegrationAccount,
        access_token: str,
        refresh_token: str,
        expires_at: datetime,
        session: AsyncSession,
    ) -> ListingIntegrationAccount:
        account.access_token = self._cipher.encrypt(access_token)
        account.refresh_token = self._cipher.encrypt(refresh_token)
        account.expires_at = expires_at
        account.status = ListingAccountStatus.CONNECTED
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
