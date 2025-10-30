"""Tests for Prometheus client stub implementation."""

from __future__ import annotations

import pytest


def test_collector_registry_creation():
    """Test creating a CollectorRegistry."""
    from app.utils._prometheus_stub import CollectorRegistry

    registry = CollectorRegistry()
    assert registry.auto_describe is True

    registry2 = CollectorRegistry(auto_describe=False)
    assert registry2.auto_describe is False


def test_collector_registry_register_and_collect():
    """Test registering metrics and collecting them."""
    from app.utils._prometheus_stub import CollectorRegistry, Counter

    registry = CollectorRegistry()
    Counter(
        name="test_counter",
        documentation="Test counter",
        labelnames=[],
        registry=registry,
    )

    collectors = list(registry.collect())
    assert len(collectors) == 1
    assert collectors[0]._name == "test_counter"


def test_collector_registry_get_sample_value():
    """Test getting sample values from registry."""
    from app.utils._prometheus_stub import CollectorRegistry, Counter

    registry = CollectorRegistry()
    counter = Counter(
        name="test_counter",
        documentation="Test counter",
        labelnames=["method"],
        registry=registry,
    )

    counter.labels(method="GET").inc(5)

    value = registry.get_sample_value("test_counter", {"method": "GET"})
    assert value == 5.0


def test_collector_registry_get_sample_value_nonexistent():
    """Test getting sample value for nonexistent metric."""
    from app.utils._prometheus_stub import CollectorRegistry

    registry = CollectorRegistry()
    value = registry.get_sample_value("nonexistent")
    assert value is None


def test_counter_basic_operations():
    """Test Counter increment operations."""
    from app.utils._prometheus_stub import CollectorRegistry, Counter

    registry = CollectorRegistry()
    counter = Counter(
        name="test_counter",
        documentation="Test counter",
        labelnames=[],
        registry=registry,
    )

    # Default increment
    counter.inc()
    assert registry.get_sample_value("test_counter", {}) == 1.0

    # Custom increment
    counter.inc(2.5)
    assert registry.get_sample_value("test_counter", {}) == 3.5


def test_counter_with_labels():
    """Test Counter with labels."""
    from app.utils._prometheus_stub import CollectorRegistry, Counter

    registry = CollectorRegistry()
    counter = Counter(
        name="http_requests",
        documentation="HTTP requests",
        labelnames=["method", "status"],
        registry=registry,
    )

    counter.labels(method="GET", status="200").inc()
    counter.labels(method="GET", status="200").inc()
    counter.labels(method="POST", status="201").inc(3)

    assert (
        registry.get_sample_value("http_requests", {"method": "GET", "status": "200"})
        == 2.0
    )
    assert (
        registry.get_sample_value("http_requests", {"method": "POST", "status": "201"})
        == 3.0
    )


def test_counter_with_positional_labels():
    """Test Counter with positional label arguments."""
    from app.utils._prometheus_stub import CollectorRegistry, Counter

    registry = CollectorRegistry()
    counter = Counter(
        name="test_counter",
        documentation="Test counter",
        labelnames=["label1", "label2"],
        registry=registry,
    )

    counter.labels("value1", "value2").inc(5)

    assert (
        registry.get_sample_value(
            "test_counter", {"label1": "value1", "label2": "value2"}
        )
        == 5.0
    )


def test_gauge_operations():
    """Test Gauge set operations."""
    from app.utils._prometheus_stub import CollectorRegistry, Gauge

    registry = CollectorRegistry()
    gauge = Gauge(
        name="temperature",
        documentation="Temperature gauge",
        labelnames=[],
        registry=registry,
    )

    gauge.set(23.5)
    assert registry.get_sample_value("temperature", {}) == 23.5

    gauge.set(25.0)
    assert registry.get_sample_value("temperature", {}) == 25.0


def test_gauge_with_labels():
    """Test Gauge with labels."""
    from app.utils._prometheus_stub import CollectorRegistry, Gauge

    registry = CollectorRegistry()
    gauge = Gauge(
        name="cpu_usage",
        documentation="CPU usage",
        labelnames=["core"],
        registry=registry,
    )

    gauge.labels(core="0").set(45.2)
    gauge.labels(core="1").set(67.8)

    assert registry.get_sample_value("cpu_usage", {"core": "0"}) == 45.2
    assert registry.get_sample_value("cpu_usage", {"core": "1"}) == 67.8


