"""Tests for security headers middleware.

Tests cover:
- All security headers are properly set
- Environment-specific CSP configuration
- HSTS configuration for production vs development
- Cache-Control for API endpoints
- Cross-Origin policies (COOP, CORP, COEP)
- Header preservation (existing headers not overwritten)
"""

import pytest
from fastapi import Request, Response

from app.middleware.security import (
    SecurityHeadersConfig,
    SecurityHeadersMiddleware,
    _build_default_csp,
    _PRODUCTION_CSP,
    _DEVELOPMENT_CSP,
)


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


class TestSecurityHeadersConfig:
    """Tests for SecurityHeadersConfig dataclass."""

    def test_default_config_values(self) -> None:
        """Test default configuration values."""
        config = SecurityHeadersConfig()
        assert config.x_content_type_options == "nosniff"
        assert config.x_frame_options == "DENY"
        assert config.referrer_policy == "strict-origin-when-cross-origin"
        assert config.x_xss_protection == "0"  # Disabled per OWASP
        assert config.cross_origin_opener_policy == "same-origin"
        assert config.cross_origin_resource_policy == "cross-origin"

    def test_production_hsts_value(self) -> None:
        """Test HSTS value for production."""
        config = SecurityHeadersConfig(environment="production")
        assert "max-age=63072000" in config.production_hsts
        assert "includeSubDomains" in config.production_hsts
        assert "preload" in config.production_hsts

    def test_development_hsts_value(self) -> None:
        """Test HSTS value for development."""
        config = SecurityHeadersConfig(environment="development")
        assert config.development_hsts == "max-age=0"

    def test_permissions_policy(self) -> None:
        """Test Permissions-Policy header value."""
        config = SecurityHeadersConfig()
        assert "geolocation=()" in config.permissions_policy
        assert "microphone=()" in config.permissions_policy
        assert "camera=()" in config.permissions_policy
        assert "payment=()" in config.permissions_policy

    def test_cache_control_api(self) -> None:
        """Test Cache-Control header for API responses."""
        config = SecurityHeadersConfig()
        assert "no-store" in config.cache_control_api
        assert "no-cache" in config.cache_control_api
        assert "private" in config.cache_control_api


class TestCSPConfiguration:
    """Tests for Content Security Policy configuration."""

    def test_build_default_csp_production(self) -> None:
        """Test CSP for production environment."""
        csp = _build_default_csp("production")
        assert csp == _PRODUCTION_CSP
        assert "default-src 'none'" in csp
        assert "frame-ancestors 'none'" in csp
        assert "upgrade-insecure-requests" in csp

    def test_build_default_csp_staging(self) -> None:
        """Test CSP for staging environment."""
        csp = _build_default_csp("staging")
        assert csp == _PRODUCTION_CSP

    def test_build_default_csp_development(self) -> None:
        """Test CSP for development environment."""
        csp = _build_default_csp("development")
        assert csp == _DEVELOPMENT_CSP
        assert "default-src 'self'" in csp
        assert "'unsafe-inline'" in csp
        assert "'unsafe-eval'" in csp

    def test_csp_auto_configured_in_config(self) -> None:
        """Test CSP is auto-configured based on environment."""
        prod_config = SecurityHeadersConfig(environment="production")
        assert prod_config.content_security_policy == _PRODUCTION_CSP

        dev_config = SecurityHeadersConfig(environment="development")
        assert dev_config.content_security_policy == _DEVELOPMENT_CSP

    def test_csp_can_be_overridden(self) -> None:
        """Test custom CSP can override default."""
        custom_csp = "default-src 'self'; script-src 'self'"
        config = SecurityHeadersConfig(
            environment="production",
            content_security_policy=custom_csp,
        )
        assert config.content_security_policy == custom_csp


class TestCacheControlHeader:
    """Tests for Cache-Control header on API endpoints."""

    @pytest.mark.asyncio
    async def test_cache_control_added_to_api_paths(self) -> None:
        """Test Cache-Control is added for API paths."""

        async def mock_call_next(request: Request) -> Response:
            return Response(content="test", media_type="application/json")

        middleware = SecurityHeadersMiddleware(app=None)  # type: ignore
        request = Request(
            scope={"type": "http", "method": "GET", "path": "/api/v1/properties"}
        )

        response = await middleware.dispatch(request, mock_call_next)

        assert "Cache-Control" in response.headers
        assert "no-store" in response.headers["Cache-Control"]

    @pytest.mark.asyncio
    async def test_cache_control_not_added_to_non_api_paths(self) -> None:
        """Test Cache-Control is not added for non-API paths."""

        async def mock_call_next(request: Request) -> Response:
            return Response(content="test", media_type="text/html")

        middleware = SecurityHeadersMiddleware(app=None)  # type: ignore
        request = Request(
            scope={"type": "http", "method": "GET", "path": "/static/style.css"}
        )

        response = await middleware.dispatch(request, mock_call_next)

        # Should not have Cache-Control added by security middleware
        assert "Cache-Control" not in response.headers


