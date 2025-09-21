"""Structured logging helpers."""

from __future__ import annotations

import logging
from typing import Any

import structlog
from structlog.stdlib import BoundLogger

from app.core.config import settings


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


def log_event(logger: BoundLogger, event: str, **kwargs: Any) -> None:
    """Emit a structured info log with consistent naming."""

    logger.info(event, **kwargs)
