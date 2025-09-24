"""Tests for the ergonomics ingestion flow."""

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import select

from backend.app.models.rkp import RefErgonomics
from flows.ergonomics import DEFAULT_ERGONOMICS_METRICS, fetch_seeded_metrics, seed_ergonomics_metrics


@pytest.mark.asyncio
async def test_seed_ergonomics_metrics(async_session_factory) -> None:
    await seed_ergonomics_metrics(async_session_factory)

    metrics = await fetch_seeded_metrics(async_session_factory)
    assert len(metrics) == len(DEFAULT_ERGONOMICS_METRICS)
    assert any(metric["notes"] for metric in metrics)

    async with async_session_factory() as session:
        result = await session.execute(select(RefErgonomics))
        stored = result.scalars().all()
        assert stored
        assert stored[0].notes
