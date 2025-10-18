"""Storage service retention and persistence coverage."""

from __future__ import annotations

from datetime import datetime, timedelta
import os

from backend._compat.datetime import UTC
from backend.app.services.storage import StorageService


def test_store_bytes_and_retention(tmp_path):
    service = StorageService(
        bucket="",
        prefix="artifacts",
        local_base_path=tmp_path,
        endpoint_url=None,
    )

    result = service.store_bytes(
        key="reports/demo.json",
        payload=b"{}",
        content_type="application/json",
    )

    stored_file = tmp_path / "artifacts" / "reports" / "demo.json"
    assert stored_file.exists()
    assert result.content_type == "application/json"

    old_file = tmp_path / "artifacts" / "reports" / "old.json"
    old_file.parent.mkdir(parents=True, exist_ok=True)
    old_file.write_text("old", encoding="utf-8")
    cutoff = datetime.now(UTC) - timedelta(days=3)
    os.utime(old_file, (cutoff.timestamp(), cutoff.timestamp()))

    removed = service.purge_expired(prefix="artifacts", older_than_days=1)
    assert str((old_file).relative_to(tmp_path)) in removed
