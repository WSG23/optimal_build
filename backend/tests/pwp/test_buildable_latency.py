"""Latency regression tests for buildable screening metrics."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")

import pytest_asyncio
from httpx import AsyncClient

from app.core.config import settings
from app.utils import metrics
from scripts.seed_screening import seed_screening_sample_data

DEFAULT_REQUEST_DEFAULTS = {
    "plot_ratio": 3.5,
    "site_area_m2": 1000.0,
    "site_coverage": 0.45,
    "floor_height_m": 4.0,
    "efficiency_factor": 0.82,
}
DEFAULT_REQUEST_OVERRIDES = {
    "typ_floor_to_floor_m": 4.0,
    "efficiency_ratio": 0.82,
}


async def _seed_screening_data(async_session_factory) -> None:
    async with async_session_factory() as session:
        await seed_screening_sample_data(session, commit=False)
        await session.commit()


@pytest_asyncio.fixture
async def buildable_client(async_session_factory, monkeypatch, app_client: AsyncClient):
    await _seed_screening_data(async_session_factory)

    monkeypatch.setattr(settings, "BUILDABLE_TYP_FLOOR_TO_FLOOR_M", 4.0)
    monkeypatch.setattr(settings, "BUILDABLE_EFFICIENCY_RATIO", 0.82)

    return app_client


@pytest.mark.asyncio
async def test_buildable_latency_p90(buildable_client):
    client = buildable_client

    payload = {
        "address": "123 Example Ave",
        "defaults": dict(DEFAULT_REQUEST_DEFAULTS),
        **DEFAULT_REQUEST_OVERRIDES,
    }

    for _ in range(5):
        response = await client.post("/api/v1/screen/buildable", json=payload)
        assert response.status_code == 200

    snapshot = metrics.histogram_percentile(metrics.PWP_BUILDABLE_DURATION_MS, 0.90)

    assert snapshot.buckets, "Expected histogram buckets to be recorded"
    assert snapshot.buckets[-1][1] == pytest.approx(5.0)

    print(f"Observed buildable P90 latency: {snapshot.value:.2f} ms")
    print(f"Bucket counts: {snapshot.buckets}")

    assert snapshot.value <= 2000.0
