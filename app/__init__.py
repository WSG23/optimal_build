"""Compatibility wrapper exposing :mod:`backend.app` as :mod:`app`.

This project historically imported modules using the short ``app`` package
name (for example ``from app.core.config import settings``).  In the current
repository layout the actual package lives under ``backend.app`` which breaks
those imports when the backend code is executed without installing the project
as a package.  Providing this lightweight wrapper keeps the original import
paths working by aliasing ``app`` to ``backend.app`` at import time.
"""

from __future__ import annotations

from importlib import import_module
import sys


def _ensure_sqlalchemy() -> None:
    """Expose the bundled lightweight SQLAlchemy implementation if needed."""

    try:  # pragma: no cover - exercised implicitly when SQLAlchemy is available
        import sqlalchemy  # noqa: F401
    except ModuleNotFoundError:
        pkg = import_module("sqlalchemy_pkg_backup")
        sys.modules.setdefault("sqlalchemy", pkg)

        for name in (
            "ext",
            "ext.asyncio",
            "orm",
            "engine",
            "sql",
            "dialects",
            "dialects.postgresql",
            "types",
            "pool",
        ):
            try:
                module = import_module(f"sqlalchemy_pkg_backup.{name}")
            except ModuleNotFoundError:
                continue
            sys.modules.setdefault(f"sqlalchemy.{name}", module)


_ensure_sqlalchemy()

_backend_app = import_module("backend.app")

# Expose ``backend.app`` under the historical ``app`` module name.  Using the
# existing module instance ensures submodules such as ``app.core`` resolve to
# the backend implementations without duplicating any package contents.
sys.modules[__name__] = _backend_app
