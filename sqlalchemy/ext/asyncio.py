"""Asyncio helpers for the SQLAlchemy stub."""

from __future__ import annotations

from typing import Any, Iterable

from .. import root_missing_error

__all__ = [
    "AsyncEngine",
    "AsyncSession",
    "AsyncResult",
    "async_sessionmaker",
    "create_async_engine",
]


class AsyncResult:
    """Placeholder representing the result of an async database operation."""

    async def scalar_one_or_none(self) -> Any:
        raise root_missing_error("AsyncResult.scalar_one_or_none")

    async def scalars(self) -> "AsyncResult":
        raise root_missing_error("AsyncResult.scalars")

    def all(self) -> list[Any]:
        raise root_missing_error("AsyncResult.all")


class AsyncSession:
    """Stub of :class:`sqlalchemy.ext.asyncio.AsyncSession`."""

    async def execute(self, *args: Any, **kwargs: Any) -> AsyncResult:
        raise root_missing_error("AsyncSession.execute")

    async def scalar(self, *args: Any, **kwargs: Any) -> Any:
        raise root_missing_error("AsyncSession.scalar")

    async def flush(self) -> None:
        raise root_missing_error("AsyncSession.flush")

    async def commit(self) -> None:
        raise root_missing_error("AsyncSession.commit")

    async def rollback(self) -> None:
        raise root_missing_error("AsyncSession.rollback")

    async def refresh(self, instance: Any) -> None:
        raise root_missing_error("AsyncSession.refresh")

    def add(self, instance: Any) -> None:
        raise root_missing_error("AsyncSession.add")

    def add_all(self, instances: Iterable[Any]) -> None:
        raise root_missing_error("AsyncSession.add_all")

    async def close(self) -> None:
        raise root_missing_error("AsyncSession.close")

    async def __aenter__(self) -> "AsyncSession":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()


class _AsyncEngineContext:
    async def __aenter__(self) -> Any:
        raise root_missing_error("AsyncEngine.begin")

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class AsyncEngine:
    """Placeholder for :class:`sqlalchemy.ext.asyncio.AsyncEngine`."""

    def begin(self) -> _AsyncEngineContext:
        return _AsyncEngineContext()

    async def dispose(self) -> None:
        raise root_missing_error("AsyncEngine.dispose")


class _AsyncSessionContext:
    async def __aenter__(self) -> AsyncSession:
        raise root_missing_error("AsyncSession")

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class _AsyncSessionFactory:
    def __call__(self, *args: Any, **kwargs: Any) -> _AsyncSessionContext:
        return _AsyncSessionContext()


class _AsyncSessionmaker:
    def __call__(self, *args: Any, **kwargs: Any) -> _AsyncSessionFactory:
        return _AsyncSessionFactory()

    def __getitem__(self, _item: Any) -> "_AsyncSessionmaker":
        return self


async_sessionmaker = _AsyncSessionmaker()


def create_async_engine(*args: Any, **kwargs: Any) -> AsyncEngine:
    return AsyncEngine()
