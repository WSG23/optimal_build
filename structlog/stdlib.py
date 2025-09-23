"""Subset of :mod:`structlog.stdlib` reimplemented for the fallback package."""

from __future__ import annotations

import logging
from typing import Any

from ._internal import BoundLogger

__all__ = ["BoundLogger", "LoggerFactory"]


class LoggerFactory:
    """Mimic the behaviour of :class:`structlog.stdlib.LoggerFactory`."""

    def __call__(self, name: str | None = None, *args: Any, **kwargs: Any) -> logging.Logger:
        if name is None and args:
            name = args[0]
        if name is None:
            return logging.getLogger()
        return logging.getLogger(name)
