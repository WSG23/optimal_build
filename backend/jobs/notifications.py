"""Notification utilities for background jobs."""

from __future__ import annotations

import json
import logging
from typing import Any, Mapping

try:  # pragma: no cover - optional dependency
    import httpx  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - graceful degradation
    httpx = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


def notify_webhook(url: str | None, payload: Mapping[str, Any]) -> bool:
    """POST ``payload`` to the provided webhook URL when available."""

    if not url:
        return False
    if httpx is None:  # pragma: no cover - optional dependency missing
        logger.warning("httpx is not installed; skipping webhook notification")
        return False
    try:
        response = httpx.post(url, json=dict(payload), timeout=10.0)
        response.raise_for_status()
    except Exception as exc:  # pragma: no cover - best-effort notification
        logger.warning("Failed to deliver webhook notification: %s", exc)
        return False
    return True


__all__ = ["notify_webhook"]
