from __future__ import annotations

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
