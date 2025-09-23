"""Lightweight httpx stub for test environments without the dependency."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Iterable, MutableMapping, Optional
from urllib.parse import parse_qs, urlencode, urlsplit


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
        data: Optional[Dict[str, Any]] = None,
        files: Optional[MutableMapping[str, tuple[str, Any, str | None]]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        path, query = _normalise_url(url)
        query_params = _merge_query(query, params)

        prepared_files: Dict[str, tuple[str, bytes, str]] = {}
        if files:
            for key, (filename, payload, content_type) in files.items():
                if hasattr(payload, "read"):
                    content = payload.read()
                else:
                    content = payload
                if isinstance(content, str):
                    content = content.encode("utf-8")
                prepared_files[key] = (
                    filename,
                    content if isinstance(content, (bytes, bytearray)) else bytes(content),
                    content_type or "application/octet-stream",
                )

        header_map = {key.lower(): value for key, value in (headers or {}).items()}

        if hasattr(self._app, "handle_request"):
            status_code, headers, payload = await self._app.handle_request(
                method=method,
                path=path,
                query_params=query_params,
                json_body=json,
                form_data=dict(data or {}),
                files=prepared_files,
                headers=header_map,
            )
            return Response(status_code, payload, dict(headers))

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
        scope_headers = {"host": self.base_url}
        scope_headers.update({key: value for key, value in header_map.items()})
        for name, value in scope_headers.items():
            scope["headers"].append((name.encode("utf-8"), value.encode("utf-8")))

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

    async def get(
        self,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        return await self.request("GET", url, params=params, headers=headers)

    async def post(
        self,
        url: str,
        *,
        json: Any = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[MutableMapping[str, tuple[str, Any, str | None]]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        return await self.request("POST", url, json=json, data=data, files=files, headers=headers)


def _normalise_url(url: str) -> tuple[str, str]:
    parsed = urlsplit(url)
    path = parsed.path or "/"
    query = parsed.query
    return path, query


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload).encode("utf-8")


def _merge_query(query: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    combined: Dict[str, Any] = {
        key: values[0] if len(values) == 1 else values
        for key, values in parse_qs(query, keep_blank_values=True).items()
    }
    if params:
        combined.update(params)
    return combined


__all__ = ["AsyncClient", "Response"]
