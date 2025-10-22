"""Redis-backed rate limiting middleware for API throttling."""

import time
from typing import Callable, Optional

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limiting using Redis."""

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        redis_client: Optional[any] = None,
    ):
        """Initialize rate limiter.

        Args:
            app: FastAPI application instance
            requests_per_minute: Maximum requests allowed per minute per client
            redis_client: Optional Redis client (for testing/dependency injection)
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        self._redis = redis_client

    @property
    def redis(self):
        """Get or create Redis client lazily."""
        if self._redis is None:
            try:
                import redis

                # Parse Redis URL from settings
                redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379")
                self._redis = redis.from_url(
                    redis_url, decode_responses=True, socket_timeout=1
                )
            except Exception as exc:
                logger.warning(
                    "rate_limit_redis_unavailable",
                    error=str(exc),
                    message="Rate limiting disabled - Redis unavailable",
                )
                # Return None to disable rate limiting if Redis is unavailable
                return None
        return self._redis

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting for health/metrics endpoints
        if request.url.path in ["/health", "/metrics", "/health/metrics", "/"]:
            return await call_next(request)

        # Skip if Redis is unavailable (fail open)
        if self.redis is None:
            return await call_next(request)

        # Get client identifier (IP address or X-Forwarded-For header)
        client_ip = self._get_client_ip(request)
        rate_limit_key = f"rate_limit:{client_ip}"

        try:
            # Increment request counter with expiry
            current_count = self.redis.incr(rate_limit_key)

            # Set expiry on first request in window
            if current_count == 1:
                self.redis.expire(rate_limit_key, self.window_seconds)

            # Check if rate limit exceeded
            if current_count > self.requests_per_minute:
                ttl = self.redis.ttl(rate_limit_key)
                retry_after = max(ttl, 1)

                logger.warning(
                    "rate_limit_exceeded",
                    client_ip=client_ip,
                    count=current_count,
                    limit=self.requests_per_minute,
                    retry_after=retry_after,
                )

                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)},
                )

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(
                max(0, self.requests_per_minute - current_count)
            )
            response.headers["X-RateLimit-Reset"] = str(
                int(time.time()) + self.window_seconds
            )

            return response

        except HTTPException:
            # Re-raise HTTP exceptions (including 429)
            raise
        except Exception as exc:
            # Log Redis errors but don't block requests (fail open)
            logger.error(
                "rate_limit_error",
                error=str(exc),
                client_ip=client_ip,
                message="Rate limiting failed - allowing request",
            )
            return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request.

        Checks X-Forwarded-For header first (for proxied requests),
        then falls back to direct client IP.
        """
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can be a comma-separated list; take the first IP
            return forwarded_for.split(",")[0].strip()

        client_host = request.client.host if request.client else "unknown"
        return client_host
