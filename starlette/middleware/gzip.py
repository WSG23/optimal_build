"""GZip middleware stub for tests."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

__all__ = ["GZipMiddleware"]


class GZipMiddleware:
    """No-op middleware that delegates requests to the wrapped ASGI app."""

    def __init__(
        self,
        app: Callable[..., Awaitable[Any]],
        *,
        minimum_size: int = 500,
        compresslevel: int = 5,
    ) -> None:
        self.app = app
        self.minimum_size = minimum_size
        self.compresslevel = compresslevel

    async def __call__(self, scope, receive, send):
        await self.app(scope, receive, send)
