"""Subset of :mod:`structlog.processors` required by the application."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Callable, MutableMapping

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
        now = datetime.now(timezone.utc if self.utc else None)
        if self.fmt == "iso":
            event_dict["timestamp"] = now.isoformat()
        else:
            event_dict["timestamp"] = now.strftime(self.fmt)
        return event_dict


def StackInfoRenderer() -> Callable[[logging.Logger, str, MutableMapping[str, Any]], MutableMapping[str, Any]]:
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


class JSONRenderer:
    """Render an event dictionary as a JSON string."""

    def __call__(
        self, _: logging.Logger, __: str, event_dict: MutableMapping[str, Any]
    ) -> str:
        return json.dumps(event_dict)
