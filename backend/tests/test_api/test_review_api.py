from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

import pytest

from app.api.v1 import review as review_api


class _ScalarResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return self

    def all(self):
        return list(self._items)


class _SessionStub:
    def __init__(self, results):
        self._results = list(results)

    async def execute(self, _stmt):
        return _ScalarResult(self._results.pop(0))


@pytest.mark.asyncio
async def test_list_sources_returns_serialised_payload():
    sources = [
        SimpleNamespace(
            id=1,
            jurisdiction="SG",
            authority="URA",
            topic="Setbacks",
            doc_title="Guidelines",
            landing_url="https://example.com",
        )
    ]
    session = _SessionStub([sources])
    payload = await review_api.list_sources(session=session, _="viewer")
    assert payload["count"] == 1
    assert payload["items"][0]["authority"] == "URA"


@pytest.mark.asyncio
async def test_list_documents_filters_when_source_specified():
    documents = [
        SimpleNamespace(
            id=10,
            source_id=5,
            version_label="2024",
            storage_path="docs/guideline.pdf",
            retrieved_at=None,
        )
    ]
    session = _SessionStub([documents])
    payload = await review_api.list_documents(session=session, source_id=5, _="viewer")
    assert payload["items"][0]["version_label"] == "2024"


@pytest.mark.asyncio
async def test_list_clauses_and_diffs_builds_expected_fields():
    clauses = [
        SimpleNamespace(
            id=7,
            document_id=3,
            clause_ref="1.1",
            section_heading="Purpose",
            text_span="Lorem ipsum",
            page_from=1,
            page_to=2,
        )
    ]
    rules = [
        SimpleNamespace(
            id=4,
            notes="Old note",
            parameter_key="height",
            operator=">",
            value="12",
        )
    ]
    session = _SessionStub([clauses, rules])
    clause_payload = await review_api.list_clauses(
        session=session, document_id=3, _="viewer"
    )
    assert clause_payload["items"][0]["clause_ref"] == "1.1"

    diff_payload = await review_api.list_diffs(session=session, rule_id=4, _="viewer")
    assert diff_payload["items"][0]["baseline"] == "Old note"
    assert diff_payload["items"][0]["updated"] == "height > 12"


@pytest.mark.asyncio
async def test_list_corpus_status_summarises_review_and_freshness():
    sources = [
        SimpleNamespace(
            id=1,
            jurisdiction="SG",
            authority="BCA",
            topic="building",
            doc_title="BCA Circulars",
            landing_url="https://example.com/bca",
            fetch_kind="html",
            update_freq_hint="weekly",
            is_active=True,
        ),
        SimpleNamespace(
            id=2,
            jurisdiction="SG",
            authority="URA",
            topic="zoning",
            doc_title="URA Master Plan",
            landing_url="https://example.com/ura",
            fetch_kind="pdf",
            update_freq_hint="monthly",
            is_active=True,
        ),
    ]
    documents = [
        SimpleNamespace(
            id=10,
            source_id=1,
            version_label="2026-04",
            storage_path="docs/bca.pdf",
            retrieved_at=datetime(2026, 4, 3, 9, 0, 0),
            suspected_update=False,
        ),
        SimpleNamespace(
            id=11,
            source_id=2,
            version_label="2026-03",
            storage_path="docs/ura.pdf",
            retrieved_at=datetime(2026, 4, 2, 8, 0, 0),
            suspected_update=True,
        ),
    ]
    rules = [
        SimpleNamespace(
            id=100,
            source_id=1,
            document_id=10,
            review_status="approved",
            is_published=True,
            source_provenance={"pages": [1]},
        ),
        SimpleNamespace(
            id=101,
            source_id=1,
            document_id=10,
            review_status="needs_review",
            is_published=False,
            source_provenance=None,
        ),
        SimpleNamespace(
            id=200,
            source_id=2,
            document_id=11,
            review_status="approved",
            is_published=False,
            source_provenance={"pages": [5]},
        ),
    ]
    session = _SessionStub([sources, documents, rules])

    payload = await review_api.list_corpus_status(
        session=session,
        jurisdiction="SG",
        authority=None,
        topic=None,
        _="viewer",
    )

    assert payload["count"] == 2
    bca_item = next(item for item in payload["items"] if item["authority"] == "BCA")
    assert bca_item["coverage_state"] == "partial"
    assert bca_item["confidence"] == "high"
    assert bca_item["freshness_state"] == "current"
    assert bca_item["review_queue_size"] == 1
    assert bca_item["latest_document"]["id"] == 10

    ura_item = next(item for item in payload["items"] if item["authority"] == "URA")
    assert ura_item["coverage_state"] == "review_pending"
    assert ura_item["freshness_state"] == "suspected_update"
    assert ura_item["rule_counts"]["published"] == 0


@pytest.mark.asyncio
async def test_list_corpus_status_returns_empty_when_no_sources():
    session = _SessionStub([[]])
    payload = await review_api.list_corpus_status(
        session=session,
        jurisdiction="SG",
        authority="BCA",
        topic="building",
        _="viewer",
    )
    assert payload == {"items": [], "count": 0}
