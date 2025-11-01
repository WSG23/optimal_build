"""Asyncio helpers for the in-memory SQLAlchemy stub."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple, Type

from .. import Select, _DeleteStatement

__all__ = [
    "AsyncEngine",
    "AsyncSession",
    "AsyncResult",
    "ScalarResult",
    "async_sessionmaker",
    "create_async_engine",
]


class _InMemoryDatabase:
    """Lightweight in-memory store keyed by model class."""

    def __init__(self) -> None:
        self._rows: Dict[Type[Any], Dict[Any, Any]] = {}
        self._pk_counters: Dict[Type[Any], int] = {}

    def add(self, instance: Any) -> None:
        model = type(instance)
        storage = self._rows.setdefault(model, {})
        pk_name = getattr(model, "__primary_key__", "id")
        ident = getattr(instance, pk_name, None)
        if ident is None:
            ident = self._pk_counters.get(model, 0) + 1
            self._pk_counters[model] = int(ident)
            setattr(instance, pk_name, ident)
        else:
            try:
                ident_int = int(ident)
            except (TypeError, ValueError):
                ident_int = len(storage) + 1
            self._pk_counters[model] = max(self._pk_counters.get(model, 0), ident_int)
        storage[ident] = instance

    def all(self, model: Type[Any]) -> Iterable[Any]:
        return list(self._rows.get(model, {}).values())

    def get(self, model: Type[Any], ident: Any) -> Any:
        return self._rows.get(model, {}).get(ident)

    def clear(self, model: Type[Any]) -> None:
        self._rows.setdefault(model, {}).clear()

    def reset(self) -> None:
        for bucket in self._rows.values():
            bucket.clear()
        self._pk_counters.clear()


class ScalarResult:
    """Container exposing scalar-oriented result helpers."""

    def __init__(self, values: Iterable[Any]) -> None:
        self._values = list(values)

    def all(self) -> List[Any]:
        return list(self._values)

    def first(self) -> Any:
        return self._values[0] if self._values else None

    def one(self) -> Any:
        if len(self._values) != 1:
            raise ValueError("Expected exactly one row")
        return self._values[0]

    def one_or_none(self) -> Any:
        if not self._values:
            return None
        if len(self._values) == 1:
            return self._values[0]
        raise ValueError("Expected at most one row")

    def scalar_one(self) -> Any:
        return self.one()

    def scalar_one_or_none(self) -> Any:
        return self.one_or_none()


class AsyncResult:
    """Result wrapper mimicking SQLAlchemy's async result API."""

    def __init__(self, rows: Iterable[Any], is_scalar: bool) -> None:
        self._rows = list(rows)
        self._is_scalar = is_scalar

    def all(self) -> List[Any]:
        return list(self._rows)

    def first(self) -> Any:
        return self._rows[0] if self._rows else None

    def scalars(self) -> ScalarResult:
        if self._is_scalar:
            return ScalarResult(self._rows)
        scalar_values = []
        for row in self._rows:
            if isinstance(row, tuple):
                scalar_values.append(row[0] if row else None)
            else:
                scalar_values.append(row)
        return ScalarResult(scalar_values)

    def scalar_one(self) -> Any:
        return self.scalars().scalar_one()

    def scalar_one_or_none(self) -> Any:
        return self.scalars().scalar_one_or_none()


class AsyncSession:
    """Async session interacting with the in-memory database."""

    def __init__(self, database: _InMemoryDatabase) -> None:
        self._database = database

    async def __aenter__(self) -> "AsyncSession":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:  # pragma: no cover - no-op
        return None

    async def commit(self) -> None:  # pragma: no cover - no-op
        return None

    async def rollback(self) -> None:  # pragma: no cover - no-op
        return None

    async def flush(self) -> None:  # pragma: no cover - no-op
        return None

    async def refresh(self, instance: Any) -> None:  # pragma: no cover - no-op
        return None

    def add(self, instance: Any) -> None:
        self._database.add(instance)

    def add_all(self, instances: Iterable[Any]) -> None:
        for instance in instances:
            self.add(instance)

    async def execute(self, statement: Any) -> AsyncResult:
        if isinstance(statement, Select):
            rows, is_scalar = statement._run(self._database)
            return AsyncResult(rows, is_scalar)
        if isinstance(statement, _DeleteStatement):
            self._database.clear(statement.model)
            return AsyncResult([], True)
        raise TypeError(f"Unsupported statement type: {type(statement)!r}")

    async def get(self, model: Type[Any], ident: Any) -> Any:
        return self._database.get(model, ident)


class _AsyncSessionFactory:
    def __init__(
        self,
        engine: "AsyncEngine" | None = None,
        expire_on_commit: bool = False,
        *,
        bind: "AsyncEngine" | None = None,
        **_: Any,
    ) -> None:
        self._engine = bind or engine or AsyncEngine()
        self._expire = expire_on_commit

    def __call__(self, *args: Any, **kwargs: Any) -> AsyncSession:
        return AsyncSession(self._engine._database)


class async_sessionmaker(_AsyncSessionFactory):  # type: ignore[misc]
    """Factory returning :class:`AsyncSession` instances."""

    def __class_getitem__(cls, _item: Any) -> Type["async_sessionmaker"]:  # noqa: D401 - generic alias support
        return cls


class _EngineConnection:
    def __init__(self, database: _InMemoryDatabase) -> None:
        self._database = database

    async def run_sync(self, fn, *args: Any, **kwargs: Any) -> Any:  # noqa: D401
        return fn(self, *args, **kwargs)


class _EngineBeginContext:
    def __init__(self, database: _InMemoryDatabase) -> None:
        self._database = database

    async def __aenter__(self) -> _EngineConnection:
        return _EngineConnection(self._database)

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class AsyncEngine:
    """Async engine backed by the in-memory database."""

    def __init__(self, database: Optional[_InMemoryDatabase] = None) -> None:
        self._database = database or _InMemoryDatabase()

    def begin(self) -> _EngineBeginContext:
        return _EngineBeginContext(self._database)

    async def dispose(self) -> None:
        self._database.reset()


def create_async_engine(*args: Any, **kwargs: Any) -> AsyncEngine:
    """Return a new :class:`AsyncEngine` ignoring connection arguments."""

    return AsyncEngine()


__all__ = [
    "AsyncEngine",
    "AsyncSession",
    "AsyncResult",
    "ScalarResult",
    "async_sessionmaker",
    "create_async_engine",
]
