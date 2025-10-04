"""Metadata describing available analytics modules.

This module is intentionally lightweight so unit tests can verify that
new analytics functionality is registered without relying on any external
systems.  The data structure is kept small and deterministic so we can
assert on it inside the test-suite.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable


@dataclass(frozen=True)
class AnalyticsModule:
    """Description for an analytics feature module."""

    name: str
    summary: str
    version: str = "1.0.0"


AVAILABLE_ANALYTICS_MODULES: Dict[str, AnalyticsModule] = {
    "streaming": AnalyticsModule(
        name="streaming",
        summary="Real-time streaming analytics for ingestion pipelines.",
        version="2.1.0",
    ),
    "hll": AnalyticsModule(
        name="hll",
        summary="HyperLogLog-based distinct counting utilities.",
        version="1.4.3",
    ),
    "persistence": AnalyticsModule(
        name="persistence",
        summary="Durable storage helpers for analytics outputs.",
    ),
    "memory_profile": AnalyticsModule(
        name="memory_profile",
        summary="In-process memory profile capture for analytics jobs.",
        version="1.2.0",
    ),
}


def iter_module_names() -> Iterable[str]:
    """Return the module identifiers in a stable order."""

    return tuple(sorted(AVAILABLE_ANALYTICS_MODULES))
