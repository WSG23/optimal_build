"""Lightweight concurrency helpers mirroring SQLAlchemy's util module."""

from __future__ import annotations

import asyncio
import sys
from typing import Any, Awaitable, Callable, TypeVar

__all__ = [
    "AsyncAdaptedLock",
    "await_only",
    "await_fallback",
    "greenlet_spawn",
    "have_greenlet",
]

T = TypeVar("T")


class AsyncAdaptedLock:
    """Minimal async lock used by SQLAlchemy's async helpers."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> "AsyncAdaptedLock":
        await self._lock.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self._lock.release()


def await_only(value: Awaitable[T] | T) -> Awaitable[T] | T:
    return value


def await_fallback(value: Awaitable[T] | T) -> Awaitable[T] | T:
    return value


async def greenlet_spawn(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    if asyncio.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    return await asyncio.to_thread(func, *args, **kwargs)


have_greenlet = True

# Provide module-style alias expected by ``from sqlalchemy.util import concurrency``.
concurrency = sys.modules[__name__]
