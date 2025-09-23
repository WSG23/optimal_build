"""A lightweight stub of httpx.AsyncClient for local testing."""

from __future__ import annotations

import asyncio
from functools import partial
from typing import Any

try:  # pragma: no cover - optional dependency for offline test runs
    from fastapi.testclient import TestClient
except ModuleNotFoundError:  # pragma: no cover - handled lazily
    TestClient = None  # type: ignore[assignment]


class _AsyncResponse:
    """Wrapper adding awaitable helpers to synchronous test responses."""

    def __init__(self, response: Any) -> None:
        self._response = response

    def __getattr__(self, name: str) -> Any:  # pragma: no cover - simple delegation
        return getattr(self._response, name)

    @property
    def status_code(self) -> int:
        return self._response.status_code

    @property
    def headers(self) -> Any:
        return self._response.headers

    def json(self) -> Any:
        return self._response.json()

    @property
    def text(self) -> str:
        payload = getattr(self._response, "content", b"")
        if isinstance(payload, bytes):
            return payload.decode("utf-8")
        return str(payload)

    def read(self) -> bytes:
        return getattr(self._response, "content", b"")

    async def aread(self) -> bytes:
        return self.read()


class AsyncClient:
    """Minimal async-compatible client delegating to FastAPI's TestClient."""

    def __init__(
        self,
        *,
        app: Any,
        base_url: str = "http://testserver",
        headers: dict[str, str] | None = None,
    ) -> None:
        if TestClient is None:
            raise ModuleNotFoundError(
                "fastapi is required to use the AsyncClient test stub"
            )
        self._test_client = TestClient(app, base_url=base_url)
        self._default_headers = dict(headers or {})

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        await self.aclose()

    async def aclose(self) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._test_client.close)

    def _apply_headers(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        if not self._default_headers:
            return kwargs
        combined = dict(self._default_headers)
        extra = kwargs.get("headers")
        if extra:
            combined.update(extra)
        updated = dict(kwargs)
        updated["headers"] = combined
        return updated

    async def get(self, url: str, **kwargs: Any):
        kwargs = self._apply_headers(kwargs)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, partial(self._test_client.get, url, **kwargs))
        return _AsyncResponse(response)

    async def post(self, url: str, **kwargs: Any):
        kwargs = self._apply_headers(kwargs)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, partial(self._test_client.post, url, **kwargs))
        return _AsyncResponse(response)

    async def put(self, url: str, **kwargs: Any):
        kwargs = self._apply_headers(kwargs)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, partial(self._test_client.put, url, **kwargs))
        return _AsyncResponse(response)

    async def delete(self, url: str, **kwargs: Any):
        kwargs = self._apply_headers(kwargs)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, partial(self._test_client.delete, url, **kwargs))
        return _AsyncResponse(response)


__all__ = ["AsyncClient"]
