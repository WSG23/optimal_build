"""Lightweight Prefect compatibility layer for offline environments."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, cast

__all__ = ["flow", "task"]

F = TypeVar("F", bound=Callable[..., Any])


def _attach_with_options(func: F) -> F:
    """Attach a ``with_options`` helper expected by Prefect tooling."""

    def _with_options(*_: Any, **__: Any) -> F:
        return func

    func.with_options = _with_options  # type: ignore[attr-defined]
    if not hasattr(func, "name"):
        func.name = func.__name__
    return func


def _apply_prefect_metadata(func: F, *, name: str | None) -> F:
    wrapped = _attach_with_options(func)
    if name:
        wrapped.name = name
    return wrapped


def _decorator_factory(name: str | None) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        return _apply_prefect_metadata(func, name=name)

    return decorator


def flow(_func: F | None = None, *, name: str | None = None) -> F | Callable[[F], F]:
    """Return a no-op decorator mimicking :func:`prefect.flow`."""

    decorator = _decorator_factory(name)
    if _func is not None and callable(_func):
        return decorator(cast(F, _func))
    return decorator


def task(_func: F | None = None, *, name: str | None = None) -> F | Callable[[F], F]:
    """Return a no-op decorator mimicking :func:`prefect.task`."""

    decorator = _decorator_factory(name)
    if _func is not None and callable(_func):
        return decorator(cast(F, _func))
    return decorator
