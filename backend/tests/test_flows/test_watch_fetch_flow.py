"""Tests for the reference document fetch flow."""

from __future__ import annotations

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import select

from app.models.rkp import RefClause, RefDocument, RefSource
from app.services.ref_documents import compute_document_checksum
from app.services.ref_fetcher import FetchResponse
from flows.watch_fetch import watch_reference_sources


class StubFetcher:
    """Simple fetcher stub returning predefined responses."""

    def __init__(self, head_response: FetchResponse, get_response: FetchResponse) -> None:
        self._head_response = head_response
        self._get_response = get_response
        self.head_calls: list[tuple[str, dict[str, str]]] = []
        self.get_calls: list[tuple[str, dict[str, str]]] = []

    async def head(self, url: str, headers=None) -> FetchResponse:
        self.head_calls.append((url, dict(headers or {})))
        return self._head_response

    async def get(self, url: str, headers=None) -> FetchResponse:
        self.get_calls.append((url, dict(headers or {})))
        return self._get_response

    async def aclose(self) -> None:  # pragma: no cover - simple stub
        return None


@pytest.mark.asyncio
async def test_watch_reference_sources_creates_documents(
    async_session_factory, ref_storage_service
) -> None:
    payload = (
        b"Clause 1.1: Means of Escape\n"
        b"Pages 1-2\n"
        b"Every building shall provide unobstructed exits."
    )

    head_response = FetchResponse(
        status_code=200,
        headers={
            "ETag": '"v1"',
            "Last-Modified": "Mon, 01 Jan 2024 00:00:00 GMT",
        },
        content=b"",
    )
    get_response = FetchResponse(
        status_code=200,
        headers={"Content-Type": "application/pdf"},
        content=payload,
    )
    fetcher = StubFetcher(head_response, get_response)

    async with async_session_factory() as session:
        await session.execute(RefClause.__table__.delete())
        await session.execute(RefDocument.__table__.delete())
        await session.execute(RefSource.__table__.delete())
        source = RefSource(
            jurisdiction="SG",
            authority="SCDF",
            topic="fire",
            doc_title="Fire Code",
            landing_url="https://example.com/fire.pdf",
            fetch_kind="pdf",
            is_active=True,
        )
        session.add(source)
        await session.commit()
        source_id = source.id

    results = await watch_reference_sources(
        async_session_factory,
        fetcher=fetcher,
        storage_service=ref_storage_service,
        limit=1,
    )

    assert fetcher.head_calls
    assert fetcher.get_calls
    last_head_url, last_head_headers = fetcher.head_calls[-1]
    assert last_head_url == "https://example.com/fire.pdf"
    assert "If-None-Match" not in last_head_headers

    assert results
    summary = results[0]
    assert summary.source_id == source_id
    assert summary.checksum == compute_document_checksum(payload)

    async with async_session_factory() as session:
        documents = (await session.execute(select(RefDocument))).scalars().all()
        assert len(documents) == 1
        document = documents[0]
        assert document.http_etag == '"v1"'
        assert document.suspected_update is True
        stored_bytes = await ref_storage_service.read_document(document.storage_path)
        assert stored_bytes == payload
