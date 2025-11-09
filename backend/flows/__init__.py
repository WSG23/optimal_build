"""Prefect flows for backend orchestration."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

if importlib.util.find_spec("sqlalchemy") is None:
    import app as _app_for_sqlalchemy_stub  # noqa: F401  pylint: disable=unused-import

    importlib.import_module("sqlalchemy")

_BACKEND_ROOT = Path(__file__).resolve().parent.parent


def ensure_backend_path() -> None:
    """Add the backend package root to ``sys.path`` when missing."""

    if str(_BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(_BACKEND_ROOT))


ensure_backend_path()

from backend.flows.analytics_flow import (  # noqa: E402  pylint: disable=wrong-import-position
    refresh_market_intelligence as _refresh_market_intelligence,
)
from backend.flows.compliance_flow import (  # noqa: E402  pylint: disable=wrong-import-position
    refresh_singapore_compliance as _refresh_singapore_compliance,
)
from backend.flows.ergonomics import (  # noqa: E402  pylint: disable=wrong-import-position
    fetch_seeded_metrics,
    seed_ergonomics_metrics as _seed_ergonomics_metrics,
)
from backend.flows.normalize_rules import (  # noqa: E402  pylint: disable=wrong-import-position
    normalize_reference_rules as _normalize_reference_rules,
)
from backend.flows.parse_segment import (  # noqa: E402  pylint: disable=wrong-import-position
    parse_reference_documents as _parse_reference_documents,
)
from backend.flows.products import (  # noqa: E402  pylint: disable=wrong-import-position
    sync_vendor_products as _sync_vendor_products,
)
from backend.flows.sync_products import (  # noqa: E402  pylint: disable=wrong-import-position
    sync_products_csv_once as _sync_products_csv_once,
)
from backend.flows.watch_fetch import (  # noqa: E402  pylint: disable=wrong-import-position
    watch_reference_sources as _watch_reference_sources,
)

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
refresh_singapore_compliance = cast(
    FlowCallable, _unwrap_flow(_refresh_singapore_compliance)
)
refresh_market_intelligence = cast(
    FlowCallable, _unwrap_flow(_refresh_market_intelligence)
)

__all__ = [
    "ensure_backend_path",
    "fetch_seeded_metrics",
    "normalize_reference_rules",
    "parse_reference_documents",
    "refresh_market_intelligence",
    "refresh_singapore_compliance",
    "seed_ergonomics_metrics",
    "sync_vendor_products",
    "sync_products_csv_once",
    "watch_reference_sources",
]
