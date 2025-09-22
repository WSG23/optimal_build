"""HTTP helpers used when fetching reference source documents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional, Protocol


@dataclass(slots=True)
class FetchResponse:
    """Lightweight container describing the result of an HTTP request."""

    status_code: int
    headers: Mapping[str, str]
    content: bytes


class DocumentFetcher(Protocol):
    """Protocol describing the subset of HTTP client behaviour we rely on."""

    async def head(self, url: str, headers: Optional[Mapping[str, str]] = None) -> FetchResponse:
        ...

    async def get(self, url: str, headers: Optional[Mapping[str, str]] = None) -> FetchResponse:
        ...

    async def aclose(self) -> None:  # pragma: no cover - optional clean-up hook
        ...


try:  # pragma: no cover - optional dependency for online environments
    import httpx
except ModuleNotFoundError:  # pragma: no cover - exercised in offline tests
    httpx = None  # type: ignore[assignment]


class HTTPXDocumentFetcher:
    """`DocumentFetcher` implementation backed by :mod:`httpx`."""

    def __init__(self, *, timeout: float = 30.0) -> None:
        if httpx is None:  # pragma: no cover - offline test fallback
            raise ModuleNotFoundError(
                "httpx is required to instantiate HTTPXDocumentFetcher"
            )
        self._client = httpx.AsyncClient(timeout=timeout)

    async def head(
        self, url: str, headers: Optional[Mapping[str, str]] = None
    ) -> FetchResponse:
        response = await self._client.head(url, headers=headers)
        return FetchResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
        )

    async def get(
        self, url: str, headers: Optional[Mapping[str, str]] = None
    ) -> FetchResponse:
        response = await self._client.get(url, headers=headers)
        return FetchResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
        )

    async def aclose(self) -> None:
        await self._client.aclose()


def get_document_fetcher(*, timeout: float = 30.0) -> DocumentFetcher:
    """Return a default :class:`DocumentFetcher` implementation."""

    return HTTPXDocumentFetcher(timeout=timeout)


__all__ = ["DocumentFetcher", "FetchResponse", "HTTPXDocumentFetcher", "get_document_fetcher"]
