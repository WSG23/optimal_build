"""Load the vendored Pydantic stub when the real package is unavailable."""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

_SHADOW_PREFIX = "pydantic_shadow_"


def _load_shadow_stub():
    search_root = Path(__file__).resolve().parent.parent
    candidates = sorted(
        name
        for _, name, _ in pkgutil.iter_modules([str(search_root)])
        if name.startswith(_SHADOW_PREFIX)
    )
    if not candidates:
        raise ModuleNotFoundError(
            "Pydantic is not installed and no pydantic_shadow_* stub directory was found"
        )
    return importlib.import_module(candidates[0])


_module = _load_shadow_stub()

__all__ = list(getattr(_module, "__all__", []))
__doc__ = getattr(_module, "__doc__", None)

for _name, _value in _module.__dict__.items():
    if _name in {
        "__name__",
        "__package__",
        "__loader__",
        "__spec__",
        "__builtins__",
        "__cached__",
    }:
        continue
    globals()[_name] = _value
