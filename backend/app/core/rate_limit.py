"""Rate limiting middleware for API protection.

Provides configurable rate limiting per endpoint, user, and IP address
to prevent abuse and ensure fair resource usage.
"""

from __future__ import annotations

import hashlib
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class RateLimitTier(str, Enum):
    """Rate limit tiers for different user types."""

    ANONYMOUS = "anonymous"
    AUTHENTICATED = "authenticated"
    PREMIUM = "premium"
    ADMIN = "admin"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    # Requests per window
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000

    # Burst allowance (short-term spike tolerance)
    burst_size: int = 10
    burst_window_seconds: int = 1

    # Per-tier multipliers
    tier_multipliers: dict[RateLimitTier, float] = field(
        default_factory=lambda: {
            RateLimitTier.ANONYMOUS: 0.5,
            RateLimitTier.AUTHENTICATED: 1.0,
            RateLimitTier.PREMIUM: 2.0,
            RateLimitTier.ADMIN: 10.0,
        }
    )


# Default configuration
DEFAULT_CONFIG = RateLimitConfig()

# Endpoint-specific overrides (more restrictive for sensitive endpoints)
ENDPOINT_LIMITS: dict[str, RateLimitConfig] = {
    "/api/v1/auth/login": RateLimitConfig(
        requests_per_minute=5,
        requests_per_hour=20,
        requests_per_day=100,
        burst_size=3,
    ),
    "/api/v1/auth/register": RateLimitConfig(
        requests_per_minute=3,
        requests_per_hour=10,
        requests_per_day=20,
        burst_size=2,
    ),
    "/api/v1/auth/forgot-password": RateLimitConfig(
        requests_per_minute=3,
        requests_per_hour=10,
        requests_per_day=20,
        burst_size=2,
    ),
    "/api/v1/projects/*/export": RateLimitConfig(
        requests_per_minute=5,
        requests_per_hour=30,
        requests_per_day=100,
        burst_size=2,
    ),
}


@dataclass
class RateLimitState:
    """Tracks rate limit state for a key."""

    minute_count: int = 0
    minute_reset: float = 0.0
    hour_count: int = 0
    hour_reset: float = 0.0
    day_count: int = 0
    day_reset: float = 0.0
    burst_tokens: float = 0.0
    burst_last_update: float = 0.0


class RateLimiter:
    """In-memory rate limiter with sliding window."""

    def __init__(self) -> None:
        self._state: dict[str, RateLimitState] = defaultdict(RateLimitState)
        self._cleanup_interval = 300  # Clean up every 5 minutes
        self._last_cleanup = time.time()

    def _get_key(
        self,
        identifier: str,
        endpoint: str,
    ) -> str:
        """Generate a unique key for rate limiting."""
        return hashlib.sha256(f"{identifier}:{endpoint}".encode()).hexdigest()[:32]

    def _cleanup_expired(self) -> None:
        """Remove expired entries to prevent memory growth."""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return

        expired_keys = []
        for key, state in self._state.items():
            # Remove if all windows have expired
            if (
                state.minute_reset < now
                and state.hour_reset < now
                and state.day_reset < now
            ):
                expired_keys.append(key)

        for key in expired_keys:
            del self._state[key]

        self._last_cleanup = now

    def _get_config_for_endpoint(self, endpoint: str) -> RateLimitConfig:
        """Get rate limit config for an endpoint, with wildcard matching."""
        # Exact match first
        if endpoint in ENDPOINT_LIMITS:
            return ENDPOINT_LIMITS[endpoint]

        # Wildcard matching (e.g., /api/v1/projects/*/export)
        for pattern, config in ENDPOINT_LIMITS.items():
            if "*" in pattern:
                # Convert to regex-like matching
                parts = pattern.split("*")
                if (
                    len(parts) == 2
                    and endpoint.startswith(parts[0])
                    and endpoint.endswith(parts[1])
                ):
                    return config

        return DEFAULT_CONFIG

    def check_rate_limit(
        self,
        identifier: str,
        endpoint: str,
        tier: RateLimitTier = RateLimitTier.ANONYMOUS,
    ) -> tuple[bool, dict[str, Any]]:
        """Check if request is within rate limits.

        Args:
            identifier: Unique identifier (IP, user ID, API key)
            endpoint: The API endpoint being accessed
            tier: User tier for limit multipliers

        Returns:
            Tuple of (allowed, headers) where headers contain rate limit info
        """
        self._cleanup_expired()

        key = self._get_key(identifier, endpoint)
        state = self._state[key]
        config = self._get_config_for_endpoint(endpoint)
        multiplier = config.tier_multipliers.get(tier, 1.0)

        now = time.time()

        # Calculate effective limits
        minute_limit = int(config.requests_per_minute * multiplier)
        hour_limit = int(config.requests_per_hour * multiplier)
        day_limit = int(config.requests_per_day * multiplier)
        burst_limit = int(config.burst_size * multiplier)

        # Reset windows if expired
        if now > state.minute_reset:
            state.minute_count = 0
            state.minute_reset = now + 60

        if now > state.hour_reset:
            state.hour_count = 0
            state.hour_reset = now + 3600

        if now > state.day_reset:
            state.day_count = 0
            state.day_reset = now + 86400

        # Token bucket for burst control
        time_passed = now - state.burst_last_update
        state.burst_tokens = min(
            burst_limit,
            state.burst_tokens
            + time_passed * (burst_limit / config.burst_window_seconds),
        )
        state.burst_last_update = now

        # Check limits
        headers = {
            "X-RateLimit-Limit-Minute": str(minute_limit),
            "X-RateLimit-Remaining-Minute": str(
                max(0, minute_limit - state.minute_count)
            ),
            "X-RateLimit-Reset-Minute": str(int(state.minute_reset)),
            "X-RateLimit-Limit-Hour": str(hour_limit),
            "X-RateLimit-Remaining-Hour": str(max(0, hour_limit - state.hour_count)),
        }

        # Check burst limit
        if state.burst_tokens < 1:
            headers["Retry-After"] = str(config.burst_window_seconds)
            return False, headers

        # Check minute limit
        if state.minute_count >= minute_limit:
            headers["Retry-After"] = str(int(state.minute_reset - now))
            return False, headers

        # Check hour limit
        if state.hour_count >= hour_limit:
            headers["Retry-After"] = str(int(state.hour_reset - now))
            return False, headers

        # Check day limit
        if state.day_count >= day_limit:
            headers["Retry-After"] = str(int(state.day_reset - now))
            return False, headers

        # Request allowed - update counters
        state.minute_count += 1
        state.hour_count += 1
        state.day_count += 1
        state.burst_tokens -= 1

        return True, headers

    def get_remaining(
        self,
        identifier: str,
        endpoint: str,
        tier: RateLimitTier = RateLimitTier.ANONYMOUS,
    ) -> dict[str, int]:
        """Get remaining requests for an identifier."""
        key = self._get_key(identifier, endpoint)
        state = self._state[key]
        config = self._get_config_for_endpoint(endpoint)
        multiplier = config.tier_multipliers.get(tier, 1.0)

        return {
            "minute": max(
                0, int(config.requests_per_minute * multiplier) - state.minute_count
            ),
            "hour": max(
                0, int(config.requests_per_hour * multiplier) - state.hour_count
            ),
            "day": max(0, int(config.requests_per_day * multiplier) - state.day_count),
        }


# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""

    def __init__(
        self,
        app: Any,
        limiter: RateLimiter | None = None,
        enabled: bool = True,
        exclude_paths: list[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.limiter = limiter or get_rate_limiter()
        self.enabled = enabled
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

    def _get_identifier(self, request: Request) -> tuple[str, RateLimitTier]:
        """Extract identifier and tier from request."""
        # Check for authenticated user
        user = getattr(request.state, "user", None)
        if user:
            user_id = getattr(user, "id", None)
            if user_id:
                # Determine tier based on user attributes
                is_admin = getattr(user, "is_superuser", False)
                is_premium = getattr(user, "is_premium", False)

                if is_admin:
                    return f"user:{user_id}", RateLimitTier.ADMIN
                elif is_premium:
                    return f"user:{user_id}", RateLimitTier.PREMIUM
                else:
                    return f"user:{user_id}", RateLimitTier.AUTHENTICATED

        # Fall back to IP address for anonymous users
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        return f"ip:{ip}", RateLimitTier.ANONYMOUS

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process request through rate limiter."""
        if not self.enabled:
            return await call_next(request)

        # Skip excluded paths
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)

        identifier, tier = self._get_identifier(request)
        allowed, headers = self.limiter.check_rate_limit(identifier, path, tier)

        if not allowed:
            response = Response(
                content='{"detail": "Rate limit exceeded. Please retry later."}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
            )
            for key, value in headers.items():
                response.headers[key] = value
            return response

        # Process request
        response = await call_next(request)

        # Add rate limit headers to successful responses
        for key, value in headers.items():
            response.headers[key] = value

        return response


def rate_limit(
    requests_per_minute: int | None = None,
    requests_per_hour: int | None = None,
    key_func: Callable[[Request], str] | None = None,
) -> Callable:
    """Decorator for endpoint-specific rate limiting.

    Usage:
        @router.get("/expensive-operation")
        @rate_limit(requests_per_minute=5)
        async def expensive_operation():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
            limiter = get_rate_limiter()

            # Get identifier
            if key_func:
                identifier = key_func(request)
            else:
                forwarded = request.headers.get("X-Forwarded-For")
                if forwarded:
                    identifier = f"ip:{forwarded.split(',')[0].strip()}"
                else:
                    identifier = (
                        f"ip:{request.client.host if request.client else 'unknown'}"
                    )

            # Create custom config for this decorator
            config = RateLimitConfig(
                requests_per_minute=requests_per_minute
                or DEFAULT_CONFIG.requests_per_minute,
                requests_per_hour=requests_per_hour or DEFAULT_CONFIG.requests_per_hour,
            )

            # Temporarily register this endpoint's config
            endpoint = request.url.path
            original_config = ENDPOINT_LIMITS.get(endpoint)
            ENDPOINT_LIMITS[endpoint] = config

            try:
                allowed, headers = limiter.check_rate_limit(
                    identifier,
                    endpoint,
                    RateLimitTier.ANONYMOUS,
                )

                if not allowed:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded. Please retry later.",
                        headers=headers,
                    )

                return await func(request, *args, **kwargs)
            finally:
                # Restore original config
                if original_config:
                    ENDPOINT_LIMITS[endpoint] = original_config
                elif endpoint in ENDPOINT_LIMITS:
                    del ENDPOINT_LIMITS[endpoint]

        return wrapper

    return decorator


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
    ) -> None:
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)
