"""Minimal implementation of :mod:`starlette.background`."""

from __future__ import annotations

import inspect
from typing import Any, Awaitable, Callable


class BackgroundTask:
    """Represents work to be executed after the response is sent."""

    def __init__(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        self._func = func
        self._args = args
        self._kwargs = kwargs

    async def __call__(self) -> None:
        result = self._func(*self._args, **self._kwargs)
        if inspect.isawaitable(result):  # pragma: no cover - rarely used
            await result


__all__ = ["BackgroundTask"]
