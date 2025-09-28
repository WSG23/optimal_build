"""Compatibility shim for the standard library :mod:`importlib` package."""

from __future__ import annotations

import sys
from collections.abc import Iterable
from pathlib import Path
from types import ModuleType

_MODULE_NAME = __name__
_THIS_MODULE = sys.modules[_MODULE_NAME]
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent


def _iter_clean_sys_path(original: Iterable[str]) -> list[str]:
    """Return ``sys.path`` entries that do not resolve to this project."""

    cleaned: list[str] = []
    for entry in original:
        resolved: Path | None
        if entry in ("", "."):
            resolved = Path.cwd().resolve()
        else:
            try:
                resolved = Path(entry).resolve()
            except (OSError, RuntimeError):
                resolved = None
        if resolved is not None and resolved == _PACKAGE_ROOT:
            continue
        cleaned.append(entry)
    return cleaned


_original_module: ModuleType | None = None
del sys.modules[_MODULE_NAME]
_original_sys_path = sys.path[:]
try:
    sys.path = _iter_clean_sys_path(_original_sys_path)
    _original_module = __import__(_MODULE_NAME)
finally:
    sys.path = _original_sys_path

if _original_module is None:
    raise ImportError("Unable to load the standard library 'importlib' package")

sys.modules[_MODULE_NAME] = _THIS_MODULE
_THIS_MODULE.__dict__.update(_original_module.__dict__)

if not hasattr(_THIS_MODULE, "util"):
    import importlib.util as _importlib_util

    _THIS_MODULE.util = _importlib_util  # type: ignore[attr-defined]

    _all = _THIS_MODULE.__dict__.get("__all__")
    if isinstance(_all, list) and "util" not in _all:
        _all.append("util")
