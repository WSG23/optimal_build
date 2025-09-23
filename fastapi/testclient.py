"""Synchronous test client mirroring :mod:`fastapi.testclient`."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
from typing import Any, Mapping, MutableMapping, Optional
from urllib.parse import urlsplit


@dataclass
class _SyncResponse:
    status_code: int
    content: bytes
    headers: Mapping[str, str]

    def json(self) -> Any:
        if not self.content:
            return None
        return json.loads(self.content.decode("utf-8"))

    @property
    def text(self) -> str:
        return self.content.decode("utf-8")


class TestClient:
    """Synchronous facade over :class:`fastapi.FastAPI.handle_request`."""

    def __init__(self, app, base_url: str = "http://testserver") -> None:
        self.app = app
        self.base_url = base_url

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        data: Optional[Mapping[str, Any]] = None,
        files: Optional[MutableMapping[str, tuple[str, Any, str | None]]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> _SyncResponse:
        path, query = self._split_url(url)
        query_params = dict(params or {})
        if query and not query_params:
            query_params.update({key: value[0] if len(value) == 1 else value for key, value in self._parse_query(query).items()})
        prepared_files = {}
        if files:
            for key, (filename, payload, content_type) in files.items():
                data_bytes = payload.read() if hasattr(payload, "read") else payload
                prepared_files[key] = (
                    filename,
                    data_bytes if isinstance(data_bytes, (bytes, bytearray)) else str(data_bytes).encode("utf-8"),
                    content_type or "application/octet-stream",
                )

        header_map = {key.lower(): value for key, value in (headers or {}).items()}

        async def _invoke():
            return await self.app.handle_request(
                method=method,
                path=path,
                query_params=query_params,
                json_body=json,
                form_data=dict(data or {}),
                files=prepared_files,
                headers=header_map,
            )

        status_code, headers, payload = asyncio.run(_invoke())
        return _SyncResponse(status_code=status_code, content=payload, headers=headers)

    def get(
        self,
        url: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> _SyncResponse:
        return self.request("GET", url, params=params, headers=headers)

    def post(
        self,
        url: str,
        *,
        json: Any = None,
        data: Optional[Mapping[str, Any]] = None,
        files: Optional[MutableMapping[str, tuple[str, Any, str | None]]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> _SyncResponse:
        return self.request("POST", url, json=json, data=data, files=files, headers=headers)

    def put(
        self,
        url: str,
        *,
        json: Any = None,
        data: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> _SyncResponse:
        return self.request("PUT", url, json=json, data=data, headers=headers)

    def delete(
        self,
        url: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
    ) -> _SyncResponse:
        return self.request("DELETE", url, headers=headers)

    def close(self) -> None:  # pragma: no cover - compatibility no-op
        return None

    @staticmethod
    def _split_url(url: str) -> tuple[str, str]:
        parsed = urlsplit(url)
        return parsed.path or "/", parsed.query

    @staticmethod
    def _parse_query(query: str) -> dict[str, list[str]]:  # pragma: no cover - defensive fallback
        parts: dict[str, list[str]] = {}
        for chunk in filter(None, query.split("&")):
            if "=" in chunk:
                name, value = chunk.split("=", 1)
            else:
                name, value = chunk, ""
            parts.setdefault(name, []).append(value)
        return parts


__all__ = ["TestClient"]
