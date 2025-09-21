"""Lightweight httpx stub for test environments without the dependency."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Iterable, Optional
from urllib.parse import urlencode, urlsplit


class Response:
    """Minimal HTTP response object."""

    def __init__(self, status_code: int, body: bytes, headers: Dict[str, str]) -> None:
        self.status_code = status_code
        self._body = body
        self.headers = headers

    def json(self) -> Any:
        if not self._body:
            return None
        return json.loads(self._body.decode("utf-8"))

    def text(self) -> str:
        return self._body.decode("utf-8")

    @property
    def content(self) -> bytes:
        return self._body


class AsyncClient:
    """Very small subset of :class:`httpx.AsyncClient` used in tests."""

    def __init__(self, *, app, base_url: str = "http://testserver") -> None:
        if app is None:
            raise RuntimeError("AsyncClient stub requires an ASGI app instance")
        self._app = app
        self.base_url = base_url

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: D401
        return None

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Any = None,
    ) -> Response:
        path, query = _normalise_url(url)
        if params:
            extra = urlencode(params, doseq=True)
            query = f"{query}&{extra}" if query else extra
        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": method.upper(),
            "path": path,
            "query_string": query.encode("utf-8"),
            "headers": [],
        }
        body = b""
        if json is not None:
            body = _json_bytes(json)
            scope["headers"].append((b"content-type", b"application/json"))
        scope["headers"].append((b"host", self.base_url.encode("utf-8")))

        receive_messages = [{"type": "http.request", "body": body, "more_body": False}]
        sent_messages: list[dict[str, Any]] = []

        async def receive() -> dict[str, Any]:
            if receive_messages:
                return receive_messages.pop(0)
            await asyncio.sleep(0)
            return {"type": "http.disconnect"}

        async def send(message: dict[str, Any]) -> None:
            sent_messages.append(message)

        await self._app(scope, receive, send)

        status_code = 500
        headers: Dict[str, str] = {}
        payload = b""
        for message in sent_messages:
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
                raw_headers: Iterable[tuple[bytes, bytes]] = message.get("headers", [])
                headers = {key.decode("utf-8"): value.decode("utf-8") for key, value in raw_headers}
            elif message["type"] == "http.response.body":
                payload += message.get("body", b"")
        return Response(status_code, payload, headers)

    async def get(self, url: str, *, params: Optional[Dict[str, Any]] = None) -> Response:
        return await self.request("GET", url, params=params)

    async def post(self, url: str, *, json: Any = None) -> Response:
        return await self.request("POST", url, json=json)


def _normalise_url(url: str) -> tuple[str, str]:
    parsed = urlsplit(url)
    path = parsed.path or "/"
    query = parsed.query
    return path, query


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload).encode("utf-8")


__all__ = ["AsyncClient", "Response"]
