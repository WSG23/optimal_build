"""Tests for the screening seed script."""

import asyncio

import pytest

pytest.importorskip("sqlalchemy")

from app.models.rkp import RefSource
from scripts.seed_screening import SeedSummary, seed_screening_sample_data
from sqlalchemy import select


def test_seed_screening_populates_reference_sources(async_session_factory) -> None:
    expected_sources = {
        ("SG", "URA", "zoning"): {
            "landing_url": "https://www.ura.gov.sg/Corporate/Planning/Master-Plan",
            "fetch_kind": "html",
        },
        ("SG", "BCA", "building"): {
            "landing_url": "https://www1.bca.gov.sg/buildsg/bca-codes/building-control-act",
            "fetch_kind": "pdf",
        },
        ("SG", "SCDF", "fire"): {
            "landing_url": "https://www.scdf.gov.sg/home/fire-safety/fire-code",
            "fetch_kind": "pdf",
        },
        ("SG", "PUB", "drainage"): {
            "landing_url": "https://www.pub.gov.sg/Documents/COP_SurfaceWaterDrainage.pdf",
            "fetch_kind": "pdf",
        },
    }

    async def _seed_once() -> SeedSummary:
        async with async_session_factory() as session:
            return await seed_screening_sample_data(session, commit=True)

    async def _fetch_sources() -> list[RefSource]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(RefSource).order_by(RefSource.authority, RefSource.topic)
            )
            return result.scalars().all()

    first_summary = asyncio.run(_seed_once())
    first_sources = asyncio.run(_fetch_sources())

    assert first_summary.sources == len(first_sources) == len(expected_sources)
    identifiers = {}
    for source in first_sources:
        key = (source.jurisdiction, source.authority, source.topic)
        assert key in expected_sources
        identifiers[key] = source.id
        expected = expected_sources[key]
        assert source.landing_url == expected["landing_url"]
        assert source.fetch_kind == expected["fetch_kind"]
        assert source.doc_title
        assert source.is_active is True

    second_summary = asyncio.run(_seed_once())
    second_sources = asyncio.run(_fetch_sources())

    assert second_summary.sources == len(second_sources) == len(expected_sources)
    for source in second_sources:
        key = (source.jurisdiction, source.authority, source.topic)
        assert key in expected_sources
        assert identifiers[key] == source.id
        assert source.landing_url == expected_sources[key]["landing_url"]
        assert source.fetch_kind == expected_sources[key]["fetch_kind"]
