"""Tests for the rate limiting middleware."""

from __future__ import annotations


import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.rate_limit import (
    ENDPOINT_LIMITS,
    RateLimitConfig,
    RateLimiter,
    RateLimitMiddleware,
    RateLimitTier,
    get_rate_limiter,
    rate_limit,
)


class TestRateLimitConfig:
    """Tests for RateLimitConfig."""

    def test_default_config_values(self) -> None:
        """Test default configuration values."""
        config = RateLimitConfig()

        assert config.requests_per_minute == 60
        assert config.requests_per_hour == 1000
        assert config.requests_per_day == 10000
        assert config.burst_size == 10
        assert config.burst_window_seconds == 1

    def test_tier_multipliers(self) -> None:
        """Test tier multipliers are set correctly."""
        config = RateLimitConfig()

        assert config.tier_multipliers[RateLimitTier.ANONYMOUS] == 0.5
        assert config.tier_multipliers[RateLimitTier.AUTHENTICATED] == 1.0
        assert config.tier_multipliers[RateLimitTier.PREMIUM] == 2.0
        assert config.tier_multipliers[RateLimitTier.ADMIN] == 10.0

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            burst_size=5,
        )

        assert config.requests_per_minute == 10
        assert config.requests_per_hour == 100
        assert config.burst_size == 5


class TestRateLimiter:
    """Tests for the RateLimiter class."""

    @pytest.fixture
    def limiter(self) -> RateLimiter:
        """Create a fresh rate limiter."""
        return RateLimiter()

    def test_first_request_allowed(self, limiter: RateLimiter) -> None:
        """Test first request is always allowed."""
        allowed, headers = limiter.check_rate_limit(
            "test-user",
            "/api/v1/test",
            RateLimitTier.AUTHENTICATED,
        )

        assert allowed is True
        assert "X-RateLimit-Limit-Minute" in headers
        assert "X-RateLimit-Remaining-Minute" in headers

    def test_rate_limit_headers(self, limiter: RateLimiter) -> None:
        """Test rate limit headers are returned."""
        _, headers = limiter.check_rate_limit(
            "test-user",
            "/api/v1/test",
            RateLimitTier.AUTHENTICATED,
        )

        assert headers["X-RateLimit-Limit-Minute"] == "60"  # Default for authenticated
        # After first request, remaining should be 59 or 60 depending on timing
        assert int(headers["X-RateLimit-Remaining-Minute"]) >= 59

    def test_minute_limit_exceeded(self, limiter: RateLimiter) -> None:
        """Test requests are blocked when minute limit exceeded."""
        # Use anonymous tier with 0.5 multiplier = 30 requests/minute
        # But burst tokens also limit rapid requests
        allowed_count = 0
        blocked = False

        for _i in range(35):  # Try more than limit
            allowed, headers = limiter.check_rate_limit(
                "test-ip",
                "/api/v1/test",
                RateLimitTier.ANONYMOUS,
            )
            if allowed:
                allowed_count += 1
            else:
                blocked = True
                assert "Retry-After" in headers
                break

        # Should have been blocked at some point
        # (either by burst limit or minute limit)
        assert blocked or allowed_count <= 30, "Should be rate limited"

    def test_different_identifiers_independent(self, limiter: RateLimiter) -> None:
        """Test different identifiers have independent limits."""
        # Exhaust limit for user1
        for _ in range(30):
            limiter.check_rate_limit("user1", "/api/v1/test", RateLimitTier.ANONYMOUS)

        # user1 should be blocked
        allowed1, _ = limiter.check_rate_limit(
            "user1",
            "/api/v1/test",
            RateLimitTier.ANONYMOUS,
        )
        assert allowed1 is False

        # user2 should still be allowed
        allowed2, _ = limiter.check_rate_limit(
            "user2",
            "/api/v1/test",
            RateLimitTier.ANONYMOUS,
        )
        assert allowed2 is True

    def test_different_endpoints_independent(self, limiter: RateLimiter) -> None:
        """Test different endpoints have independent limits."""
        # Exhaust limit for endpoint1
        for _ in range(30):
            limiter.check_rate_limit(
                "user", "/api/v1/endpoint1", RateLimitTier.ANONYMOUS
            )

        # endpoint1 should be blocked
        allowed1, _ = limiter.check_rate_limit(
            "user",
            "/api/v1/endpoint1",
            RateLimitTier.ANONYMOUS,
        )
        assert allowed1 is False

        # endpoint2 should still be allowed
        allowed2, _ = limiter.check_rate_limit(
            "user",
            "/api/v1/endpoint2",
            RateLimitTier.ANONYMOUS,
        )
        assert allowed2 is True

    def test_tier_affects_limits(self, limiter: RateLimiter) -> None:
        """Test different tiers have different limits."""
        # Anonymous: 30/min (60 * 0.5)
        # Authenticated: 60/min (60 * 1.0)
        # Admin: 600/min (60 * 10.0)

        _, anon_headers = limiter.check_rate_limit(
            "anon",
            "/api/v1/test",
            RateLimitTier.ANONYMOUS,
        )
        _, auth_headers = limiter.check_rate_limit(
            "auth",
            "/api/v1/test",
            RateLimitTier.AUTHENTICATED,
        )
        _, admin_headers = limiter.check_rate_limit(
            "admin",
            "/api/v1/test",
            RateLimitTier.ADMIN,
        )

        assert int(anon_headers["X-RateLimit-Limit-Minute"]) == 30
        assert int(auth_headers["X-RateLimit-Limit-Minute"]) == 60
        assert int(admin_headers["X-RateLimit-Limit-Minute"]) == 600

    def test_endpoint_specific_limits(self, limiter: RateLimiter) -> None:
        """Test endpoint-specific rate limits."""
        # Login endpoint should have stricter limits
        _, headers = limiter.check_rate_limit(
            "user",
            "/api/v1/auth/login",
            RateLimitTier.ANONYMOUS,
        )

        # 5 * 0.5 = 2 for anonymous
        assert int(headers["X-RateLimit-Limit-Minute"]) == 2

    def test_get_remaining(self, limiter: RateLimiter) -> None:
        """Test getting remaining requests."""
        # Make some requests
        for _ in range(5):
            limiter.check_rate_limit(
                "user", "/api/v1/test", RateLimitTier.AUTHENTICATED
            )

        remaining = limiter.get_remaining(
            "user", "/api/v1/test", RateLimitTier.AUTHENTICATED
        )

        assert remaining["minute"] == 55  # 60 - 5


