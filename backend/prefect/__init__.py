"""Lightweight Prefect stubs for offline testing."""

from __future__ import annotations

from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def flow(name: str | None = None) -> Callable[[F], F]:
    """Return a no-op decorator mimicking `prefect.flow`."""

    def decorator(func: F) -> F:
        return func

    return decorator
