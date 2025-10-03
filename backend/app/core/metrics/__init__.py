"""Metrics aggregation utilities."""

from __future__ import annotations

from typing import Mapping

from app.utils import metrics as prometheus_metrics

from .roi import (
    DECISION_REVIEW_BASELINE_SECONDS,
    EXPORT_BASELINE_SECONDS,
    OVERLAY_BASELINE_SECONDS,
    RoiSnapshot,
    compute_project_roi,
)


class MetricsCollector:
    """Thin wrapper that records metrics against named Prometheus gauges."""

    _GAUGE_MAP = {
        "market_intelligence.cap_rate": lambda: prometheus_metrics.MARKET_INTEL_CAP_RATE_GAUGE,
        "market_intelligence.rental_psf": lambda: prometheus_metrics.MARKET_INTEL_RENTAL_PSF_GAUGE,
    }

    def record_gauge(
        self,
        metric_name: str,
        value: float | int,
        tags: Mapping[str, str] | None = None,
    ) -> None:
        """Record a gauge metric if the name is recognised."""

        gauge_factory = self._GAUGE_MAP.get(metric_name)
        if gauge_factory is None:
            raise KeyError(f"Unknown gauge metric: {metric_name}")

        gauge = gauge_factory()
        label_names = getattr(gauge, "_labelnames", ())
        tag_map = dict(tags or {})
        label_values = [tag_map.get(name, "") for name in label_names]
        gauge.labels(*label_values).set(float(value))


__all__ = [
    "MetricsCollector",
    "DECISION_REVIEW_BASELINE_SECONDS",
    "EXPORT_BASELINE_SECONDS",
    "OVERLAY_BASELINE_SECONDS",
    "RoiSnapshot",
    "compute_project_roi",
]
