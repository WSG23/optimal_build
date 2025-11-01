"""Security headers middleware for the FastAPI application."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Awaitable, Callable

from fastapi import Request, Response

try:  # pragma: no cover - prefer Starlette when available
    from starlette.middleware.base import BaseHTTPMiddleware
except ModuleNotFoundError:  # pragma: no cover - lightweight fallback

    class BaseHTTPMiddleware:  # type: ignore[no-redef]
        def __init__(self, app) -> None:
            self.app = app

        async def dispatch(self, request: Request, call_next):  # pragma: no cover
            return await call_next(request)

        async def __call__(self, scope, receive, send):
            request = Request(scope=scope)

            async def call_next(_: Request):
                await self.app(scope, receive, send)
                return Response()

            response = await self.dispatch(request, call_next)
            payload = await response.render()
            await send(
                {
                    "type": "http.response.start",
                    "status": response.status_code,
                    "headers": [
                        (k.encode(), v.encode()) for k, v in response.headers.items()
                    ],
                }
            )
            await send({"type": "http.response.body", "body": payload})

@dataclass(slots=True)
class SecurityHeadersConfig:
    """Configuration governing which headers are injected."""

    environment: str = os.getenv("ENVIRONMENT", "development")
    strict_environments: tuple[str, ...] = ("production", "staging")
    production_hsts: str = "max-age=63072000; includeSubDomains; preload"
    development_hsts: str | None = "max-age=0"
    content_security_policy: str = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    permissions_policy: str = "geolocation=(), microphone=(), camera=()"
    cross_origin_opener_policy: str = "same-origin"
    cross_origin_resource_policy: str = "cross-origin"
    referrer_policy: str = "strict-origin-when-cross-origin"
    x_content_type_options: str = "nosniff"
    x_frame_options: str = "DENY"
    x_xss_protection: str = "1; mode=block"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject standard security headers for every response."""

    def __init__(
        self,
        app: Callable[..., Awaitable[Response]],
        *,
        config: SecurityHeadersConfig | None = None,
    ) -> None:
        super().__init__(app)
        self._config = config or SecurityHeadersConfig()

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        headers = response.headers

        hsts_value = self._select_hsts_value()
        if hsts_value:
            headers.setdefault("Strict-Transport-Security", hsts_value)

        headers.setdefault("X-Content-Type-Options", self._config.x_content_type_options)
        headers.setdefault("X-Frame-Options", self._config.x_frame_options)
        headers.setdefault("Referrer-Policy", self._config.referrer_policy)
        headers.setdefault("X-XSS-Protection", self._config.x_xss_protection)

        if "Content-Security-Policy" not in headers and self._config.content_security_policy:
            headers["Content-Security-Policy"] = self._config.content_security_policy

        if self._config.permissions_policy:
            headers.setdefault("Permissions-Policy", self._config.permissions_policy)

        if self._config.cross_origin_opener_policy:
            headers.setdefault(
                "Cross-Origin-Opener-Policy", self._config.cross_origin_opener_policy
            )

        if self._config.cross_origin_resource_policy:
            headers.setdefault(
                "Cross-Origin-Resource-Policy", self._config.cross_origin_resource_policy
            )

        return response

    def _select_hsts_value(self) -> str | None:
        """Choose the appropriate HSTS directive for the configured environment."""

        environment = (self._config.environment or "").strip().lower()
        strict_environments = {env.strip().lower() for env in self._config.strict_environments}
        if environment in strict_environments:
            return self._config.production_hsts
        return self._config.development_hsts


__all__ = ["SecurityHeadersMiddleware", "SecurityHeadersConfig"]
