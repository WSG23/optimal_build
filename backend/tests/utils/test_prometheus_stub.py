"""Unit tests for the internal Prometheus stub helpers."""

from __future__ import annotations

import math

import pytest

from app.utils import _prometheus_stub as prom


def test_counter_registers_and_increments() -> None:
    registry = prom.CollectorRegistry()
    counter = prom.Counter("demo_counter", "Demo metric", (), registry)

    # Counter starts undefined until the first increment creates the sample.
    assert registry.get_sample_value("demo_counter") is None
    counter.inc()
    assert registry.get_sample_value("demo_counter") == 1

    # Explicit increments add to the running total.
    counter.inc(4)
    assert registry.get_sample_value("demo_counter") == 5


def test_gauge_tracks_latest_value_and_labels() -> None:
    registry = prom.CollectorRegistry()
    gauge = prom.Gauge("temperature", "Room temperature", ("room",), registry)

    # Gauge values are keyed by labels; nothing is recorded until set() is called.
    assert registry.get_sample_value("temperature") is None
    gauge.set(22.5)
    assert registry.get_sample_value("temperature") == pytest.approx(22.5)

    # Using positional labels should populate the metric-specific key.
    gauge.labels("lab").set(19.0)
    assert registry.get_sample_value("temperature", {"room": "lab"}) == pytest.approx(
        19.0
    )


def test_histogram_records_sum_count_and_buckets() -> None:
    registry = prom.CollectorRegistry()
    histogram = prom.Histogram(
        "request_latency_seconds",
        "Test histogram",
        ("route",),
        registry,
        buckets=(0.1, 0.5, 1.0, math.inf),
    )

    sample = histogram.labels(route="/api")
    sample.observe(0.08)
    sample.observe(0.6)
    sample.observe(1.4)

    # Count and sum reflect all observations.
    assert sample.count() == 3
    assert sample.sum() == pytest.approx(0.08 + 0.6 + 1.4)

    # Buckets accumulate cumulative counts (inclusive upper bounds).
    assert sample.bucket_counts() == [
        (0.1, 1.0),  # only the first value fits under 0.1
        (0.5, 1.0),  # still one value under 0.5
        (1.0, 2.0),  # two values <= 1.0
        (math.inf, 3.0),  # all values eventually counted in +Inf bucket
    ]

    # Registry exposes the histogram metric itself; sample holds the aggregates.
    assert histogram.get_sample_value({"route": "/api"}) == pytest.approx(sample.sum())


def test_histogram_label_instances_are_cached() -> None:
    registry = prom.CollectorRegistry()
    histogram = prom.Histogram("events", "Event histogram", ("kind",), registry)

    first = histogram.labels("error")
    second = histogram.labels(kind="error")
    third = histogram.labels("warning")

    assert first is second, "label lookups for the same key should return the cache"
    assert first is not third, "different label values map to distinct samples"


def test_registry_collect_iterates_registered_metrics() -> None:
    registry = prom.CollectorRegistry()
    prom.Counter("a", "a", (), registry)
    prom.Gauge("b", "b", (), registry)
    prom.Histogram("c", "c", (), registry)

    collected_names = {metric._name for metric in registry.collect()}
    assert collected_names == {"a", "b", "c"}
