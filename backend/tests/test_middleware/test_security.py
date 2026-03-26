"""Tests for security headers middleware."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable

import pytest
from fastapi import Request, Response

from app.middleware.security import SecurityHeadersConfig, SecurityHeadersMiddleware


def _build_request(
    *,
    method: str = "GET",
    path: str = "/",
    scheme: str = "http",
    headers: dict[str, str] | None = None,
    host: str = "testserver",
) -> Request:
    merged_headers = {"host": host}
    if headers:
        merged_headers.update(headers)
    return Request(
        scope={
            "type": "http",
            "method": method,
            "path": path,
            "headers": [
                (key.lower().encode("utf-8"), value.encode("utf-8"))
                for key, value in merged_headers.items()
            ],
            "scheme": scheme,
            "server": ("testserver", 443 if scheme == "https" else 80),
            "client": ("testclient", 123),
            "root_path": "",
            "query_string": b"",
            "state": {},
        }
    )


async def _dummy_app(*_args: object, **_kwargs: object) -> Response:
    return Response(content="stub", media_type="text/plain")


def _build_middleware(
    config: SecurityHeadersConfig | None = None,
) -> SecurityHeadersMiddleware:
    app: Callable[..., Awaitable[Response]] = _dummy_app
    return SecurityHeadersMiddleware(app=app, config=config)


@pytest.mark.asyncio
async def test_dispatch_adds_security_headers_for_secure_requests() -> None:
    """Secure responses should receive the full default header set."""

    async def mock_call_next(_: Request) -> Response:
        return Response(content="test", media_type="text/plain")

    config = SecurityHeadersConfig(environment="production")
    middleware = _build_middleware(config)

    request = _build_request(scheme="https")
    response = await middleware.dispatch(request, mock_call_next)

    assert response.headers["Strict-Transport-Security"] == config.production_hsts
    assert response.headers["X-Content-Type-Options"] == config.x_content_type_options
    assert response.headers["X-Frame-Options"] == config.x_frame_options
    assert response.headers["Referrer-Policy"] == config.referrer_policy
    assert response.headers["X-XSS-Protection"] == config.x_xss_protection
    assert (
        response.headers["Content-Security-Policy"]
        == config.api_content_security_policy
    )
    assert response.headers["Permissions-Policy"] == config.permissions_policy
    assert (
        response.headers["Cross-Origin-Opener-Policy"]
        == config.cross_origin_opener_policy
    )
    assert (
        response.headers["Cross-Origin-Resource-Policy"]
        == config.cross_origin_resource_policy
    )


@pytest.mark.asyncio
async def test_dispatch_skips_hsts_for_insecure_requests() -> None:
    """HSTS should not be emitted when the request is not HTTPS."""

    async def mock_call_next(_: Request) -> Response:
        return Response(content="test", media_type="text/plain")

    config = SecurityHeadersConfig(environment="production")
    middleware = _build_middleware(config)

    request = _build_request(scheme="http")
    response = await middleware.dispatch(request, mock_call_next)

    assert "Strict-Transport-Security" not in response.headers


@pytest.mark.asyncio
async def test_dispatch_preserves_existing_headers() -> None:
    """Pre-existing headers should not be overwritten."""

    async def mock_call_next(_: Request) -> Response:
        response = Response(content="test", media_type="text/plain")
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
        response.headers["Custom-Header"] = "custom-value"
        return response

    config = SecurityHeadersConfig(environment="production")
    middleware = _build_middleware(config)
    request = _build_request(scheme="https")

    response = await middleware.dispatch(request, mock_call_next)

    assert response.headers["Strict-Transport-Security"] == "max-age=31536000"
    assert response.headers["Custom-Header"] == "custom-value"
    assert response.headers["X-Content-Type-Options"] == config.x_content_type_options
    assert response.headers["X-Frame-Options"] == config.x_frame_options


@pytest.mark.asyncio
async def test_dispatch_preserves_existing_csp() -> None:
    """A response that already set CSP should keep its own policy."""

    async def mock_call_next(_: Request) -> Response:
        response = Response(content="test", media_type="text/plain")
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response

    config = SecurityHeadersConfig(environment="production")
    middleware = _build_middleware(config)
    request = _build_request(scheme="https")

    response = await middleware.dispatch(request, mock_call_next)

    assert response.headers["Content-Security-Policy"] == "default-src 'self'"
    assert response.headers["Strict-Transport-Security"] == config.production_hsts
    assert response.headers["X-Content-Type-Options"] == config.x_content_type_options


@pytest.mark.asyncio
async def test_dispatch_uses_setdefault() -> None:
    """Headers already present should keep their original values."""

    async def mock_call_next(_: Request) -> Response:
        response = Response(content="test", media_type="text/plain")
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    config = SecurityHeadersConfig(environment="production")
    middleware = _build_middleware(config)
    request = _build_request(scheme="https")

    response = await middleware.dispatch(request, mock_call_next)

    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


@pytest.mark.asyncio
async def test_dispatch_injects_nonce_for_html_responses() -> None:
    """HTML responses should receive a per-request nonce in the body and CSP."""

    async def mock_call_next(_: Request) -> Response:
        return Response(
            content="<html><style>body{}</style><script>console.log('x')</script></html>",
            media_type="text/html",
        )

    config = SecurityHeadersConfig(environment="production")
    middleware = _build_middleware(config)
    request = _build_request(scheme="https")

    response = await middleware.dispatch(request, mock_call_next)

    nonce = request.state.csp_nonce
    assert f"'nonce-{nonce}'" in response.headers["Content-Security-Policy"]
    body = response.body.decode("utf-8")
    assert f'<style nonce="{nonce}">' in body
    assert f'<script nonce="{nonce}">' in body


@pytest.mark.asyncio
async def test_dispatch_rejects_invalid_cookie_origin() -> None:
    """Cross-site mutating browser requests with cookies should be rejected."""

    async def mock_call_next(_: Request) -> Response:
        return Response(content="ok", media_type="text/plain")

    config = SecurityHeadersConfig(
        environment="production",
        allowed_origins=("https://app.example.com",),
    )
    middleware = _build_middleware(config)
    request = _build_request(
        method="POST",
        path="/session/update",
        scheme="https",
        host="api.example.com",
        headers={
            "origin": "https://evil.example.com",
            "cookie": "session=abc123",
            "x-correlation-id": "cid-browser",
        },
    )

    response = await middleware.dispatch(request, mock_call_next)

    assert response.status_code == 403
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.headers["Strict-Transport-Security"] == config.production_hsts
    payload = json.loads(response.body)
    assert payload["code"] == "origin_validation_failed"
    assert payload["correlation_id"] == "cid-browser"


@pytest.mark.asyncio
async def test_dispatch_allows_cookie_origin_from_allowlist() -> None:
    """Explicitly allowed browser origins should pass through."""

    async def mock_call_next(_: Request) -> Response:
        return Response(content="ok", media_type="text/plain")

    config = SecurityHeadersConfig(
        environment="production",
        allowed_origins=("https://app.example.com",),
    )
    middleware = _build_middleware(config)
    request = _build_request(
        method="POST",
        path="/session/update",
        scheme="https",
        host="api.example.com",
        headers={
            "origin": "https://app.example.com",
            "cookie": "session=abc123",
        },
    )

    response = await middleware.dispatch(request, mock_call_next)

    assert response.status_code == 200
    assert response.body == b"ok"


@pytest.mark.asyncio
async def test_dispatch_with_empty_response() -> None:
    """Security headers should still be applied to empty responses."""

    async def mock_call_next(_: Request) -> Response:
        return Response(content="", status_code=204)

    middleware = _build_middleware()
    request = _build_request(scheme="https")

    response = await middleware.dispatch(request, mock_call_next)

    assert response.status_code == 204
    assert "X-Content-Type-Options" in response.headers
    assert "X-Frame-Options" in response.headers
