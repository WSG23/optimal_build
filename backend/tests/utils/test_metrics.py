from __future__ import annotations

import math

import pytest

from app.utils import metrics


def test_counter_value_supports_labels():
    metrics.reset_metrics()
    assert metrics.counter_value(metrics.PWP_BUILDABLE_TOTAL, {}) == 0
    metrics.REQUEST_COUNTER.labels(endpoint="/api/v1/demo").inc()
    value = metrics.counter_value(metrics.REQUEST_COUNTER, {"endpoint": "/api/v1/demo"})
    assert value == 1.0


def test_histogram_percentile_and_rendering():
    metrics.reset_metrics()
    histogram = metrics.PWP_BUILDABLE_DURATION_MS
    histogram.observe(120)
    histogram.observe(240)
    percentile = metrics.histogram_percentile(histogram, 0.5)
    assert percentile.value > 0
    assert percentile.buckets
    exported = metrics.render_latest_metrics()
    assert b"pwp_buildable_duration_ms" in exported


def test_histogram_percentile_from_bucket_counts_handles_sorted_data():
    buckets = [(100.0, 1.0), (200.0, 3.0), (math.inf, 3.0)]
    percentile = metrics.histogram_percentile_from_bucket_counts(buckets, 0.5)
    assert percentile.value == 125.0
    with pytest.raises(RuntimeError):
        metrics.histogram_percentile_from_bucket_counts([], 0.5)


def test_histogram_percentile_validates_bounds_and_observations():
    metrics.reset_metrics()
    histogram = metrics.PWP_BUILDABLE_DURATION_MS
    with pytest.raises(ValueError):
        metrics.histogram_percentile(histogram, 1.5)
    with pytest.raises(ValueError):
        metrics.histogram_percentile(histogram, 0.5)
