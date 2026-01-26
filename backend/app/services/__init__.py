"""Service layer exports."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "alerts",
    "buildable",
    "costs",
    "finance",
    "heritage_overlay",
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


def __getattr__(name: str) -> Any:
    """Lazily import service modules to avoid eager side effects."""

    if name in __all__:
        module = import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + __all__)
