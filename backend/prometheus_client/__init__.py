"""Minimal Prometheus client stubs for offline testing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple


@dataclass
class _ValueHolder:
    value: float = 0.0

    def get(self) -> float:
        return self.value


class CollectorRegistry:
    """Simple registry to track metric instances."""

    def __init__(self, auto_describe: bool = True) -> None:
        self.auto_describe = auto_describe
        self._metrics: list[_MetricBase] = []

    def register(self, metric: "_MetricBase") -> None:
        self._metrics.append(metric)


class _MetricBase:
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
        self._metrics: Dict[Tuple[str, ...], "_Sample"] = {}
        if registry is not None:
            registry.register(self)

    def clear(self) -> None:
        self._metrics.clear()

    def labels(self, **labels: str) -> "_Sample":
        key = tuple(labels.get(label, "") for label in self._labelnames)
        if key not in self._metrics:
            self._metrics[key] = _Sample()
        return self._metrics[key]

    def _iter_samples(self) -> Iterable[Tuple[Dict[str, str], "_Sample"]]:
        for key, sample in self._metrics.items():
            label_map = dict(zip(self._labelnames, key))
            yield label_map, sample


class _Sample:
    def __init__(self) -> None:
        self._value = _ValueHolder()

    def inc(self, amount: float = 1.0) -> None:
        self._value.value += amount

    def set(self, value: float) -> None:
        self._value.value = value


class Counter(_MetricBase):
    """Counter metric stub."""

    pass


class Gauge(_MetricBase):
    """Gauge metric stub."""

    pass


def generate_latest(registry: CollectorRegistry) -> bytes:
    """Render metrics in a basic text format."""

    lines: list[str] = []
    for metric in registry._metrics:
        lines.append(f"# HELP {metric._name} {metric._documentation}")
        lines.append(f"# TYPE {metric._name} gauge")
        for label_map, sample in metric._iter_samples():
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
    "generate_latest",
]
