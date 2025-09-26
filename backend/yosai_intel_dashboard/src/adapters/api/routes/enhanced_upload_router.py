"""Enhanced upload router with configurable compliance audit logging."""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, MutableMapping

try:  # pragma: no cover - fallback for environments without FastAPI installed
    from fastapi import APIRouter, Depends
except ModuleNotFoundError:  # pragma: no cover
    from backend._stub_loader import load_package_stub

    load_package_stub("fastapi", "fastapi_stub_1758768319", "FastAPI")
    from fastapi import APIRouter, Depends

try:  # pragma: no cover - fallback for environments without Pydantic installed
    from pydantic import BaseModel, Field
except ModuleNotFoundError:  # pragma: no cover
    from backend._stub_loader import load_package_stub

    load_package_stub("pydantic", "pydantic", "Pydantic")
    from pydantic import BaseModel, Field

__all__ = [
    "AUDIT_DB_ENV_VAR",
    "ComplianceAuditLogger",
    "EnhancedUploadAuditRecord",
    "get_audit_logger",
    "get_audit_logger_dependency",
    "router",
]

AUDIT_DB_ENV_VAR = "ENHANCED_UPLOAD_AUDIT_DB"
AUDIT_DIR_ENV_VAR = "ENHANCED_UPLOAD_AUDIT_DIR"
_DEFAULT_DB_FILENAME = "enhanced_upload_audit.db"


def _resolve_storage_directory() -> Path:
    """Return the base directory for persisting audit data."""

    override = os.getenv(AUDIT_DIR_ENV_VAR)
    if override:
        return Path(override).expanduser()

    xdg_data_home = os.getenv("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home).expanduser() / "yosai_intel_dashboard"

    return Path(tempfile.gettempdir()) / "yosai_intel_dashboard"


def resolve_audit_db_path() -> Path:
    """Return the configured SQLite database path for audit persistence."""

    override = os.getenv(AUDIT_DB_ENV_VAR)
    if override:
        return Path(override).expanduser()

    base_dir = _resolve_storage_directory()
    return base_dir / _DEFAULT_DB_FILENAME


@dataclass(slots=True)
class ComplianceAuditLogger:
    """Persist compliance audit records for enhanced uploads."""

    db_path: Path

    def __post_init__(self) -> None:
        self._initialise_database()

    def _initialise_database(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS enhanced_upload_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    actor TEXT,
                    filename TEXT,
                    status TEXT,
                    payload TEXT
                )
                """
            )
            connection.commit()

    def log_upload_event(
        self,
        *,
        actor: str | None,
        filename: str | None,
        status: str,
        payload: Mapping[str, Any] | None = None,
    ) -> None:
        """Persist an audit record for an enhanced upload operation."""

        serialised = json.dumps(payload or {}, default=str)
        created_at = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO enhanced_upload_audit (
                    created_at,
                    actor,
                    filename,
                    status,
                    payload
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (created_at, actor, filename, status, serialised),
            )
            connection.commit()


class EnhancedUploadAuditRecord(BaseModel):
    """Payload accepted by the audit endpoint."""

    actor: str | None = Field(default=None, description="Identity triggering the upload")
    filename: str | None = Field(default=None, description="Uploaded file name")
    status: str = Field(description="Outcome of the upload workflow")
    payload: MutableMapping[str, Any] | None = Field(
        default=None, description="Additional metadata captured for the upload"
    )


@lru_cache(maxsize=1)
def _build_logger(db_path: str) -> ComplianceAuditLogger:
    return ComplianceAuditLogger(Path(db_path))


def reset_audit_logger_cache() -> None:
    """Clear the cached audit logger instance (useful for tests)."""

    _build_logger.cache_clear()  # type: ignore[attr-defined]


def get_audit_logger() -> ComplianceAuditLogger:
    """Return a cached audit logger backed by the configured database."""

    db_path = resolve_audit_db_path()
    return _build_logger(str(db_path))


def get_audit_logger_dependency() -> ComplianceAuditLogger:
    """Expose ``ComplianceAuditLogger`` as a FastAPI dependency."""

    return get_audit_logger()


router = APIRouter(prefix="/enhanced-upload", tags=["Enhanced Upload"])


@router.post("/audit", status_code=201)
async def record_enhanced_upload_audit(
    record: EnhancedUploadAuditRecord,
    audit_logger: ComplianceAuditLogger = Depends(get_audit_logger_dependency),
) -> dict[str, str]:
    """Record an enhanced upload audit event and acknowledge receipt."""

    audit_logger.log_upload_event(
        actor=record.actor,
        filename=record.filename,
        status=record.status,
        payload=dict(record.payload or {}),
    )
    return {"detail": "audit record stored"}
