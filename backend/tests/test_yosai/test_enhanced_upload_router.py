"""Regression tests for the enhanced upload router audit logging."""

from __future__ import annotations

import importlib
import json
import sqlite3
import sys
from pathlib import Path

import pytest

MODULE_PATH = (
    "backend.yosai_intel_dashboard.src.adapters.api.routes.enhanced_upload_router"
)


def _reload_router_module() -> None:
    sys.modules.pop(MODULE_PATH, None)
    importlib.import_module(MODULE_PATH)


def test_router_import_does_not_touch_read_only_filesystem(monkeypatch: pytest.MonkeyPatch) -> None:
    """Importing the router must not attempt filesystem writes."""

    monkeypatch.delenv("ENHANCED_UPLOAD_AUDIT_DB", raising=False)
    monkeypatch.delenv("ENHANCED_UPLOAD_AUDIT_DIR", raising=False)

    def _fail_write_bytes(self: Path, data: bytes) -> None:  # pragma: no cover - defensive
        raise PermissionError("Filesystem is read-only")

    monkeypatch.setattr(Path, "write_bytes", _fail_write_bytes, raising=True)

    def _fail_connect(*_args, **_kwargs) -> sqlite3.Connection:  # pragma: no cover - defensive
        raise AssertionError("sqlite3.connect should not be invoked during module import")

    monkeypatch.setattr(sqlite3, "connect", _fail_connect)

    _reload_router_module()


@pytest.mark.parametrize("env_var", ["ENHANCED_UPLOAD_AUDIT_DB", "ENHANCED_UPLOAD_AUDIT_DIR"])
def test_audit_records_persist_to_configured_location(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, env_var: str
) -> None:
    """Audit records persist to the configured writable location."""

    db_dir = tmp_path / "audit"
    db_dir.mkdir()
    db_path = db_dir / "custom.db"

    monkeypatch.setenv(env_var, str(db_path if env_var.endswith("_DB") else db_dir))

    module = importlib.import_module(MODULE_PATH)
    module.reset_audit_logger_cache()

    logger = module.get_audit_logger()
    logger.log_upload_event(
        actor="alice",
        filename="layout.pdf",
        status="accepted",
        payload={"project_id": 42},
    )

    resolved = module.resolve_audit_db_path()
    assert resolved.exists()
    assert resolved == db_path if env_var.endswith("_DB") else db_dir / "enhanced_upload_audit.db"

    with sqlite3.connect(resolved) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT actor, filename, status, payload FROM enhanced_upload_audit"
        ).fetchone()

    assert row["actor"] == "alice"
    assert row["filename"] == "layout.pdf"
    assert row["status"] == "accepted"
    assert json.loads(row["payload"]) == {"project_id": 42}

    module.reset_audit_logger_cache()

