"""Tests for the screening seed script."""

import asyncio

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import select

from app.models.rkp import RefSource
from scripts.seed_screening import seed_screening_sample_data


def test_seed_screening_populates_reference_sources(async_session_factory) -> None:
    async def _run():
        async with async_session_factory() as session:
            summary = await seed_screening_sample_data(session, commit=False)
            result = await session.execute(select(RefSource))
            sources = result.scalars().all()
        return summary, sources

    summary, sources = asyncio.run(_run())

    assert summary.sources == len(sources)
    authorities = {source.authority for source in sources}
    assert {"URA", "BCA", "SCDF", "PUB"} <= authorities
    assert all(source.jurisdiction == "SG" for source in sources)
    assert all(source.doc_title for source in sources)
    assert all(source.landing_url.startswith("http") for source in sources)
