"""Metrics instrumentation tests for buildable screening."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")

from app.utils import metrics

pytest_plugins = ("tests.pwp.test_buildable_golden",)

from tests.pwp.test_buildable_golden import (  # noqa: E402
    DEFAULT_REQUEST_DEFAULTS,
    DEFAULT_REQUEST_OVERRIDES,
)


def _scrape_metric_value(metrics_text: str, metric_name: str) -> float | None:
    for line in metrics_text.splitlines():
        if line.startswith(f"{metric_name} "):
            try:
                return float(line.split()[1])
            except (IndexError, ValueError):
                continue
    return None


@pytest.mark.asyncio
async def test_buildable_metrics_increment(buildable_client):
    client, _ = buildable_client

    payload = {
        "address": "123 Example Ave",
        "defaults": dict(DEFAULT_REQUEST_DEFAULTS),
        **DEFAULT_REQUEST_OVERRIDES,
    }

    before_total = metrics.counter_value(metrics.PWP_BUILDABLE_TOTAL, {})
    metrics_output_before = metrics.render_latest_metrics().decode()
    before_total_rendered = _scrape_metric_value(
        metrics_output_before, "pwp_buildable_total"
    ) or 0.0
    before_duration_rendered = _scrape_metric_value(
        metrics_output_before, "pwp_buildable_duration_ms_count"
    ) or 0.0

    response = await client.post("/api/v1/screen/buildable", json=payload)
    assert response.status_code == 200

    after_total = metrics.counter_value(metrics.PWP_BUILDABLE_TOTAL, {})
    assert after_total == pytest.approx(before_total + 1.0)

    metrics_output = metrics.render_latest_metrics().decode()
    after_total_rendered = _scrape_metric_value(metrics_output, "pwp_buildable_total")
    after_duration_rendered = _scrape_metric_value(
        metrics_output, "pwp_buildable_duration_ms_count"
    )

    assert after_total_rendered is not None
    assert after_duration_rendered is not None
    assert after_total_rendered == pytest.approx(before_total_rendered + 1.0)
    assert after_duration_rendered == pytest.approx(before_duration_rendered + 1.0)
