"""Background jobs for assembling analytics report bundles."""

from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Mapping

from app.services.storage import get_storage_service
from backend.jobs import job

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
    relative_key = f"{REPORT_PREFIX}/{target_name}" if REPORT_PREFIX else target_name
    output_path = storage.local_base_path / storage.prefix / relative_key
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(report_payload, indent=2, default=str)
    output_path.write_text(payload, encoding="utf-8")

    uri = storage._to_uri(Path(storage.prefix) / relative_key)  # type: ignore[attr-defined]

    return {
        "uri": uri,
        "bucket": storage.bucket,
        "key": f"{storage.prefix}/{relative_key}" if storage.prefix else relative_key,
        "bytes_written": len(payload.encode("utf-8")),
        "content_type": content_type,
        "stored_at": datetime.now(UTC).isoformat(),
    }


__all__ = ["generate_market_report_bundle"]
