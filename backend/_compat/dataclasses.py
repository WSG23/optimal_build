"""Compatibility helpers for dataclass features across Python versions."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Callable, TypeVar, dataclass_transform, overload

_T = TypeVar("_T")

__all__ = ["compat_dataclass"]


# Overloads to match dataclass signature for mypy
@overload
@dataclass_transform()
def compat_dataclass(cls: type[_T]) -> type[_T]: ...


@overload
@dataclass_transform()
def compat_dataclass(
    *,
    init: bool = True,
    repr: bool = True,
    eq: bool = True,
    order: bool = False,
    unsafe_hash: bool = False,
    frozen: bool = False,
    slots: bool = False,
) -> Callable[[type[_T]], type[_T]]: ...


@dataclass_transform()
def compat_dataclass(
    *args: Any, **kwargs: Any
) -> Callable[[type[_T]], type[_T]] | type[_T]:
    """Wrap :func:`dataclass` while ignoring unsupported keyword arguments.

    This wrapper removes the `slots` parameter on Python < 3.10 for compatibility.
    """
    if sys.version_info < (3, 10):
        kwargs.pop("slots", None)

    return dataclass(*args, **kwargs)  # type: ignore[return-value]
