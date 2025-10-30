"""Tests for the reference source fetcher and HTTP client helpers."""

from __future__ import annotations


import pytest

from urllib.error import URLError

from app.models.rkp import RefDocument, RefSource
from app.services import reference_sources
from app.services.reference_sources import (
    FetchedDocument,
    HTTPResponse,
    ReferenceSourceFetcher,
    SimpleHTTPClient,
)


class _FakeHTTPClient:
    """Simple stub that returns queued responses."""

    def __init__(self) -> None:
        self.head_calls: list[tuple[str, dict[str, str] | None]] = []
        self.get_calls: list[tuple[str, dict[str, str] | None]] = []
        self._head_side_effects: list[HTTPResponse | Exception] = []
        self._get_side_effects: list[HTTPResponse | Exception] = []

    def queue_head(self, effect: HTTPResponse | Exception) -> None:
        self._head_side_effects.append(effect)

    def queue_get(self, effect: HTTPResponse | Exception) -> None:
        self._get_side_effects.append(effect)

    async def head(
        self, url: str, headers: dict[str, str] | None = None
    ) -> HTTPResponse:
        self.head_calls.append((url, headers))
        effect = self._head_side_effects.pop(0)
        if isinstance(effect, Exception):
            raise effect
        return effect

    async def get(
        self, url: str, headers: dict[str, str] | None = None
    ) -> HTTPResponse:
        self.get_calls.append((url, headers))
        effect = self._get_side_effects.pop(0)
        if isinstance(effect, Exception):
            raise effect
        return effect


def _make_source(fetch_kind: str = "pdf") -> RefSource:
    return RefSource(
        jurisdiction="SG",
        authority="URA",
        topic="zoning",
        doc_title="Master Plan",
        landing_url="https://example.com/doc.pdf",
        fetch_kind=fetch_kind,
    )


def _make_document() -> RefDocument:
    return RefDocument(
        source_id=1,
        version_label="2024",
        storage_path="s3://bucket/doc.pdf",
        file_hash="abc123",
        http_etag="etag-1",
        http_last_modified="Wed, 01 May 2024 00:00:00 GMT",
    )


@pytest.mark.asyncio
async def test_fetch_skips_when_head_reports_not_modified():
    client = _FakeHTTPClient()
    client.queue_head(
        HTTPResponse(
            status_code=304,
            headers={"Etag": "etag-1"},
            content=b"",
        )
    )
    fetcher = ReferenceSourceFetcher(http_client=client)

    result = await fetcher.fetch(_make_source(), existing=_make_document())

    assert result is None
    # No GET request should be issued once the HEAD indicates no update.
    assert client.get_calls == []


@pytest.mark.asyncio
async def test_fetch_returns_document_with_combined_headers():
    client = _FakeHTTPClient()
    client.queue_head(
        HTTPResponse(
            status_code=200,
            headers={"Etag": "etag-2", "Content-Type": "application/pdf"},
            content=b"",
        )
    )
    client.queue_get(
        HTTPResponse(
            status_code=200,
            headers={"Last-Modified": "Thu, 02 May 2024 00:00:00 GMT"},
            content=b"%PDF-1.7",
        )
    )
    fetcher = ReferenceSourceFetcher(http_client=client)

    document = await fetcher.fetch(_make_source(), existing=_make_document())

    assert isinstance(document, FetchedDocument)
    assert document.content == b"%PDF-1.7"
    # HEAD headers take precedence when present.
    assert document.etag == "etag-2"
    assert document.content_type == "application/pdf"
    assert document.last_modified == "Thu, 02 May 2024 00:00:00 GMT"


@pytest.mark.asyncio
async def test_fetch_handles_head_not_supported():
    client = _FakeHTTPClient()
    # 405 should cause _safe_head to return None and fall back to GET.
    client.queue_head(
        HTTPResponse(
            status_code=405,
            headers={},
            content=b"",
        )
    )
    client.queue_get(
        HTTPResponse(
            status_code=200,
            headers={"Content-Type": "text/html"},
            content=b"<html>ok</html>",
        )
    )
    fetcher = ReferenceSourceFetcher(http_client=client)

    document = await fetcher.fetch(_make_source("html"), existing=_make_document())

    assert document is not None
    # GET request should still have been made even though HEAD was unsupported.
    assert len(client.get_calls) == 1


