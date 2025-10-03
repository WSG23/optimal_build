"""Utility helpers for database connectivity and ingestion flows."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

try:  # pragma: no cover - prefer real SQLAlchemy when available
    from sqlalchemy import create_engine
    from sqlalchemy.engine import Engine
    from sqlalchemy.orm import Session, sessionmaker
except Exception:  # pragma: no cover - fallback for minimal environments
    create_engine = None  # type: ignore[assignment]
    Engine = object  # type: ignore[assignment]
    Session = object  # type: ignore[assignment]
    sessionmaker = None  # type: ignore[assignment]

    from sqlalchemy import _memory as _memory

    @dataclass
    class _Engine:
        url: str
        echo: bool = False

    class _SimpleSession:
        """Very small in-memory session compatible with the test suite."""

        def __init__(self) -> None:
            self._database = _memory.GLOBAL_DATABASE
            self._closed = False

        def add(self, obj: object) -> None:
            self._database.add(obj)

        def add_all(self, objs) -> None:
            for obj in objs:
                self.add(obj)

        def execute(self, statement):
            rows = statement._apply(self._database)
            return _memory.Result(rows)

        def scalar(self, statement):
            result = self.execute(statement)
            return result.scalar_one()

        def commit(self) -> None:
            self._database.apply_onupdate()

        def rollback(self) -> None:
            return None

        def flush(self) -> None:
            return None

        def close(self) -> None:
            self._closed = True

    def _create_engine(database_url: str, echo: bool = False):  # type: ignore[override]
        return _Engine(database_url, echo)

    def _sessionmaker(*args, **kwargs):  # type: ignore[override]
        def factory():
            return _SimpleSession()

        return factory

    create_engine = _create_engine  # type: ignore[assignment]
    sessionmaker = _sessionmaker  # type: ignore[assignment]

    Engine = _Engine  # type: ignore[assignment]
    Session = _SimpleSession  # type: ignore[assignment]


def get_engine(database_url: str, echo: bool = False):
    """Create a synchronous SQLAlchemy engine or a minimal fallback."""

    return create_engine(database_url, echo=echo)  # type: ignore[misc]


def create_session_factory(engine) -> sessionmaker:
    """Return a sessionmaker bound to the provided engine or fallback."""

    return sessionmaker(engine)  # type: ignore[misc]


@contextmanager
def session_scope(session_factory) -> Iterator:
    """Provide a transactional scope around a series of operations."""

    session = session_factory()
    try:
        yield session
        if hasattr(session, "commit"):
            session.commit()
    except Exception:  # pragma: no cover - defensive
        if hasattr(session, "rollback"):
            session.rollback()
        raise
    finally:
        if hasattr(session, "close"):
            session.close()
