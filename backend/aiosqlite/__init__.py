"""Lightweight aiosqlite shim for environments without the real package."""

from __future__ import annotations

import asyncio
import sqlite3
from typing import Any, Callable, Coroutine, Iterable, Optional

__all__ = ["connect", "Connection", "Cursor"]


Error = sqlite3.Error
DatabaseError = sqlite3.DatabaseError
IntegrityError = sqlite3.IntegrityError
OperationalError = sqlite3.OperationalError
ProgrammingError = sqlite3.ProgrammingError
NotSupportedError = sqlite3.NotSupportedError


sqlite_version = sqlite3.sqlite_version
sqlite_version_info = sqlite3.sqlite_version_info


class Cursor:
    def __init__(self, cursor: sqlite3.Cursor) -> None:
        self._cursor = cursor
        self.rowcount = -1

    async def execute(self, sql: str, parameters: Iterable[Any] | None = None) -> "Cursor":
        self._cursor.execute(sql, tuple(parameters or ()))
        self.rowcount = self._cursor.rowcount
        return self

    async def fetchone(self) -> Optional[tuple[Any, ...]]:
        return self._cursor.fetchone()

    async def fetchall(self) -> list[tuple[Any, ...]]:
        return self._cursor.fetchall()

    async def fetchmany(self, size: int | None = None) -> list[tuple[Any, ...]]:
        if size is None:
            return await self.fetchall()
        return self._cursor.fetchmany(size)

    async def close(self) -> None:
        self._cursor.close()

    @property
    def description(self) -> Any:
        return self._cursor.description

    @property
    def lastrowid(self) -> Any:
        return self._cursor.lastrowid


class Connection:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    async def __aenter__(self) -> "Connection":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def cursor(self) -> Cursor:
        return Cursor(self._connection.cursor())

    async def execute(self, sql: str, parameters: Iterable[Any] | None = None) -> Cursor:
        cursor = await self.cursor()
        await cursor.execute(sql, parameters)
        return cursor

    async def create_function(
        self,
        name: str,
        num_params: int,
        func: Callable[..., Any],
        *,
        deterministic: bool = False,
    ) -> None:
        self._connection.create_function(
            name,
            num_params,
            func,
            deterministic=deterministic,
        )

    async def commit(self) -> None:
        self._connection.commit()

    async def rollback(self) -> None:
        self._connection.rollback()

    async def close(self) -> None:
        self._connection.close()

    @property
    def row_factory(self):  # type: ignore[override]
        return self._connection.row_factory

    @row_factory.setter
    def row_factory(self, factory):  # type: ignore[override]
        self._connection.row_factory = factory


class _ConnectionCoroutine:
    def __init__(self, coro: Coroutine[Any, Any, Connection]) -> None:
        self._coro = coro
        self.daemon = True

    def __await__(self):
        return self._coro.__await__()


async def _connect(database: str, **kwargs: Any) -> Connection:
    params = dict(kwargs)
    params.setdefault("check_same_thread", False)
    connection = sqlite3.connect(database, **params)
    return Connection(connection)


def connect(database: str, **kwargs: Any) -> _ConnectionCoroutine:
    return _ConnectionCoroutine(_connect(database, **kwargs))
