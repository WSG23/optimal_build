from __future__ import annotations

import pytest
from sqlalchemy import func, select

import httpx

from app.models.rkp import RefClause, RefDocument, RefRule, RefSource
from app.services.storage import StorageConfig, StorageService
from flows.parse_segment import parse_segment
from flows.watch_fetch import watch_fetch


@pytest.mark.asyncio
async def test_watch_fetch_flow(session, session_factory, monkeypatch, tmp_path) -> None:
    source = RefSource(
        jurisdiction="SG",
        authority="BCA",
        topic="fire",
        doc_title="Watch Source",
        landing_url="https://example.test/watch.pdf",
        fetch_kind="pdf",
        selectors={},
    )
    session.add(source)
    await session.commit()

    storage_config = {
        "bucket": "flow-bucket",
        "endpoint_url": str(tmp_path),
        "access_key": "test",
        "secret_key": "test",
        "region_name": "us-east-1",
        "use_ssl": False,
    }

    async def fake_get(self, url):  # type: ignore[override]
        class FakeResponse:
            content = b"rule parameter_key >= 10"
            headers = {"content-type": "text/plain"}

            def raise_for_status(self) -> None:
                return None

        return FakeResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    results = await watch_fetch(
        session_factory=session_factory,
        storage_config=storage_config,
        sources=[{"id": source.id, "url": "https://example.test/document"}],
    )
    assert results
    document = await session.get(RefDocument, results[0]["document_id"])
    assert document is not None


@pytest.mark.asyncio
async def test_parse_segment_flow(session, session_factory, tmp_path) -> None:
    storage_config = {
        "bucket": "parse-bucket",
        "endpoint_url": str(tmp_path),
        "access_key": "test",
        "secret_key": "test",
        "region_name": "us-east-1",
        "use_ssl": False,
    }
    storage = StorageService(StorageConfig(**storage_config))

    source = RefSource(
        jurisdiction="SG",
        authority="BCA",
        topic="fire",
        doc_title="Parse Source",
        landing_url="https://example.test/parse.pdf",
        fetch_kind="pdf",
        selectors={},
    )
    session.add(source)
    await session.flush()

    key = "documents/parse.txt"
    storage.store_bytes(b"egress.corridor.min_width_mm >= 1200 mm", key, content_type="text/plain")
    document = RefDocument(
        source_id=source.id,
        version_label="v1",
        storage_path=key,
        file_hash="hash123",
        suspected_update=False,
    )
    session.add(document)
    await session.commit()

    result = await parse_segment(
        session_factory=session_factory,
        storage_config=storage_config,
        document_id=document.id,
    )
    assert result["clauses"] == 1
    assert result["rules"] == 1

    clause_count = await session.scalar(select(func.count()).select_from(RefClause))
    rule_count = await session.scalar(select(func.count()).select_from(RefRule))
    assert clause_count == 1
    assert rule_count == 1