def test_histogram_basic_observe():
    """Test Histogram observe operations."""
    from app.utils._prometheus_stub import CollectorRegistry, Histogram

    registry = CollectorRegistry()
    histogram = Histogram(
        name="request_duration",
        documentation="Request duration",
        labelnames=[],
        registry=registry,
    )

    histogram.observe(0.5)
    histogram.observe(1.2)
    histogram.observe(2.8)

    # Check the sample value (sum)
    value = registry.get_sample_value("request_duration", {})
    assert value == pytest.approx(4.5)


def test_histogram_with_custom_buckets():
    """Test Histogram with custom buckets."""
    from app.utils._prometheus_stub import CollectorRegistry, Histogram

    registry = CollectorRegistry()
    histogram = Histogram(
        name="custom_hist",
        documentation="Custom histogram",
        labelnames=[],
        registry=registry,
        buckets=[0.1, 0.5, 1.0, 5.0, 10.0, float("inf")],
    )

    histogram.observe(0.3)
    histogram.observe(0.7)
    histogram.observe(2.5)

    # Get the sample
    sample = histogram.labels()
    assert sample.count() == 3.0
    assert sample.sum() == pytest.approx(3.5)

    bucket_counts = sample.bucket_counts()
    # 0.3 < 0.5, so buckets [0.5, 1.0, 5.0, 10.0, inf] should each have count 1
    # 0.7 < 1.0, so buckets [1.0, 5.0, 10.0, inf] should each have count 2
    # 2.5 < 5.0, so buckets [5.0, 10.0, inf] should each have count 3
    assert len(bucket_counts) == 6
    assert bucket_counts[0] == (0.1, 0.0)  # No values <= 0.1
    assert bucket_counts[1] == (0.5, 1.0)  # 0.3 <= 0.5
    assert bucket_counts[2] == (1.0, 2.0)  # 0.3, 0.7 <= 1.0
    assert bucket_counts[3] == (5.0, 3.0)  # all values <= 5.0


def test_histogram_observations():
    """Test Histogram observations tracking."""
    from app.utils._prometheus_stub import CollectorRegistry, Histogram

    registry = CollectorRegistry()
    histogram = Histogram(
        name="test_hist",
        documentation="Test histogram",
        labelnames=[],
        registry=registry,
    )

    histogram.observe(1.0)
    histogram.observe(2.0)
    histogram.observe(3.0)

    sample = histogram.labels()
    observations = sample.observations()
    assert observations == [1.0, 2.0, 3.0]


def test_histogram_with_labels():
    """Test Histogram with labels."""
    from app.utils._prometheus_stub import CollectorRegistry, Histogram

    registry = CollectorRegistry()
    histogram = Histogram(
        name="request_latency",
        documentation="Request latency",
        labelnames=["endpoint"],
        registry=registry,
    )

    histogram.labels(endpoint="/api/users").observe(0.1)
    histogram.labels(endpoint="/api/users").observe(0.2)
    histogram.labels(endpoint="/api/posts").observe(0.5)

    users_sample = histogram.labels(endpoint="/api/users")
    assert users_sample.count() == 2.0
    assert users_sample.sum() == pytest.approx(0.3)

    posts_sample = histogram.labels(endpoint="/api/posts")
    assert posts_sample.count() == 1.0
    assert posts_sample.sum() == pytest.approx(0.5)


def test_metric_clear():
    """Test clearing metrics."""
    from app.utils._prometheus_stub import CollectorRegistry, Counter

    registry = CollectorRegistry()
    counter = Counter(
        name="test_counter",
        documentation="Test counter",
        labelnames=["label"],
        registry=registry,
    )

    counter.labels(label="value1").inc(5)
    counter.labels(label="value2").inc(3)

    assert registry.get_sample_value("test_counter", {"label": "value1"}) == 5.0

    counter.clear()

    assert registry.get_sample_value("test_counter", {"label": "value1"}) is None


