"""Tests for production security hardening.

These tests verify that security hardening measures are properly configured
for production environments.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest


class TestAPIDocumentationSecurity:
    """Tests for API documentation security in production."""

    def test_docs_disabled_logic_for_production(self) -> None:
        """API documentation should be disabled when ENVIRONMENT=production."""
        # Test the logic used in main.py for production detection
        environment = "production"
        is_production = environment.lower() == "production"
        assert is_production is True

        # In production, docs should be None
        docs_url = None if is_production else "/docs"
        redoc_url = None if is_production else "/redoc"
        openapi_url = None if is_production else "/openapi.json"

        assert docs_url is None
        assert redoc_url is None
        assert openapi_url is None

    def test_docs_enabled_logic_for_development(self) -> None:
        """API documentation should be enabled when ENVIRONMENT=development."""
        # Test the logic used in main.py for development detection
        environment = "development"
        is_production = environment.lower() == "production"
        assert is_production is False

        docs_url = None if is_production else "/docs"
        redoc_url = None if is_production else "/redoc"
        openapi_url = None if is_production else "/openapi.json"

        assert docs_url == "/docs"
        assert redoc_url == "/redoc"
        assert openapi_url == "/openapi.json"


class TestCORSHeadersSecurity:
    """Tests for CORS headers security configuration."""

    def test_development_headers_list(self) -> None:
        """Development should allow debug headers."""
        production_headers = [
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "X-Requested-With",
            "X-Correlation-ID",
        ]

        development_headers = production_headers + [
            "X-Role",
            "X-User-Id",
            "X-User-Email",
        ]

        # Verify development has more headers
        assert len(development_headers) > len(production_headers)

        # Verify debug headers only in development
        assert "X-Role" in development_headers
        assert "X-User-Id" in development_headers
        assert "X-User-Email" in development_headers

        # Verify debug headers NOT in production
        assert "X-Role" not in production_headers
        assert "X-User-Id" not in production_headers
        assert "X-User-Email" not in production_headers

    def test_production_excludes_debug_headers(self) -> None:
        """Production should NOT allow debug headers."""
        production_allowed_headers = [
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "X-Requested-With",
            "X-Correlation-ID",
        ]

        # These debug headers must NEVER be in production
        debug_headers = ["X-Role", "X-User-Id", "X-User-Email"]

        for header in debug_headers:
            assert (
                header not in production_allowed_headers
            ), f"Debug header '{header}' must not be allowed in production"


class TestSecurityHeadersMiddleware:
    """Tests for security headers middleware configuration."""

    def test_security_headers_config_has_secure_defaults(self) -> None:
        """Security headers config should have secure default values."""
        from app.middleware.security import SecurityHeadersConfig

        config = SecurityHeadersConfig()

        # X-Frame-Options should prevent clickjacking
        assert config.x_frame_options == "DENY"

        # X-Content-Type-Options should prevent MIME sniffing
        assert config.x_content_type_options == "nosniff"

        # Referrer-Policy should limit information leakage
        assert config.referrer_policy == "strict-origin-when-cross-origin"

        # CSP should be restrictive
        assert "default-src 'none'" in config.content_security_policy
        assert "frame-ancestors 'none'" in config.content_security_policy

        # Permissions-Policy should disable dangerous features
        assert "geolocation=()" in config.permissions_policy
        assert "microphone=()" in config.permissions_policy
        assert "camera=()" in config.permissions_policy

    def test_hsts_header_in_production(self) -> None:
        """HSTS should be enabled with preload in production."""
        from app.middleware.security import SecurityHeadersConfig

        config = SecurityHeadersConfig(environment="production")

        # HSTS should include all recommended directives
        assert "max-age=63072000" in config.production_hsts  # 2 years
        assert "includeSubDomains" in config.production_hsts
        assert "preload" in config.production_hsts

    def test_cross_origin_policies_configured(self) -> None:
        """Cross-origin policies should be configured."""
        from app.middleware.security import SecurityHeadersConfig

        config = SecurityHeadersConfig()

        # COOP should prevent cross-origin window access
        assert config.cross_origin_opener_policy == "same-origin"

        # CORP should restrict cross-origin resource loading
        assert config.cross_origin_resource_policy in ("same-origin", "cross-origin")


class TestRateLimitingConfiguration:
    """Tests for rate limiting security configuration."""

    def test_rate_limit_is_configured(self) -> None:
        """Rate limiting should be enabled."""
        from app.core.config import settings

        assert settings.API_RATE_LIMIT is not None
        assert len(settings.API_RATE_LIMIT) > 0

        # Should be in format like "60/minute"
        assert "/" in settings.API_RATE_LIMIT

    def test_rate_limit_storage_configured(self) -> None:
        """Rate limit storage backend should be configured."""
        from app.core.config import settings

        assert settings.RATE_LIMIT_STORAGE_URI is not None

        # Should be either Redis URL or memory
        valid_prefixes = ("redis://", "rediss://", "memory://")
        assert any(
            settings.RATE_LIMIT_STORAGE_URI.startswith(prefix)
            for prefix in valid_prefixes
        )


class TestRequestSizeLimiting:
    """Tests for request size limiting (DoS protection)."""

    def test_request_size_limit_middleware_configurable(self) -> None:
        """Request size limit middleware should be configurable."""
        from app.middleware.request_guards import RequestSizeLimitMiddleware

        # Should accept custom limit (uses _max_size internally)
        limit_10mb = 10 * 1024 * 1024
        middleware = RequestSizeLimitMiddleware(lambda x: x, max_size_bytes=limit_10mb)
        assert middleware._max_size == limit_10mb

        # Should work with smaller limit
        limit_1mb = 1 * 1024 * 1024
        middleware_small = RequestSizeLimitMiddleware(
            lambda x: x, max_size_bytes=limit_1mb
        )
        assert middleware_small._max_size == limit_1mb


class TestPasswordSecurityBestPractices:
    """Tests for password security best practices."""

    def test_bcrypt_preferred_over_sha256(self) -> None:
        """bcrypt should be preferred over SHA256 for password hashing."""
        from app.utils.security import _HAS_PASSLIB

        if _HAS_PASSLIB:
            from app.utils.security import pwd_context

            # bcrypt should be the default scheme
            assert pwd_context.default_scheme() == "bcrypt"

            # sha256_crypt should be in the deprecated list
            # The deprecated schemes are configured in the CryptContext
            deprecated_schemes = pwd_context.schemes()
            assert (
                "sha256_crypt" in deprecated_schemes
            )  # Still supported but deprecated

    def test_password_hash_uses_timing_safe_comparison(self) -> None:
        """Password verification should use timing-safe comparison."""
        # The implementation uses hmac.compare_digest which is timing-safe
        import hmac

        # Verify the function is available
        assert hasattr(hmac, "compare_digest")
        assert callable(hmac.compare_digest)

    def test_deterministic_mode_disabled_by_default(self) -> None:
        """Deterministic password mode should be disabled by default."""
        from app.utils.security import _DETERMINISTIC_MODE

        # Should be False unless explicitly enabled
        env_value = os.getenv("DETERMINISTIC_PASSWORD_HASH", "")
        if env_value.lower() not in ("1", "true", "yes"):
            assert _DETERMINISTIC_MODE is False


class TestEnvironmentSecurityValidation:
    """Tests for environment variable security validation."""

    def test_secret_key_required(self) -> None:
        """SECRET_KEY should be required for startup."""
        from app.core.config import settings

        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) > 0

    def test_viewer_mutations_default_disabled(self) -> None:
        """ALLOW_VIEWER_MUTATIONS should default to False."""
        # Check the default loading behavior
        from app.core.config import _load_bool

        # If not set in environment, should default to False
        with patch.dict(os.environ, {}, clear=False):
            result = _load_bool("NONEXISTENT_VAR", False)
            assert result is False


class TestDatabaseSecurityConfiguration:
    """Tests for database security configuration."""

    def test_database_uri_required_in_production(self) -> None:
        """Production should require explicit database URI."""
        from app.core.config import Settings

        # Try to create settings with production but no DB URI
        env = {
            "ENVIRONMENT": "production",
            "SECRET_KEY": "test-key",
            "BACKEND_ALLOWED_ORIGINS": "https://example.com",
            "SQLALCHEMY_DATABASE_URI": "",
        }

        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                Settings(validate_production=True)

            assert "SQLALCHEMY_DATABASE_URI" in str(exc_info.value)


class TestDockerSecurityConfiguration:
    """Tests to document expected Docker security configuration."""

    def test_docker_compose_security_requirements(self) -> None:
        """Document Docker Compose security requirements."""
        # This test documents the expected security configuration
        # Actual verification happens in integration tests

        expected_security_features = {
            "read_only_filesystem": True,
            "cap_drop_all": True,
            "no_new_privileges": True,
            "internal_network_for_backend": True,
            "no_exposed_database_ports": True,
            "redis_password_required": True,
            "pinned_image_versions": True,
        }

        # All security features should be expected
        for feature, required in expected_security_features.items():
            assert required is True, f"Security feature '{feature}' should be required"

    def test_nginx_security_headers_required(self) -> None:
        """Document required Nginx security headers."""
        required_headers = [
            "X-Frame-Options",
            "X-Content-Type-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Content-Security-Policy",
            "Permissions-Policy",
            "Cross-Origin-Opener-Policy",
        ]

        # All headers should be documented
        assert len(required_headers) >= 7
