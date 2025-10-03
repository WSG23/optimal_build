"""Compatibility helpers for dataclass features across Python versions."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

_T = TypeVar("_T")

__all__ = ["compat_dataclass"]


def compat_dataclass(*args: Any, **kwargs: Any) -> Callable[[type[_T]], type[_T]]:
    """Wrap :func:`dataclass` while ignoring unsupported keyword arguments."""

    if sys.version_info < (3, 10):
        kwargs.pop("slots", None)

    return dataclass(*args, **kwargs)
