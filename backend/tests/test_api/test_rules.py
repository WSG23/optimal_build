from __future__ import annotations

import pytest

from app.models.rkp import RefDocument, RefRule, RefSource


@pytest.mark.asyncio
async def test_rules_endpoints(session, client) -> None:
    source = RefSource(
        jurisdiction="SG",
        authority="BCA",
        topic="fire",
        doc_title="API Sample",
        landing_url="https://example.test/api.pdf",
        fetch_kind="pdf",
        selectors={},
    )
    session.add(source)
    await session.flush()

    document = RefDocument(
        source_id=source.id,
        version_label="v1",
        storage_path="docs/api.pdf",
        file_hash="hash",
        suspected_update=False,
    )
    session.add(document)
    await session.flush()

    rule = RefRule(
        source_id=source.id,
        document_id=document.id,
        jurisdiction="SG",
        authority="BCA",
        topic="fire",
        clause_ref="C1",
        parameter_key="egress.corridor.min_width_mm",
        operator=">=",
        value="1200",
        unit="mm",
        applicability={"occupancy": ["residential"]},
        exceptions=[],
        source_provenance={"document_id": document.id, "pages": [1]},
        review_status="approved",
    )
    session.add(rule)
    await session.commit()

    search_response = await client.get("/api/v1/rules/search", params={"query": "egress"})
    assert search_response.status_code == 200
    payload = search_response.json()
    assert payload["count"] == 1

    by_clause = await client.get("/api/v1/rules/by-clause", params={"clause_ref": "C1"})
    assert by_clause.status_code == 200
    assert "egress.corridor.min_width_mm" in by_clause.json()["rules"]

    snapshot = await client.get("/api/v1/rules/snapshot")
    assert snapshot.status_code == 200
    assert snapshot.json()["total_rules"] == 1
