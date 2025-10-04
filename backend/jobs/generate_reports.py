"""Background jobs for assembling analytics report bundles."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Mapping

from app.services.storage import get_storage_service
from backend._compat.datetime import UTC
from backend.jobs import job
from backend.jobs.notifications import notify_webhook

REPORT_PREFIX = "reports"


def _default_filename(suffix: str = "json") -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"market-report-{timestamp}.{suffix}"


@job(name="market.generate_report_bundle")
def generate_market_report_bundle(
    report_payload: Mapping[str, Any],
    *,
    filename: str | None = None,
    content_type: str = "application/json",
) -> dict[str, Any]:
    """Persist a market report bundle to object storage.

    The job serialises ``report_payload`` as JSON and writes it to the configured
    storage backend. A dictionary describing the stored artefact is returned so
    callers can surface download links or auditing information.
    """

    storage = get_storage_service()
    target_name = filename or _default_filename()
    payload_bytes = json.dumps(report_payload, indent=2, default=str).encode("utf-8")
    result = storage.store_bytes(
        key=f"{REPORT_PREFIX}/{target_name}",
        payload=payload_bytes,
        content_type=content_type,
    )

    event_payload = {
        **result.as_dict(),
        "stored_at": datetime.now(UTC).isoformat(),
    }

    webhook_url = os.getenv("MARKET_REPORT_WEBHOOK_URL")
    notify_webhook(webhook_url, event_payload)

    return event_payload


__all__ = ["generate_market_report_bundle"]
