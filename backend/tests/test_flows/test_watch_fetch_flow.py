"""Tests for the reference source watch flow."""

from __future__ import annotations

import hashlib
from typing import Mapping

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import select

from app.models.rkp import RefDocument, RefSource
from app.services.reference_sources import HTTPResponse, ReferenceSourceFetcher
from app.services.reference_storage import ReferenceStorage
from flows.watch_fetch import watch_reference_sources


class FakeHTTPClient:
    """Stub HTTP client that returns preconfigured responses."""

    def __init__(
        self,
        *,
        head_response: HTTPResponse,
        get_response: HTTPResponse,
    ) -> None:
        self._head_response = head_response
        self._get_response = get_response
        self.head_calls: list[tuple[str, Mapping[str, str]]] = []
        self.get_calls: list[tuple[str, Mapping[str, str]]] = []

    async def head(self, url: str, headers=None) -> HTTPResponse:
        mapping = dict(headers or {})
        self.head_calls.append((url, mapping))
        return self._head_response

    async def get(self, url: str, headers=None) -> HTTPResponse:
        mapping = dict(headers or {})
        self.get_calls.append((url, mapping))
        return self._get_response


@pytest.mark.asyncio
async def test_watch_fetch_records_new_document(async_session_factory, tmp_path) -> None:
    storage = ReferenceStorage(base_path=tmp_path, bucket="")

    async with async_session_factory() as session:
        source = RefSource(
            jurisdiction="SG",
            authority="BCA",
            topic="fire",
            doc_title="Fire Code",
            landing_url="https://example.com/fire-v1.pdf",
            fetch_kind="pdf",
            is_active=True,
        )
        session.add(source)
        await session.commit()
        source_id = source.id

    head_response = HTTPResponse(
        status_code=200,
        headers={"ETag": "etag-v1", "Last-Modified": "Wed, 01 Jan 2024 00:00:00 GMT"},
        content=b"",
    )
    get_payload = b"%PDF-1.4\nSample payload"
    get_response = HTTPResponse(
        status_code=200,
        headers={"Content-Type": "application/pdf", "ETag": "etag-v1"},
        content=get_payload,
    )
    fake_client = FakeHTTPClient(head_response=head_response, get_response=get_response)
    fetcher = ReferenceSourceFetcher(http_client=fake_client)

    results = await watch_reference_sources(async_session_factory, fetcher=fetcher, storage=storage)
    assert len(results) == 1
    document_id = results[0]["document_id"]

    async with async_session_factory() as session:
        document = await session.get(RefDocument, document_id)
        assert document is not None
        assert document.source_id == source_id
        assert document.suspected_update is True
        assert document.http_etag == "etag-v1"
        assert document.http_last_modified == "Wed, 01 Jan 2024 00:00:00 GMT"
        stored = await storage.read_document(document.storage_path)
        assert stored == get_payload

        # Reset the flag to avoid affecting downstream parsing tests.
        document.suspected_update = False
        await session.commit()

    assert fake_client.head_calls
    assert fake_client.get_calls


@pytest.mark.asyncio
async def test_watch_fetch_skips_when_not_modified(async_session_factory, tmp_path) -> None:
    storage = ReferenceStorage(base_path=tmp_path, bucket="")
    existing_payload = b"Existing PDF payload"

    async with async_session_factory() as session:
        source = RefSource(
            jurisdiction="SG",
            authority="BCA",
            topic="fire",
            doc_title="Fire Code",
            landing_url="https://example.com/fire-latest.pdf",
            fetch_kind="pdf",
            is_active=True,
        )
        session.add(source)
        await session.flush()
        location = await storage.write_document(source_id=source.id, payload=existing_payload, suffix=".pdf")
        document = RefDocument(
            source_id=source.id,
            version_label="v1",
            storage_path=location.storage_path,
            file_hash=hashlib.sha256(existing_payload).hexdigest(),
            http_etag="etag-existing",
            http_last_modified="Wed, 01 Jan 2024 00:00:00 GMT",
            suspected_update=False,
        )
        session.add(document)
        await session.commit()
        document_id = document.id

    head_response = HTTPResponse(status_code=304, headers={}, content=b"")
    get_response = HTTPResponse(status_code=304, headers={}, content=b"")
    fake_client = FakeHTTPClient(head_response=head_response, get_response=get_response)
    fetcher = ReferenceSourceFetcher(http_client=fake_client)

    results = await watch_reference_sources(async_session_factory, fetcher=fetcher, storage=storage)
    assert results == []
    assert len(fake_client.get_calls) == 0
    assert fake_client.head_calls
    matching_headers = [
        headers
        for url, headers in fake_client.head_calls
        if "fire-latest.pdf" in url
    ]
    assert matching_headers, "expected HEAD call for the updated source"
    assert matching_headers[0].get("If-None-Match") == "etag-existing"

    async with async_session_factory() as session:
        updated = await session.get(RefDocument, document_id)
        assert updated is not None
        documents = (
            await session.execute(select(RefDocument).where(RefDocument.source_id == updated.source_id))
        ).scalars().all()
        assert len(documents) == 1
