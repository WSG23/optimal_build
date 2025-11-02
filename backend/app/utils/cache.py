"""Lightweight asynchronous caching primitives."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Dict, Hashable, Tuple

__all__ = ["TTLCache"]


class TTLCache:
    """Simple time-based cache for async workflows.

    The cache stores values for ``ttl_seconds`` and returns deep copies when a
    ``copy`` callable is provided to avoid callers mutating the cached entry.
    """

    def __init__(
        self,
        ttl_seconds: float,
        *,
        copy: Callable[[Any], Any] | None = None,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self._ttl = float(ttl_seconds)
        self._copy = copy
        self._store: Dict[Hashable, Tuple[float, Any]] = {}
        self._lock = asyncio.Lock()

    def _clone(self, value: Any) -> Any:
        if self._copy is None:
            return value
        return self._copy(value)

    async def get(self, key: Hashable) -> Any | None:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at <= time.monotonic():
                self._store.pop(key, None)
                return None
            return self._clone(value)

    async def set(self, key: Hashable, value: Any) -> None:
        async with self._lock:
            self._store[key] = (time.monotonic() + self._ttl, self._clone(value))

    async def invalidate(self, key: Hashable) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()
