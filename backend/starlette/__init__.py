"""Expose Starlette via a bundled stub when available, fall back to the real package."""

from __future__ import annotations

import importlib
import pkgutil
import sys
from pathlib import Path
from types import ModuleType

from backend._stub_loader import load_optional_package


def _load_shadow_stub() -> ModuleType:
    search_root = Path(__file__).resolve().parents[2]
    candidates = sorted(
        name
        for _, name, _ in pkgutil.iter_modules([str(search_root)])
        if name.startswith("starlette_shadow_")
    )
    if not candidates:
        raise ModuleNotFoundError(
            "Starlette is not installed and no starlette_shadow_* stub directory was found"
        )
    return importlib.import_module(candidates[0])


def _load_module() -> ModuleType:
    try:
        return load_optional_package(
            __name__,
            "starlette",
            "Starlette",
        )
    except ModuleNotFoundError:
        return _load_shadow_stub()


_starlette = _load_module()
globals().update(_starlette.__dict__)
sys.modules[__name__] = _starlette
