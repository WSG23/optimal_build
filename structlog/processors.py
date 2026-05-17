"""Subset of :mod:`structlog.processors` required by the application."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, MutableMapping
from typing import Any

try:  # Python 3.11 provides datetime.UTC; older versions require timezone.utc
    from datetime import UTC, datetime  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - fallback for Python < 3.11
    from datetime import datetime, timezone

    UTC = timezone.utc

__all__ = [
    "JSONRenderer",
    "StackInfoRenderer",
    "TimeStamper",
    "add_log_level",
    "format_exc_info",
]


def add_log_level(
    _: logging.Logger, method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """Annotate *event_dict* with the level name if one is not already set."""

    event_dict.setdefault("level", method_name)
    return event_dict


class TimeStamper:
    """Mimic :class:`structlog.processors.TimeStamper` for timestamp injection."""

    def __init__(self, fmt: str, utc: bool = False) -> None:
        self.fmt = fmt
        self.utc = utc

    def __call__(
        self, _: logging.Logger, __: str, event_dict: MutableMapping[str, Any]
    ) -> MutableMapping[str, Any]:
        now = datetime.now(UTC if self.utc else None)
        if self.fmt == "iso":
            event_dict["timestamp"] = now.isoformat()
        else:
            event_dict["timestamp"] = now.strftime(self.fmt)
        return event_dict


def StackInfoRenderer() -> (
    Callable[[logging.Logger, str, MutableMapping[str, Any]], MutableMapping[str, Any]]
):
    """Return a renderer compatible with the real structlog API."""

    def _renderer(
        _: logging.Logger, __: str, event_dict: MutableMapping[str, Any]
    ) -> MutableMapping[str, Any]:
        return event_dict

    return _renderer


def format_exc_info(
    _: logging.Logger, __: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """Passthrough that retains the structure expected by the application."""

    return event_dict


def _json_default(value: Any) -> Any:
    """Best-effort conversion for JSON-incompatible values in log records.

    Why: Application code passes UUIDs, datetimes, Decimals, Paths, and Pydantic
    models as structured log fields. Without this fallback, a single such field
    causes ``json.dumps`` to raise, which crashes the request the logger is
    serving (the renderer runs inside the request path).
    """

    try:
        from datetime import date, datetime
        from decimal import Decimal
        from pathlib import PurePath
        from uuid import UUID
    except Exception:  # pragma: no cover - imports always succeed
        return str(value)

    if isinstance(value, (UUID, PurePath)):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (set, frozenset, tuple)):
        return list(value)
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return value.hex()
    return str(value)


class JSONRenderer:
    """Render an event dictionary as a JSON string."""

    def __call__(
        self, _: logging.Logger, __: str, event_dict: MutableMapping[str, Any]
    ) -> str:
        return json.dumps(event_dict, default=_json_default)
