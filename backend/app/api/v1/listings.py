"""API endpoints for managing external listing integrations (mock)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, cast
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Role, get_request_role
from app.core.database import get_session
from app.core.jwt_auth import TokenData, get_optional_user
from app.models.listing_integration import (
    ListingIntegrationAccount,
    ListingPublication,
    ListingPublicationStatus,
    ListingProvider,
)
from app.services.analytics_capture import (
    capture_external_call,
    capture_failure,
    capture_rejection,
    capture_status_transition,
    capture_success,
)
from app.services.integrations.accounts import ListingIntegrationAccountService
from app.services.integrations.edgeprop import EdgePropClient
from app.services.integrations.propertyguru import PropertyGuruClient
from app.services.integrations.zoho import ZohoClient

router = APIRouter(prefix="/integrations/listings", tags=["Commercial Property Agent"])

account_service = ListingIntegrationAccountService()
CLIENTS: Dict[ListingProvider, Any] = {
    ListingProvider.PROPERTYGURU: PropertyGuruClient(),
    ListingProvider.EDGEPROP: EdgePropClient(),
    ListingProvider.ZOHO_CRM: ZohoClient(),
}
logger = structlog.get_logger()
REQUEST_NONE = cast(Request, None)


async def _commit_if_supported(session: Any) -> None:
    commit = getattr(session, "commit", None)
    if commit is not None:
        await commit()


def _request_id(request: Request | None) -> str | None:
    return request.headers.get("x-request-id") if request is not None else None


def _correlation_id(request: Request | None) -> str | None:
    if request is None:
        return None
    value = request.scope.get("correlation_id")
    return str(value) if value is not None else None


def _serialize_account(account: ListingIntegrationAccount) -> dict[str, Any]:
    client = CLIENTS.get(account.provider)
    provider_status = (
        client.source_metadata().model_dump(mode="json")
        if client is not None and hasattr(client, "source_metadata")
        else None
    )
    return {
        "id": account.id,
        "user_id": account.user_id,
        "provider": account.provider.value,
        "status": account.status.value,
        "created_at": account.created_at.isoformat() if account.created_at else None,
        "updated_at": account.updated_at.isoformat() if account.updated_at else None,
        "metadata": account.metadata,
        "expires_at": account.expires_at.isoformat() if account.expires_at else None,
        "provider_status": provider_status,
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


@router.post("/{provider}/connect")
async def connect_account(
    provider: str,
    payload: dict[str, str],
    request: Request = REQUEST_NONE,
    session: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
    token: TokenData | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Mock endpoint to store PropertyGuru tokens."""

    user_id = _ensure_user(token)
    provider_enum = _resolve_provider(provider)
    code = payload.get("code")
    redirect_uri = payload.get("redirect_uri", "")
    if not code:
        if request is not None:
            await capture_rejection(
                source="listings.connect",
                reason="Missing authorization code",
                request=request,
                request_payload=payload,
                status_code=400,
                operation="connect_account",
            )
        raise HTTPException(status_code=400, detail="Missing authorization code")

    client = _client_for(provider_enum)
    try:
        tokens = await client.exchange_authorization_code(code, redirect_uri)
    except Exception as exc:
        await capture_external_call(
            session,
            provider=provider_enum.value,
            api_name="oauth_token_exchange",
            endpoint="exchange_authorization_code",
            method="POST",
            request_payload=payload,
            error=exc,
            request_id=_request_id(request),
            correlation_id=_correlation_id(request),
        )
        if request is not None:
            await capture_failure(
                source="listings.connect",
                error=exc,
                request=request,
                request_payload=payload,
                operation="connect_account",
                status_code=502,
            )
        await _commit_if_supported(session)
        raise HTTPException(
            status_code=502,
            detail=f"{provider_enum.value.title()} authorization failed",
        ) from exc
    await capture_external_call(
        session,
        provider=provider_enum.value,
        api_name="oauth_token_exchange",
        endpoint="exchange_authorization_code",
        method="POST",
        request_payload=payload,
        response_payload={
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "expires_at": tokens.expires_at,
        },
        status_code=200,
        request_id=_request_id(request),
        correlation_id=_correlation_id(request),
    )
    account = await account_service.upsert_account(
        user_id=user_id,
        provider=provider_enum,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_at=tokens.expires_at,
        metadata={"mode": "mock"},
        session=session,
    )
    await capture_status_transition(
        session,
        entity_type="listing_integration_account",
        entity_id=str(account.id),
        status_field="status",
        from_status=None,
        to_status="connected",
        reason="oauth_connect",
        request_id=_request_id(request),
        correlation_id=_correlation_id(request),
        metadata={"provider": provider_enum.value, "redirect_uri": redirect_uri},
    )
    await capture_success(
        session,
        source="listings.connect",
        operation="connect_account",
        request=request,
        request_payload=payload,
        response_payload={
            "account_id": str(account.id),
            "provider": provider_enum.value,
        },
        entity_type="listing_integration_account",
        entity_id=str(account.id),
        provider=provider_enum.value,
    )
    await _commit_if_supported(session)
    return _serialize_account(account)


