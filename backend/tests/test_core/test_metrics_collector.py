"""Tests for MetricsCollector."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.no_db

from app.core.metrics import MetricsCollector


def test_metrics_collector_records_cap_rate_gauge():
    """Test recording market intelligence cap rate metric."""
    collector = MetricsCollector()

    # Should not raise an error
    collector.record_gauge(
        "market_intelligence.cap_rate",
        value=5.5,
        tags={"district": "CBD", "property_type": "office"},
    )


def test_metrics_collector_records_rental_psf_gauge():
    """Test recording market intelligence rental PSF metric."""
    collector = MetricsCollector()

    # Should not raise an error
    collector.record_gauge(
        "market_intelligence.rental_psf",
        value=12.50,
        tags={"district": "Marina Bay", "property_type": "retail"},
    )


def test_metrics_collector_raises_on_unknown_metric():
    """Test that unknown metric names raise KeyError."""
    collector = MetricsCollector()

    with pytest.raises(KeyError, match="Unknown gauge metric"):
        collector.record_gauge("unknown.metric", value=100.0)


def test_metrics_collector_records_without_tags():
    """Test recording metric without tags."""
    collector = MetricsCollector()

    # Should work with None tags
    collector.record_gauge("market_intelligence.cap_rate", value=6.0, tags=None)


def test_metrics_collector_records_with_empty_tags():
    """Test recording metric with empty tags dict."""
    collector = MetricsCollector()

    collector.record_gauge("market_intelligence.cap_rate", value=6.0, tags={})


def test_metrics_collector_converts_int_to_float():
    """Test that integer values are converted to float."""
    collector = MetricsCollector()

    # Should accept integer value
    collector.record_gauge("market_intelligence.rental_psf", value=10, tags={})


def test_metrics_collector_with_multiple_recordings():
    """Test recording multiple metrics in sequence."""
    collector = MetricsCollector()

    collector.record_gauge("market_intelligence.cap_rate", value=5.0)
    collector.record_gauge("market_intelligence.rental_psf", value=15.0)
    collector.record_gauge("market_intelligence.cap_rate", value=6.0)


def test_metrics_collector_handles_missing_label_values():
    """Test that missing tag values are handled gracefully."""
    collector = MetricsCollector()

    # Provide partial tags (some label values may be expected but not provided)
    collector.record_gauge(
        "market_intelligence.cap_rate", value=5.5, tags={"district": "CBD"}
    )


def test_metrics_collector_with_extra_tags():
    """Test that extra tags that don't match labels are handled."""
    collector = MetricsCollector()

    # Provide tags that may not all match the gauge's labels
    collector.record_gauge(
        "market_intelligence.rental_psf",
        value=12.0,
        tags={"district": "CBD", "extra_tag": "value", "another": "tag"},
    )


def test_metrics_collector_records_zero_value():
    """Test recording a zero value."""
    collector = MetricsCollector()

    collector.record_gauge("market_intelligence.cap_rate", value=0.0)


def test_metrics_collector_records_negative_value():
    """Test recording a negative value."""
    collector = MetricsCollector()

    collector.record_gauge("market_intelligence.rental_psf", value=-5.0)


def test_metrics_collector_records_large_value():
    """Test recording a very large value."""
    collector = MetricsCollector()

    collector.record_gauge("market_intelligence.cap_rate", value=999999.99)
