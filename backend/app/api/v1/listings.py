"""API endpoints for managing external listing integrations (mock)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Role, get_request_role
from app.core.database import get_session
from app.core.jwt_auth import TokenData, get_optional_user
from app.models.listing_integration import ListingProvider
from app.services.integrations.accounts import ListingIntegrationAccountService
from app.services.integrations.propertyguru import PropertyGuruClient

router = APIRouter(prefix="/integrations/listings", tags=["Commercial Property Agent"])

account_service = ListingIntegrationAccountService()
mock_propertyguru = PropertyGuruClient()
logger = structlog.get_logger()


def _ensure_user(token: TokenData | None) -> UUID:
    if token is None or not token.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required"
        )
    return UUID(token.user_id)


@router.get("/accounts")
async def list_listing_accounts(
    session: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
    token: TokenData | None = Depends(get_optional_user),
) -> list[dict[str, Any]]:
    """Return linked listing accounts for the current user."""

    user_id = _ensure_user(token)
    accounts = await account_service.list_accounts(user_id=user_id, session=session)
    return [account.as_dict() for account in accounts]


@router.post("/propertyguru/connect")
async def connect_propertyguru_account(
    payload: dict[str, str],
    session: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
    token: TokenData | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Mock endpoint to store PropertyGuru tokens."""

    user_id = _ensure_user(token)
    code = payload.get("code")
    redirect_uri = payload.get("redirect_uri", "")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    tokens = await mock_propertyguru.exchange_authorization_code(code, redirect_uri)
    account = await account_service.upsert_account(
        user_id=user_id,
        provider=ListingProvider.PROPERTYGURU,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_at=tokens.expires_at,
        metadata={"mode": "mock"},
        session=session,
    )
    return account.as_dict()


@router.post("/propertyguru/publish")
async def publish_propertyguru_listing(
    payload: dict[str, Any],
    session: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
    token: TokenData | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Mock publish endpoint that returns an echo payload."""

    user_id = _ensure_user(token)
    account = await account_service.get_account(
        user_id=user_id,
        provider=ListingProvider.PROPERTYGURU,
        session=session,
    )
    if account is None:
        raise HTTPException(status_code=404, detail="PropertyGuru account not linked")
    if not account_service.is_token_valid(account):
        raise HTTPException(status_code=401, detail="PropertyGuru access token expired")

    if account_service.needs_refresh(account):
        logger = structlog.get_logger()
        logger.info("propertyguru.token_refresh_required", account_id=account.id)

    listing_id, provider_payload = await mock_propertyguru.publish_listing(payload)
    return {"listing_id": listing_id, "provider_payload": provider_payload}


@router.post("/propertyguru/disconnect")
async def disconnect_propertyguru_account(
    session: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
    token: TokenData | None = Depends(get_optional_user),
) -> dict[str, Any]:
    user_id = _ensure_user(token)
    account = await account_service.get_account(
        user_id=user_id,
        provider=ListingProvider.PROPERTYGURU,
        session=session,
    )
    if account is None:
        raise HTTPException(status_code=404, detail="PropertyGuru account not linked")

    await account_service.revoke_account(account=account, session=session)
    return {"status": "disconnected", "provider": ListingProvider.PROPERTYGURU.value}
