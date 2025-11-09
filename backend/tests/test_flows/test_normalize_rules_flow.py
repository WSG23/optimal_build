"""Tests for the reference rule normalisation flow."""

from __future__ import annotations

import pytest

pytest.importorskip("sqlalchemy")

from app.models.rkp import RefClause, RefDocument, RefRule, RefSource
from flows.normalize_rules import normalize_reference_rules
from sqlalchemy import select


@pytest.mark.asyncio
async def test_normalize_reference_rules_extracts_zoning_metrics(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        source = RefSource(
            jurisdiction="SG",
            authority="URA",
            topic="zoning",
            doc_title="URA Zoning Handbook",
            landing_url="https://example.com/zoning.pdf",
        )
        session.add(source)
        await session.flush()

        document = RefDocument(
            source_id=source.id,
            version_label="2024",
            storage_path="s3://bucket/ura-2024.pdf",
            file_hash="hash-2024",
        )
        session.add(document)
        await session.flush()

        clause = RefClause(
            document_id=document.id,
            clause_ref="5.1",
            section_heading="Zoning Controls",
            text_span=(
                "The URA Master Plan specifies a maximum gross plot ratio of 3.5. "
                "Building height shall not exceed 120 metres within the precinct. "
                "Site coverage must not exceed 65 percent for new developments. "
                "A minimum front setback of 7.5 m is required along arterial roads."
            ),
            page_from=12,
            page_to=14,
        )
        session.add(clause)
        await session.commit()
        clause_id = clause.id
        document_id = document.id
        source_id = source.id

    results = await normalize_reference_rules(async_session_factory)
    assert any(item["parameter_key"] == "zoning.max_far" for item in results)

    async with async_session_factory() as session:
        rules = (
            (await session.execute(select(RefRule).order_by(RefRule.parameter_key)))
            .scalars()
            .all()
        )

    assert {rule.parameter_key for rule in rules} == {
        "zoning.max_building_height_m",
        "zoning.max_far",
        "zoning.setback.front_min_m",
        "zoning.site_coverage.max_percent",
    }

    for rule in rules:
        assert rule.source_id == source_id
        assert rule.document_id == document_id
        assert rule.clause_ref == "5.1"
        assert rule.review_status == "needs_review"
        if rule.parameter_key == "zoning.max_far":
            assert rule.value == "3.5"
            assert rule.operator == "<="
            assert rule.unit == "ratio"
        elif rule.parameter_key == "zoning.max_building_height_m":
            assert rule.value == "120"
            assert rule.unit == "m"
        elif rule.parameter_key == "zoning.site_coverage.max_percent":
            assert rule.value == "65"
            assert rule.unit == "percent"
        elif rule.parameter_key == "zoning.setback.front_min_m":
            assert rule.value == "7.5"
            assert rule.unit == "m"

        provenance = rule.source_provenance or {}
        assert provenance["document_id"] == document_id
        assert provenance["clause_id"] == clause_id
        assert provenance["document_hash"] == "hash-2024"
        assert provenance["pages"] == [12, 14]

    # Re-running the flow should update existing rules rather than duplicating them.
    repeat_results = await normalize_reference_rules(async_session_factory)
    assert len(repeat_results) == len(results)

    async with async_session_factory() as session:
        total_rules = (
            (
                await session.execute(
                    select(RefRule).where(RefRule.document_id == document_id)
                )
            )
            .scalars()
            .all()
        )
    assert len(total_rules) == 4
