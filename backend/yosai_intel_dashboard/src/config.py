"""Configuration entry-points for the Yosai Intel Dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.yosai_intel_dashboard.src.infrastructure.config.constants import API_PORT
from backend.yosai_intel_dashboard.src.infrastructure.config.dynamic_config import (
    dynamic_config,
)

__all__ = ["Settings", "get_settings"]


@dataclass(frozen=True, slots=True)
class Settings:
    """Container for resolved dashboard settings."""

    api_port: int
    enhanced_upload_audit_db: Path | None
    enhanced_upload_audit_dir: Path | None

    def as_dict(self) -> dict[str, Any]:
        """Expose the resolved settings as a serialisable mapping."""

        return {
            "api_port": self.api_port,
            "enhanced_upload_audit_db": (
                str(self.enhanced_upload_audit_db)
                if self.enhanced_upload_audit_db is not None
                else None
            ),
            "enhanced_upload_audit_dir": (
                str(self.enhanced_upload_audit_dir)
                if self.enhanced_upload_audit_dir is not None
                else None
            ),
        }


def _coerce_port(candidate: Any, default: int) -> int:
    try:
        value = int(str(candidate))
    except (TypeError, ValueError):
        return default

    if 0 < value <= 65535:
        return value
    return default


def _coerce_path(candidate: Any) -> Path | None:
    if candidate is None:
        return None

    text = str(candidate).strip()
    if not text:
        return None

    return Path(text).expanduser()


def get_settings() -> Settings:
    """Return the current dashboard settings snapshot."""

    config = dynamic_config.as_dict()
    return Settings(
        api_port=_coerce_port(config.get("API_PORT"), API_PORT),
        enhanced_upload_audit_db=_coerce_path(config.get("ENHANCED_UPLOAD_AUDIT_DB")),
        enhanced_upload_audit_dir=_coerce_path(config.get("ENHANCED_UPLOAD_AUDIT_DIR")),
    )
