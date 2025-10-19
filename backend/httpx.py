"""A lightweight stub of httpx.AsyncClient for local testing."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Iterable, MutableMapping
from functools import partial
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit
from uuid import uuid4

_TEST_CLIENT: Any | None = None
_TEST_CLIENT_UNAVAILABLE = False


def _get_test_client() -> Any:
    """Import FastAPI's TestClient lazily to avoid circular imports."""

    global _TEST_CLIENT, _TEST_CLIENT_UNAVAILABLE
    if _TEST_CLIENT is not None:
        return _TEST_CLIENT
    if _TEST_CLIENT_UNAVAILABLE:
        return None

    try:  # pragma: no cover - optional dependency for offline test runs
        from fastapi.testclient import TestClient
    except Exception:  # pragma: no cover - handled lazily and across httpx versions
        import sys
        from pathlib import Path

        repo_root = Path(__file__).resolve().parents[1]
        if str(repo_root) not in sys.path:
            sys.path.append(str(repo_root))

        try:
            from fastapi.testclient import TestClient  # type: ignore[assignment]
        except (
            Exception
        ):  # pragma: no cover - propagate meaningful error if fully unavailable
            _TEST_CLIENT_UNAVAILABLE = True
            return None
    _TEST_CLIENT = TestClient
    return TestClient


class Response:
    def __init__(self, status_code: int, body: bytes, headers: dict[str, str]) -> None:
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