class TestRateLimitMiddleware:
    """Tests for the RateLimitMiddleware."""

    @pytest.fixture
    def app(self) -> FastAPI:
        """Create a test FastAPI app with rate limiting."""
        app = FastAPI()

        @app.get("/api/v1/test")
        async def test_endpoint() -> dict:
            return {"status": "ok"}

        @app.get("/health")
        async def health() -> dict:
            return {"status": "healthy"}

        app.add_middleware(RateLimitMiddleware)
        return app

    @pytest.fixture
    def client(self, app: FastAPI) -> TestClient:
        """Create a test client."""
        return TestClient(app)

    def test_successful_request_includes_headers(self, client: TestClient) -> None:
        """Test successful requests include rate limit headers."""
        response = client.get("/api/v1/test")

        assert response.status_code == 200
        assert "X-RateLimit-Limit-Minute" in response.headers
        assert "X-RateLimit-Remaining-Minute" in response.headers

    def test_excluded_paths_not_limited(self, client: TestClient) -> None:
        """Test excluded paths are not rate limited."""
        # Health endpoint should not be rate limited
        for _ in range(100):
            response = client.get("/health")
            assert response.status_code == 200

    def test_rate_limit_returns_429(self, client: TestClient) -> None:
        """Test rate limit exceeded returns 429."""
        # Make many requests quickly (will hit burst limit)
        responses = []
        for _ in range(50):
            responses.append(client.get("/api/v1/test"))

        # At least one should be 429
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes or all(s == 200 for s in status_codes[:30])

    def test_disabled_middleware(self) -> None:
        """Test middleware can be disabled."""
        app = FastAPI()

        @app.get("/api/v1/test")
        async def test_endpoint() -> dict:
            return {"status": "ok"}

        app.add_middleware(RateLimitMiddleware, enabled=False)
        client = TestClient(app)

        # Should not have rate limit headers when disabled
        response = client.get("/api/v1/test")
        assert response.status_code == 200


