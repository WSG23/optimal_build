"""Lightweight httpx stub for test environments without the dependency."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

try:  # Prefer the installed dependency when it is available.
    from backend._stub_loader import import_runtime_dependency
except ModuleNotFoundError:  # pragma: no cover - backend namespace not available
    import_runtime_dependency = None  # type: ignore[assignment]


_httpx_module: Any | None = None
_REPO_ROOT = Path(__file__).resolve().parents[1]
_STUB_MODULE = sys.modules[__name__]


def _is_repo_path(entry: str) -> bool:
    try:
        resolved = Path(entry).resolve()
    except OSError:  # pragma: no cover - guard against malformed entries
        return False
    return resolved == _REPO_ROOT or _REPO_ROOT in resolved.parents


def _load_real_httpx() -> Any | None:
    """Import the real httpx package by temporarily removing the repo stub."""

    original_sys_path = sys.path[:]
    module: Any | None = None
    try:
        sys.modules.pop(__name__, None)
        sys.modules.pop("httpx", None)
        filtered: list[str] = []
        for entry in original_sys_path:
            if entry in {"", "."}:
                continue
            if _is_repo_path(entry):
                continue
            filtered.append(entry)
        sys.path = filtered
        module = importlib.import_module("httpx")
    except ImportError:  # pragma: no cover - handled by fallback stub
        module = None
        return None
    finally:
        sys.path = original_sys_path
        if module is None:
            sys.modules[__name__] = _STUB_MODULE
    return module


if import_runtime_dependency is not None:
    try:
        sys.modules.pop(__name__, None)
        sys.modules.pop("httpx", None)
        _httpx_module = import_runtime_dependency("httpx", "HTTPX")
        globals().update(_httpx_module.__dict__)
    except ModuleNotFoundError:  # pragma: no cover - fall back to stub definitions
        _httpx_module = _load_real_httpx()
else:
    _httpx_module = _load_real_httpx()


if _httpx_module is not None:
    sys.modules[__name__] = _httpx_module
    globals().update(_httpx_module.__dict__)
else:
    from importlib import import_module as _import_module

    try:
        _httpx_stub = _import_module("backend.httpx")
    except ModuleNotFoundError as exc:  # pragma: no cover - guard unusual setups
        raise ModuleNotFoundError(
            "The bundled HTTPX stub requires the 'backend.httpx' module."
        ) from exc

    sys.modules[__name__] = _httpx_stub
    globals().update(_httpx_stub.__dict__)


__all__ = ["AsyncClient", "Response"]
