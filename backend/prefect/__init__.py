"""Minimal Prefect compatibility layer for tests."""

from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable, TypeVar

__all__ = ["flow"]

F = TypeVar("F", bound=Callable[..., Any])


def flow(_func: F | None = None, *, name: str | None = None) -> Callable[[F], F] | F:
    def decorator(func: F) -> F:
        flow_name = name or getattr(func, "__name__", "flow")
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                return await func(*args, **kwargs)

            setattr(async_wrapper, "flow_name", flow_name)
            return async_wrapper  # type: ignore[return-value]

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        setattr(wrapper, "flow_name", flow_name)
        return wrapper  # type: ignore[return-value]

    if _func is None:
        return decorator
    return decorator(_func)