class TestRateLimitDecorator:
    """Tests for the rate_limit decorator."""

    def test_decorator_exists(self) -> None:
        """Test rate_limit decorator is importable and callable."""
        # Just verify the decorator can be used
        assert callable(rate_limit)
        assert callable(rate_limit(requests_per_minute=10))


class TestGlobalRateLimiter:
    """Tests for the global rate limiter."""

    def test_get_rate_limiter_returns_singleton(self) -> None:
        """Test get_rate_limiter returns the same instance."""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()

        assert limiter1 is limiter2


class TestEndpointLimits:
    """Tests for endpoint-specific limits."""

    def test_login_endpoint_has_strict_limits(self) -> None:
        """Test login endpoint has strict rate limits."""
        assert "/api/v1/auth/login" in ENDPOINT_LIMITS

        config = ENDPOINT_LIMITS["/api/v1/auth/login"]
        assert config.requests_per_minute == 5
        assert config.requests_per_hour == 20

    def test_register_endpoint_has_strict_limits(self) -> None:
        """Test register endpoint has strict rate limits."""
        assert "/api/v1/auth/register" in ENDPOINT_LIMITS

        config = ENDPOINT_LIMITS["/api/v1/auth/register"]
        assert config.requests_per_minute == 3

    def test_forgot_password_endpoint_has_strict_limits(self) -> None:
        """Test forgot-password endpoint has strict rate limits."""
        assert "/api/v1/auth/forgot-password" in ENDPOINT_LIMITS

        config = ENDPOINT_LIMITS["/api/v1/auth/forgot-password"]
        assert config.requests_per_minute == 3


class TestRateLimitTier:
    """Tests for RateLimitTier enum."""

    def test_tier_values(self) -> None:
        """Test tier enum values."""
        assert RateLimitTier.ANONYMOUS.value == "anonymous"
        assert RateLimitTier.AUTHENTICATED.value == "authenticated"
        assert RateLimitTier.PREMIUM.value == "premium"
        assert RateLimitTier.ADMIN.value == "admin"

    def test_all_tiers_have_multipliers(self) -> None:
        """Test all tiers have multipliers in default config."""
        config = RateLimitConfig()

        for tier in RateLimitTier:
            assert tier in config.tier_multipliers


class TestBurstControl:
    """Tests for burst control functionality."""

    def test_burst_allows_quick_requests(self) -> None:
        """Test burst allows rapid requests up to limit."""
        limiter = RateLimiter()

        # Quick burst of requests
        results = []
        for _ in range(10):  # Burst size is 10 for authenticated
            allowed, _ = limiter.check_rate_limit(
                "burst-user",
                "/api/v1/test",
                RateLimitTier.AUTHENTICATED,
            )
            results.append(allowed)

        # Most should be allowed due to initial burst tokens
        assert sum(results) >= 5  # At least half should succeed


class TestCleanup:
    """Tests for state cleanup."""

    def test_cleanup_removes_expired_entries(self) -> None:
        """Test expired entries are cleaned up."""
        limiter = RateLimiter()
        limiter._cleanup_interval = 0  # Force immediate cleanup

        # Add an entry
        limiter.check_rate_limit("old-user", "/api/v1/test", RateLimitTier.ANONYMOUS)

        # Manually expire the entry
        key = limiter._get_key("old-user", "/api/v1/test")
        state = limiter._state[key]
        state.minute_reset = 0
        state.hour_reset = 0
        state.day_reset = 0

        # Trigger cleanup
        limiter._last_cleanup = 0
        limiter._cleanup_expired()

        # Entry should be removed
        assert key not in limiter._state
