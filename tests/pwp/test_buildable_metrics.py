"""Metrics instrumentation regression tests for the buildable endpoint."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")

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


def _metric_value(metrics_text: str, metric_name: str) -> float:
    """Extract a Prometheus sample value from text output."""

    prefix = f"{metric_name} "
    for line in metrics_text.splitlines():
        sample = line.strip()
        if not sample or sample.startswith("#"):
            continue
        if not sample.startswith(prefix):
            continue
        try:
            _, raw_value = sample.split(" ", 1)
        except ValueError:
            continue
        try:
            return float(raw_value.strip())
        except ValueError:
            continue
    return 0.0


@pytest.mark.asyncio
async def test_buildable_metrics_increment(
    async_session_factory, app_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Trigger the endpoint and ensure exported metrics advance."""

    async with async_session_factory() as session:
        await seed_screening_sample_data(session, commit=True)

    monkeypatch.setattr(settings, "BUILDABLE_TYP_FLOOR_TO_FLOOR_M", 4.0)
    monkeypatch.setattr(settings, "BUILDABLE_EFFICIENCY_RATIO", 0.82)

    payload = {
        "address": "123 Example Ave",
        "defaults": dict(DEFAULT_REQUEST_DEFAULTS),
        **DEFAULT_REQUEST_OVERRIDES,
    }

    baseline_metrics = await app_client.get("/health/metrics")
    assert baseline_metrics.status_code == 200

    total_before = _metric_value(baseline_metrics.text, "pwp_buildable_total")
    duration_count_before = _metric_value(
        baseline_metrics.text, "pwp_buildable_duration_ms_count"
    )

    response = await app_client.post("/api/v1/screen/buildable", json=payload)
    assert response.status_code == 200

    assert metrics.counter_value(metrics.PWP_BUILDABLE_TOTAL, {}) == pytest.approx(
        total_before + 1.0
    )

    metrics_response = await app_client.get("/health/metrics")
    assert metrics_response.status_code == 200

    total_after = _metric_value(metrics_response.text, "pwp_buildable_total")
    duration_count_after = _metric_value(
        metrics_response.text, "pwp_buildable_duration_ms_count"
    )

    assert total_after == pytest.approx(total_before + 1.0)
    assert duration_count_after == pytest.approx(duration_count_before + 1.0)
