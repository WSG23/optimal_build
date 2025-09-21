from __future__ import annotations

import pytest

from app.models.rkp import RefDocument, RefRule, RefSource
from app.services.rules import RuleService


@pytest.mark.asyncio
async def test_rule_search_and_snapshot(session) -> None:
    source = RefSource(
        jurisdiction="SG",
        authority="BCA",
        topic="fire",
        doc_title="Sample Code",
        landing_url="https://example.test/sample.pdf",
        fetch_kind="pdf",
        selectors={},
    )
    session.add(source)
    await session.flush()

    document = RefDocument(
        source_id=source.id,
        version_label="v1",
        storage_path="docs/sample.pdf",
        file_hash="abc123",
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

    service = RuleService(session)
    results = await service.search(query="egress")
    assert results
    assert results[0]["parameter_key"] == "egress.corridor.min_width_mm"
    assert results[0]["value_normalized"] == pytest.approx(1.2)

    grouped = await service.rules_by_clause("C1")
    assert "egress.corridor.min_width_mm" in grouped

    snapshot = await service.snapshot()
    assert snapshot["total_rules"] == 1
    assert snapshot["by_authority"]["BCA"] == 1