@router.post("/{provider}/publish")
async def publish_listing(
    provider: str,
    payload: dict[str, Any],
    request: Request = REQUEST_NONE,
    session: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
    token: TokenData | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """Mock publish endpoint that returns an echo payload."""

    user_id = _ensure_user(token)
    provider_enum = _resolve_provider(provider)
    account = await account_service.get_account(
        user_id=user_id,
        provider=provider_enum,
        session=session,
    )
    if account is None:
        if request is not None:
            await capture_rejection(
                source="listings.publish",
                reason=f"{provider_enum.value.title()} account not linked",
                request=request,
                request_payload=payload,
                status_code=404,
                operation="publish_listing",
            )
        raise HTTPException(
            status_code=404, detail=f"{provider_enum.value.title()} account not linked"
        )
    if not account_service.is_token_valid(account):
        if request is not None:
            await capture_rejection(
                source="listings.publish",
                reason=f"{provider_enum.value.title()} access token expired",
                request=request,
                request_payload=payload,
                status_code=401,
                operation="publish_listing",
            )
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
    provider_status = (
        client.source_metadata().model_dump(mode="json")
        if hasattr(client, "source_metadata")
        else None
    )
    publication: ListingPublication | None = None
    raw_property_id = payload.get("property_id")
    if raw_property_id:
        publication = ListingPublication(
            property_id=UUID(str(raw_property_id)),
            account_id=account.id,
            status=ListingPublicationStatus.QUEUED,
            payload={
                "request": payload,
                "provider_status": provider_status,
            },
            last_synced_at=datetime.now(timezone.utc),
        )
        session.add(publication)
        await session.flush()
    try:
        listing_id, provider_payload = await client.publish_listing(payload)
    except Exception as exc:
        if publication is not None:
            publication.status = ListingPublicationStatus.FAILED
            publication.last_error = str(exc)
            publication.last_synced_at = datetime.now(timezone.utc)
            publication.payload = {
                "request": payload,
                "provider_status": provider_status,
                "error": str(exc),
            }
            await capture_status_transition(
                session,
                entity_type="listing_publication",
                entity_id=str(publication.id),
                status_field="status",
                from_status=ListingPublicationStatus.QUEUED.value,
                to_status=ListingPublicationStatus.FAILED.value,
                reason="provider_publish_failed",
                request_id=_request_id(request),
                correlation_id=_correlation_id(request),
                metadata={"provider": provider_enum.value, "error": str(exc)},
            )
        await capture_external_call(
            session,
            provider=provider_enum.value,
            api_name="listing_publish",
            endpoint="publish_listing",
            method="POST",
            request_payload=payload,
            status_code=502,
            error=exc,
            metadata={"provider_status": provider_status},
            request_id=_request_id(request),
            correlation_id=_correlation_id(request),
            entity_type="listing_publication",
            entity_id=str(publication.id) if publication is not None else None,
        )
        if request is not None:
            await capture_failure(
                source="listings.publish",
                error=exc,
                request=request,
                request_payload=payload,
                raw_payload={"provider_status": provider_status},
                operation="publish_listing",
                status_code=502,
            )
        await _commit_if_supported(session)
        raise HTTPException(
            status_code=502,
            detail=f"{provider_enum.value.title()} publish failed",
        ) from exc
    if publication is not None:
        publication.provider_listing_id = str(listing_id)
        publication.status = ListingPublicationStatus.PUBLISHED
        publication.published_at = datetime.now(timezone.utc)
        publication.last_synced_at = datetime.now(timezone.utc)
        publication.payload = {
            "request": payload,
            "provider_payload": provider_payload,
            "provider_status": provider_status,
        }
        await capture_status_transition(
            session,
            entity_type="listing_publication",
            entity_id=str(publication.id),
            status_field="status",
            from_status=ListingPublicationStatus.QUEUED.value,
            to_status=ListingPublicationStatus.PUBLISHED.value,
            reason="provider_publish_success",
            request_id=_request_id(request),
            correlation_id=_correlation_id(request),
            metadata={
                "provider": provider_enum.value,
                "provider_listing_id": listing_id,
            },
        )
    await capture_external_call(
        session,
        provider=provider_enum.value,
        api_name="listing_publish",
        endpoint="publish_listing",
        method="POST",
        request_payload=payload,
        response_payload=provider_payload,
        status_code=200,
        metadata={"provider_status": provider_status},
        request_id=_request_id(request),
        correlation_id=_correlation_id(request),
        entity_type="listing_publication",
        entity_id=str(publication.id) if publication is not None else None,
    )
    await capture_success(
        session,
        source="listings.publish",
        operation="publish_listing",
        request=request,
        request_payload=payload,
        response_payload={
            "listing_id": listing_id,
            "provider_payload": provider_payload,
            "provider_status": provider_status,
            "publication_id": str(publication.id) if publication is not None else None,
        },
        entity_type="listing_publication",
        entity_id=str(publication.id) if publication is not None else None,
        provider=provider_enum.value,
    )
    await _commit_if_supported(session)
    return {
        "listing_id": listing_id,
        "provider_payload": provider_payload,
        "provider_status": provider_status,
    }


@router.post("/{provider}/disconnect")
async def disconnect_account(
    provider: str,
    request: Request = REQUEST_NONE,
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
    await capture_status_transition(
        session,
        entity_type="listing_integration_account",
        entity_id=str(account.id),
        status_field="status",
        from_status="connected",
        to_status="revoked",
        reason="disconnect_account",
        request_id=_request_id(request),
        correlation_id=_correlation_id(request),
        metadata={"provider": provider_enum.value},
    )
    client = _client_for(provider_enum)
    provider_status = (
        client.source_metadata().model_dump(mode="json")
        if hasattr(client, "source_metadata")
        else None
    )
    await capture_success(
        session,
        source="listings.disconnect",
        operation="disconnect_account",
        request=request,
        response_payload={"status": "disconnected", "provider": provider_enum.value},
        entity_type="listing_integration_account",
        entity_id=str(account.id),
        provider=provider_enum.value,
    )
    await _commit_if_supported(session)
    return {
        "status": "disconnected",
        "provider": provider_enum.value,
        "provider_status": provider_status,
    }


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