def test_generate_latest_counter():
    """Test generate_latest for Counter metrics."""
    from app.utils._prometheus_stub import CollectorRegistry, Counter, generate_latest

    registry = CollectorRegistry()
    counter = Counter(
        name="test_counter",
        documentation="A test counter",
        labelnames=["method"],
        registry=registry,
    )

    counter.labels(method="GET").inc(10)

    output = generate_latest(registry)
    output_str = output.decode()

    assert "# HELP test_counter A test counter" in output_str
    assert "# TYPE test_counter counter" in output_str
    assert (
        'test_counter{method="GET"} 10' in output_str
        or 'test_counter{method="GET"} 10.0' in output_str
    )


def test_generate_latest_gauge():
    """Test generate_latest for Gauge metrics."""
    from app.utils._prometheus_stub import CollectorRegistry, Gauge, generate_latest

    registry = CollectorRegistry()
    gauge = Gauge(
        name="temperature",
        documentation="Temperature in celsius",
        labelnames=[],
        registry=registry,
    )

    gauge.set(23.5)

    output = generate_latest(registry)
    output_str = output.decode()

    assert "# HELP temperature Temperature in celsius" in output_str
    assert "# TYPE temperature gauge" in output_str
    assert "temperature 23.5" in output_str


def test_generate_latest_histogram():
    """Test generate_latest for Histogram metrics."""
    from app.utils._prometheus_stub import CollectorRegistry, Histogram, generate_latest

    registry = CollectorRegistry()
    histogram = Histogram(
        name="request_duration",
        documentation="Request duration in seconds",
        labelnames=[],
        registry=registry,
        buckets=[0.1, 0.5, 1.0, float("inf")],
    )

    histogram.observe(0.3)
    histogram.observe(0.7)

    output = generate_latest(registry)
    output_str = output.decode()

    assert "# HELP request_duration Request duration in seconds" in output_str
    assert "# TYPE request_duration histogram" in output_str
    assert (
        'request_duration_bucket{le="0.1"} 0' in output_str
        or 'request_duration_bucket{le="0.1"} 0.0' in output_str
    )
    assert (
        'request_duration_bucket{le="0.5"} 1' in output_str
        or 'request_duration_bucket{le="0.5"} 1.0' in output_str
    )
    assert (
        'request_duration_bucket{le="1"} 2' in output_str
        or 'request_duration_bucket{le="1"} 2.0' in output_str
    )
    assert (
        'request_duration_bucket{le="+Inf"} 2' in output_str
        or 'request_duration_bucket{le="+Inf"} 2.0' in output_str
    )
    assert (
        "request_duration_sum 1" in output_str
        or "request_duration_sum 1.0" in output_str
    )
    assert (
        "request_duration_count 2" in output_str
        or "request_duration_count 2.0" in output_str
    )


def test_generate_latest_histogram_with_labels():
    """Test generate_latest for Histogram with labels."""
    from app.utils._prometheus_stub import CollectorRegistry, Histogram, generate_latest

    registry = CollectorRegistry()
    histogram = Histogram(
        name="request_duration",
        documentation="Request duration",
        labelnames=["endpoint"],
        registry=registry,
        buckets=[0.1, 1.0, float("inf")],
    )

    histogram.labels(endpoint="/api").observe(0.5)

    output = generate_latest(registry)
    output_str = output.decode()

    assert 'request_duration_bucket{endpoint="/api",le="0.1"}' in output_str
    assert 'request_duration_bucket{endpoint="/api",le="1"}' in output_str
    assert 'request_duration_bucket{endpoint="/api",le="+Inf"}' in output_str
    assert 'request_duration_sum{endpoint="/api"}' in output_str
    assert 'request_duration_count{endpoint="/api"}' in output_str


def test_metric_without_registry():
    """Test creating metrics without registering them."""
    from app.utils._prometheus_stub import Counter

    counter = Counter(
        name="unregistered_counter",
        documentation="Not registered",
        labelnames=[],
        registry=None,
    )

    counter.inc()
    # Should not raise, just not be in any registry


