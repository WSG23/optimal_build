"""Zoho CRM integration client (mock)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Tuple

from backend._compat.datetime import utcnow

import structlog

logger = structlog.get_logger()


_DATACLASS_KWARGS = {"slots": True} if sys.version_info >= (3, 10) else {}


@dataclass(**_DATACLASS_KWARGS)
class OAuthBundle:
    access_token: str
    refresh_token: str
    expires_at: datetime


class ZohoClient:
    """Stub client for Zoho CRM interactions."""

    AUTH_BASE_URL = "https://accounts.zoho.com/oauth/v2"
    LEADS_BASE_URL = "https://www.zohoapis.com/crm/v2/Leads"

    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        self.client_id = client_id
        self.client_secret = client_secret

    async def exchange_authorization_code(
        self, code: str, redirect_uri: str
    ) -> OAuthBundle:
        logger.info("zoho.exchange_code", redirect_uri=redirect_uri)
        now = utcnow()
        return OAuthBundle(
            access_token=f"zoho-access-{code}",
            refresh_token=f"zoho-refresh-{code}",
            expires_at=now + timedelta(hours=1),
        )

    async def refresh_tokens(self, refresh_token: str) -> OAuthBundle:
        logger.info("zoho.refresh_token")
        now = utcnow()
        return OAuthBundle(
            access_token=f"zoho-access-{refresh_token[:8]}",
            refresh_token=refresh_token,
            expires_at=now + timedelta(hours=1),
        )

    async def publish_listing(
        self, payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        logger.info("zoho.publish_lead", payload_keys=list(payload.keys()))
        lead_id = payload.get("external_id", "zoho-lead")
        return lead_id, {"echo": payload}

    async def remove_listing(self, listing_id: str) -> bool:
        logger.info("zoho.remove_lead", listing_id=listing_id)
        return True