class _StubAsyncClient:
    def __init__(
        self,
        *,
        app: Any,
        base_url: str = "http://testserver",
        headers: dict[str, str] | None = None,
        **_: Any,
    ) -> None:
        if app is None:
            raise RuntimeError("AsyncClient stub requires an ASGI app instance")
        self._app = app
        self.base_url = base_url
        self._default_headers = _prepare_headers(headers, json_payload=None)

    async def __aenter__(self) -> _StubAsyncClient:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def aclose(self) -> None:
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
        prepared_headers = _prepare_headers(headers, json, base=self._default_headers)

        prepared_files: dict[str, tuple[str | None, bytes, str]] = {}
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
        body = b""
        if json is not None:
            body = _json_bytes(json)
        elif prepared_files or data:
            boundary = f"----httpxboundary{uuid4().hex}"
            parts: list[bytes] = []
            for key, value in (data or {}).items():
                value_str = str(value)
                parts.append(
                    (
                        f"--{boundary}\r\n"
                        f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
                    ).encode("utf-8")
                    + value_str.encode("utf-8")
                    + b"\r\n"
                )
            for key, (filename, content, content_type) in prepared_files.items():
                filename_value = filename or key
                parts.append(
                    (
                        f"--{boundary}\r\n"
                        f'Content-Disposition: form-data; name="{key}"; filename="{filename_value}"\r\n'
                        f"Content-Type: {content_type}\r\n\r\n"
                    ).encode("utf-8")
                    + content
                    + b"\r\n"
                )
            parts.append(f"--{boundary}--\r\n".encode("utf-8"))
            body = b"".join(parts)
            prepared_headers[
                "content-type"
            ] = f"multipart/form-data; boundary={boundary}"
        elif data:
            body = urlencode(data).encode("utf-8")
            prepared_headers.setdefault(
                "content-type", "application/x-www-form-urlencoded"
            )

        if hasattr(self._app, "handle_request"):
            status_code, resp_headers, payload = await self._app.handle_request(
                method=method,
                path=path,
                query_params=query_params,
                json_body=json,
                form_data=dict(data or {}),
                files=prepared_files,
                headers=prepared_headers,
            )
            header_map = {
                str(key).lower(): str(value)
                for key, value in dict(resp_headers).items()
            }
            _normalise_content_type(header_map)
            return Response(status_code, payload, header_map)

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

        receive_messages = [{"type": "http.request", "body": body, "more_body": False}]
        sent_messages: list[dict[str, Any]] = []
        stream_complete = asyncio.Event()

        async def receive() -> dict[str, Any]:
            if receive_messages:
                return receive_messages.pop(0)
            await stream_complete.wait()
            return {"type": "http.disconnect"}

        async def send(message: dict[str, Any]) -> None:
            sent_messages.append(message)
            if message["type"] == "http.response.body" and not message.get(
                "more_body", False
            ):
                stream_complete.set()

        await self._app(scope, receive, send)

        if not stream_complete.is_set():
            stream_complete.set()

        status_code = 500
        resp_headers: dict[str, str] = {}
        payload = b""
        for message in sent_messages:
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
                raw_headers: Iterable[tuple[bytes, bytes]] = message.get("headers", [])
                resp_headers = {
                    key.decode("utf-8").lower(): value.decode("utf-8")
                    for key, value in raw_headers
                }
                _normalise_content_type(resp_headers)
            elif message["type"] == "http.response.body":
                payload += message.get("body", b"")
        return Response(status_code, payload, resp_headers)

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
        app: Any | None = None,
        transport: Any | None = None,
        base_url: str = "http://testserver",
        headers: dict[str, str] | None = None,
        **extra: Any,
    ) -> None:
        if transport is not None and hasattr(transport, "app") and app is None:
            app = transport.app
        if app is None:
            raise RuntimeError("AsyncClient stub requires an ASGI app instance")
        self._mode: str
        self._default_headers = dict(headers or {})
        test_client = _get_test_client()
        if test_client is not None:
            self._mode = "testclient"
            self._test_client = test_client(app, base_url=base_url)
        else:
            self._mode = "stub"
            self._default_headers = {}
            self._stub_client = _StubAsyncClient(
                app=app,
                base_url=base_url,
                headers=headers,
                **extra,
            )

    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        await self.aclose()

    async def aclose(self) -> None:
        if getattr(self, "_mode", "testclient") == "testclient":
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._test_client.close)
            return

        stub_client = getattr(self, "_stub_client", None)
        if stub_client is not None:
            await stub_client.aclose()

    def _apply_headers(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        if self._mode != "testclient" or not self._default_headers:
            return kwargs
        combined = dict(self._default_headers)
        extra = kwargs.get("headers")
        if extra:
            combined.update(extra)
        updated = dict(kwargs)
        updated["headers"] = combined
        return updated

    async def get(self, url: str, **kwargs: Any):
        if self._mode == "testclient":
            kwargs = self._apply_headers(kwargs)
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None, partial(self._test_client.get, url, **kwargs)
            )
            return _AsyncResponse(response)

        return await self._stub_client.get(url, **kwargs)

    async def post(self, url: str, **kwargs: Any):
        if self._mode == "testclient":
            kwargs = self._apply_headers(kwargs)
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None, partial(self._test_client.post, url, **kwargs)
            )
            return _AsyncResponse(response)

        return await self._stub_client.post(url, **kwargs)

    async def put(self, url: str, **kwargs: Any):
        if self._mode == "testclient":
            kwargs = self._apply_headers(kwargs)
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None, partial(self._test_client.put, url, **kwargs)
            )
            return _AsyncResponse(response)

        return await self._stub_client.put(url, **kwargs)

    async def delete(self, url: str, **kwargs: Any):
        if self._mode == "testclient":
            kwargs = self._apply_headers(kwargs)
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None, partial(self._test_client.delete, url, **kwargs)
            )
            return _AsyncResponse(response)

        return await self._stub_client.delete(url, **kwargs)


def _normalise_url(url: str) -> tuple[str, str]:
    parsed = urlsplit(url)
    path = parsed.path or "/"
    query = parsed.query
    return path, query


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


def _normalise_content_type(headers: dict[str, str]) -> None:
    value = headers.get("content-type")
    if value and ";" in value:
        headers["content-type"] = value.split(";", 1)[0]


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload).encode("utf-8")


class ASGITransport:
    """Placeholder transport matching httpx.ASGITransport for tests."""

    def __init__(self, *, app: Any) -> None:
        self.app = app


__all__ = ["AsyncClient", "ASGITransport", "Response"]
