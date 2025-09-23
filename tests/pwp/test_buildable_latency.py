"""Latency regression test for PWP buildable screening histogram exports."""

from __future__ import annotations

from collections.abc import Iterable

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


def _extract_histogram_buckets(
    metrics_text: str, metric_name: str
) -> list[tuple[float, float]]:
    prefix = f"{metric_name}_bucket"
    buckets: list[tuple[float, float]] = []
    for line in metrics_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not stripped.startswith(prefix):
            continue
        try:
            sample, raw_value = stripped.split(" ", 1)
        except ValueError:
            continue
        try:
            count = float(raw_value.strip())
        except ValueError:
            continue
        label_start = sample.find("{")
        label_end = sample.find("}", label_start + 1)
        if label_start == -1 or label_end == -1:
            continue
        label_section = sample[label_start + 1 : label_end]
        labels = _parse_labels(label_section.split(","))
        le_label = labels.get("le")
        if le_label is None:
            continue
        if le_label == "+Inf":
            upper = float("inf")
        else:
            try:
                upper = float(le_label)
            except ValueError:
                continue
        buckets.append((upper, count))

    buckets.sort(key=lambda item: item[0])
    return buckets


def _parse_labels(parts: Iterable[str]) -> dict[str, str]:
    labels: dict[str, str] = {}
    for part in parts:
        if not part or "=" not in part:
            continue
        key, raw = part.split("=", 1)
        labels[key.strip()] = raw.strip().strip('"')
    return labels


@pytest.mark.asyncio
async def test_buildable_latency_p90(
    async_session_factory, app_client: AsyncClient, monkeypatch
) -> None:
    async with async_session_factory() as session:
        await seed_screening_sample_data(session, commit=True)

    monkeypatch.setattr(settings, "BUILDABLE_TYP_FLOOR_TO_FLOOR_M", 4.0)
    monkeypatch.setattr(settings, "BUILDABLE_EFFICIENCY_RATIO", 0.82)

    payload = {
        "address": "123 Example Ave",
        "defaults": dict(DEFAULT_REQUEST_DEFAULTS),
        **DEFAULT_REQUEST_OVERRIDES,
    }

    for _ in range(5):
        response = await app_client.post("/api/v1/screen/buildable", json=payload)
        assert response.status_code == 200

    metrics_response = await app_client.get("/health/metrics")
    assert metrics_response.status_code == 200

    buckets = _extract_histogram_buckets(
        metrics_response.text, "pwp_buildable_duration_ms"
    )

    assert buckets, "Expected histogram buckets to be exported"
    assert buckets[-1][1] == pytest.approx(5.0)

    snapshot = metrics.histogram_percentile_from_bucket_counts(buckets, 0.90)

    print(f"Observed buildable P90 latency: {snapshot.value:.2f} ms")
    print(f"Bucket counts: {snapshot.buckets}")

    assert snapshot.value <= 2000.0
