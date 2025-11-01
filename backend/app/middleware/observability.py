"""Middleware for observability and API error logging."""

from __future__ import annotations

from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from structlog.stdlib import BoundLogger

from app.utils.logging import get_logger, log_event


class ApiErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Capture unhandled exceptions and 5xx responses for monitoring."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        logger: BoundLogger | None = None,
    ) -> None:
        super().__init__(app)
        self._logger = logger or get_logger(__name__)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Any:
        """Log unexpected exceptions and server error responses."""

        try:
            response = await call_next(request)
        except Exception as exc:
            log_event(
                self._logger,
                "api_exception",
                method=request.method,
                path=request.url.path,
                client_host=request.client.host if request.client else None,
                error=str(exc),
            )
            raise

        if response.status_code >= 500:
            log_event(
                self._logger,
                "api_error_response",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
            )

        return response
