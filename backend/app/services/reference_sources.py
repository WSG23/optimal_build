"""Helpers for fetching reference source documents."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Mapping, MutableMapping, Optional
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.models.rkp import RefDocument, RefSource


@dataclass(slots=True)
class HTTPResponse:
    """Simplified HTTP response payload."""

    status_code: int
    headers: Mapping[str, str]
    content: bytes


class SimpleHTTPClient:
    """Minimal HTTP client using ``urllib`` for asynchronous flows."""

    async def head(self, url: str, headers: Optional[Mapping[str, str]] = None) -> HTTPResponse:
        return await self._request("HEAD", url, headers=headers)

    async def get(self, url: str, headers: Optional[Mapping[str, str]] = None) -> HTTPResponse:
        return await self._request("GET", url, headers=headers)

    async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
    ) -> HTTPResponse:
        def _perform_request() -> HTTPResponse:
            request = Request(url, method=method, headers=dict(headers or {}))
            try:
                with urlopen(request) as response:  # nosec B310 - used for controlled fetches
                    payload = b"" if method == "HEAD" else response.read()
                    return HTTPResponse(response.status, dict(response.headers.items()), payload)
            except HTTPError as exc:  # pragma: no cover - network errors exercised in tests
                payload = exc.read() if hasattr(exc, "read") else b""
                return HTTPResponse(exc.code, dict(getattr(exc, "headers", {}) or {}), payload)

        return await asyncio.to_thread(_perform_request)


@dataclass(slots=True)
class FetchedDocument:
    """Result of fetching a reference document."""

    content: bytes
    etag: Optional[str]
    last_modified: Optional[str]
    content_type: Optional[str]


class ReferenceSourceFetcher:
    """Fetch reference sources with conditional requests."""

    def __init__(self, http_client: Optional[SimpleHTTPClient] = None) -> None:
        self._http = http_client or SimpleHTTPClient()

    async def fetch(
        self,
        source: RefSource,
        existing: Optional[RefDocument] = None,
    ) -> Optional[FetchedDocument]:
        """Fetch ``source`` if it has been updated since ``existing``."""

        fetch_kind = (getattr(source, "fetch_kind", None) or "pdf").lower()
        conditional_headers = self._conditional_headers(existing)
        head_response: Optional[HTTPResponse] = None
        if fetch_kind in {"pdf", "html", "sitemap"}:
            head_response = await self._safe_head(
                source.landing_url,
                headers=conditional_headers or None,
            )
            if head_response and self._is_not_modified(head_response, existing):
                return None
        elif conditional_headers:
            head_response = await self._safe_head(
                source.landing_url,
                headers=conditional_headers or None,
            )
            if head_response and head_response.status_code == 304:
                return None

        response = await self._http.get(source.landing_url, headers=conditional_headers or None)
        if response.status_code == 304:
            return None
        if response.status_code >= 400:
            raise RuntimeError(
                f"Failed to fetch reference source {source.id}: HTTP {response.status_code}"
            )

        headers: MutableMapping[str, str] = {}
        if head_response:
            headers.update({k.lower(): v for k, v in head_response.headers.items()})
        headers.update({k.lower(): v for k, v in response.headers.items()})

        return FetchedDocument(
            content=response.content,
            etag=headers.get("etag"),
            last_modified=headers.get("last-modified"),
            content_type=headers.get("content-type"),
        )

    async def _safe_head(
        self,
        url: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Optional[HTTPResponse]:
        try:
            response = await self._http.head(url, headers=headers or None)
        except Exception:  # pragma: no cover - defensive fallback for unsupported HEAD
            return None
        if response.status_code in {405, 501}:
            return None
        return response

    def _conditional_headers(self, existing: Optional[RefDocument]) -> Mapping[str, str]:
        headers: dict[str, str] = {}
        if existing and existing.http_etag:
            headers["If-None-Match"] = existing.http_etag
        if existing and existing.http_last_modified:
            headers["If-Modified-Since"] = existing.http_last_modified
        return headers

    def _is_not_modified(
        self,
        response: HTTPResponse,
        existing: Optional[RefDocument],
    ) -> bool:
        if response.status_code == 304:
            return True
        if not existing:
            return False
        etag = _get_header(response.headers, "etag")
        if etag and existing.http_etag and etag == existing.http_etag:
            return True
        last_modified = _get_header(response.headers, "last-modified")
        if last_modified and existing.http_last_modified and last_modified == existing.http_last_modified:
            return True
        return False


def _get_header(headers: Mapping[str, str], key: str) -> Optional[str]:
    key_lower = key.lower()
    for header, value in headers.items():
        if header.lower() == key_lower:
            return value
    return None


__all__ = ["FetchedDocument", "HTTPResponse", "ReferenceSourceFetcher", "SimpleHTTPClient"]
