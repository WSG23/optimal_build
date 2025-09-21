"""A lightweight stub of httpx.AsyncClient for local testing."""

from __future__ import annotations

import asyncio
from functools import partial
from typing import Any

try:  # pragma: no cover - optional dependency for offline test runs
    from fastapi.testclient import TestClient
except ModuleNotFoundError:  # pragma: no cover - handled lazily
    TestClient = None  # type: ignore[assignment]


class AsyncClient:
    """Minimal async-compatible client delegating to FastAPI's TestClient."""

    def __init__(self, *, app: Any, base_url: str = "http://testserver") -> None:
        if TestClient is None:
            raise ModuleNotFoundError(
                "fastapi is required to use the AsyncClient test stub"
            )
        self._test_client = TestClient(app, base_url=base_url)

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        await self.aclose()

    async def aclose(self) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._test_client.close)

    async def get(self, url: str, **kwargs: Any):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(self._test_client.get, url, **kwargs))

    async def post(self, url: str, **kwargs: Any):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(self._test_client.post, url, **kwargs))

    async def put(self, url: str, **kwargs: Any):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(self._test_client.put, url, **kwargs))

    async def delete(self, url: str, **kwargs: Any):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(self._test_client.delete, url, **kwargs))


__all__ = ["AsyncClient"]
