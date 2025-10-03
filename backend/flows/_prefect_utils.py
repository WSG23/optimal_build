"""Shared Prefect flow utilities."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar, cast

_ResultT = TypeVar("_ResultT")

__all__ = ["resolve_flow_callable"]


def resolve_flow_callable(flow_like: object) -> Callable[..., Awaitable[_ResultT]]:
    """Return the coroutine function wrapped by Prefect's decorators."""

    for attr in ("__wrapped__", "fn"):
        candidate = getattr(flow_like, attr, None)
        if callable(candidate):
            return cast(Callable[..., Awaitable[_ResultT]], candidate)
    if callable(flow_like):
        return cast(Callable[..., Awaitable[_ResultT]], flow_like)
    raise TypeError(f"Expected a callable Prefect flow, received {flow_like!r}")
