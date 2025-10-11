"""EdgeProp integration client (mock)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Tuple

import structlog

logger = structlog.get_logger()


@dataclass(slots=True)
class OAuthBundle:
    access_token: str
    refresh_token: str
    expires_at: datetime


class EdgePropClient:
    """Stub client for EdgeProp API interactions."""

    AUTH_BASE_URL = "https://api.edgeprop.sg/oauth/oauth2"
    LISTING_BASE_URL = "https://api.edgeprop.sg/listings"

    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        self.client_id = client_id
        self.client_secret = client_secret

    async def exchange_authorization_code(
        self, code: str, redirect_uri: str
    ) -> OAuthBundle:
        logger.info("edgeprop.exchange_code", redirect_uri=redirect_uri)
        now = datetime.utcnow()
        return OAuthBundle(
            access_token=f"edgeprop-access-{code}",
            refresh_token=f"edgeprop-refresh-{code}",
            expires_at=now + timedelta(hours=1),
        )

    async def refresh_tokens(self, refresh_token: str) -> OAuthBundle:
        logger.info("edgeprop.refresh_token")
        now = datetime.utcnow()
        return OAuthBundle(
            access_token=f"edgeprop-access-{refresh_token[:8]}",
            refresh_token=refresh_token,
            expires_at=now + timedelta(hours=1),
        )

    async def publish_listing(
        self, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        logger.info("edgeprop.publish_listing", payload_keys=list(payload.keys()))
        listing_id = payload.get("external_id", "edgeprop-listing")
        return listing_id, {"echo": payload}

    async def remove_listing(self, listing_id: str) -> bool:
        logger.info("edgeprop.remove_listing", listing_id=listing_id)
        return True
