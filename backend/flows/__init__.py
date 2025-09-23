"""Prefect flows for backend orchestration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from .ergonomics import fetch_seeded_metrics, seed_ergonomics_metrics as _seed_ergonomics_metrics
from .normalize_rules import normalize_reference_rules as _normalize_reference_rules
from .parse_segment import parse_reference_documents as _parse_reference_documents
from .products import sync_vendor_products as _sync_vendor_products
from .sync_products import sync_products_csv_once as _sync_products_csv_once
from .watch_fetch import watch_reference_sources as _watch_reference_sources

FlowCallable = Callable[..., Any]


def _unwrap_flow(flow_like: Callable[..., Any] | object) -> FlowCallable:
    """Return the underlying coroutine for a Prefect flow-like object."""

    for attr in ("__wrapped__", "fn"):
        candidate = getattr(flow_like, attr, None)
        if callable(candidate):
            return cast(FlowCallable, candidate)
    if callable(flow_like):
        return cast(FlowCallable, flow_like)
    raise TypeError(f"Expected a callable Prefect flow, received {flow_like!r}")


seed_ergonomics_metrics = cast(FlowCallable, _unwrap_flow(_seed_ergonomics_metrics))
normalize_reference_rules = cast(FlowCallable, _unwrap_flow(_normalize_reference_rules))
parse_reference_documents = cast(FlowCallable, _unwrap_flow(_parse_reference_documents))
sync_vendor_products = cast(FlowCallable, _unwrap_flow(_sync_vendor_products))
sync_products_csv_once = cast(FlowCallable, _unwrap_flow(_sync_products_csv_once))
watch_reference_sources = cast(FlowCallable, _unwrap_flow(_watch_reference_sources))

__all__ = [
    "fetch_seeded_metrics",
    "normalize_reference_rules",
    "parse_reference_documents",
    "seed_ergonomics_metrics",
    "sync_vendor_products",
    "sync_products_csv_once",
    "watch_reference_sources",
]
