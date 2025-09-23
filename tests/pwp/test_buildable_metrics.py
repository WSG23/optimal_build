"""Integration tests for buildable screening Prometheus metrics."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")

from backend.tests.pwp.test_buildable_golden import (  # noqa: E402
    DEFAULT_REQUEST_DEFAULTS,
    DEFAULT_REQUEST_OVERRIDES,
    buildable_client,
)


def _metric_value(metrics_text: str, metric_name: str) -> float:
    """Extract the numeric value for a metric from Prometheus text output."""

    for line in metrics_text.splitlines():
        if not line or line.startswith("#"):
            continue
        if not line.startswith(metric_name):
            continue
        try:
            return float(line.rsplit(" ", 1)[-1])
        except ValueError:
            continue
    return 0.0


@pytest.mark.asyncio
async def test_buildable_metrics_increment_after_request(buildable_client) -> None:
    """Calling buildable screening should increment the exported metrics."""

    client, _ = buildable_client

    initial_metrics = (await client.get("/health/metrics")).text
    initial_total = _metric_value(initial_metrics, "pwp_buildable_total")
    initial_duration_count = _metric_value(
        initial_metrics, "pwp_buildable_duration_ms_count"
    )
    initial_duration_sum = _metric_value(
        initial_metrics, "pwp_buildable_duration_ms_sum"
    )

    payload = {
        "address": "123 Example Ave",
        "defaults": dict(DEFAULT_REQUEST_DEFAULTS),
        **DEFAULT_REQUEST_OVERRIDES,
    }

    response = await client.post("/api/v1/screen/buildable", json=payload)
    assert response.status_code == 200

    metrics_text = (await client.get("/health/metrics")).text
    final_total = _metric_value(metrics_text, "pwp_buildable_total")
    final_duration_count = _metric_value(
        metrics_text, "pwp_buildable_duration_ms_count"
    )
    final_duration_sum = _metric_value(metrics_text, "pwp_buildable_duration_ms_sum")

    assert "pwp_buildable_total" in metrics_text
    assert "pwp_buildable_duration_ms" in metrics_text

    assert final_total >= initial_total + 1.0
    assert final_duration_count >= initial_duration_count + 1.0
    assert final_duration_sum > initial_duration_sum
