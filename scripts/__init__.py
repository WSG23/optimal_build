"""Utility scripts namespace shared across repo root and backend helpers."""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_BACKEND_SCRIPTS = _ROOT.parent / "backend" / "scripts"

if _BACKEND_SCRIPTS.exists():
    backend_scripts_str = str(_BACKEND_SCRIPTS)
    if backend_scripts_str not in __path__:
        __path__.append(backend_scripts_str)
