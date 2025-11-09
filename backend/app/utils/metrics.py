"""Prometheus metrics utilities."""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Any, cast

try:  # pragma: no cover - exercised when dependency is available
    from prometheus_client import (
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback for offline tests
    from app.utils._prometheus_stub import (
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )


GenerateLatest = Callable[[CollectorRegistry], bytes]
_GENERATE_LATEST: GenerateLatest = cast(GenerateLatest, generate_latest)


REGISTRY: CollectorRegistry
REQUEST_COUNTER: Counter
REQUEST_LATENCY_MS: Histogram
REQUEST_ERROR_COUNTER: Counter
INGESTION_RUN_COUNTER: Counter
INGESTED_RECORD_COUNTER: Counter
ALERT_COUNTER: Counter
MARKET_INTEL_CAP_RATE_GAUGE: Gauge
MARKET_INTEL_RENTAL_PSF_GAUGE: Gauge
COST_ADJUSTMENT_GAUGE: Gauge
PWP_BUILDABLE_TOTAL: Counter
PWP_BUILDABLE_DURATION_MS: Histogram
FINANCE_FEASIBILITY_TOTAL: Counter
FINANCE_FEASIBILITY_DURATION_MS: Histogram
FINANCE_EXPORT_TOTAL: Counter
FINANCE_EXPORT_DURATION_MS: Histogram
ENTITLEMENTS_ROADMAP_COUNTER: Counter
ENTITLEMENTS_STUDY_COUNTER: Counter
ENTITLEMENTS_ENGAGEMENT_COUNTER: Counter
ENTITLEMENTS_LEGAL_COUNTER: Counter
ENTITLEMENTS_EXPORT_COUNTER: Counter
PREVIEW_JOBS_CREATED_TOTAL: Counter
PREVIEW_JOBS_COMPLETED_TOTAL: Counter
PREVIEW_JOB_DURATION_MS: Histogram
PREVIEW_QUEUE_DEPTH: Gauge


def _initialize_metrics() -> None:
    """Create a fresh registry and metric instances."""

    global REGISTRY
    global REQUEST_COUNTER
    global REQUEST_LATENCY_MS
    global REQUEST_ERROR_COUNTER
    global INGESTION_RUN_COUNTER
    global INGESTED_RECORD_COUNTER
    global ALERT_COUNTER
    global MARKET_INTEL_CAP_RATE_GAUGE
    global MARKET_INTEL_RENTAL_PSF_GAUGE
    global COST_ADJUSTMENT_GAUGE
    global PWP_BUILDABLE_TOTAL
    global PWP_BUILDABLE_DURATION_MS
    global FINANCE_FEASIBILITY_TOTAL
    global FINANCE_FEASIBILITY_DURATION_MS
    global FINANCE_EXPORT_TOTAL
    global FINANCE_EXPORT_DURATION_MS
    global ENTITLEMENTS_ROADMAP_COUNTER
    global ENTITLEMENTS_STUDY_COUNTER
    global ENTITLEMENTS_ENGAGEMENT_COUNTER
    global ENTITLEMENTS_LEGAL_COUNTER
    global ENTITLEMENTS_EXPORT_COUNTER
    global PREVIEW_JOBS_CREATED_TOTAL
    global PREVIEW_JOBS_COMPLETED_TOTAL
    global PREVIEW_JOB_DURATION_MS
    global PREVIEW_QUEUE_DEPTH

    REGISTRY = CollectorRegistry(auto_describe=True)

    REQUEST_COUNTER = Counter(
        "api_requests_total",
        "Total API requests processed by endpoint.",
        labelnames=("endpoint",),
        registry=REGISTRY,
    )

    REQUEST_LATENCY_MS = Histogram(
        "api_request_duration_ms",
        "API request latency in milliseconds by endpoint.",
        labelnames=("endpoint",),
        registry=REGISTRY,
    )

    REQUEST_ERROR_COUNTER = Counter(
        "api_requests_failed_total",
        "Total API requests that resulted in 5xx responses.",
        labelnames=("endpoint", "status_code"),
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

    MARKET_INTEL_CAP_RATE_GAUGE = Gauge(
        "market_intelligence_cap_rate",
        "Latest market intelligence cap rate median by property type and location.",
        labelnames=("property_type", "location"),
        registry=REGISTRY,
    )

    MARKET_INTEL_RENTAL_PSF_GAUGE = Gauge(
        "market_intelligence_rental_psf",
        "Latest market intelligence rental PSF median by property type and location.",
        labelnames=("property_type", "location"),
        registry=REGISTRY,
    )

    COST_ADJUSTMENT_GAUGE = Gauge(
        "pwp_cost_adjustment_scalar",
        "Latest cost index scalar applied to PWP pro-forma adjustments.",
        labelnames=("series",),
        registry=REGISTRY,
    )

    PWP_BUILDABLE_TOTAL = Counter(
        "pwp_buildable_total",
        "Number of buildable screening requests processed.",
        labelnames=(),
        registry=REGISTRY,
    )

    PWP_BUILDABLE_DURATION_MS = Histogram(
        "pwp_buildable_duration_ms",
        "Duration of buildable screening computations in milliseconds.",
        labelnames=(),
        registry=REGISTRY,
    )

    FINANCE_FEASIBILITY_TOTAL = Counter(
        "finance_feasibility_total",
        "Number of finance feasibility calculations processed.",
        labelnames=(),
        registry=REGISTRY,
    )

    FINANCE_FEASIBILITY_DURATION_MS = Histogram(
        "finance_feasibility_duration_ms",
        "Duration of finance feasibility calculations in milliseconds.",
        labelnames=(),
        registry=REGISTRY,
    )

    FINANCE_EXPORT_TOTAL = Counter(
        "finance_export_total",
        "Number of finance scenario exports processed.",
        labelnames=(),
        registry=REGISTRY,
    )

    FINANCE_EXPORT_DURATION_MS = Histogram(
        "finance_export_duration_ms",
        "Duration of finance scenario exports in milliseconds.",
        labelnames=(),
        registry=REGISTRY,
    )

    ENTITLEMENTS_ROADMAP_COUNTER = Counter(
        "entitlements_roadmap_requests_total",
        "Entitlements roadmap endpoint operations by type.",
        labelnames=("operation",),
        registry=REGISTRY,
    )

    ENTITLEMENTS_STUDY_COUNTER = Counter(
        "entitlements_study_requests_total",
        "Entitlements study endpoint operations by type.",
        labelnames=("operation",),
        registry=REGISTRY,
    )

    ENTITLEMENTS_ENGAGEMENT_COUNTER = Counter(
        "entitlements_engagement_requests_total",
        "Entitlements engagement endpoint operations by type.",
        labelnames=("operation",),
        registry=REGISTRY,
    )

    ENTITLEMENTS_LEGAL_COUNTER = Counter(
        "entitlements_legal_requests_total",
        "Entitlements legal instrument endpoint operations by type.",
        labelnames=("operation",),
        registry=REGISTRY,
    )

    ENTITLEMENTS_EXPORT_COUNTER = Counter(
        "entitlements_export_requests_total",
        "Entitlements export requests processed by format.",
        labelnames=("format",),
        registry=REGISTRY,
    )

    PREVIEW_JOBS_CREATED_TOTAL = Counter(
        "preview_generation_jobs_total",
        "Preview generation jobs enqueued.",
        labelnames=("scenario", "backend"),
        registry=REGISTRY,
    )

    PREVIEW_JOBS_COMPLETED_TOTAL = Counter(
        "preview_generation_jobs_completed_total",
        "Preview generation jobs completed grouped by outcome.",
        labelnames=("outcome",),
        registry=REGISTRY,
    )

    PREVIEW_JOB_DURATION_MS = Histogram(
        "preview_generation_job_duration_ms",
        "End-to-end preview job duration in milliseconds.",
        labelnames=("outcome",),
        registry=REGISTRY,
    )

    PREVIEW_QUEUE_DEPTH = Gauge(
        "preview_generation_queue_depth",
        "Current queued preview jobs awaiting processing.",
        labelnames=("backend",),
        registry=REGISTRY,
    )


_initialize_metrics()


def reset_metrics() -> None:
    """Clear tracked metric values for tests."""

    _initialize_metrics()


def counter_value(counter: Counter, labels: dict[str, str]) -> float:
    """Return the current value for a labelled counter."""

    label_names: Iterable[str] = tuple(getattr(counter, "_labelnames", ()))
    labels = labels or {}
    sample: Any | None = None
    labels_fn = getattr(counter, "labels", None)
    should_use_labels = bool(labels) or bool(label_names)
    if callable(labels_fn) and should_use_labels:
        try:
            sample = labels_fn(**labels)
        except (TypeError, ValueError):
            # Some client libraries expect positional values; fall back to that ordering.
            positional = [labels[name] for name in label_names if name in labels]
            try:
                sample = labels_fn(*positional)
            except ValueError:
                sample = None
    if sample is None:
        sample = counter

    value_holder = getattr(sample, "_value", None)
    if value_holder is not None and hasattr(value_holder, "get"):
        return float(value_holder.get())

    sample_getter = getattr(REGISTRY, "get_sample_value", None)
    counter_name = getattr(counter, "_name", "")
    if callable(sample_getter) and counter_name:
        value = sample_getter(counter_name, labels)
        if value is not None:
            return float(value)

    return 0.0


@dataclass(frozen=True)
class HistogramPercentile:
    """Summary of a histogram percentile calculation."""

    percentile: float
    value: float
    buckets: tuple[tuple[float, float], ...]


def histogram_percentile(
    histogram: Histogram,
    percentile: float,
    labels: dict[str, str] | None = None,
) -> HistogramPercentile:
    """Compute a percentile for a Prometheus histogram."""

    if not 0.0 <= percentile <= 1.0:
        raise ValueError("Percentile must be expressed as a value between 0 and 1")

    labels = labels or {}
    normalized_labels = _normalize_histogram_labels(histogram, labels)
    buckets, observations = _collect_histogram_data(histogram, normalized_labels)
    if not buckets:
        raise RuntimeError("No observations recorded for histogram")

    value: float
    if observations:
        value = _percentile_from_observations(observations, percentile)
    else:
        value = _percentile_from_buckets(buckets, percentile)

    return HistogramPercentile(
        percentile=percentile, value=value, buckets=tuple(buckets)
    )


def histogram_percentile_from_bucket_counts(
    buckets: Sequence[tuple[float, float]], percentile: float
) -> HistogramPercentile:
    """Compute a percentile from exported histogram bucket counts.

    Parameters
    ----------
    buckets:
        An iterable of ``(upper_bound, cumulative_count)`` pairs. Bucket
        boundaries should be numeric (``float("inf")`` is accepted for the
        terminal bucket) and counts should represent cumulative observation
        totals as emitted by Prometheus' text exposition format.
    percentile:
        Desired percentile expressed as a floating point value between 0 and 1
        (e.g. ``0.9`` for the 90th percentile).
    """

    if not 0.0 <= percentile <= 1.0:
        raise ValueError("Percentile must be expressed as a value between 0 and 1")

    normalized = [(float(upper), float(count)) for upper, count in buckets]
    if not normalized:
        raise RuntimeError("No bucket counts were provided for percentile calculation")

    normalized.sort(key=lambda item: item[0])
    value = _percentile_from_buckets(normalized, percentile)
    return HistogramPercentile(
        percentile=percentile, value=value, buckets=tuple(normalized)
    )


def export_metrics() -> bytes:
    """Return metrics in Prometheus text format."""

    return _GENERATE_LATEST(REGISTRY)


def _normalize_histogram_labels(
    histogram: Histogram, labels: dict[str, str]
) -> dict[str, str]:
    names: Iterable[str] = getattr(histogram, "_labelnames", ())
    return {name: str(labels.get(name, "")) for name in names}


def _collect_histogram_data(
    histogram: Histogram, labels: dict[str, str]
) -> tuple[list[tuple[float, float]], list[float]]:
    buckets: list[tuple[float, float]] = []
    observations: list[float] = []

    metrics_map = getattr(histogram, "_metrics", None)
    label_names: Sequence[str] = tuple(getattr(histogram, "_labelnames", ()))
    if isinstance(metrics_map, dict):
        key = tuple(labels.get(name, "") for name in label_names)
        sample = metrics_map.get(key)
        if sample is not None:
            bucket_method = getattr(sample, "bucket_counts", None)
            if callable(bucket_method):
                buckets = [
                    (float(bound), float(count)) for bound, count in bucket_method()
                ]
            observation_method = getattr(sample, "observations", None)
            if callable(observation_method):
                observations = [float(value) for value in observation_method()]
            if buckets:
                return buckets, observations

    metric_name = getattr(histogram, "_name", "")
    for metric in REGISTRY.collect():
        candidate_name = getattr(metric, "name", getattr(metric, "_name", ""))
        if candidate_name != metric_name:
            continue
        samples = getattr(metric, "samples", None)
        if samples is None:
            continue
        bucket_results: list[tuple[float, float]] = []
        for sample in samples:
            sample_name = getattr(sample, "name", "")
            sample_labels = getattr(sample, "labels", {})
            if not _labels_match(sample_labels, labels):
                continue
            if sample_name == f"{metric_name}_bucket":
                bound_label = sample_labels.get("le")
                if bound_label is None:
                    continue
                if bound_label == "+Inf":
                    bound = float("inf")
                else:
                    try:
                        bound = float(bound_label)
                    except (TypeError, ValueError):
                        continue
                bucket_results.append((bound, float(sample.value)))
        bucket_results.sort(key=lambda item: item[0])
        if bucket_results:
            buckets = bucket_results
        break

    return buckets, observations


def _labels_match(sample_labels: dict[str, str], expected: dict[str, str]) -> bool:
    for key, value in expected.items():
        if sample_labels.get(key, "") != value:
            return False
    return True


def _percentile_from_observations(values: list[float], percentile: float) -> float:
    if not values:
        raise ValueError("Histogram percentile requested with no observations")
    if len(values) == 1:
        return float(values[0])

    sorted_values = sorted(values)
    rank = percentile * (len(sorted_values) - 1)
    lower_index = math.floor(rank)
    upper_index = math.ceil(rank)
    lower_value = sorted_values[lower_index]
    upper_value = sorted_values[upper_index]
    if lower_index == upper_index:
        return float(lower_value)
    fraction = rank - lower_index
    return float(lower_value + (upper_value - lower_value) * fraction)


def _percentile_from_buckets(
    buckets: Sequence[tuple[float, float]], percentile: float
) -> float:
    if not buckets:
        raise ValueError("Histogram percentile requested without bucket data")

    total = buckets[-1][1]
    if total <= 0:
        raise ValueError("Histogram percentile requested before any observations")

    target = percentile * total
    previous_upper = 0.0
    previous_count = 0.0

    for upper, cumulative in buckets:
        if cumulative >= target:
            if math.isinf(upper):
                return previous_upper
            if cumulative == previous_count:
                return float(upper)
            proportion = (target - previous_count) / (cumulative - previous_count)
            return float(previous_upper + (upper - previous_upper) * proportion)
        previous_upper = upper
        previous_count = cumulative

    return float(buckets[-1][0])


def render_latest_metrics() -> bytes:
    """Render metrics for exposure via HTTP endpoints."""

    return _GENERATE_LATEST(REGISTRY)
