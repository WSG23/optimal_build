"""Security headers middleware for the FastAPI application."""

from __future__ import annotations

import base64
import os
import re
import secrets
from dataclasses import dataclass
from typing import Any, Awaitable, Callable
from urllib.parse import urlsplit

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


_SAFE_BROWSER_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})
_NONCE_BYTES = 16
_FORWARDED_PROTO_RE = re.compile(r"(?:^|[;,\s])proto=(https?)(?:$|[;,\s])", re.I)
_NONCE_TAG_PATTERNS = {
    "script": re.compile(
        r"(?P<prefix><script)(?![^>]*\bnonce=)(?P<suffix>\s|>)",
        re.IGNORECASE,
    ),
    "style": re.compile(
        r"(?P<prefix><style)(?![^>]*\bnonce=)(?P<suffix>\s|>)",
        re.IGNORECASE,
    ),
}


def _generate_csp_nonce() -> str:
    """Return a cryptographically secure CSP nonce."""

    token = secrets.token_bytes(_NONCE_BYTES)
    return base64.urlsafe_b64encode(token).decode("ascii").rstrip("=")


def _normalise_origin(origin: str) -> str | None:
    """Return a normalised ``scheme://host[:port]`` origin string."""

    candidate = origin.strip()
    if not candidate or candidate.lower() == "null":
        return None
    parsed = urlsplit(candidate)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"


def _request_origin(request: Request) -> str | None:
    """Return the request origin using the effective scheme and host."""

    host = request.headers.get("host", "").strip().lower()
    if not host:
        return None
    scheme = "https" if _request_is_secure(request) else request.url.scheme.lower()
    return f"{scheme}://{host}"


def _request_is_secure(request: Request) -> bool:
    """Return whether the current request reached the app over HTTPS."""

    scheme = str(request.scope.get("scheme") or request.url.scheme or "").lower()
    if scheme in {"https", "wss"}:
        return True

    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    if forwarded_proto:
        first_proto = forwarded_proto.split(",", 1)[0].strip().lower()
        if first_proto == "https":
            return True

    if request.headers.get("x-forwarded-ssl", "").strip().lower() == "on":
        return True

    forwarded = request.headers.get("forwarded", "")
    match = _FORWARDED_PROTO_RE.search(forwarded)
    if match:
        return match.group(1).lower() == "https"

    return False


def _is_html_response(response: Response) -> bool:
    """Return whether the response is HTML and should receive HTML-specific CSP."""

    content_type = response.headers.get("content-type") or response.media_type or ""
    content_type = content_type.split(";", 1)[0].strip().lower()
    return content_type in {"text/html", "application/xhtml+xml"}


def _inject_nonce_into_html(html: str, nonce: str) -> str:
    """Inject ``nonce`` attributes into inline ``script`` and ``style`` tags."""

    updated = html
    for pattern in _NONCE_TAG_PATTERNS.values():
        updated = pattern.sub(
            lambda match: (
                f'{match.group("prefix")} nonce="{nonce}"{match.group("suffix")}'
            ),
            updated,
        )
    return updated


