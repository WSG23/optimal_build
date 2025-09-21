"""Prometheus metrics utilities."""

from __future__ import annotations

from typing import Dict

from prometheus_client import CollectorRegistry, Counter, Gauge, generate_latest


REGISTRY: CollectorRegistry = CollectorRegistry(auto_describe=True)

REQUEST_COUNTER: Counter = Counter(
    "api_requests_total",
    "Total API requests processed by endpoint.",
    labelnames=("endpoint",),
    registry=REGISTRY,
)

INGESTION_RUN_COUNTER: Counter = Counter(
    "prefect_ingestion_runs_total",
    "Number of Prefect ingestion runs recorded.",
    labelnames=("flow",),
    registry=REGISTRY,
)

INGESTED_RECORD_COUNTER: Counter = Counter(
    "prefect_ingested_records_total",
    "Total records ingested by flow.",
    labelnames=("flow",),
    registry=REGISTRY,
)

ALERT_COUNTER: Counter = Counter(
    "ingestion_alerts_total",
    "Alerts emitted during ingestion runs by level.",
    labelnames=("level",),
    registry=REGISTRY,
)

COST_ADJUSTMENT_GAUGE: Gauge = Gauge(
    "pwp_cost_adjustment_scalar",
    "Latest cost index scalar applied to PWP pro-forma adjustments.",
    labelnames=("series",),
    registry=REGISTRY,
)


def reset_metrics() -> None:
    """Clear tracked metric values for tests."""

    for metric in (REQUEST_COUNTER, INGESTION_RUN_COUNTER, INGESTED_RECORD_COUNTER, ALERT_COUNTER, COST_ADJUSTMENT_GAUGE):
        metric.clear()


def counter_value(counter: Counter, labels: Dict[str, str]) -> float:
    """Return the current value for a labelled counter."""

    sample = counter.labels(**labels)
    return float(sample._value.get())


def render_latest_metrics() -> bytes:
    """Render metrics for exposure via HTTP endpoints."""

    return generate_latest(REGISTRY)
