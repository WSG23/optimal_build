"""Tests for database dependency helpers."""

from __future__ import annotations

import importlib.util
import sys
import types
from collections.abc import Generator
from pathlib import Path

import pytest

pytestmark = pytest.mark.no_db

_ROOT = Path(__file__).resolve().parents[3]


def _load_module(name: str, relative_path: str):
    module_path = _ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module {name} from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


_sqlalchemy = types.ModuleType("sqlalchemy")
_orm_module = types.ModuleType("sqlalchemy.orm")


class Session:  # pragma: no cover - compatibility stub
    def close(self) -> None:
        pass


_orm_module.Session = Session
_sqlalchemy.orm = _orm_module
sys.modules.setdefault("sqlalchemy", _sqlalchemy)
sys.modules.setdefault("sqlalchemy.orm", _orm_module)

_db_module = _load_module("db_utils_stub", "backend/app/utils/db.py")
session_dependency = _db_module.session_dependency

sys.modules.pop("sqlalchemy", None)
sys.modules.pop("sqlalchemy.orm", None)


class DummySession:
    """Minimal session stub tracking ``close`` calls."""

    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:  # pragma: no cover - trivial setter
        self.closed = True


def _session_factory() -> DummySession:
    return DummySession()


def test_session_dependency_yields_and_closes_session() -> None:
    """The dependency should yield a session and always close it."""

    dependency = session_dependency(_session_factory)
    generator: Generator[DummySession, None, None] = dependency()

    session = next(generator)
    assert isinstance(session, DummySession)
    assert not session.closed

    with pytest.raises(StopIteration):
        next(generator)

    assert session.closed
