"""Fallback Prometheus client for offline testing.

This module exposes a very small subset of the `prometheus_client` interface.
It mirrors the behaviour relied upon in the test-suite so that our code can be
validated without the third-party dependency installed.  When the real
``prometheus_client`` package is available it should take precedence and this
stub will remain unused.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from math import isinf
from dataclasses import dataclass


@dataclass
class _ValueHolder:
    """Container for numeric metric values."""

    value: float = 0.0

    def get(self) -> float:
        return self.value


class CollectorRegistry:
    """Simplified collector registry."""

    def __init__(self, auto_describe: bool = True) -> None:
        self.auto_describe = auto_describe
        self._collectors: dict[str, _MetricBase] = {}

    def register(self, metric: _MetricBase) -> None:
        self._collectors[metric._name] = metric

    def collect(self) -> Iterable[_MetricBase]:
        return self._collectors.values()

    def get_sample_value(
        self, name: str, labels: dict[str, str] | None = None
    ) -> float | None:
        metric = self._collectors.get(name)
        if metric is None:
            return None
        return metric.get_sample_value(labels or {})


class _MetricBase:
    _type: str = "gauge"

    def __init__(
        self,
        name: str,
        documentation: str,
        labelnames: Iterable[str],
        registry: CollectorRegistry | None,
        **_: object,
    ) -> None:
        self._name = name
        self._documentation = documentation
        self._labelnames = tuple(labelnames)
        self._metrics: dict[tuple[str, ...], _Sample] = {}
        if registry is not None:
            registry.register(self)

    def clear(self) -> None:
        self._metrics.clear()

    def _label_key(self, labels: dict[str, str]) -> tuple[str, ...]:
        return tuple(labels.get(label, "") for label in self._labelnames)

    def labels(self, **labels: str) -> _Sample:
        key = self._label_key(labels)
        if key not in self._metrics:
            self._metrics[key] = _Sample()
        return self._metrics[key]

    def _iter_samples(self) -> Iterator[tuple[dict[str, str], _Sample]]:
        for key, sample in self._metrics.items():
            label_map = {name: value for name, value in zip(self._labelnames, key)}
            yield label_map, sample

    def get_sample_value(self, labels: dict[str, str]) -> float | None:
        key = tuple(labels.get(label, "") for label in self._labelnames)
        sample = self._metrics.get(key)
        if sample is None:
            return None
        return sample._value.get()


class _Sample:
    def __init__(self) -> None:
        self._value = _ValueHolder()

    def inc(self, amount: float = 1.0) -> None:
        self._value.value += amount

    def set(self, value: float) -> None:
        self._value.value = value


class _HistogramSample(_Sample):
    def __init__(self, bounds: Sequence[float]) -> None:
        super().__init__()
        self._count = _ValueHolder()
        self._bounds = tuple(bounds)
        self._bucket_counts: list[float] = [0.0 for _ in self._bounds]
        self._observations: list[float] = []

    def observe(self, amount: float) -> None:
        self._count.value += 1.0
        self._value.value += amount
        self._observations.append(amount)
        for index, bound in enumerate(self._bounds):
            if amount <= bound:
                self._bucket_counts[index] += 1.0

    def count(self) -> float:
        return self._count.get()

    def sum(self) -> float:
        return self._value.get()

    def bucket_counts(self) -> list[tuple[float, float]]:
        return list(zip(self._bounds, self._bucket_counts))

    def observations(self) -> list[float]:
        return list(self._observations)


class Counter(_MetricBase):
    """Counter metric stub."""

    _type = "counter"

    def inc(self, amount: float = 1.0) -> None:
        self.labels().inc(amount)


class Gauge(_MetricBase):
    """Gauge metric stub."""

    _type = "gauge"

    def set(self, value: float) -> None:
        self.labels().set(value)


class Histogram(_MetricBase):
    """Histogram metric stub supporting sum, count, and buckets."""

    _type = "histogram"
    DEFAULT_BUCKETS: tuple[float, ...] = (
        0.005,
        0.01,
        0.025,
        0.05,
        0.075,
        0.1,
        0.25,
        0.5,
        0.75,
        1.0,
        2.5,
        5.0,
        7.5,
        10.0,
        float("inf"),
    )

    def __init__(
        self,
        name: str,
        documentation: str,
        labelnames: Iterable[str],
        registry: CollectorRegistry | None,
        *,
        buckets: Sequence[float] | None = None,
        **kwargs: object,
    ) -> None:
        self._upper_bounds: tuple[float, ...] = tuple(
            buckets if buckets is not None else self.DEFAULT_BUCKETS
        )
        super().__init__(name, documentation, labelnames, registry, **kwargs)

    def labels(self, **labels: str) -> _HistogramSample:
        key = self._label_key(labels)
        sample = self._metrics.get(key)
        if not isinstance(sample, _HistogramSample):
            sample = _HistogramSample(self._upper_bounds)
            self._metrics[key] = sample
        return sample

    def observe(self, amount: float) -> None:
        self.labels().observe(amount)


def generate_latest(registry: CollectorRegistry) -> bytes:
    """Render metrics in a Prometheus text exposition format."""

    lines: list[str] = []
    for metric in registry.collect():
        lines.append(f"# HELP {metric._name} {metric._documentation}")
        lines.append(f"# TYPE {metric._name} {metric._type}")
        for label_map, sample in metric._iter_samples():
            if metric._type == "histogram" and isinstance(sample, _HistogramSample):
                for bound, value in sample.bucket_counts():
                    bound_label = "+Inf" if isinf(bound) else f"{bound:g}"
                    bucket_labels = dict(label_map)
                    bucket_labels["le"] = bound_label
                    if bucket_labels:
                        labels = ",".join(
                            f'{k}="{v}"' for k, v in bucket_labels.items()
                        )
                        lines.append(f"{metric._name}_bucket{{{labels}}} {value}")
                    else:
                        lines.append(
                            f'{metric._name}_bucket{{le="{bound_label}"}} {value}'
                        )
                if label_map:
                    labels = ",".join(f'{k}="{v}"' for k, v in label_map.items())
                    lines.append(f"{metric._name}_sum{{{labels}}} {sample.sum()}")
                    lines.append(f"{metric._name}_count{{{labels}}} {sample.count()}")
                else:
                    lines.append(f"{metric._name}_sum {sample.sum()}")
                    lines.append(f"{metric._name}_count {sample.count()}")
                continue
            if label_map:
                labels = ",".join(f'{k}="{v}"' for k, v in label_map.items())
                lines.append(f"{metric._name}{{{labels}}} {sample._value.get()}")
            else:
                lines.append(f"{metric._name} {sample._value.get()}")
    return "\n".join(lines).encode()


__all__ = [
    "CollectorRegistry",
    "Counter",
    "Gauge",
    "Histogram",
    "generate_latest",
]
