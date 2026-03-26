"""Service layer exports."""

from __future__ import annotations

from importlib import import_module
from typing import Final

_EXPORTED_MODULES: Final[tuple[str, ...]] = (
    "alerts",
    "buildable",
    "costs",
    "deals",
    "entitlements",
    "finance",
    "heritage_overlay",
    "ingestion",
    "integrations",
    "normalize",
    "overlay_ingest",
    "products",
    "pwp",
    "reference_parsers",
    "reference_sources",
    "reference_storage",
    "standards",
    "storage",
)


def __getattr__(name: str) -> object:
    """Lazy-load service submodules on first access."""

    if name not in _EXPORTED_MODULES:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module = import_module(f".{name}", __name__)
    globals()[name] = module
    return module


__all__ = list(_EXPORTED_MODULES)
