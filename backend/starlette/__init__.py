"""Expose Starlette by deferring to the installed package or the vendored stub."""

from __future__ import annotations

import importlib
import importlib.util
import pkgutil
import sys
from pathlib import Path
from types import ModuleType

try:
    from backend._stub_loader import import_runtime_dependency
except ModuleNotFoundError:
    backend_root = Path(__file__).resolve().parents[1]
    repo_root = backend_root.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    stub_loader_path = backend_root / "_stub_loader.py"
    if not stub_loader_path.exists():  # pragma: no cover - defensive guard
        raise

    backend_package = sys.modules.setdefault("backend", ModuleType("backend"))
    existing_path = list(getattr(backend_package, "__path__", []))
    if str(backend_root) not in existing_path:
        existing_path.append(str(backend_root))
    backend_package.__path__ = existing_path

    spec = importlib.util.spec_from_file_location(
        "backend._stub_loader", stub_loader_path
    )
    if spec is None or spec.loader is None:  # pragma: no cover - safety net
        raise

    module = importlib.util.module_from_spec(spec)
    sys.modules["backend._stub_loader"] = module
    spec.loader.exec_module(module)
    import_runtime_dependency = module.import_runtime_dependency

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
