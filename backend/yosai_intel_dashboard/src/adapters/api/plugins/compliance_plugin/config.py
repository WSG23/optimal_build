"""Compliance plugin configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.yosai_intel_dashboard.src.config import get_settings

__all__ = ["ComplianceConfig"]


@dataclass(frozen=True, slots=True)
class ComplianceConfig:
    """Resolved configuration for compliance-related features."""

    audit_db_path: Path | None
    audit_directory: Path | None

    @classmethod
    def load(cls) -> "ComplianceConfig":
        """Load configuration from the global dashboard settings."""

        settings = get_settings()
        return cls(
            audit_db_path=settings.enhanced_upload_audit_db,
            audit_directory=settings.enhanced_upload_audit_dir,
        )

    def resolve_directory(self, fallback: Path) -> Path:
        """Return the directory that should persist compliance data."""

        if self.audit_directory is not None:
            return self.audit_directory
        return fallback

    def resolve_database_path(self, *, default_filename: str, fallback_directory: Path) -> Path:
        """Return the concrete database path for audit persistence."""

        if self.audit_db_path is not None:
            return self.audit_db_path
        directory = self.resolve_directory(fallback_directory)
        return directory / default_filename
