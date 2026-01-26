"""Zoho CRM integration client."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Tuple

import httpx
import structlog
from backend._compat.datetime import utcnow

from app.core.config import settings

logger = structlog.get_logger()


_DATACLASS_KWARGS = {"slots": True} if sys.version_info >= (3, 10) else {}


@dataclass(**_DATACLASS_KWARGS)
class OAuthBundle:
    access_token: str
    refresh_token: str
    expires_at: datetime


class ZohoClient:
    """Client for Zoho CRM interactions."""

    AUTH_BASE_URL = "https://accounts.zoho.com/oauth/v2"
    LEADS_BASE_URL = "https://www.zohoapis.com/crm/v2/Leads"

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        token_url: str | None = None,
        listing_url: str | None = None,
    ) -> None:
        self.client_id = client_id or settings.ZOHO_CLIENT_ID
        self.client_secret = client_secret or settings.ZOHO_CLIENT_SECRET
        self.token_url = token_url or settings.ZOHO_TOKEN_URL
        self.listing_url = listing_url or settings.ZOHO_LISTING_URL
        try:
            self.client = httpx.AsyncClient(timeout=30.0)
        except RuntimeError:  # pragma: no cover
            logger.warning("httpx AsyncClient unavailable; Zoho disabled")
            self.client = None

    def _require_client(self) -> httpx.AsyncClient:
        if self.client is None:
            raise RuntimeError("Zoho HTTP client is unavailable")
        return self.client

    def _require_credentials(self) -> None:
        if not self.client_id or not self.client_secret:
            raise RuntimeError("Zoho OAuth credentials not configured")

    def _resolve_token_url(self) -> str:
        if self.token_url:
            return self.token_url
        return f"{self.AUTH_BASE_URL}/token"

    def _resolve_listing_url(self) -> str:
        if self.listing_url:
            return self.listing_url
        return self.LEADS_BASE_URL

    async def exchange_authorization_code(
        self, code: str, redirect_uri: str
    ) -> OAuthBundle:
        self._require_credentials()
        client = self._require_client()
        response = await client.post(
            self._resolve_token_url(),
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"Zoho token exchange failed with status {response.status_code}"
            )
        payload = response.json()
        access_token = payload.get("access_token")
        refresh_token = payload.get("refresh_token")
        expires_in = payload.get("expires_in") or payload.get("expiresIn")
        if not access_token or not refresh_token:
            raise RuntimeError("Zoho token response missing tokens")
        expires_at = utcnow() + timedelta(seconds=int(expires_in or 3600))
        return OAuthBundle(
            access_token=str(access_token),
            refresh_token=str(refresh_token),
            expires_at=expires_at,
        )

    async def refresh_tokens(self, refresh_token: str) -> OAuthBundle:
        self._require_credentials()
        client = self._require_client()
        response = await client.post(
            self._resolve_token_url(),
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"Zoho token refresh failed with status {response.status_code}"
            )
        payload = response.json()
        access_token = payload.get("access_token")
        new_refresh = payload.get("refresh_token") or refresh_token
        expires_in = payload.get("expires_in") or payload.get("expiresIn")
        if not access_token:
            raise RuntimeError("Zoho refresh response missing access token")
        expires_at = utcnow() + timedelta(seconds=int(expires_in or 3600))
        return OAuthBundle(
            access_token=str(access_token),
            refresh_token=str(new_refresh),
            expires_at=expires_at,
        )

    async def publish_listing(
        self, payload: Dict[str, Any], access_token: str | None = None
    ) -> Tuple[str, Dict[str, Any]]:
        if not access_token:
            raise RuntimeError("Zoho access token required")
        client = self._require_client()
        response = await client.post(
            self._resolve_listing_url(),
            json=payload,
            headers={"Authorization": f"Zoho-oauthtoken {access_token}"},
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"Zoho listing publish failed with status {response.status_code}"
            )
        response_payload = response.json()
        listing_id = response_payload.get("id") or payload.get("external_id")
        if not listing_id:
            raise RuntimeError("Zoho response missing listing id")
        return str(listing_id), response_payload

    async def remove_listing(
        self, listing_id: str, access_token: str | None = None
    ) -> bool:
        if not access_token:
            raise RuntimeError("Zoho access token required")
        client = self._require_client()
        response = await client.delete(
            f"{self._resolve_listing_url().rstrip('/')}/{listing_id}",
            headers={"Authorization": f"Zoho-oauthtoken {access_token}"},
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"Zoho listing delete failed with status {response.status_code}"
            )
        return True
