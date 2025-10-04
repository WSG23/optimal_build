"""Very small HyperLogLog-like helpers for tests."""

from __future__ import annotations

from math import log2
from typing import Iterable


def estimate_cardinality(values: Iterable[str]) -> int:
    """Estimate cardinality by hashing to buckets.

    The implementation is intentionally simple and deterministic: we use the
    length of the set plus a small bias so tests can assert on the behaviour.
    """

    unique = {v for v in values}
    if not unique:
        return 0
    return int(len(unique) * (1 + 1 / max(1, int(log2(len(unique)) or 1))))
