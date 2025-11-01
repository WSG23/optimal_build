"""Tests for security headers middleware."""

import pytest
from fastapi import Request, Response

from app.middleware.security import SecurityHeadersConfig, SecurityHeadersMiddleware


@pytest.mark.asyncio
async def test_dispatch_adds_security_headers():
    """Test that dispatch method adds security headers."""

    # Create a mock call_next function that returns a response
    async def mock_call_next(request: Request) -> Response:
        return Response(content="test", media_type="text/plain")

    # Create middleware instance (we don't need a real app for unit testing)
    config = SecurityHeadersConfig(environment="production")
    middleware = SecurityHeadersMiddleware(app=None, config=config)  # type: ignore

    # Create a mock request
    request = Request(scope={"type": "http", "method": "GET", "path": "/"})

    # Call dispatch
    response = await middleware.dispatch(request, mock_call_next)

    # Verify all security headers are present
    assert "Strict-Transport-Security" in response.headers
    assert response.headers["Strict-Transport-Security"] == config.production_hsts

    assert response.headers["X-Content-Type-Options"] == config.x_content_type_options
    assert response.headers["X-Frame-Options"] == config.x_frame_options
    assert response.headers["Referrer-Policy"] == config.referrer_policy
    assert response.headers["X-XSS-Protection"] == config.x_xss_protection
    assert response.headers["Content-Security-Policy"] == config.content_security_policy
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
async def test_dispatch_adds_development_hsts():
    """Non-production environments should emit the development HSTS directive."""

    async def mock_call_next(request: Request) -> Response:
        return Response(content="test", media_type="text/plain")

    config = SecurityHeadersConfig(environment="development")
    middleware = SecurityHeadersMiddleware(app=None, config=config)  # type: ignore

    request = Request(scope={"type": "http", "method": "GET", "path": "/"})
    response = await middleware.dispatch(request, mock_call_next)

    if config.development_hsts is None:
        assert "Strict-Transport-Security" not in response.headers
    else:
        assert response.headers["Strict-Transport-Security"] == config.development_hsts


@pytest.mark.asyncio
async def test_dispatch_preserves_existing_headers():
    """Test that dispatch doesn't overwrite existing headers."""

    # Create a mock call_next that returns a response with existing headers
    async def mock_call_next(request: Request) -> Response:
        response = Response(content="test", media_type="text/plain")
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
        response.headers["Custom-Header"] = "custom-value"
        return response

    config = SecurityHeadersConfig(environment="production")
    middleware = SecurityHeadersMiddleware(app=None, config=config)  # type: ignore
    request = Request(scope={"type": "http", "method": "GET", "path": "/"})

    response = await middleware.dispatch(request, mock_call_next)

    # Existing HSTS header should NOT be overwritten
    assert response.headers["Strict-Transport-Security"] == "max-age=31536000"

    # Custom header should be preserved
    assert response.headers["Custom-Header"] == "custom-value"

    # Other security headers should still be added
    assert response.headers["X-Content-Type-Options"] == config.x_content_type_options
    assert response.headers["X-Frame-Options"] == config.x_frame_options


@pytest.mark.asyncio
async def test_dispatch_preserves_existing_csp():
    """Test that existing Content-Security-Policy is not overwritten."""

    async def mock_call_next(request: Request) -> Response:
        response = Response(content="test", media_type="text/plain")
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response

    config = SecurityHeadersConfig(environment="production")
    middleware = SecurityHeadersMiddleware(app=None, config=config)  # type: ignore
    request = Request(scope={"type": "http", "method": "GET", "path": "/"})

    response = await middleware.dispatch(request, mock_call_next)

    # Custom CSP should be preserved
    assert response.headers["Content-Security-Policy"] == "default-src 'self'"

    # Other security headers should still be added
    assert response.headers["Strict-Transport-Security"] == config.production_hsts
    assert response.headers["X-Content-Type-Options"] == config.x_content_type_options


@pytest.mark.asyncio
async def test_dispatch_uses_setdefault():
    """Test that setdefault is used so existing values aren't changed."""

    async def mock_call_next(request: Request) -> Response:
        response = Response(content="test", media_type="text/plain")
        # Pre-set multiple headers
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    config = SecurityHeadersConfig(environment="production")
    middleware = SecurityHeadersMiddleware(app=None, config=config)  # type: ignore
    request = Request(scope={"type": "http", "method": "GET", "path": "/"})

    response = await middleware.dispatch(request, mock_call_next)

    # Pre-existing values should be preserved
    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert response.headers["Referrer-Policy"] == "no-referrer"

    # Headers not pre-set should be added with default values
    assert response.headers["X-Content-Type-Options"] == "nosniff"


@pytest.mark.asyncio
async def test_dispatch_with_empty_response():
    """Test that headers are added even to empty responses."""

    async def mock_call_next(request: Request) -> Response:
        return Response(content="", status_code=204)

    middleware = SecurityHeadersMiddleware(app=None)  # type: ignore
    request = Request(scope={"type": "http", "method": "GET", "path": "/"})

    response = await middleware.dispatch(request, mock_call_next)

    assert response.status_code == 204
    # Security headers should still be present
    assert "X-Content-Type-Options" in response.headers
    assert "X-Frame-Options" in response.headers
