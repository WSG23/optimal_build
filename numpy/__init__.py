"""Lightweight numpy stub for tests that require minimal API surface."""

from __future__ import annotations

import math
from statistics import mean as _stats_mean
from typing import Iterable, Sequence

__all__ = ["array", "sqrt", "mean", "ndarray", "__version__"]

__version__ = "0.0-test-stub"


class ndarray(list):
    """Simplified ndarray representation backed by ``list``."""

    def __array__(self) -> "ndarray":  # pragma: no cover - compatibility hook
        return self


class bool_(int):
    """Minimal numpy bool representation."""


def array(values: Iterable[float]) -> ndarray:
    """Return a list-backed array for compatibility."""

    return ndarray(values)


def sqrt(value: float | int) -> float:
    """Return the non-negative square root of ``value``."""

    return math.sqrt(float(value))


def mean(values: Sequence[float] | Iterable[float]) -> float:
    """Return the arithmetic mean of ``values``."""

    seq = list(values)
    if not seq:
        raise ValueError("mean requires at least one data point")
    return float(_stats_mean(seq))


def isscalar(value: object) -> bool:
    return not isinstance(value, (list, tuple, set, dict))