@pytest.mark.asyncio
async def test_fetch_handles_head_exception():
    client = _FakeHTTPClient()

    class _Boom(RuntimeError):
        pass

    client.queue_head(_Boom("HEAD failed"))
    client.queue_get(
        HTTPResponse(
            status_code=200,
            headers={},
            content=b"{}",
        )
    )
    fetcher = ReferenceSourceFetcher(http_client=client)

    document = await fetcher.fetch(_make_source("json"), existing=_make_document())

    # Even though HEAD raised, the fetch should succeed thanks to the fallback.
    assert document is not None
    assert document.content == b"{}"


@pytest.mark.asyncio
async def test_fetch_returns_none_when_get_reports_not_modified():
    client = _FakeHTTPClient()
    client.queue_head(
        HTTPResponse(
            status_code=200,
            headers={"Etag": "etag-2"},
            content=b"",
        )
    )
    client.queue_get(
        HTTPResponse(
            status_code=304,
            headers={},
            content=b"",
        )
    )
    fetcher = ReferenceSourceFetcher(http_client=client)

    result = await fetcher.fetch(_make_source(), existing=_make_document())

    assert result is None


@pytest.mark.asyncio
async def test_fetch_raises_on_http_error():
    client = _FakeHTTPClient()
    client.queue_head(
        HTTPResponse(
            status_code=200,
            headers={},
            content=b"",
        )
    )
    client.queue_get(
        HTTPResponse(
            status_code=500,
            headers={},
            content=b"error",
        )
    )
    fetcher = ReferenceSourceFetcher(http_client=client)

    with pytest.raises(RuntimeError):
        await fetcher.fetch(_make_source(), existing=_make_document())


def test_conditional_headers_include_etag_and_last_modified():
    fetcher = ReferenceSourceFetcher()
    headers = fetcher._conditional_headers(_make_document())  # type: ignore[attr-defined]

    assert headers["If-None-Match"] == "etag-1"
    assert headers["If-Modified-Since"] == "Wed, 01 May 2024 00:00:00 GMT"


class _DummyResponse:
    """Context manager mimicking urllib response objects."""

    def __init__(self, status: int, headers: dict[str, str], payload: bytes) -> None:
        self.status = status
        self.headers = headers
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_DummyResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


async def _immediate_to_thread(func, *args, **kwargs):
    return func(*args, **kwargs)


async def _no_sleep(_delay: float) -> None:  # pragma: no cover - best effort
    return None


@pytest.mark.asyncio
async def test_simple_http_client_success(monkeypatch):
    client = SimpleHTTPClient(timeout=0.1, max_attempts=1)
    monkeypatch.setattr(reference_sources.asyncio, "to_thread", _immediate_to_thread)

    def fake_urlopen(request, timeout):
        assert request.method == "GET"
        assert timeout == 0.1
        return _DummyResponse(200, {"X-Test": "true"}, b"payload")

    monkeypatch.setattr(reference_sources, "urlopen", fake_urlopen)

    response = await client.get("https://example.com/file")

    assert response.status_code == 200
    assert response.headers["X-Test"] == "true"
    assert response.content == b"payload"


@pytest.mark.asyncio
async def test_simple_http_client_retries_and_recovers(monkeypatch):
    client = SimpleHTTPClient(
        timeout=0.1, max_attempts=2, backoff_factor=0, max_backoff=0
    )
    monkeypatch.setattr(reference_sources.asyncio, "to_thread", _immediate_to_thread)
    monkeypatch.setattr(reference_sources.asyncio, "sleep", _no_sleep)

    attempts: list[str] = []

    def fake_urlopen(request, timeout):
        attempts.append(request.method)
        if len(attempts) == 1:
            raise URLError("temporary failure")
        return _DummyResponse(
            200, {"X-Test": "retry"}, b"" if request.method == "HEAD" else b"ok"
        )

    monkeypatch.setattr(reference_sources, "urlopen", fake_urlopen)

    response = await client.head("https://example.com/head")

    assert attempts == ["HEAD", "HEAD"]
    assert response.status_code == 200
    assert response.content == b""


@pytest.mark.asyncio
async def test_simple_http_client_raises_after_exhausting_attempts(monkeypatch):
    client = SimpleHTTPClient(
        timeout=0.1, max_attempts=2, backoff_factor=0, max_backoff=0
    )
    monkeypatch.setattr(reference_sources.asyncio, "to_thread", _immediate_to_thread)
    monkeypatch.setattr(reference_sources.asyncio, "sleep", _no_sleep)

    def fake_urlopen(request, timeout):
        raise URLError("still down")

    monkeypatch.setattr(reference_sources, "urlopen", fake_urlopen)

    with pytest.raises(RuntimeError):
        await client.get("https://example.com/fail")
