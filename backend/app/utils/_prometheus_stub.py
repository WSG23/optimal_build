"""Fallback Prometheus client for offline testing.

This module exposes a very small subset of the `prometheus_client` interface.
It mirrors the behaviour relied upon in the test-suite so that our code can be
validated without the third-party dependency installed.  When the real
``prometheus_client`` package is available it should take precedence and this
stub will remain unused.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, Tuple


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
        self._collectors: Dict[str, _MetricBase] = {}

    def register(self, metric: "_MetricBase") -> None:
        self._collectors[metric._name] = metric

    def collect(self) -> Iterable["_MetricBase"]:
        return self._collectors.values()

    def get_sample_value(
        self, name: str, labels: Dict[str, str] | None = None
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
    ) -> None:
        self._name = name
        self._documentation = documentation
        self._labelnames = tuple(labelnames)
        self._metrics: Dict[Tuple[str, ...], _Sample] = {}
        if registry is not None:
            registry.register(self)

    def clear(self) -> None:
        self._metrics.clear()

    def labels(self, **labels: str) -> "_Sample":
        key = tuple(labels.get(label, "") for label in self._labelnames)
        if key not in self._metrics:
            self._metrics[key] = _Sample()
        return self._metrics[key]

    def _iter_samples(self) -> Iterator[Tuple[Dict[str, str], "_Sample"]]:
        for key, sample in self._metrics.items():
            label_map = dict(zip(self._labelnames, key))
            yield label_map, sample

    def get_sample_value(self, labels: Dict[str, str]) -> float | None:
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
    def __init__(self) -> None:
        super().__init__()
        self._count = _ValueHolder()

    def observe(self, amount: float) -> None:
        self._count.value += 1.0
        self._value.value += amount

    def count(self) -> float:
        return self._count.get()

    def sum(self) -> float:
        return self._value.get()


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
    """Histogram metric stub supporting sum and count."""

    _type = "histogram"

    def labels(self, **labels: str) -> _HistogramSample:  # type: ignore[override]
        key = tuple(labels.get(label, "") for label in self._labelnames)
        if key not in self._metrics:
            self._metrics[key] = _HistogramSample()
        sample = self._metrics[key]
        assert isinstance(sample, _HistogramSample)
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
                if label_map:
                    labels = ",".join(f"{k}=\"{v}\"" for k, v in label_map.items())
                    lines.append(f"{metric._name}_sum{{{labels}}} {sample.sum()}")
                    lines.append(f"{metric._name}_count{{{labels}}} {sample.count()}")
                else:
                    lines.append(f"{metric._name}_sum {sample.sum()}")
                    lines.append(f"{metric._name}_count {sample.count()}")
                continue
            if label_map:
                labels = ",".join(f"{k}=\"{v}\"" for k, v in label_map.items())
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
