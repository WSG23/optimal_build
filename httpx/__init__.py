"""Lightweight httpx stub for test environments without the dependency."""

from __future__ import annotations

import sys
from typing import Any

try:  # Prefer the installed dependency when it is available.
    from backend._stub_loader import import_runtime_dependency
except ModuleNotFoundError:  # pragma: no cover - backend namespace not available
    import_runtime_dependency = None  # type: ignore[assignment]


_httpx_module: Any | None = None
if import_runtime_dependency is not None:
    try:
        _httpx_module = import_runtime_dependency("httpx", "HTTPX")
    except ModuleNotFoundError:  # pragma: no cover - fall back to stub definitions
        _httpx_module = None


if _httpx_module is not None:
    sys.modules[__name__] = _httpx_module
    globals().update(_httpx_module.__dict__)
else:
    import asyncio
    import json
    from collections.abc import Iterable, MutableMapping
    from typing import Dict, Optional
    from urllib.parse import parse_qs, urlencode, urlsplit

    class Response:
        """Minimal HTTP response object."""

        def __init__(
            self, status_code: int, body: bytes, headers: dict[str, str]
        ) -> None:
            self.status_code = status_code
            self._body = body
            self.headers = headers

        def json(self) -> Any:
            if not self._body:
                return None
            return json.loads(self._body.decode("utf-8"))

        @property
        def text(self) -> str:
            return self._body.decode("utf-8")

        @property
        def content(self) -> bytes:
            return self._body

        def read(self) -> bytes:
            return self.content

        async def aread(self) -> bytes:
            return self.content

    class AsyncClient:
        """Very small subset of :class:`httpx.AsyncClient` used in tests."""

        def __init__(
            self,
            *,
            app,
            base_url: str = "http://testserver",
            headers: dict[str, str] | None = None,
        ) -> None:
            if app is None:
                raise RuntimeError("AsyncClient stub requires an ASGI app instance")
            self._app = app
            self.base_url = base_url
            self._default_headers = _prepare_headers(headers, json_payload=None)

        async def __aenter__(self) -> AsyncClient:
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: D401
            return None

        async def request(
            self,
            method: str,
            url: str,
            *,
            params: dict[str, Any] | None = None,
            headers: dict[str, str] | None = None,
            json: Any = None,
            data: dict[str, Any] | None = None,
            files: MutableMapping[str, tuple[str, Any, str | None]] | None = None,
        ) -> Response:
            path, query = _normalise_url(url)
            query_params = _merge_query(query, params)
            prepared_headers = _prepare_headers(
                headers, json, base=self._default_headers
            )

            prepared_files: dict[str, tuple[str, bytes, str]] = {}
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
                        (
                            content
                            if isinstance(content, (bytes, bytearray))
                            else bytes(content)
                        ),
                        content_type or "application/octet-stream",
                    )

            if hasattr(self._app, "handle_request"):
                status_code, headers, payload = await self._app.handle_request(
                    method=method,
                    path=path,
                    query_params=query_params,
                    json_body=json,
                    form_data=dict(data or {}),
                    files=prepared_files,
                    headers=prepared_headers,
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
            if prepared_headers:
                for key, value in prepared_headers.items():
                    scope["headers"].append(
                        (key.encode("utf-8"), str(value).encode("utf-8"))
                    )
            else:
                scope["headers"].append((b"host", self.base_url.encode("utf-8")))
            if not any(key == b"host" for key, _ in scope["headers"]):
                scope["headers"].append((b"host", self.base_url.encode("utf-8")))

            receive_messages = [
                {"type": "http.request", "body": body, "more_body": False}
            ]
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
            headers: dict[str, str] = {}
            payload = b""
            for message in sent_messages:
                if message["type"] == "http.response.start":
                    status_code = message.get("status", 500)
                    raw_headers: Iterable[tuple[bytes, bytes]] = message.get(
                        "headers", []
                    )
                    headers = {
                        key.decode("utf-8"): value.decode("utf-8")
                        for key, value in raw_headers
                    }
                elif message["type"] == "http.response.body":
                    payload += message.get("body", b"")
            return Response(status_code, payload, headers)

        async def get(
            self,
            url: str,
            *,
            params: dict[str, Any] | None = None,
            headers: dict[str, str] | None = None,
        ) -> Response:
            return await self.request("GET", url, params=params, headers=headers)

        async def post(
            self,
            url: str,
            *,
            headers: dict[str, str] | None = None,
            json: Any = None,
            data: dict[str, Any] | None = None,
            files: MutableMapping[str, tuple[str, Any, str | None]] | None = None,
        ) -> Response:
            return await self.request(
                "POST", url, headers=headers, json=json, data=data, files=files
            )

        async def put(
            self,
            url: str,
            *,
            headers: dict[str, str] | None = None,
            json: Any = None,
            data: dict[str, Any] | None = None,
        ) -> Response:
            return await self.request("PUT", url, headers=headers, json=json, data=data)

        async def delete(
            self,
            url: str,
            *,
            headers: dict[str, str] | None = None,
            json: Any = None,
        ) -> Response:
            return await self.request("DELETE", url, headers=headers, json=json)

    def _normalise_url(url: str) -> tuple[str, str]:
        parsed = urlsplit(url)
        path = parsed.path or "/"
        query = parsed.query
        return path, query

    def _json_bytes(payload: Any) -> bytes:
        return json.dumps(payload).encode("utf-8")


def _merge_query(query: str, params: dict[str, Any] | None) -> dict[str, Any]:
    combined: dict[str, Any] = {
        key: values[0] if len(values) == 1 else values
        for key, values in parse_qs(query, keep_blank_values=True).items()
    }
    if params:
        combined.update(params)
    return combined


def _prepare_headers(
    headers: dict[str, str] | None,
    json_payload: Any,
    *,
    base: dict[str, str] | None = None,
) -> dict[str, str]:
    prepared: dict[str, str] = dict(base or {})
    if headers:
        for key, value in headers.items():
            prepared[key.lower()] = str(value)
    if json_payload is not None and "content-type" not in prepared:
        prepared["content-type"] = "application/json"
    return prepared


__all__ = ["AsyncClient", "Response"]
