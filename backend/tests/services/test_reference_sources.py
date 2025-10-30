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
