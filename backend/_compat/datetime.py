"""Compatibility helpers for datetime timezone constants."""

from __future__ import annotations

from datetime import datetime, timezone

try:  # Python 3.11+
    from datetime import UTC  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - fallback for older interpreters
    UTC = timezone.utc  # type: ignore[assignment]

__all__ = ["UTC", "datetime"]