@dataclass(slots=True)
class SecurityHeadersConfig:
    """Configuration governing which headers are injected."""

    environment: str = os.getenv("ENVIRONMENT", "development")
    strict_environments: tuple[str, ...] = ("production", "staging")
    production_hsts: str = "max-age=63072000; includeSubDomains; preload"
    development_hsts: str | None = "max-age=0"
    api_content_security_policy: str = (
        "default-src 'none'; "
        "frame-ancestors 'none'; "
        "base-uri 'none'; "
        "form-action 'none'; "
        "object-src 'none'"
    )
    html_content_security_policy: str = (
        "default-src 'self'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'; "
        "form-action 'self'; "
        "object-src 'none'; "
        "img-src 'self' data: blob: https:; "
        "font-src 'self' data:; "
        "style-src 'self' 'nonce-{nonce}' https:; "
        "script-src 'self' 'nonce-{nonce}'; "
        "connect-src 'self' https: wss:"
    )
    permissions_policy: str = "geolocation=(), microphone=(), camera=()"
    cross_origin_opener_policy: str = "same-origin"
    cross_origin_resource_policy: str = "cross-origin"
    referrer_policy: str = "strict-origin-when-cross-origin"
    x_content_type_options: str = "nosniff"
    x_frame_options: str = "DENY"
    x_xss_protection: str = "1; mode=block"
    allowed_origins: tuple[str, ...] = ()
    enforce_browser_origin_for_cookie_auth: bool = True
    browser_state_changing_methods: tuple[str, ...] = ("POST", "PUT", "PATCH", "DELETE")
    expose_nonce_header: bool = False
    csp_report_only: bool = False


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
        origin_rejection = self._maybe_reject_cross_site_browser_request(request)
        if origin_rejection is not None:
            response = origin_rejection
            self._apply_content_security_policy(response, nonce=None)
        else:
            nonce = _generate_csp_nonce()
            request.state.csp_nonce = nonce
            request.scope["csp_nonce"] = nonce
            response = await call_next(request)
            self._apply_content_security_policy(response, nonce)

        self._apply_transport_security(request, response)
        headers = response.headers

        headers.setdefault(
            "X-Content-Type-Options", self._config.x_content_type_options
        )
        headers.setdefault("X-Frame-Options", self._config.x_frame_options)
        headers.setdefault("Referrer-Policy", self._config.referrer_policy)
        headers.setdefault("X-XSS-Protection", self._config.x_xss_protection)

        if self._config.permissions_policy:
            headers.setdefault("Permissions-Policy", self._config.permissions_policy)

        if self._config.cross_origin_opener_policy:
            headers.setdefault(
                "Cross-Origin-Opener-Policy", self._config.cross_origin_opener_policy
            )

        if self._config.cross_origin_resource_policy:
            headers.setdefault(
                "Cross-Origin-Resource-Policy",
                self._config.cross_origin_resource_policy,
            )

        return response

    def _apply_transport_security(self, request: Request, response: Response) -> None:
        """Apply HSTS only when the request is actually secure."""

        hsts_value = self._select_hsts_value(request)
        if hsts_value:
            response.headers.setdefault("Strict-Transport-Security", hsts_value)

    def _apply_content_security_policy(
        self,
        response: Response,
        nonce: str | None,
    ) -> None:
        """Apply the appropriate CSP for HTML vs API responses."""
        headers = response.headers

        header_name = (
            "Content-Security-Policy-Report-Only"
            if self._config.csp_report_only
            else "Content-Security-Policy"
        )
        if header_name in headers:
            return

        if nonce is not None and _is_html_response(response):
            headers[header_name] = self._config.html_content_security_policy.format(
                nonce=nonce
            )
            self._inject_nonce_into_response_body(response, nonce)
            if self._config.expose_nonce_header:
                headers.setdefault("X-CSP-Nonce", nonce)
            return

        if self._config.api_content_security_policy:
            headers[header_name] = self._config.api_content_security_policy

    def _inject_nonce_into_response_body(self, response: Response, nonce: str) -> None:
        """Inject nonce attributes into HTML responses when the body is available."""

        body = getattr(response, "body", None)
        if not isinstance(body, (bytes, bytearray)):
            return
        updated_body = _inject_nonce_into_html(
            body.decode("utf-8", errors="replace"),
            nonce,
        ).encode("utf-8")
        if updated_body == body:
            return
        response.body = updated_body
        response.headers["content-length"] = str(len(updated_body))

    def _select_hsts_value(self, request: Request) -> str | None:
        """Choose the appropriate HSTS directive for the configured environment."""

        if not _request_is_secure(request):
            return None

        environment = (self._config.environment or "").strip().lower()
        strict_environments = {
            env.strip().lower() for env in self._config.strict_environments
        }
        if environment in strict_environments:
            return self._config.production_hsts
        return self._config.development_hsts

    def _maybe_reject_cross_site_browser_request(
        self,
        request: Request,
    ) -> Response | None:
        """Reject cookie-authenticated mutating browser requests from invalid origins."""

        if not self._config.enforce_browser_origin_for_cookie_auth:
            return None

        method = request.method.upper()
        if method in _SAFE_BROWSER_METHODS:
            return None
        if method not in set(self._config.browser_state_changing_methods):
            return None
        if "cookie" not in request.headers:
            return None

        origin = _normalise_origin(request.headers.get("origin", ""))
        if origin is not None:
            if self._origin_is_allowed(request, origin):
                return None
            from app.utils.problem_details import problem_response

            return problem_response(
                request=request,
                status_code=403,
                detail="Browser origin is not allowed for cookie-authenticated mutation requests.",
                code="origin_validation_failed",
            )

        sec_fetch_site = request.headers.get("sec-fetch-site", "").strip().lower()
        if sec_fetch_site == "cross-site":
            from app.utils.problem_details import problem_response

            return problem_response(
                request=request,
                status_code=403,
                detail=(
                    "Cross-site browser request rejected for "
                    "cookie-authenticated mutation request."
                ),
                code="origin_validation_failed",
            )
        return None

    def _origin_is_allowed(self, request: Request, origin: str) -> bool:
        """Return whether ``origin`` is valid for the current request."""

        if origin == _request_origin(request):
            return True

        allowed_origins = {
            normalised
            for normalised in (
                _normalise_origin(candidate)
                for candidate in self._config.allowed_origins
            )
            if normalised is not None
        }
        return "*" in self._config.allowed_origins or origin in allowed_origins


__all__ = ["SecurityHeadersMiddleware", "SecurityHeadersConfig"]
