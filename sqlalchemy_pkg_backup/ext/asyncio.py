"""Asynchronous engine and session implementations for the in-memory stub."""

from __future__ import annotations

import inspect
from typing import Any, Iterable

from .._memory import (
    DeleteStatement,
    GLOBAL_DATABASE,
    Result,
    SelectStatement,
    TextClause,
)

__all__ = [
    "AsyncEngine",
    "AsyncSession",
    "async_sessionmaker",
    "create_async_engine",
]


class AsyncSession:
    """Asynchronous session persisting data within the in-memory database."""

    def __init__(self, database=GLOBAL_DATABASE) -> None:
        self._database = database

    async def execute(self, statement: Any, *args: Any, **kwargs: Any) -> Result:
        if isinstance(statement, SelectStatement):
            rows = statement._apply(self._database)
            return Result(rows)
        if isinstance(statement, DeleteStatement):
            self._database.delete_all(statement.model)
            return Result(())
        if isinstance(statement, TextClause):
            return Result(())
        raise TypeError(f"Unsupported statement type: {type(statement)!r}")

    async def scalar(self, statement: Any, *args: Any, **kwargs: Any) -> Any:
        result = await self.execute(statement, *args, **kwargs)
        return result.scalar_one_or_none()

    async def flush(
        self,
    ) -> None:  # noqa: D401 - the in-memory store writes immediately
        return None

    async def commit(self) -> None:
        self._database.apply_onupdate()

    async def rollback(self) -> None:
        return None

    async def refresh(self, instance: Any) -> None:
        return None

    def add(self, instance: Any) -> None:
        self._database.add(instance)

    def add_all(self, instances: Iterable[Any]) -> None:
        self._database.add_all(instances)

    async def get(self, model: type, pk: Any) -> Any:
        return self._database.get(model, pk)

    async def close(self) -> None:
        return None

    async def __aenter__(self) -> "AsyncSession":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class _SyncConnection:
    def __init__(self, database) -> None:
        self._database = database

    async def run_sync(self, fn, *args: Any, **kwargs: Any) -> Any:
        result = fn(*args, **kwargs)
        if inspect.isawaitable(result):  # pragma: no cover - defensive
            return await result
        return result


class _BeginContext:
    def __init__(self, database) -> None:
        self._database = database

    async def __aenter__(self) -> _SyncConnection:
        return _SyncConnection(self._database)

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class AsyncEngine:
    """Engine wrapper returning :class:`AsyncSession` instances."""

    def __init__(self, database=GLOBAL_DATABASE) -> None:
        self._database = database

    def begin(self) -> _BeginContext:
        return _BeginContext(self._database)

    async def dispose(self) -> None:  # noqa: D401 - nothing to clean up
        return None


class _AsyncSessionContext:
    def __init__(self, database) -> None:
        self._session = AsyncSession(database)

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self._session.close()


class _AsyncSessionFactory:
    def __init__(self, database) -> None:
        self._database = database

    def __call__(self) -> _AsyncSessionContext:
        return _AsyncSessionContext(self._database)


class _AsyncSessionmaker:
    def __getitem__(self, _item: Any) -> "_AsyncSessionmaker":
        return self

    def __call__(
        self, *args: Any, bind: AsyncEngine | None = None, **kwargs: Any
    ) -> _AsyncSessionFactory:
        engine = bind
        if engine is None and args:
            engine = args[0]
        if engine is None:
            engine = AsyncEngine()
        return _AsyncSessionFactory(engine._database)


async_sessionmaker = _AsyncSessionmaker()


def create_async_engine(*args: Any, **kwargs: Any) -> AsyncEngine:
    return AsyncEngine()
