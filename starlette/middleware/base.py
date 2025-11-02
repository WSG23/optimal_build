"""Base middleware helpers for the Starlette stub."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from starlette.types import ASGIApp

RequestResponseEndpoint = Callable[[Any], Awaitable[Any]]

__all__ = ["BaseHTTPMiddleware", "RequestResponseEndpoint"]


class BaseHTTPMiddleware:
    """Simplified BaseHTTPMiddleware that forwards requests to the wrapped app."""

    def __init__(self, app: ASGIApp, **_: Any) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        await self.app(scope, receive, send)

    async def dispatch(self, request: Any, call_next: RequestResponseEndpoint) -> Any:
        return await call_next(request)
