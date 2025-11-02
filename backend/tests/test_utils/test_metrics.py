"""Tests exercising Prometheus metrics utilities."""

from __future__ import annotations

import math

import pytest

pytestmark = [pytest.mark.no_db]

from app.utils import metrics


def test_reset_metrics_creates_fresh_registry() -> None:
    """Calling ``reset_metrics`` should replace the collector registry."""

    metrics.reset_metrics()
    original_registry = metrics.REGISTRY
    metrics.REQUEST_COUNTER.labels(endpoint="rules").inc()
    assert metrics.counter_value(metrics.REQUEST_COUNTER, {"endpoint": "rules"}) == 1.0

    metrics.reset_metrics()

    assert metrics.REGISTRY is not original_registry
    assert metrics.counter_value(metrics.REQUEST_COUNTER, {"endpoint": "rules"}) == 0.0


def test_counter_value_falls_back_to_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    """When label resolution fails the registry should provide a sample value."""

    class DummyRegistry:
        def get_sample_value(self, name: str, labels: dict[str, str]) -> float | None:
            if name == "dummy_counter" and labels == {"status": "ok"}:
                return 3.5
            return None

    class DummyCounter:
        _labelnames = ("status",)
        _name = "dummy_counter"

        def labels(self, *args: str, **kwargs: str) -> None:
            if kwargs:
                raise TypeError("unexpected label name")
            raise ValueError("positional labels unsupported")

    monkeypatch.setattr(metrics, "REGISTRY", DummyRegistry())

    value = metrics.counter_value(DummyCounter(), {"status": "ok"})
    assert math.isclose(value, 3.5)

    metrics.reset_metrics()


def test_histogram_percentile_with_observations() -> None:
    """Recorded histogram observations should drive percentile calculations."""

    metrics.reset_metrics()
    histogram = metrics.FINANCE_FEASIBILITY_DURATION_MS
    histogram.observe(100.0)
    histogram.observe(200.0)

    result = metrics.histogram_percentile(histogram, 0.75)

    assert math.isclose(result.percentile, 0.75)
    assert result.value >= 0.0
    assert result.buckets


def test_histogram_percentile_requires_bucket_data() -> None:
    """Requesting a percentile without buckets should raise an error."""

    metrics.reset_metrics()
    histogram = metrics.FINANCE_FEASIBILITY_DURATION_MS

    with pytest.raises(ValueError):
        metrics.histogram_percentile(histogram, 0.5)


def test_histogram_percentile_from_bucket_counts_orders_buckets() -> None:
    """Bucket counts should be normalised and sorted before interpolation."""

    result = metrics.histogram_percentile_from_bucket_counts(
        [(10.0, 3.0), (float("inf"), 4.0), (5.0, 1.0)],
        0.75,
    )

    assert math.isclose(result.percentile, 0.75)
    assert result.buckets == ((5.0, 1.0), (10.0, 3.0), (float("inf"), 4.0))
    assert math.isclose(result.value, 10.0)


def test_render_latest_metrics_emits_text() -> None:
    """Rendered metrics should include updated counter samples."""

    metrics.reset_metrics()
    metrics.REQUEST_COUNTER.labels(endpoint="health").inc()

    output = metrics.render_latest_metrics()

    assert isinstance(output, bytes)
    assert b"api_requests_total" in output
