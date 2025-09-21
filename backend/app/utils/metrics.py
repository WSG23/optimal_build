"""Prometheus metrics utilities."""

from __future__ import annotations

from typing import Dict

try:  # pragma: no cover - exercised when dependency is available
    from prometheus_client import CollectorRegistry, Counter, Gauge, generate_latest
except ModuleNotFoundError:  # pragma: no cover - fallback for offline tests
    from app.utils._prometheus_stub import (  # type: ignore
        CollectorRegistry,
        Counter,
        Gauge,
        generate_latest,
    )


REGISTRY: CollectorRegistry
REQUEST_COUNTER: Counter
INGESTION_RUN_COUNTER: Counter
INGESTED_RECORD_COUNTER: Counter
ALERT_COUNTER: Counter
COST_ADJUSTMENT_GAUGE: Gauge


def _initialize_metrics() -> None:
    """Create a fresh registry and metric instances."""

    global REGISTRY
    global REQUEST_COUNTER
    global INGESTION_RUN_COUNTER
    global INGESTED_RECORD_COUNTER
    global ALERT_COUNTER
    global COST_ADJUSTMENT_GAUGE

    REGISTRY = CollectorRegistry(auto_describe=True)

    REQUEST_COUNTER = Counter(
        "api_requests_total",
        "Total API requests processed by endpoint.",
        labelnames=("endpoint",),
        registry=REGISTRY,
    )

    INGESTION_RUN_COUNTER = Counter(
        "prefect_ingestion_runs_total",
        "Number of Prefect ingestion runs recorded.",
        labelnames=("flow",),
        registry=REGISTRY,
    )

    INGESTED_RECORD_COUNTER = Counter(
        "prefect_ingested_records_total",
        "Total records ingested by flow.",
        labelnames=("flow",),
        registry=REGISTRY,
    )

    ALERT_COUNTER = Counter(
        "ingestion_alerts_total",
        "Alerts emitted during ingestion runs by level.",
        labelnames=("level",),
        registry=REGISTRY,
    )

    COST_ADJUSTMENT_GAUGE = Gauge(
        "pwp_cost_adjustment_scalar",
        "Latest cost index scalar applied to PWP pro-forma adjustments.",
        labelnames=("series",),
        registry=REGISTRY,
    )


_initialize_metrics()


def reset_metrics() -> None:
    """Clear tracked metric values for tests."""

    _initialize_metrics()


def counter_value(counter: Counter, labels: Dict[str, str]) -> float:
    """Return the current value for a labelled counter."""

    sample = counter.labels(**labels)
    value_holder = getattr(sample, "_value", None)
    if value_holder is not None and hasattr(value_holder, "get"):
        return float(value_holder.get())

    sample_getter = getattr(REGISTRY, "get_sample_value", None)
    counter_name = getattr(counter, "_name", "")
    if callable(sample_getter) and counter_name:
        value = sample_getter(counter_name, labels)
        if value is not None:
            return float(value)

    raise RuntimeError("Unable to read counter value from Prometheus metric")


def render_latest_metrics() -> bytes:
    """Render metrics for exposure via HTTP endpoints."""

    return generate_latest(REGISTRY)
