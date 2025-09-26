"""Load FastAPI from the environment or fall back to the bundled stub.

This repository vendors a lightweight FastAPI-compatible implementation that is
only used in test environments where the real dependency might be absent. When
the genuine distribution is installed the loader below defers to it so that
application code continues to benefit from the full feature set.
"""

from __future__ import annotations

import importlib
import pkgutil
import sys
from pathlib import Path
from types import ModuleType

_SHADOW_PREFIX = "fastapi_shadow_"


def _load_runtime_distribution() -> ModuleType | None:
    """Return the installed FastAPI package when available."""

    try:
        from backend._stub_loader import import_runtime_dependency
    except ModuleNotFoundError:
        return None

    try:
        return import_runtime_dependency("fastapi", "FastAPI")
    except ModuleNotFoundError:
        return None


def _load_shadow_stub() -> ModuleType:
    """Import the vendored FastAPI stub stored in the repository root."""

    search_root = Path(__file__).resolve().parent.parent
    candidates = sorted(
        name
        for _, name, _ in pkgutil.iter_modules([str(search_root)])
        if name.startswith(_SHADOW_PREFIX)
    )
    if not candidates:
        raise ModuleNotFoundError(
            "FastAPI is not installed and no fastapi_shadow_* stub directory was found"
        )
    return importlib.import_module(candidates[0])


_module = _load_runtime_distribution() or _load_shadow_stub()
_module_name = _module.__name__

__doc__ = getattr(_module, "__doc__", None)
__all__ = list(getattr(_module, "__all__", []))

if hasattr(_module, "__file__"):
    __file__ = _module.__file__  # type: ignore[assignment]
if hasattr(_module, "__path__"):
    __path__ = list(_module.__path__)  # type: ignore[assignment]

# Copy public attributes so ``import fastapi`` exposes the expected API.
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


# Ensure submodules that were imported under the shadow namespace are reachable
# via the canonical ``fastapi`` package path.
if _module_name != __name__:
    shadow_prefix = f"{_module_name}."
    canonical_prefix = f"{__name__}."
    for existing_name, module in list(sys.modules.items()):
        if not existing_name.startswith(shadow_prefix):
            continue
        canonical_name = canonical_prefix + existing_name[len(shadow_prefix) :]
        sys.modules.setdefault(canonical_name, module)


# Avoid leaking helper globals.
del ModuleType
del Path
del importlib
del pkgutil
del sys
del _SHADOW_PREFIX
del _load_runtime_distribution
del _load_shadow_stub
del _module
del _module_name
