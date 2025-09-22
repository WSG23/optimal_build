"""Lightweight Prefect stubs for offline testing."""

from __future__ import annotations

from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def flow(_func: F | None = None, *, name: str | None = None) -> Callable[[F], F] | F:
    """Return a no-op decorator mimicking `prefect.flow`."""

    def decorator(func: F) -> F:
        return func

    if _func is not None and callable(_func):
        return decorator(_func)
    return decorator


def task(_func: F | None = None, *, name: str | None = None) -> Callable[[F], F] | F:
    """Return a no-op decorator mimicking `prefect.task`."""

    def decorator(func: F) -> F:
        return func

    if _func is not None and callable(_func):
        return decorator(_func)
    return decorator


__all__ = ["flow", "task"]
