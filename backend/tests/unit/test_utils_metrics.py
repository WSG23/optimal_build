from __future__ import annotations


import pytest

from app.utils import metrics

pytestmark = pytest.mark.no_db


def test_reset_metrics_reinitialises_registry() -> None:
    metrics.reset_metrics()
    first_registry = metrics.REGISTRY
    metrics.reset_metrics()
    assert metrics.REGISTRY is not first_registry
    # Ensure counters are reset
    assert metrics.counter_value(metrics.REQUEST_COUNTER, {"endpoint": "health"}) == 0.0


def test_counter_value_with_labels() -> None:
    metrics.reset_metrics()
    metrics.REQUEST_COUNTER.labels(endpoint="/deals").inc()
    metrics.REQUEST_COUNTER.labels(endpoint="/deals").inc(3)
    assert metrics.counter_value(
        metrics.REQUEST_COUNTER, {"endpoint": "/deals"}
    ) == pytest.approx(4.0)


def test_histogram_percentile_from_observations() -> None:
    metrics.reset_metrics()
    histogram = metrics.PWP_BUILDABLE_DURATION_MS
    histogram.observe(25)
    histogram.observe(75)
    histogram.observe(100)
    percentile = metrics.histogram_percentile(histogram, 0.5)
    assert percentile.percentile == pytest.approx(0.5)
    assert percentile.value >= 0.0
    assert percentile.buckets  # ensure bucket metadata is captured


def test_histogram_percentile_from_bucket_counts() -> None:
    buckets = [(10.0, 2.0), (20.0, 5.0), (float("inf"), 8.0)]
    percentile = metrics.histogram_percentile_from_bucket_counts(buckets, 0.75)
    assert percentile.value == pytest.approx(20.0)
    assert percentile.buckets == ((10.0, 2.0), (20.0, 5.0), (float("inf"), 8.0))


def test_histogram_percentile_invalid_inputs() -> None:
    metrics.reset_metrics()
    with pytest.raises(ValueError):
        metrics.histogram_percentile(metrics.PWP_BUILDABLE_DURATION_MS, -0.5)
    with pytest.raises(RuntimeError):
        metrics.histogram_percentile_from_bucket_counts([], 0.5)
