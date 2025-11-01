"""Service layer exports."""

from . import entitlements  # noqa: F401
from . import (
    alerts,
    buildable,
    costs,
    finance,
    ingestion,
    integrations,
    normalize,
    overlay_ingest,
    products,
    pwp,
    reference_parsers,
    reference_sources,
    reference_storage,
    standards,
    storage,
)

try:  # pragma: no cover - optional dependency guard for lightweight environments
    from . import deals
except ImportError:  # pragma: no cover - skip deals services when metrics deps missing
    deals = None  # type: ignore[assignment]

__all__ = [
    "alerts",
    "buildable",
    "costs",
    "finance",
    "ingestion",
    "normalize",
    "overlay_ingest",
    "products",
    "pwp",
    "entitlements",
    "deals",
    "integrations",
    "reference_parsers",
    "reference_sources",
    "reference_storage",
    "standards",
    "storage",
]
