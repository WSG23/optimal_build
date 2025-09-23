"""Lightweight Prefect flow shim used in offline environments."""

from __future__ import annotations

from typing import Any, Callable, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])


def _attach_with_options(func: F) -> F:
    """Attach a ``with_options`` helper expected by Prefect tooling."""

    def _with_options(*_: Any, **__: Any) -> F:
        return func

    setattr(func, "with_options", _with_options)  # type: ignore[attr-defined]
    if not hasattr(func, "name"):
        setattr(func, "name", func.__name__)
    return func


def flow(_func: F | None = None, *, name: str | None = None) -> F | Callable[[F], F]:
    """Return a no-op decorator that preserves the wrapped coroutine."""

    def decorator(func: F) -> F:
        wrapped = _attach_with_options(func)
        if name:
            setattr(wrapped, "name", name)
        return wrapped

    if _func is not None and callable(_func):
        return decorator(cast(F, _func))
    return decorator


def task(_func: F | None = None, *, name: str | None = None) -> F | Callable[[F], F]:
    """Return a no-op decorator mimicking :func:`prefect.task`."""

    def decorator(func: F) -> F:
        wrapped = _attach_with_options(func)
        if name:
            setattr(wrapped, "name", name)
        return wrapped

    if _func is not None and callable(_func):
        return decorator(cast(F, _func))
    return decorator


__all__ = ["flow", "task"]
