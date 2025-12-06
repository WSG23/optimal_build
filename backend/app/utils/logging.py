"""Structured logging helpers."""

from __future__ import annotations

import structlog
from structlog.stdlib import BoundLogger

import json
import logging
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Protocol, cast
from uuid import UUID


class _MetadataModule(Protocol):
    """Minimal protocol for importlib metadata providers."""

    PackageNotFoundError: type[Exception]

    def version(self, distribution: str) -> str: ...


importlib_metadata: _MetadataModule | None

try:  # pragma: no cover - importlib.metadata available on Python 3.8+
    from importlib import metadata as _importlib_metadata_module
except ImportError:  # pragma: no cover - runtime older than Python 3.8
    try:
        import importlib_metadata as _importlib_metadata_backport  # type: ignore
    except ModuleNotFoundError:  # pragma: no cover - no metadata helpers available
        importlib_metadata = None
    else:
        importlib_metadata = cast(_MetadataModule, _importlib_metadata_backport)
else:
    importlib_metadata = cast(_MetadataModule, _importlib_metadata_module)


class _PackageNotFoundError(Exception):
    """Fallback when metadata helpers are unavailable."""


PackageNotFoundError: type[Exception]
if importlib_metadata is not None:
    PackageNotFoundError = importlib_metadata.PackageNotFoundError
else:
    PackageNotFoundError = _PackageNotFoundError

from app.core.config import settings


def _structlog_distribution_present() -> bool:
    """Return ``True`` when the real ``structlog`` package is installed."""

    metadata_module = importlib_metadata
    if metadata_module is None:
        return False
    try:
        metadata_module.version("structlog")
    except PackageNotFoundError:
        return False
    except Exception:  # pragma: no cover - defensive against metadata issues
        return False
    return True


if (
    getattr(structlog, "_IS_VENDORED_STRUCTLOG", False)
    and not _structlog_distribution_present()
):
    logging.getLogger(__name__).warning(
        "structlog distribution not installed; using vendored fallback stub."
    )


def configure_logging() -> None:
    """Configure structlog for the application."""

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(level=log_level, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> BoundLogger:
    """Return a structured logger."""

    logger = structlog.get_logger(name)
    return logger.bind(app=settings.PROJECT_NAME)


def _serialise_for_logging(value: Any) -> Any:
    """Convert *value* into something JSON serialisable for structlog."""

    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (Decimal,)):  # quantised textual representation
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _serialise_for_logging(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_serialise_for_logging(item) for item in value]
    try:
        json.dumps(value)
    except TypeError:
        return str(value)
    return value


def log_event(logger: BoundLogger, event: str, **kwargs: Any) -> None:
    """Emit a structured info log with consistent naming."""

    serialised_kwargs = {
        key: _serialise_for_logging(value) for key, value in kwargs.items()
    }
    logger.info(event, **serialised_kwargs)
