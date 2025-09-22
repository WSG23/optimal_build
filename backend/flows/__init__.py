"""Prefect flows for backend orchestration.

This module is resilient to optional dependencies (such as Prefect) being
unavailable in lightweight test environments. When a dependency is missing the
corresponding flow is simply omitted from ``__all__`` so imports like
``from backend.flows.sync_products import sync_products_csv_once`` continue to
work without requiring the full orchestration stack.
"""

from __future__ import annotations

from typing import List

try:  # pragma: no cover - exercised only when optional dependencies are available
    from .ergonomics import fetch_seeded_metrics, seed_ergonomics_metrics
except ModuleNotFoundError:  # pragma: no cover - triggered when Prefect is absent
    fetch_seeded_metrics = None  # type: ignore[assignment]
    seed_ergonomics_metrics = None  # type: ignore[assignment]

try:  # pragma: no cover - exercised only when document parsing deps are available
    from .parse_segment import parse_reference_documents
except ModuleNotFoundError:  # pragma: no cover - optional dependency missing
    parse_reference_documents = None  # type: ignore[assignment]

from .products import sync_vendor_products
from .sync_products import sync_products_csv_once

try:  # pragma: no cover - exercised only when watcher dependencies are available
    from .watch_fetch import watch_reference_sources
except ModuleNotFoundError:  # pragma: no cover - optional dependency missing
    watch_reference_sources = None  # type: ignore[assignment]

__all__: List[str] = ["sync_products_csv_once", "sync_vendor_products"]

if fetch_seeded_metrics is not None:
    __all__.extend(["fetch_seeded_metrics", "seed_ergonomics_metrics"])
if parse_reference_documents is not None:
    __all__.append("parse_reference_documents")
if watch_reference_sources is not None:
    __all__.append("watch_reference_sources")
