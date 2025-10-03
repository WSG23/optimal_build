"""Helper to expose the bundled SQLAlchemy fallback when the dependency is absent."""

from __future__ import annotations

import sys
from importlib import import_module
from typing import Iterable

__all__ = ["ensure_sqlalchemy"]

# Submodules that the bundled fallback provides. We mirror them under the
# ``sqlalchemy`` namespace so downstream imports continue to work unchanged.
_STUB_SUBMODULES: tuple[str, ...] = (
    "ext",
    "ext.asyncio",
    "orm",
    "engine",
    "sql",
    "dialects",
    "dialects.postgresql",
    "types",
    "pool",
)


def ensure_sqlalchemy(*, _modules: Iterable[str] = _STUB_SUBMODULES) -> None:
    """Expose the lightweight SQLAlchemy replacement if the real package is missing."""

    try:  # pragma: no cover - executed implicitly when SQLAlchemy is installed
        import_module("sqlalchemy")
        return
    except ModuleNotFoundError:
        pkg = import_module("sqlalchemy_pkg_backup")
        sys.modules.setdefault("sqlalchemy", pkg)

        for name in _modules:
            try:
                module = import_module(f"sqlalchemy_pkg_backup.{name}")
            except ModuleNotFoundError:
                continue
            sys.modules.setdefault(f"sqlalchemy.{name}", module)