def test_value_holder():
    """Test _ValueHolder operations."""
    from app.utils._prometheus_stub import _ValueHolder

    holder = _ValueHolder()
    assert holder.get() == 0.0

    holder.value = 42.5
    assert holder.get() == 42.5


def test_sample_operations():
    """Test _Sample inc and set operations."""
    from app.utils._prometheus_stub import _Sample

    sample = _Sample()
    assert sample._value.get() == 0.0

    sample.inc()
    assert sample._value.get() == 1.0

    sample.inc(5)
    assert sample._value.get() == 6.0

    sample.set(10)
    assert sample._value.get() == 10.0


def test_histogram_default_buckets():
    """Test Histogram uses DEFAULT_BUCKETS when none specified."""
    from app.utils._prometheus_stub import CollectorRegistry, Histogram

    registry = CollectorRegistry()
    histogram = Histogram(
        name="default_buckets",
        documentation="Uses default buckets",
        labelnames=[],
        registry=registry,
    )

    # Verify default buckets are used
    assert histogram._upper_bounds == Histogram.DEFAULT_BUCKETS
    assert float("inf") in histogram._upper_bounds


def test_histogram_sample_with_inf_bound():
    """Test histogram sample correctly handles infinity bound."""
    from app.utils._prometheus_stub import _HistogramSample

    sample = _HistogramSample([0.1, 1.0, 10.0, float("inf")])

    sample.observe(0.05)
    sample.observe(0.5)
    sample.observe(5.0)
    sample.observe(999999.0)

    bucket_counts = sample.bucket_counts()
    assert bucket_counts[0] == (0.1, 1.0)  # 0.05 <= 0.1
    assert bucket_counts[1] == (1.0, 2.0)  # 0.05, 0.5 <= 1.0
    assert bucket_counts[2] == (10.0, 3.0)  # 0.05, 0.5, 5.0 <= 10.0
    assert bucket_counts[3][0] == float("inf")
    assert bucket_counts[3][1] == 4.0  # all values <= inf


def test_multiple_metrics_in_registry():
    """Test multiple different metric types in same registry."""
    from app.utils._prometheus_stub import (
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )

    registry = CollectorRegistry()

    counter = Counter("requests_total", "Total requests", [], registry)
    gauge = Gauge("active_connections", "Active connections", [], registry)
    histogram = Histogram(
        "request_duration",
        "Request duration",
        [],
        registry,
        buckets=[0.1, 1.0, float("inf")],
    )

    counter.inc(100)
    gauge.set(42)
    histogram.observe(0.5)

    output = generate_latest(registry).decode()

    assert "requests_total 100" in output
    assert "active_connections 42" in output
    assert "request_duration_sum 0.5" in output


def test_metric_labels_with_mixed_args_and_kwargs():
    """Test metric labels with both positional and keyword arguments."""
    from app.utils._prometheus_stub import CollectorRegistry, Counter

    registry = CollectorRegistry()
    counter = Counter(
        name="test_counter",
        documentation="Test counter",
        labelnames=["label1", "label2", "label3"],
        registry=registry,
    )

    # Mix positional and keyword arguments
    counter.labels("value1", label2="value2", label3="value3").inc(5)

    assert (
        registry.get_sample_value(
            "test_counter", {"label1": "value1", "label2": "value2", "label3": "value3"}
        )
        == 5.0
    )


def test_get_sample_value_with_partial_labels():
    """Test get_sample_value with missing labels defaults to empty string."""
    from app.utils._prometheus_stub import CollectorRegistry, Counter

    registry = CollectorRegistry()
    counter = Counter(
        name="test_counter",
        documentation="Test counter",
        labelnames=["label1", "label2"],
        registry=registry,
    )

    counter.labels(label1="value1", label2="value2").inc(5)

    # Query with only one label should use empty string for missing ones
    value = registry.get_sample_value("test_counter", {"label1": "value1"})
    # This won't match because label2 defaults to "" in the key, but we set it to "value2"
    assert value is None

    # Correct query with all labels
    value = registry.get_sample_value(
        "test_counter", {"label1": "value1", "label2": "value2"}
    )
    assert value == 5.0
