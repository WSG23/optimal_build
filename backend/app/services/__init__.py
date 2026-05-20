"""Service layer exports."""

from __future__ import annotations

import sys
from importlib import import_module
from types import ModuleType
from typing import Final

_EXPORTED_MODULES: Final[tuple[str, ...]] = (
    "alerts",
    "buildable",
    "costs",
    "deals",
    "developer_condition_service",
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


def _counterpart(name: str) -> str | None:
    if name.startswith("backend."):
        return name.removeprefix("backend.")
    if name.startswith("app."):
        return f"backend.{name}"
    return None


def _register_alias(module_name: str, module: ModuleType) -> None:
    alias = _counterpart(module_name)
    if alias and alias not in sys.modules:
        sys.modules[alias] = module


def _load_submodule(module_name: str) -> ModuleType:
    module = import_module(f".{module_name}", __name__)
    globals()[module_name] = module
    _register_alias(f"{__name__}.{module_name}", module)
    return module


def __getattr__(name: str) -> object:
    """Lazy-load service submodules on first access."""

    if name not in _EXPORTED_MODULES:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    return _load_submodule(name)


_ALIAS = _counterpart(__name__)
if _ALIAS and _ALIAS in sys.modules:
    _existing: ModuleType = sys.modules[_ALIAS]
    globals().update(_existing.__dict__)
    sys.modules[__name__] = _existing
else:
    _register_alias(__name__, sys.modules[__name__])
    __all__ = list(_EXPORTED_MODULES)
