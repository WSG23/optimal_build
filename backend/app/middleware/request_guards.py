"""Request guard middleware for size limits and correlation IDs.

Provides DoS protection via request size limits and request tracing
via correlation IDs propagated through logs.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Any, Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.utils.logging import get_logger, log_event

logger = get_logger(__name__)

# Context variable to store correlation ID for the current request
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Get the correlation ID for the current request context.

    Returns:
        The correlation ID string, or empty string if not in request context.
    """
    return correlation_id_var.get()


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request body size for DoS protection.

    Rejects requests with Content-Length exceeding the configured limit
    with a 413 Payload Too Large response.
    """

    def __init__(
        self,
        app: Callable[..., Awaitable[Response]],
        *,
        max_size_bytes: int = 10 * 1024 * 1024,  # 10 MB default
    ) -> None:
        """Initialize the middleware.

        Args:
            app: The ASGI application
            max_size_bytes: Maximum allowed request body size in bytes
        """
        super().__init__(app)
        self._max_size = max_size_bytes

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Check request size before processing.

        Args:
            request: The incoming request
            call_next: The next middleware/handler

        Returns:
            The response, or 413 if request too large
        """
        content_length = request.headers.get("content-length")

        if content_length:
            try:
                size = int(content_length)
                if size > self._max_size:
                    log_event(
                        logger,
                        "request_too_large",
                        content_length=size,
                        max_allowed=self._max_size,
                        path=request.url.path,
                        client=request.client.host if request.client else "unknown",
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": f"Request body too large. Maximum allowed: {self._max_size} bytes."
                        },
                    )
            except ValueError:
                # Invalid content-length header, let it through
                # and let the framework handle it
                pass

        return await call_next(request)


class CorrelationIdMiddleware:
    """Middleware to generate and propagate correlation IDs for request tracing.

    Generates a unique ID for each request and:
    - Stores it in context for use by loggers
    - Adds it to response headers for client correlation
    - Accepts incoming correlation IDs from X-Correlation-ID header

    Uses pure ASGI implementation for compatibility with streaming responses.
    """

    HEADER_NAME = "X-Correlation-ID"

    def __init__(self, app: Any) -> None:
        """Initialize the middleware.

        Args:
            app: The ASGI application
        """
        self.app = app

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        """Process the request with correlation ID tracking.

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract correlation ID from headers
        headers = dict(scope.get("headers", []))
        correlation_id = headers.get(b"x-correlation-id", b"").decode("utf-8")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Store in context for loggers
        token = correlation_id_var.set(correlation_id)

        # Get request info for logging
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")
        client = scope.get("client", ("unknown", 0))
        client_host = client[0] if client else "unknown"

        # Log request start
        log_event(
            logger,
            "request_start",
            correlation_id=correlation_id,
            method=method,
            path=path,
            client=client_host,
        )

        status_code = 0

        async def send_wrapper(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
                # Add correlation ID to response headers
                headers = list(message.get("headers", []))
                headers.append((b"x-correlation-id", correlation_id.encode("utf-8")))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)

            # Log request completion
            log_event(
                logger,
                "request_complete",
                correlation_id=correlation_id,
                method=method,
                path=path,
                status_code=status_code,
            )
        finally:
            # Reset context variable
            correlation_id_var.reset(token)


__all__ = [
    "RequestSizeLimitMiddleware",
    "CorrelationIdMiddleware",
    "get_correlation_id",
    "correlation_id_var",
]
