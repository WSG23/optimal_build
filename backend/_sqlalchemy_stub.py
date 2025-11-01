"""Helper to ensure SQLAlchemy (or the bundled stub) is importable for tests."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Iterable


def _load_repository_stub() -> None:
    """Attempt to load the vendored SQLAlchemy stub if present."""

    repo_root = Path(__file__).resolve().parents[1]
    stub_dir = repo_root / "sqlalchemy"
    if not stub_dir.exists():
        return

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    importlib.import_module("sqlalchemy")


def _iter_third_party_wheels(package: str) -> Iterable[Path]:
    """Yield wheel files for ``package`` stored under ``third_party/python``."""

    repo_root = Path(__file__).resolve().parents[1]
    wheel_dir = repo_root / "third_party" / "python"
    if not wheel_dir.exists():
        return ()

    pattern = f"{package}-*.whl"
    return sorted(wheel_dir.glob(pattern))


def _load_wheel_distribution(module_name: str, package: str) -> bool:
    """Attempt to import ``module_name`` from a vendored wheel distribution."""

    imported = False
    for wheel in _iter_third_party_wheels(package):
        wheel_path = str(wheel)
        if wheel_path not in sys.path:
            sys.path.insert(0, wheel_path)
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue
        else:
            imported = True
            break
    return imported


def ensure_sqlalchemy() -> bool:
    """Import SQLAlchemy, falling back to the in-repo stub when necessary.

    Returns
    -------
    bool
        ``True`` when SQLAlchemy (or the vendored stub) is importable, ``False``
        otherwise.
    """

    try:
        importlib.import_module("sqlalchemy")
        return True
    except ModuleNotFoundError:
        pass

    if _load_wheel_distribution("sqlalchemy", "SQLAlchemy"):
        _load_wheel_distribution("aiosqlite", "aiosqlite")
        _load_wheel_distribution("alembic", "alembic")
        _load_wheel_distribution("mako", "mako")
        return True

    try:
        from ._stub_loader import load_optional_package
    except ModuleNotFoundError:
        load_optional_package = None  # type: ignore[assignment]

    if load_optional_package is not None:
        try:
            load_optional_package("sqlalchemy", "sqlalchemy", "SQLAlchemy")
        except ModuleNotFoundError:
            _load_repository_stub()
    else:
        _load_repository_stub()

    try:
        importlib.import_module("sqlalchemy")
    except ModuleNotFoundError:  # pragma: no cover - dependency unavailable
        return False

    if not _load_wheel_distribution("aiosqlite", "aiosqlite"):
        try:  # pragma: no cover - optional dependency may already exist
            importlib.import_module("aiosqlite")
        except ModuleNotFoundError:
            pass

    if not _load_wheel_distribution("alembic", "alembic"):
        try:  # pragma: no cover - optional dependency may already exist
            importlib.import_module("alembic")
        except ModuleNotFoundError:
            pass

    if not _load_wheel_distribution("mako", "mako"):
        try:  # pragma: no cover - optional dependency may already exist
            importlib.import_module("mako")
        except ModuleNotFoundError:
            pass
    return True


__all__ = ["ensure_sqlalchemy"]
