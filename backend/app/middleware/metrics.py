"""Prometheus metrics middleware for automatic HTTP request tracking."""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils import metrics


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track HTTP request latency and errors with Prometheus."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request and track metrics."""
        # Skip metrics endpoint to avoid recursion
        if request.url.path in ["/metrics", "/health/metrics"]:
            return await call_next(request)

        method = request.method
        path = request.url.path
        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = str(response.status_code)

            # Track request duration
            duration = time.time() - start_time
            metrics.HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method, path=path, status_code=status_code
            ).observe(duration)

            # Track errors (4xx and 5xx)
            if response.status_code >= 400:
                error_type = "client_error" if response.status_code < 500 else "server_error"
                metrics.HTTP_REQUEST_ERRORS_TOTAL.labels(
                    method=method, path=path, error_type=error_type
                ).inc()

            return response

        except Exception as exc:
            # Track unhandled exceptions
            duration = time.time() - start_time
            metrics.HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method, path=path, status_code="500"
            ).observe(duration)

            metrics.HTTP_REQUEST_ERRORS_TOTAL.labels(
                method=method, path=path, error_type="exception"
            ).inc()

            raise
