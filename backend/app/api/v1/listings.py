"""API endpoints for managing external listing integrations."""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import Role, get_request_role
from app.core.config import settings
from app.core.database import get_session
from app.core.jwt_auth import TokenData, get_optional_user
from app.models.listing_integration import ListingIntegrationAccount, ListingProvider
from app.services.integrations.accounts import ListingIntegrationAccountService
from app.services.integrations.edgeprop import EdgePropClient
from app.services.integrations.propertyguru import PropertyGuruClient
from app.services.integrations.zoho import ZohoClient
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/integrations/listings", tags=["Commercial Property Agent"])

account_service = ListingIntegrationAccountService()
CLIENTS: Dict[ListingProvider, Any] = {
    ListingProvider.PROPERTYGURU: PropertyGuruClient(
        client_id=settings.PROPERTYGURU_CLIENT_ID,
        client_secret=settings.PROPERTYGURU_CLIENT_SECRET,
        token_url=settings.PROPERTYGURU_TOKEN_URL,
        listing_url=settings.PROPERTYGURU_LISTING_URL,
    ),
    ListingProvider.EDGEPROP: EdgePropClient(
        client_id=settings.EDGEPROP_CLIENT_ID,
        client_secret=settings.EDGEPROP_CLIENT_SECRET,
        token_url=settings.EDGEPROP_TOKEN_URL,
        listing_url=settings.EDGEPROP_LISTING_URL,
    ),
    ListingProvider.ZOHO_CRM: ZohoClient(
        client_id=settings.ZOHO_CLIENT_ID,
        client_secret=settings.ZOHO_CLIENT_SECRET,
        token_url=settings.ZOHO_TOKEN_URL,
        listing_url=settings.ZOHO_LISTING_URL,
    ),
}
PROVIDER_METADATA: Dict[ListingProvider, Dict[str, str]] = {
    ListingProvider.PROPERTYGURU: {
        "label": "PropertyGuru",
        "description": "Singapore's leading property portal",
        "brand_color": "#00aaff",
    },
    ListingProvider.EDGEPROP: {
        "label": "EdgeProp",
        "description": "The Edge Singapore property platform",
        "brand_color": "#ff6b35",
    },
    ListingProvider.ZOHO_CRM: {
        "label": "Zoho CRM",
        "description": "CRM and lead management",
        "brand_color": "#e42527",
    },
}
logger = structlog.get_logger()


def _serialize_account(account: ListingIntegrationAccount) -> dict[str, Any]:
    return {
        "id": account.id,
        "user_id": account.user_id,
        "provider": account.provider.value,
        "status": account.status.value,
        "created_at": account.created_at.isoformat() if account.created_at else None,
        "updated_at": account.updated_at.isoformat() if account.updated_at else None,
        "metadata": account.metadata,
        "expires_at": account.expires_at.isoformat() if account.expires_at else None,
    }


def _serialize_provider(provider: ListingProvider) -> dict[str, Any]:
    meta = PROVIDER_METADATA.get(provider, {})
    label = meta.get("label") or provider.value.replace("_", " ").title()
    return {
        "provider": provider.value,
        "label": label,
        "description": meta.get("description", ""),
        "brand_color": meta.get("brand_color", ""),
    }


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
    return [_serialize_account(account) for account in accounts]


@router.get("/providers")
async def list_listing_providers() -> list[dict[str, Any]]:
    """Return supported listing providers and display metadata."""
    return [_serialize_provider(provider) for provider in ListingProvider]


@router.post("/{provider}/connect")
async def connect_account(
    provider: str,
    payload: dict[str, str],
    session: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
    token: TokenData | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Store external listing provider tokens for the current user."""

    user_id = _ensure_user(token)
    provider_enum = _resolve_provider(provider)
    code = payload.get("code")
    redirect_uri = payload.get("redirect_uri", "")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    client = _client_for(provider_enum)
    tokens = await client.exchange_authorization_code(code, redirect_uri)
    provider_meta = PROVIDER_METADATA.get(provider_enum, {})
    account = await account_service.upsert_account(
        user_id=user_id,
        provider=provider_enum,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_at=tokens.expires_at,
        metadata=provider_meta or None,
        session=session,
    )
    return _serialize_account(account)


@router.post("/{provider}/publish")
async def publish_listing(
    provider: str,
    payload: dict[str, Any],
    session: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
    token: TokenData | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Publish a listing payload to the external provider."""

    user_id = _ensure_user(token)
    provider_enum = _resolve_provider(provider)
    account = await account_service.get_account(
        user_id=user_id,
        provider=provider_enum,
        session=session,
    )
    if account is None:
        raise HTTPException(
            status_code=404, detail=f"{provider_enum.value.title()} account not linked"
        )
    if not account_service.is_token_valid(account):
        raise HTTPException(
            status_code=401,
            detail=f"{provider_enum.value.title()} access token expired",
        )

    if account_service.needs_refresh(account):
        logger.info(
            "listing.token_refresh_required",
            provider=provider_enum.value,
            account_id=account.id,
        )

    client = _client_for(provider_enum)
    listing_id, provider_payload = await client.publish_listing(
        payload, access_token=account.access_token
    )
    return {"listing_id": listing_id, "provider_payload": provider_payload}


@router.post("/{provider}/disconnect")
async def disconnect_account(
    provider: str,
    session: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
    token: TokenData | None = Depends(get_optional_user),
) -> dict[str, Any]:
    user_id = _ensure_user(token)
    provider_enum = _resolve_provider(provider)
    account = await account_service.get_account(
        user_id=user_id,
        provider=provider_enum,
        session=session,
    )
    if account is None:
        raise HTTPException(
            status_code=404, detail=f"{provider_enum.value.title()} account not linked"
        )

    await account_service.revoke_account(account=account, session=session)
    return {"status": "disconnected", "provider": provider_enum.value}


def _resolve_provider(value: str) -> ListingProvider:
    try:
        return ListingProvider(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=404, detail=f"Unknown provider '{value}'"
        ) from exc


def _client_for(provider: ListingProvider) -> Any:
    client = CLIENTS.get(provider)
    if client is None:
        raise HTTPException(
            status_code=501, detail=f"Provider '{provider.value}' not supported"
        )
    return client
