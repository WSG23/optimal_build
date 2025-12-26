"""Exception handler middleware for standardized error responses.

This middleware catches all AppError exceptions and converts them to
standardized JSON responses. It also handles unexpected exceptions
with proper logging and correlation ID tracking.

Usage:
    # In main.py
    from app.middleware.exception_handler import register_exception_handlers

    register_exception_handlers(app)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import (
    AppError,
    ErrorResponse,
    RateLimitError,
    ServiceUnavailableError,
)
from app.utils.logging import get_logger, log_event

if TYPE_CHECKING:
    from fastapi import Response

logger = get_logger(__name__)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle AppError exceptions with standardized response format.

    Args:
        request: The incoming request
        exc: The AppError exception

    Returns:
        JSONResponse with standardized error format
    """
    # Get correlation ID from request state (set by CorrelationIdMiddleware)
    correlation_id = getattr(request.state, "correlation_id", None)

    # Log the error with context
    log_event(
        logger,
        "app_error",
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        correlation_id=correlation_id,
        path=request.url.path,
        method=request.method,
    )

    # Build response
    response = exc.to_response(correlation_id=correlation_id)
    json_response = JSONResponse(
        status_code=exc.status_code,
        content=response.to_dict(),
    )

    # Add retry-after header for rate limit and service unavailable errors
    if isinstance(exc, (RateLimitError, ServiceUnavailableError)):
        if exc.retry_after:
            json_response.headers["Retry-After"] = str(exc.retry_after)

    # Add correlation ID header for tracing
    if correlation_id:
        json_response.headers["X-Correlation-ID"] = correlation_id

    return json_response


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with logging and generic response.

    This handler catches all exceptions not handled by specific handlers,
    logs them with full context for debugging, and returns a generic
    error response to avoid leaking implementation details.

    Args:
        request: The incoming request
        exc: The unhandled exception

    Returns:
        JSONResponse with generic error message
    """
    correlation_id = getattr(request.state, "correlation_id", None)

    # Log the full exception with traceback
    log_event(
        logger,
        "unhandled_exception",
        error_type=type(exc).__name__,
        error_message=str(exc),
        correlation_id=correlation_id,
        path=request.url.path,
        method=request.method,
        level="error",
    )

    # Return generic error response (don't leak implementation details)
    response = ErrorResponse(
        error_code="INTERNAL_ERROR",
        message="An unexpected error occurred. Please try again later.",
        status_code=500,
        correlation_id=correlation_id,
    )

    json_response = JSONResponse(
        status_code=500,
        content=response.to_dict(),
    )

    if correlation_id:
        json_response.headers["X-Correlation-ID"] = correlation_id

    return json_response


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI application.

    This function should be called once during application startup to
    register all custom exception handlers.

    Args:
        app: The FastAPI application instance
    """
    # Register handler for all AppError subclasses
    app.add_exception_handler(AppError, app_error_handler)

    # Note: We don't register a generic Exception handler here because
    # it would override FastAPI's built-in handlers for validation errors
    # and other framework exceptions. The ApiErrorLoggingMiddleware
    # already handles logging of unhandled exceptions.


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for catching and handling unhandled exceptions.

    This middleware provides a last-resort catch for any exceptions
    that slip through the exception handlers. It ensures all errors
    return a consistent JSON response format.
    """

    async def dispatch(self, request: Request, call_next: object) -> "Response":
        """Process the request and catch any unhandled exceptions."""
        try:
            response = await call_next(request)  # type: ignore[operator]
            return response
        except AppError as exc:
            # This shouldn't normally be reached since we have exception handlers,
            # but provides a fallback
            return await app_error_handler(request, exc)
        except Exception as exc:
            # Catch any other exceptions
            return await unhandled_exception_handler(request, exc)


__all__ = [
    "ExceptionHandlerMiddleware",
    "app_error_handler",
    "register_exception_handlers",
    "unhandled_exception_handler",
]
