"""Utility for obtaining a logger with a structlog-style API."""

from __future__ import annotations

import importlib.util
import logging
from typing import Any


class _StructlogShim:
    """Minimal shim that emulates structlog's logging API."""

    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)

    def bind(self, **_: object) -> "_StructlogShim":  # pragma: no cover - compatibility hook
        """Mimic structlog's ``bind`` returning a logger instance."""

        return self

    def _log(self, level: int, event: str, **kwargs: object) -> None:
        message = event
        if kwargs:
            extras = " ".join(f"{key}={value!r}" for key, value in sorted(kwargs.items()))
            message = f"{event} | {extras}"
        self._logger.log(level, message)

    def info(self, event: str, **kwargs: object) -> None:
        self._log(logging.INFO, event, **kwargs)

    def warning(self, event: str, **kwargs: object) -> None:
        self._log(logging.WARNING, event, **kwargs)

    def error(self, event: str, **kwargs: object) -> None:
        self._log(logging.ERROR, event, **kwargs)

    def debug(self, event: str, **kwargs: object) -> None:
        self._log(logging.DEBUG, event, **kwargs)

    def exception(self, event: str, **kwargs: object) -> None:
        self._log(logging.ERROR, event, **kwargs)

_STRUCTLOG_SPEC = importlib.util.find_spec("structlog")

if _STRUCTLOG_SPEC is not None:  # pragma: no cover - structlog unavailable in tests
    import structlog as _structlog

    def get_logger(name: str) -> Any:
        return _structlog.get_logger(name)
else:  # pragma: no cover - fallback covered in tests

    def get_logger(name: str) -> _StructlogShim:
        logging.basicConfig(level=logging.INFO)
        return _StructlogShim(name)


__all__ = ["get_logger"]
