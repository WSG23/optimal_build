"""Helpers for fetching reference source documents."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, MutableMapping
from typing import Final
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from backend._compat import compat_dataclass
from app.models.rkp import RefDocument, RefSource


@compat_dataclass(slots=True)
class HTTPResponse:
    """Simplified HTTP response payload."""

    status_code: int
    headers: Mapping[str, str]
    content: bytes


class SimpleHTTPClient:
    """Minimal HTTP client using ``urllib`` for asynchronous flows."""

    _DEFAULT_TIMEOUT: Final[float] = 10.0
    _DEFAULT_MAX_ATTEMPTS: Final[int] = 3
    _DEFAULT_BACKOFF_FACTOR: Final[float] = 0.5
    _DEFAULT_MAX_BACKOFF: Final[float] = 5.0

    def __init__(
        self,
        *,
        timeout: float | None = None,
        max_attempts: int | None = None,
        backoff_factor: float | None = None,
        max_backoff: float | None = None,
    ) -> None:
        self._timeout = timeout or self._DEFAULT_TIMEOUT
        self._max_attempts = max_attempts or self._DEFAULT_MAX_ATTEMPTS
        self._backoff_factor = backoff_factor or self._DEFAULT_BACKOFF_FACTOR
        self._max_backoff = max_backoff or self._DEFAULT_MAX_BACKOFF

    async def head(
        self, url: str, headers: Mapping[str, str] | None = None
    ) -> HTTPResponse:
        return await self._request("HEAD", url, headers=headers)

    async def get(
        self, url: str, headers: Mapping[str, str] | None = None
    ) -> HTTPResponse:
        return await self._request("GET", url, headers=headers)

    async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
    ) -> HTTPResponse:
        last_error: Exception | None = None

        for attempt in range(1, self._max_attempts + 1):

            def _perform_request() -> HTTPResponse:
                request = Request(url, method=method, headers=dict(headers or {}))
                try:
                    with urlopen(
                        request, timeout=self._timeout
                    ) as response:  # nosec B310 - controlled upstream fetches
                        payload = b"" if method == "HEAD" else response.read()
                        return HTTPResponse(
                            response.status, dict(response.headers.items()), payload
                        )
                except HTTPError as exc:  # pragma: no cover - handled by mocks in tests
                    payload = exc.read() if hasattr(exc, "read") else b""
                    return HTTPResponse(
                        exc.code, dict(getattr(exc, "headers", {}) or {}), payload
                    )

            try:
                return await asyncio.to_thread(_perform_request)
            except (URLError, TimeoutError) as exc:
                last_error = exc
            except Exception as exc:  # pragma: no cover - defensive catch-all
                last_error = exc

            if attempt == self._max_attempts:
                break

            delay = min(
                self._max_backoff,
                self._backoff_factor * (2 ** (attempt - 1)),
            )
            if delay > 0:
                await asyncio.sleep(delay)

        raise RuntimeError(
            f"HTTP request to {url} failed after {self._max_attempts} attempts"
        ) from last_error


@compat_dataclass(slots=True)
class FetchedDocument:
    """Result of fetching a reference document."""

    content: bytes
    etag: str | None
    last_modified: str | None
    content_type: str | None


class ReferenceSourceFetcher:
    """Fetch reference sources with conditional requests."""

    def __init__(self, http_client: SimpleHTTPClient | None = None) -> None:
        self._http = http_client or SimpleHTTPClient()

    async def fetch(
        self,
        source: RefSource,
        existing: RefDocument | None = None,
    ) -> FetchedDocument | None:
        """Fetch ``source`` if it has been updated since ``existing``."""

        fetch_kind = (getattr(source, "fetch_kind", None) or "pdf").lower()
        conditional_headers = self._conditional_headers(existing)
        head_response: HTTPResponse | None = None
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

        response = await self._http.get(
            source.landing_url, headers=conditional_headers or None
        )
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
        headers: Mapping[str, str] | None = None,
    ) -> HTTPResponse | None:
        try:
            response = await self._http.head(url, headers=headers or None)
        except Exception:  # pragma: no cover - defensive fallback for unsupported HEAD
            return None
        if response.status_code in {405, 501}:
            return None
        return response

    def _conditional_headers(self, existing: RefDocument | None) -> Mapping[str, str]:
        headers: dict[str, str] = {}
        if existing and existing.http_etag:
            headers["If-None-Match"] = existing.http_etag
        if existing and existing.http_last_modified:
            headers["If-Modified-Since"] = existing.http_last_modified
        return headers

    def _is_not_modified(
        self,
        response: HTTPResponse,
        existing: RefDocument | None,
    ) -> bool:
        if response.status_code == 304:
            return True
        if not existing:
            return False
        etag = _get_header(response.headers, "etag")
        if etag and existing.http_etag and etag == existing.http_etag:
            return True
        last_modified = _get_header(response.headers, "last-modified")
        if (
            last_modified
            and existing.http_last_modified
            and last_modified == existing.http_last_modified
        ):
            return True
        return False


def _get_header(headers: Mapping[str, str], key: str) -> str | None:
    key_lower = key.lower()
    for header, value in headers.items():
        if header.lower() == key_lower:
            return value
    return None


__all__ = [
    "FetchedDocument",
    "HTTPResponse",
    "ReferenceSourceFetcher",
    "SimpleHTTPClient",
]
