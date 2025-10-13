"""PropertyGuru integration client (scaffolding)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Tuple

import structlog

from backend._compat.datetime import utcnow

logger = structlog.get_logger()


_DATACLASS_KWARGS = {"slots": True} if sys.version_info >= (3, 10) else {}


@dataclass(**_DATACLASS_KWARGS)
class OAuthTokenBundle:
    access_token: str
    refresh_token: str
    expires_at: datetime


class PropertyGuruClient:
    """Stub client for PropertyGuru API interactions."""

    AUTH_BASE_URL = "https://api.propertyguru.com.sg/oauth"
    LISTING_BASE_URL = "https://api.propertyguru.com.sg/listings"

    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        self.client_id = client_id
        self.client_secret = client_secret

    async def exchange_authorization_code(
        self, code: str, redirect_uri: str
    ) -> OAuthTokenBundle:
        """Exchange an authorization code for access/refresh tokens.

        PropertyGuru's real API requires a POST to their OAuth endpoint; for now we
        return a placeholder bundle and log the usage so callers can wire the real
        implementation later.
        """

        logger.info(
            "propertyguru.exchange_code",
            redirect_uri=redirect_uri,
        )
        now = utcnow()
        return OAuthTokenBundle(
            access_token=f"mock-access-{code}",
            refresh_token=f"mock-refresh-{code}",
            expires_at=now + timedelta(hours=1),
        )

    async def refresh_tokens(self, refresh_token: str) -> OAuthTokenBundle:
        logger.info("propertyguru.refresh_token")
        now = utcnow()
        return OAuthTokenBundle(
            access_token=f"mock-access-{refresh_token[:8]}",
            refresh_token=refresh_token,
            expires_at=now + timedelta(hours=1),
        )

    async def publish_listing(
        self, listing_payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Publish or update a listing on PropertyGuru (stub)."""

        logger.info(
            "propertyguru.publish_listing", payload_keys=list(listing_payload.keys())
        )
        listing_id = listing_payload.get("external_id", "mock-listing")
        return listing_id, {"echo": listing_payload}

    async def remove_listing(self, listing_id: str) -> bool:
        logger.info("propertyguru.remove_listing", listing_id=listing_id)
        return True
