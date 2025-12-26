"""Security headers middleware for the FastAPI application.

This middleware injects comprehensive security headers into all HTTP responses
to protect against common web vulnerabilities:

- HSTS: Enforces HTTPS connections
- CSP: Prevents XSS and injection attacks
- X-Frame-Options: Prevents clickjacking
- X-Content-Type-Options: Prevents MIME sniffing
- Referrer-Policy: Controls referrer information
- Permissions-Policy: Restricts browser features
- Cross-Origin-*-Policy: Controls cross-origin resource sharing

Usage:
    from app.middleware.security import SecurityHeadersMiddleware

    app.add_middleware(SecurityHeadersMiddleware)

    # With custom configuration
    config = SecurityHeadersConfig(environment="production")
    app.add_middleware(SecurityHeadersMiddleware, config=config)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from fastapi import Request, Response

try:  # pragma: no cover - prefer Starlette when available
    from starlette.middleware.base import BaseHTTPMiddleware
except ModuleNotFoundError:  # pragma: no cover - lightweight fallback

    class BaseHTTPMiddleware:  # type: ignore[no-redef]
        def __init__(self, app: Any) -> None:
            self.app = app

        async def dispatch(
            self, request: Request, call_next: Any
        ) -> Any:  # pragma: no cover
            return await call_next(request)

        async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
            request = Request(scope=scope)

            async def call_next(_: Request) -> Response:
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


# Production CSP: Strict policy for API-only backend
# - 'self' for same-origin resources
# - 'none' for scripts/styles (API doesn't serve HTML)
# - frame-ancestors 'none' prevents embedding in iframes
_PRODUCTION_CSP = (
    "default-src 'none'; "
    "frame-ancestors 'none'; "
    "base-uri 'none'; "
    "form-action 'none'; "
    "upgrade-insecure-requests"
)

# Development CSP: More permissive for local development
# Allows inline scripts/styles for dev tools and error pages
_DEVELOPMENT_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "font-src 'self' data:; "
    "connect-src 'self' ws: wss: http://localhost:* http://127.0.0.1:*; "
    "frame-ancestors 'self'"
)


def _build_default_csp(environment: str) -> str:
    """Build the default CSP based on environment."""
    env_lower = (environment or "").strip().lower()
    if env_lower in ("production", "staging"):
        return _PRODUCTION_CSP
    return _DEVELOPMENT_CSP


@dataclass(slots=True)
class SecurityHeadersConfig:
    """Configuration governing which security headers are injected.

    Attributes:
        environment: Current environment (development, staging, production)
        strict_environments: Environments that use strict security settings
        production_hsts: HSTS header value for production (2 years with preload)
        development_hsts: HSTS header value for development (disabled)
        content_security_policy: CSP header value (auto-configured by environment)
        permissions_policy: Permissions-Policy header value
        cross_origin_opener_policy: COOP header value
        cross_origin_resource_policy: CORP header value
        cross_origin_embedder_policy: COEP header value (new)
        referrer_policy: Referrer-Policy header value
        x_content_type_options: X-Content-Type-Options header value
        x_frame_options: X-Frame-Options header value
        x_xss_protection: X-XSS-Protection header value (legacy, kept for compatibility)
        cache_control_api: Cache-Control for API responses
    """

    environment: str = field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "development")
    )
    strict_environments: tuple[str, ...] = ("production", "staging")

    # HSTS configuration
    # Production: 2 years with includeSubDomains and preload
    # Development: Disabled (max-age=0)
    production_hsts: str = "max-age=63072000; includeSubDomains; preload"
    development_hsts: str | None = "max-age=0"

    # Content Security Policy (auto-configured based on environment)
    content_security_policy: str | None = None

    # Permissions Policy: Disable unnecessary browser features
    # geolocation, microphone, camera disabled by default
    # Add more as needed: accelerometer, gyroscope, magnetometer, payment, usb
    permissions_policy: str = (
        "geolocation=(), " "microphone=(), " "camera=(), " "payment=(), " "usb=()"
    )

    # Cross-Origin policies
    cross_origin_opener_policy: str = "same-origin"
    cross_origin_resource_policy: str = "cross-origin"
    cross_origin_embedder_policy: str | None = (
        None  # Requires CORP headers on resources
    )

    # Other security headers
    referrer_policy: str = "strict-origin-when-cross-origin"
    x_content_type_options: str = "nosniff"
    x_frame_options: str = "DENY"
    x_xss_protection: str = "0"  # Disabled per OWASP recommendation (can cause issues)

    # API-specific headers
    cache_control_api: str = "no-store, no-cache, must-revalidate, private"

    def __post_init__(self) -> None:
        """Auto-configure CSP if not explicitly set."""
        if self.content_security_policy is None:
            self.content_security_policy = _build_default_csp(self.environment)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject comprehensive security headers for every response.

    This middleware adds the following security headers:
    - Strict-Transport-Security (HSTS): Forces HTTPS connections
    - Content-Security-Policy (CSP): Prevents XSS and injection attacks
    - X-Frame-Options: Prevents clickjacking
    - X-Content-Type-Options: Prevents MIME sniffing
    - Referrer-Policy: Controls referrer information leakage
    - Permissions-Policy: Restricts browser features
    - Cross-Origin-Opener-Policy (COOP): Isolates browsing context
    - Cross-Origin-Resource-Policy (CORP): Controls resource sharing
    - Cross-Origin-Embedder-Policy (COEP): Controls embedding resources
    - Cache-Control: Prevents caching of sensitive API responses

    Headers are only added if not already present in the response,
    allowing individual endpoints to override defaults.
    """

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

        # HSTS: Enforce HTTPS (different values for prod vs dev)
        hsts_value = self._select_hsts_value()
        if hsts_value:
            headers.setdefault("Strict-Transport-Security", hsts_value)

        # Core security headers
        headers.setdefault(
            "X-Content-Type-Options", self._config.x_content_type_options
        )
        headers.setdefault("X-Frame-Options", self._config.x_frame_options)
        headers.setdefault("Referrer-Policy", self._config.referrer_policy)

        # X-XSS-Protection: Set to 0 per OWASP recommendation
        # Modern browsers have better protections, and this header can cause issues
        headers.setdefault("X-XSS-Protection", self._config.x_xss_protection)

        # Content Security Policy
        if (
            "Content-Security-Policy" not in headers
            and self._config.content_security_policy
        ):
            headers["Content-Security-Policy"] = self._config.content_security_policy

        # Permissions Policy (formerly Feature-Policy)
        if self._config.permissions_policy:
            headers.setdefault("Permissions-Policy", self._config.permissions_policy)

        # Cross-Origin policies
        if self._config.cross_origin_opener_policy:
            headers.setdefault(
                "Cross-Origin-Opener-Policy", self._config.cross_origin_opener_policy
            )

        if self._config.cross_origin_resource_policy:
            headers.setdefault(
                "Cross-Origin-Resource-Policy",
                self._config.cross_origin_resource_policy,
            )

        if self._config.cross_origin_embedder_policy:
            headers.setdefault(
                "Cross-Origin-Embedder-Policy",
                self._config.cross_origin_embedder_policy,
            )

        # Cache-Control for API responses (prevent caching of sensitive data)
        # Only add to API paths, not static files
        if request.url.path.startswith("/api/"):
            headers.setdefault("Cache-Control", self._config.cache_control_api)

        return response

    def _select_hsts_value(self) -> str | None:
        """Choose the appropriate HSTS directive for the configured environment."""

        environment = (self._config.environment or "").strip().lower()
        strict_environments = {
            env.strip().lower() for env in self._config.strict_environments
        }
        if environment in strict_environments:
            return self._config.production_hsts
        return self._config.development_hsts

    def _is_production(self) -> bool:
        """Check if running in production environment."""
        environment = (self._config.environment or "").strip().lower()
        return environment in {
            env.strip().lower() for env in self._config.strict_environments
        }


__all__ = ["SecurityHeadersMiddleware", "SecurityHeadersConfig"]
