"""Helper to ensure SQLAlchemy (or the bundled stub) is importable for tests."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _load_repository_stub() -> None:
    """Attempt to load the vendored SQLAlchemy stub if present."""

    repo_root = Path(__file__).resolve().parents[1]
    stub_dir = repo_root / "sqlalchemy"
    if not stub_dir.exists():
        return

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    importlib.import_module("sqlalchemy")


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
    return True


__all__ = ["ensure_sqlalchemy"]
