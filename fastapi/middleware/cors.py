"""CORS middleware placeholder for the FastAPI stub."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

__all__ = ["CORSMiddleware"]


class CORSMiddleware:
    """No-op CORS middleware used to satisfy application wiring."""

    def __init__(self, app: Callable, **options: Any) -> None:
        self.app = app
        self.options = options

    async def __call__(self, scope: Dict[str, Any], receive: Callable[[], Awaitable[Dict[str, Any]]], send: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        await self.app(scope, receive, send)
