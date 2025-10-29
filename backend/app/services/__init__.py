"""Service layer exports."""

from __future__ import annotations

import importlib
from types import ModuleType

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


def __getattr__(name: str) -> ModuleType:
    if name in __all__:
        return importlib.import_module(f"{__name__}.{name}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(__all__ + [*globals().keys()])
