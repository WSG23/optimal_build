"""Report generation job coverage."""

from __future__ import annotations

import os

from backend.app.services.storage import reset_storage_service
from backend.jobs.generate_reports import generate_market_report_bundle
import pytest


@pytest.fixture(autouse=True)
def _clear_storage(monkeypatch, tmp_path):
    monkeypatch.setenv("STORAGE_BUCKET", "")
    monkeypatch.setenv("STORAGE_PREFIX", "")
    monkeypatch.setenv("STORAGE_LOCAL_PATH", str(tmp_path))
    monkeypatch.delenv("STORAGE_RETENTION_DAYS", raising=False)
    monkeypatch.setenv("MARKET_REPORT_WEBHOOK_URL", "")
    reset_storage_service()
    yield
    reset_storage_service()


def test_generate_market_report_bundle(tmp_path):
    payload = {"records": 1}
    result = generate_market_report_bundle(payload)

    assert result["bytes_written"] > 0
    assert os.path.exists(tmp_path / result["key"])
