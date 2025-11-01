"""Asyncio helpers for the in-memory SQLAlchemy stub."""

from __future__ import annotations

from typing import Any

from .. import (
    AsyncEngine as _BaseAsyncEngine,
    AsyncSession as _BaseAsyncSession,
    _Result as _BaseResult,
    create_async_engine as _create_async_engine,
)

__all__ = [
    "AsyncEngine",
    "AsyncSession",
    "AsyncResult",
    "ScalarResult",
    "async_sessionmaker",
    "create_async_engine",
]


class ScalarResult(_BaseResult):
    """Container exposing scalar-oriented result helpers."""

    def scalars(self) -> "ScalarResult":  # type: ignore[override]
        return self


class AsyncResult(_BaseResult):
    """Async-compatible result wrapper."""

    def scalars(self) -> ScalarResult:  # type: ignore[override]
        result = super().scalars()
        return ScalarResult(getattr(result, "_values", []))


class AsyncSession(_BaseAsyncSession):
    """Async session interacting with the shared in-memory database."""

    async def execute(self, statement: Any, *args: Any, **kwargs: Any) -> AsyncResult:  # type: ignore[override]
        base_result = await super().execute(statement, *args, **kwargs)
        return AsyncResult(getattr(base_result, "_values", []))

    async def scalar(self, statement: Any, *args: Any, **kwargs: Any) -> Any:  # type: ignore[override]
        result = await self.execute(statement, *args, **kwargs)
        return result.scalar_one_or_none()


class _AsyncSessionContext:
    def __init__(self, args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
        self._args = args
        self._kwargs = kwargs
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> AsyncSession:
        self._session = AsyncSession(*self._args, **self._kwargs)
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        if self._session is not None:
            await self._session.close()
        self._session = None


class async_sessionmaker:  # type: ignore[misc]
    """Factory returning :class:`AsyncSession` instances."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._args = args
        self._kwargs = kwargs

    def __call__(self, *args: Any, **kwargs: Any) -> _AsyncSessionContext:
        if args or kwargs:
            combined_kwargs = dict(self._kwargs)
            combined_kwargs.update(kwargs)
            combined_args = tuple(self._args) + tuple(args)
        else:
            combined_args = tuple(self._args)
            combined_kwargs = dict(self._kwargs)
        return _AsyncSessionContext(combined_args, combined_kwargs)

    @classmethod
    def __class_getitem__(cls, _item: Any) -> type["async_sessionmaker"]:  # noqa: D401
        return cls


AsyncEngine = _BaseAsyncEngine
create_async_engine = _create_async_engine


class _AsyncioNamespace:
    def __init__(self) -> None:
        self.greenlet_spawn = None


engine = _AsyncioNamespace()
result = _AsyncioNamespace()
session = _AsyncioNamespace()
