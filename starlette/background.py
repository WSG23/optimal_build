"""Background tasks for the Starlette stub."""

from __future__ import annotations

import inspect
from typing import Any, Awaitable, Callable

__all__ = ["BackgroundTask"]


class BackgroundTask:
    """Lightweight stand-in for :class:`starlette.background.BackgroundTask`."""

    def __init__(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        self.func = func
        self.args = args
        self.kwargs = kwargs

    async def __call__(self) -> Any:
        result = self.func(*self.args, **self.kwargs)
        if inspect.isawaitable(result):
            return await result
        return result


__all__ = ["BackgroundTask"]
