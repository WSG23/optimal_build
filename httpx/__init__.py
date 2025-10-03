"""Lightweight httpx stub for test environments without the dependency."""

from __future__ import annotations

import sys
from typing import Any

try:  # Prefer the installed dependency when it is available.
    from backend._stub_loader import import_runtime_dependency
except ModuleNotFoundError:  # pragma: no cover - backend namespace not available
    import_runtime_dependency = None  # type: ignore[assignment]


_httpx_module: Any | None = None
if import_runtime_dependency is not None:
    try:
        _httpx_module = import_runtime_dependency("httpx", "HTTPX")
    except ModuleNotFoundError:  # pragma: no cover - fall back to stub definitions
        _httpx_module = None


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
