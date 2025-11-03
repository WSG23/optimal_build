"""Tests for the reference source fetching helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import pytest

from app.models.rkp import RefDocument, RefSource
from app.services.reference_sources import (
    FetchedDocument,
    HTTPResponse,
    ReferenceSourceFetcher,
)


@dataclass
class _StubHTTPClient:
    head_response: Optional[HTTPResponse] = None
    get_response: Optional[HTTPResponse] = None
    head_exception: Exception | None = None
    get_exception: Exception | None = None

    async def head(
        self, url: str, headers: dict[str, str] | None = None
    ) -> HTTPResponse:
        if self.head_exception:
            raise self.head_exception
        return self.head_response or HTTPResponse(200, {}, b"")

    async def get(
        self, url: str, headers: dict[str, str] | None = None
    ) -> HTTPResponse:
        if self.get_exception:
            raise self.get_exception
        if self.get_response is None:
            raise AssertionError("get_response not configured")
        return self.get_response


def _make_source(**overrides: Any) -> RefSource:
    payload = dict(
        id=1,
        jurisdiction="SG",
        authority="URA",
        topic="zoning",
        doc_title="Zoning Reference",
        landing_url="https://example.com/zoning.pdf",
        fetch_kind="pdf",
    )
    payload.update(overrides)
    return RefSource(**payload)


def _make_document(**overrides: Any) -> RefDocument:
    payload = dict(
        id=10,
        source_id=1,
        version_label="v1",
        storage_path="s3://bucket/path.pdf",
        file_hash="abc123",
        http_etag='"etag-1"',
        http_last_modified="Wed, 01 Jan 2025 00:00:00 GMT",
    )
    payload.update(overrides)
    return RefDocument(**payload)


@pytest.mark.asyncio
async def test_fetch_skips_when_not_modified() -> None:
    client = _StubHTTPClient(
        head_response=HTTPResponse(
            status_code=304, headers={"ETag": '"etag-1"'}, content=b""
        )
    )
    fetcher = ReferenceSourceFetcher(http_client=client)

    result = await fetcher.fetch(_make_source(), existing=_make_document())

    assert result is None


@pytest.mark.asyncio
async def test_fetch_returns_combined_headers() -> None:
    client = _StubHTTPClient(
        head_response=HTTPResponse(
            status_code=200,
            headers={
                "ETag": '"etag-2"',
                "Last-Modified": "Thu, 02 Jan 2025 00:00:00 GMT",
            },
            content=b"",
        ),
        get_response=HTTPResponse(
            status_code=200,
            headers={"Content-Type": "application/pdf"},
            content=b"%PDF-1.4...",
        ),
    )
    fetcher = ReferenceSourceFetcher(http_client=client)

    result = await fetcher.fetch(_make_source(), existing=_make_document())

    assert isinstance(result, FetchedDocument)
    assert result.content == b"%PDF-1.4..."
    assert result.etag == '"etag-2"'
    assert result.last_modified == "Thu, 02 Jan 2025 00:00:00 GMT"
    assert result.content_type == "application/pdf"


@pytest.mark.asyncio
async def test_fetch_raises_on_error_status() -> None:
    client = _StubHTTPClient(
        head_response=HTTPResponse(status_code=200, headers={}, content=b""),
        get_response=HTTPResponse(status_code=500, headers={}, content=b""),
    )
    fetcher = ReferenceSourceFetcher(http_client=client)

    with pytest.raises(RuntimeError) as excinfo:
        await fetcher.fetch(_make_source(), existing=None)

    assert "HTTP 500" in str(excinfo.value)


@pytest.mark.asyncio
async def test_fetch_handles_head_unsupported() -> None:
    client = _StubHTTPClient(
        head_exception=RuntimeError("HEAD unsupported"),
        get_response=HTTPResponse(
            status_code=200,
            headers={"Content-Type": "text/html"},
            content=b"<html></html>",
        ),
    )
    fetcher = ReferenceSourceFetcher(http_client=client)

    result = await fetcher.fetch(_make_source(fetch_kind="html"), existing=None)

    assert result is not None
    assert result.content_type == "text/html"


@pytest.mark.asyncio
async def test_fetch_treats_method_not_allowed_head_as_none() -> None:
    client = _StubHTTPClient(
        head_response=HTTPResponse(status_code=405, headers={}, content=b""),
        get_response=HTTPResponse(status_code=200, headers={}, content=b"data"),
    )
    fetcher = ReferenceSourceFetcher(http_client=client)

    result = await fetcher.fetch(_make_source(), existing=None)

    assert isinstance(result, FetchedDocument)
    assert result.content == b"data"


def test_conditional_headers_and_not_modified_logic() -> None:
    fetcher = ReferenceSourceFetcher()
    existing = _make_document()

    headers = fetcher._conditional_headers(existing)
    assert headers["If-None-Match"] == existing.http_etag
    assert headers["If-Modified-Since"] == existing.http_last_modified

    response = HTTPResponse(
        status_code=200, headers={"ETag": existing.http_etag}, content=b""
    )
    assert fetcher._is_not_modified(response, existing) is True

    response = HTTPResponse(
        status_code=200, headers={"ETag": '"different"'}, content=b""
    )
    assert fetcher._is_not_modified(response, existing) is False


@pytest.mark.asyncio
async def test_fetch_without_existing_document() -> None:
    """Test fetch without existing document (no conditional headers)."""
    client = _StubHTTPClient(
        head_response=HTTPResponse(status_code=200, headers={}, content=b""),
        get_response=HTTPResponse(
            status_code=200,
            headers={"Content-Type": "application/pdf"},
            content=b"PDF content",
        ),
    )
    fetcher = ReferenceSourceFetcher(http_client=client)

    result = await fetcher.fetch(_make_source(), existing=None)

    assert result is not None
    assert result.content == b"PDF content"


@pytest.mark.asyncio
async def test_fetch_with_non_pdf_fetch_kind() -> None:
    """Test fetch with non-pdf/html/sitemap fetch_kind (no HEAD request)."""
    client = _StubHTTPClient(
        get_response=HTTPResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            content=b'{"data": "test"}',
        )
    )
    fetcher = ReferenceSourceFetcher(http_client=client)

    # Use a fetch_kind that's not pdf/html/sitemap
    source = _make_source(fetch_kind="json")
    result = await fetcher.fetch(source, existing=None)

    assert result is not None
    assert result.content == b'{"data": "test"}'


@pytest.mark.asyncio
async def test_fetch_conditional_with_non_standard_fetch_kind() -> None:
    """Test conditional fetch with non-pdf/html/sitemap and existing document."""
    client = _StubHTTPClient(
        head_response=HTTPResponse(status_code=304, headers={}, content=b"")
    )
    fetcher = ReferenceSourceFetcher(http_client=client)

    source = _make_source(fetch_kind="api")
    existing = _make_document()
    result = await fetcher.fetch(source, existing=existing)

    assert result is None  # 304 means not modified


@pytest.mark.asyncio
async def test_fetch_returns_none_on_304_from_get() -> None:
    """Test fetch returns None when GET returns 304."""
    client = _StubHTTPClient(
        head_response=HTTPResponse(status_code=200, headers={}, content=b""),
        get_response=HTTPResponse(status_code=304, headers={}, content=b""),
    )
    fetcher = ReferenceSourceFetcher(http_client=client)

    result = await fetcher.fetch(_make_source(), existing=_make_document())

    assert result is None


@pytest.mark.asyncio
async def test_fetch_head_501_not_implemented() -> None:
    """Test fetch handles HEAD 501 (Not Implemented) gracefully."""
    client = _StubHTTPClient(
        head_response=HTTPResponse(status_code=501, headers={}, content=b""),
        get_response=HTTPResponse(status_code=200, headers={}, content=b"data"),
    )
    fetcher = ReferenceSourceFetcher(http_client=client)

    result = await fetcher.fetch(_make_source(), existing=None)

    assert result is not None
    assert result.content == b"data"


def test_is_not_modified_with_last_modified_header() -> None:
    """Test _is_not_modified uses Last-Modified header."""
    fetcher = ReferenceSourceFetcher()
    existing = _make_document()

    response = HTTPResponse(
        status_code=200,
        headers={"Last-Modified": existing.http_last_modified},
        content=b"",
    )
    assert fetcher._is_not_modified(response, existing) is True


def test_is_not_modified_returns_false_without_existing() -> None:
    """Test _is_not_modified returns False when no existing document."""
    fetcher = ReferenceSourceFetcher()

    response = HTTPResponse(
        status_code=200, headers={"ETag": '"some-etag"'}, content=b""
    )
    assert fetcher._is_not_modified(response, None) is False
