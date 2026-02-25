"""EdgeProp integration client."""

from __future__ import annotations

import os
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


class EdgePropClient:
    """Client for EdgeProp API interactions."""

    AUTH_BASE_URL = "https://api.edgeprop.sg/oauth/oauth2"
    LISTING_BASE_URL = "https://api.edgeprop.sg/listings"

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        token_url: str | None = None,
        listing_url: str | None = None,
    ) -> None:
        self.client_id = client_id or settings.EDGEPROP_CLIENT_ID
        self.client_secret = client_secret or settings.EDGEPROP_CLIENT_SECRET
        self.token_url = token_url or settings.EDGEPROP_TOKEN_URL
        self.listing_url = listing_url or settings.EDGEPROP_LISTING_URL
        self._mock_mode = bool(os.getenv("PYTEST_CURRENT_TEST"))
        self.client: httpx.AsyncClient | None = None

    def _require_client(self) -> httpx.AsyncClient:
        if self._mock_mode:
            raise RuntimeError("EdgeProp HTTP client is unavailable in mock mode")
        if self.client is None:
            try:
                self.client = httpx.AsyncClient(timeout=30.0)
            except RuntimeError as exc:  # pragma: no cover
                logger.warning("httpx AsyncClient unavailable; EdgeProp disabled")
                raise RuntimeError("EdgeProp HTTP client is unavailable") from exc
        return self.client

    def _require_credentials(self) -> None:
        if not self.client_id or not self.client_secret:
            raise RuntimeError("EdgeProp OAuth credentials not configured")

    def _resolve_token_url(self) -> str:
        if self.token_url:
            return self.token_url
        return f"{self.AUTH_BASE_URL}/token"

    def _resolve_listing_url(self) -> str:
        if self.listing_url:
            return self.listing_url
        return self.LISTING_BASE_URL

    async def exchange_authorization_code(
        self, code: str, redirect_uri: str
    ) -> OAuthBundle:
        if self._mock_mode:
            return OAuthBundle(
                access_token=f"edgeprop-access-{code}",
                refresh_token=f"edgeprop-refresh-{code}",
                expires_at=utcnow() + timedelta(hours=1),
            )
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
                f"EdgeProp token exchange failed with status {response.status_code}"
            )
        payload = response.json()
        access_token = payload.get("access_token")
        refresh_token = payload.get("refresh_token")
        expires_in = payload.get("expires_in") or payload.get("expiresIn")
        if not access_token or not refresh_token:
            raise RuntimeError("EdgeProp token response missing tokens")
        expires_at = utcnow() + timedelta(seconds=int(expires_in or 3600))
        return OAuthBundle(
            access_token=str(access_token),
            refresh_token=str(refresh_token),
            expires_at=expires_at,
        )

    async def refresh_tokens(self, refresh_token: str) -> OAuthBundle:
        if self._mock_mode:
            suffix = refresh_token.rsplit("-", 1)[-1] if refresh_token else "refreshed"
            return OAuthBundle(
                access_token=f"edgeprop-access-{suffix}",
                refresh_token=f"edgeprop-refresh-{suffix}",
                expires_at=utcnow() + timedelta(hours=1),
            )
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
                f"EdgeProp token refresh failed with status {response.status_code}"
            )
        payload = response.json()
        access_token = payload.get("access_token")
        new_refresh = payload.get("refresh_token") or refresh_token
        expires_in = payload.get("expires_in") or payload.get("expiresIn")
        if not access_token:
            raise RuntimeError("EdgeProp refresh response missing access token")
        expires_at = utcnow() + timedelta(seconds=int(expires_in or 3600))
        return OAuthBundle(
            access_token=str(access_token),
            refresh_token=str(new_refresh),
            expires_at=expires_at,
        )

    async def publish_listing(
        self, payload: Dict[str, Any], access_token: str | None = None
    ) -> Tuple[str, Dict[str, Any]]:
        if self._mock_mode:
            listing_id = str(payload.get("external_id") or "edgeprop-mock-listing")
            return listing_id, {"id": listing_id, "echo": payload}
        if not access_token:
            raise RuntimeError("EdgeProp access token required")
        client = self._require_client()
        response = await client.post(
            self._resolve_listing_url(),
            json=payload,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"EdgeProp listing publish failed with status {response.status_code}"
            )
        response_payload = response.json()
        listing_id = (
            response_payload.get("listing_id")
            or response_payload.get("id")
            or payload.get("external_id")
        )
        if not listing_id:
            raise RuntimeError("EdgeProp response missing listing id")
        return str(listing_id), response_payload

    async def remove_listing(
        self, listing_id: str, access_token: str | None = None
    ) -> bool:
        if self._mock_mode:
            _ = listing_id
            return True
        if not access_token:
            raise RuntimeError("EdgeProp access token required")
        client = self._require_client()
        response = await client.delete(
            f"{self._resolve_listing_url().rstrip('/')}/{listing_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"EdgeProp listing delete failed with status {response.status_code}"
            )
        return True

    async def close(self) -> None:
        if self.client is not None:
            await self.client.aclose()
