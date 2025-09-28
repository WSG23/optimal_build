"""Security headers middleware for the FastAPI application."""

from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject standard security headers for every response."""

    def __init__(self, app: Callable[..., Awaitable[Response]]) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        headers = response.headers

        headers.setdefault(
            "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
        )
        headers.setdefault("X-Content-Type-Options", "nosniff")
        headers.setdefault("X-Frame-Options", "DENY")
        headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        headers.setdefault("X-XSS-Protection", "1; mode=block")
        if "Content-Security-Policy" not in headers:
            headers["Content-Security-Policy"] = (
                "default-src 'none'; frame-ancestors 'none'"
            )

        return response


__all__ = ["SecurityHeadersMiddleware"]
