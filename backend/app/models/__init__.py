"""Model package exports.

The package itself stays import-light. Call ``load_model_modules()`` when the full
SQLAlchemy model registry is required for metadata or mapper configuration.
"""

from __future__ import annotations

from functools import lru_cache
from importlib import import_module
import sys
from types import ModuleType
from typing import Final


def _counterpart(name: str) -> str | None:
    """Return the alternate import path for ``app``/``backend.app`` modules."""

    if name.startswith("backend."):
        return name.removeprefix("backend.")
    if name.startswith("app."):
        return f"backend.{name}"
    return None


def _register_alias(module_name: str, module: ModuleType) -> None:
    """Register the mirrored ``app``/``backend.app`` import path for a module."""

    alias = _counterpart(module_name)
    if alias and alias not in sys.modules:
        sys.modules[alias] = module


_MODEL_MODULES: Final[tuple[str, ...]] = (
    "agent_advisory",
    "ai_agents",
    "ai_config",
    "audit",
    "business_performance",
    "developer_checklists",
    "developer_condition",
    "development_phase",
    "entitlements",
    "finance",
    "hong_kong_property",
    "imports",
    "listing_integration",
    "new_zealand_property",
    "overlay",
    "preview",
    "projects",
    "property",
    "regulatory",
    "rkp",
    "rulesets",
    "seattle_property",
    "singapore_property",
    "team",
    "toronto_property",
    "users",
    "workflow",
)


def _load_submodule(module_name: str) -> ModuleType:
    """Import a model submodule and register its mirrored alias path."""

    module = import_module(f".{module_name}", __name__)
    globals()[module_name] = module
    _register_alias(f"{__name__}.{module_name}", module)
    return module


@lru_cache(maxsize=1)
def load_model_modules() -> None:
    """Import every ORM module so SQLAlchemy metadata and relationships are complete."""

    for module_name in _MODEL_MODULES:
        _load_submodule(module_name)


def __getattr__(name: str) -> ModuleType:
    """Lazy-load model submodules when accessed from the package namespace."""

    if name in _MODEL_MODULES:
        return _load_submodule(name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


_ALIAS = _counterpart(__name__)
if _ALIAS and _ALIAS in sys.modules:
    _existing: ModuleType = sys.modules[_ALIAS]
    globals().update(_existing.__dict__)
    sys.modules[__name__] = _existing
else:
    from .base import Base

    _register_alias(__name__, sys.modules[__name__])
    __all__ = ["Base", "load_model_modules", *_MODEL_MODULES]