class TestCrossOriginEmbedderPolicy:
    """Tests for Cross-Origin-Embedder-Policy header."""

    @pytest.mark.asyncio
    async def test_coep_not_set_by_default(self) -> None:
        """Test COEP is not set by default (requires careful consideration)."""

        async def mock_call_next(request: Request) -> Response:
            return Response(content="test", media_type="text/plain")

        config = SecurityHeadersConfig()
        assert config.cross_origin_embedder_policy is None

        middleware = SecurityHeadersMiddleware(app=None, config=config)  # type: ignore
        request = Request(scope={"type": "http", "method": "GET", "path": "/"})

        response = await middleware.dispatch(request, mock_call_next)

        assert "Cross-Origin-Embedder-Policy" not in response.headers

    @pytest.mark.asyncio
    async def test_coep_can_be_enabled(self) -> None:
        """Test COEP can be enabled via configuration."""

        async def mock_call_next(request: Request) -> Response:
            return Response(content="test", media_type="text/plain")

        config = SecurityHeadersConfig(cross_origin_embedder_policy="require-corp")
        middleware = SecurityHeadersMiddleware(app=None, config=config)  # type: ignore
        request = Request(scope={"type": "http", "method": "GET", "path": "/"})

        response = await middleware.dispatch(request, mock_call_next)

        assert response.headers["Cross-Origin-Embedder-Policy"] == "require-corp"


class TestXSSProtectionDisabled:
    """Tests for X-XSS-Protection being disabled (OWASP recommendation)."""

    @pytest.mark.asyncio
    async def test_xss_protection_is_zero(self) -> None:
        """Test X-XSS-Protection is set to 0 per OWASP guidelines."""

        async def mock_call_next(request: Request) -> Response:
            return Response(content="test", media_type="text/plain")

        config = SecurityHeadersConfig()
        middleware = SecurityHeadersMiddleware(app=None, config=config)  # type: ignore
        request = Request(scope={"type": "http", "method": "GET", "path": "/"})

        response = await middleware.dispatch(request, mock_call_next)

        # OWASP recommends X-XSS-Protection: 0
        # See: https://owasp.org/www-project-secure-headers/
        assert response.headers["X-XSS-Protection"] == "0"


class TestEnvironmentDetection:
    """Tests for environment-based header configuration."""

    @pytest.mark.asyncio
    async def test_production_gets_strict_hsts(self) -> None:
        """Test production environment gets strict HSTS."""

        async def mock_call_next(request: Request) -> Response:
            return Response(content="test", media_type="text/plain")

        config = SecurityHeadersConfig(environment="production")
        middleware = SecurityHeadersMiddleware(app=None, config=config)  # type: ignore
        request = Request(scope={"type": "http", "method": "GET", "path": "/"})

        response = await middleware.dispatch(request, mock_call_next)

        hsts = response.headers["Strict-Transport-Security"]
        assert "max-age=63072000" in hsts
        assert "preload" in hsts

    @pytest.mark.asyncio
    async def test_staging_gets_strict_hsts(self) -> None:
        """Test staging environment gets strict HSTS."""

        async def mock_call_next(request: Request) -> Response:
            return Response(content="test", media_type="text/plain")

        config = SecurityHeadersConfig(environment="staging")
        middleware = SecurityHeadersMiddleware(app=None, config=config)  # type: ignore
        request = Request(scope={"type": "http", "method": "GET", "path": "/"})

        response = await middleware.dispatch(request, mock_call_next)

        hsts = response.headers["Strict-Transport-Security"]
        assert "max-age=63072000" in hsts

    @pytest.mark.asyncio
    async def test_development_gets_relaxed_hsts(self) -> None:
        """Test development environment gets relaxed HSTS."""

        async def mock_call_next(request: Request) -> Response:
            return Response(content="test", media_type="text/plain")

        config = SecurityHeadersConfig(environment="development")
        middleware = SecurityHeadersMiddleware(app=None, config=config)  # type: ignore
        request = Request(scope={"type": "http", "method": "GET", "path": "/"})

        response = await middleware.dispatch(request, mock_call_next)

        hsts = response.headers["Strict-Transport-Security"]
        assert hsts == "max-age=0"
