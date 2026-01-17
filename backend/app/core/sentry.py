"""Sentry error tracking integration.

This module provides Sentry initialization and configuration for
production error tracking and performance monitoring.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_sentry_initialized = False


def init_sentry(
    dsn: str | None = None,
    environment: str | None = None,
    release: str | None = None,
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1,
) -> bool:
    """Initialize Sentry error tracking.

    Args:
        dsn: Sentry DSN. If not provided, uses SENTRY_DSN env var.
        environment: Environment name (production, staging, development).
        release: Application version/release identifier.
        traces_sample_rate: Percentage of transactions to trace (0.0 to 1.0).
        profiles_sample_rate: Percentage of transactions to profile (0.0 to 1.0).

    Returns:
        True if Sentry was initialized successfully, False otherwise.
    """
    global _sentry_initialized

    if _sentry_initialized:
        logger.debug("Sentry already initialized")
        return True

    dsn = dsn or os.getenv("SENTRY_DSN")
    if not dsn:
        logger.info("Sentry DSN not configured, error tracking disabled")
        return False

    environment = environment or os.getenv("ENVIRONMENT", "development")
    release = release or os.getenv("PROJECT_VERSION", "1.0.0")

    try:
        import sentry_sdk
        from sentry_sdk.integrations.asyncio import AsyncioIntegration
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        # Configure logging integration
        logging_integration = LoggingIntegration(
            level=logging.INFO,  # Capture INFO and above as breadcrumbs
            event_level=logging.ERROR,  # Send ERROR and above as events
        )

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=f"optimal-build@{release}",
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                StarletteIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                AsyncioIntegration(),
                logging_integration,
            ],
            # Performance monitoring settings
            enable_tracing=True,
            # Security settings
            send_default_pii=False,  # Don't send personally identifiable information
            # Filtering
            before_send=_before_send,
            before_send_transaction=_before_send_transaction,
            # Additional options
            attach_stacktrace=True,
            include_local_variables=True,
            max_breadcrumbs=50,
        )

        _sentry_initialized = True
        logger.info(
            f"Sentry initialized for environment={environment}, release={release}"
        )
        return True

    except ImportError:
        logger.warning("sentry-sdk not installed, error tracking disabled")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return False


def _before_send(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """Filter events before sending to Sentry.

    Args:
        event: The event data.
        hint: Additional hint data including the original exception.

    Returns:
        The event to send, or None to drop the event.
    """
    # Don't send events in development
    if os.getenv("ENVIRONMENT") == "development":
        return None

    # Filter out expected errors
    if "exc_info" in hint:
        exc_type, exc_value, _ = hint["exc_info"]
        exc_name = exc_type.__name__ if exc_type else ""

        # Don't send rate limit errors
        if exc_name == "RateLimitExceeded":
            return None

        # Don't send validation errors
        if exc_name in ("ValidationError", "RequestValidationError"):
            return None

        # Don't send expected HTTP errors
        if exc_name == "HTTPException":
            status_code = getattr(exc_value, "status_code", 500)
            if status_code in (400, 401, 403, 404, 422):
                return None

    # Scrub sensitive data from request
    if "request" in event:
        request = event["request"]
        if "headers" in request:
            headers = request["headers"]
            # Remove authorization headers
            sensitive_headers = [
                "authorization",
                "x-api-key",
                "cookie",
                "x-csrf-token",
            ]
            for header in sensitive_headers:
                if header in headers:
                    headers[header] = "[Filtered]"

        # Remove sensitive query params
        if "query_string" in request:
            query = request["query_string"]
            if "token" in query or "key" in query or "password" in query:
                request["query_string"] = "[Filtered]"

    return event


def _before_send_transaction(
    event: dict[str, Any], hint: dict[str, Any]
) -> dict[str, Any] | None:
    """Filter transactions before sending to Sentry.

    Args:
        event: The transaction data.
        hint: Additional hint data.

    Returns:
        The transaction to send, or None to drop it.
    """
    # Don't trace health checks
    transaction_name = event.get("transaction", "")
    if transaction_name in ("/health", "/metrics", "/health/metrics"):
        return None

    return event


def capture_exception(error: Exception, **context: Any) -> str | None:
    """Capture an exception and send it to Sentry.

    Args:
        error: The exception to capture.
        **context: Additional context to attach to the event.

    Returns:
        The Sentry event ID if captured, None otherwise.
    """
    if not _sentry_initialized:
        return None

    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_extra(key, value)
            return sentry_sdk.capture_exception(error)
    except Exception as e:
        logger.error(f"Failed to capture exception in Sentry: {e}")
        return None


def capture_message(message: str, level: str = "info", **context: Any) -> str | None:
    """Capture a message and send it to Sentry.

    Args:
        message: The message to capture.
        level: Log level (debug, info, warning, error, fatal).
        **context: Additional context to attach to the event.

    Returns:
        The Sentry event ID if captured, None otherwise.
    """
    if not _sentry_initialized:
        return None

    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_extra(key, value)
            return sentry_sdk.capture_message(message, level=level)
    except Exception as e:
        logger.error(f"Failed to capture message in Sentry: {e}")
        return None


def set_user(user_id: str | int, email: str | None = None, **extra: Any) -> None:
    """Set the current user context for Sentry.

    Args:
        user_id: Unique user identifier.
        email: User's email address.
        **extra: Additional user attributes.
    """
    if not _sentry_initialized:
        return

    try:
        import sentry_sdk

        user_data: dict[str, Any] = {"id": str(user_id)}
        if email:
            user_data["email"] = email
        user_data.update(extra)
        sentry_sdk.set_user(user_data)
    except Exception as e:
        logger.error(f"Failed to set Sentry user: {e}")


def set_tag(key: str, value: str) -> None:
    """Set a tag on the current scope.

    Args:
        key: Tag name.
        value: Tag value.
    """
    if not _sentry_initialized:
        return

    try:
        import sentry_sdk

        sentry_sdk.set_tag(key, value)
    except Exception as e:
        logger.error(f"Failed to set Sentry tag: {e}")


def add_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    **data: Any,
) -> None:
    """Add a breadcrumb to the current scope.

    Args:
        message: Breadcrumb message.
        category: Category for grouping breadcrumbs.
        level: Log level.
        **data: Additional data to attach.
    """
    if not _sentry_initialized:
        return

    try:
        import sentry_sdk

        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data if data else None,
        )
    except Exception as e:
        logger.error(f"Failed to add Sentry breadcrumb: {e}")
