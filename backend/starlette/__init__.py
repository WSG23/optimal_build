"""Expose Starlette by deferring to the installed package or the vendored stub."""

from __future__ import annotations

import importlib
import pkgutil
import sys
from pathlib import Path
from types import ModuleType

from backend._stub_loader import import_runtime_dependency

_SHADOW_PREFIX = "starlette_shadow_"


def _load_runtime_distribution() -> ModuleType | None:
    try:
        return import_runtime_dependency("starlette", "Starlette")
    except ModuleNotFoundError:
        return None


def _load_shadow_stub() -> ModuleType:
    search_root = Path(__file__).resolve().parents[2]
    candidates = sorted(
        name
        for _, name, _ in pkgutil.iter_modules([str(search_root)])
        if name.startswith(_SHADOW_PREFIX)
    )
    if not candidates:
        raise ModuleNotFoundError(
            "Starlette is not installed and no starlette_shadow_* stub directory was found"
        )
    return importlib.import_module(candidates[0])


_module = _load_runtime_distribution() or _load_shadow_stub()
globals().update(_module.__dict__)
sys.modules[__name__] = _module

if _module.__name__ != __name__:
    shadow_prefix = f"{_module.__name__}."
    canonical_prefix = f"{__name__}."
    for module_name, module in list(sys.modules.items()):
        if not module_name.startswith(shadow_prefix):
            continue
        canonical_name = canonical_prefix + module_name[len(shadow_prefix) :]
        sys.modules.setdefault(canonical_name, module)

del ModuleType
del Path
del importlib
del pkgutil
del _SHADOW_PREFIX
del _module
del _load_runtime_distribution
del _load_shadow_stub
