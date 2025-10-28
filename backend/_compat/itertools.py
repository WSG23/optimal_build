"""Compatibility helpers for itertools across Python versions."""

from __future__ import annotations

import sys
from itertools import zip_longest
from typing import Iterable, Iterator, Tuple, TypeVar

_T = TypeVar("_T")

__all__ = ["compat_zip"]


def compat_zip(
    *iterables: Iterable[_T], strict: bool = False
) -> Iterator[Tuple[_T, ...]]:
    """Mirror :func:`zip` with the ``strict`` keyword across Python versions.

    Python 3.10 introduced the ``strict`` parameter. For older interpreters we
    emulate the behaviour, raising ``ValueError`` when lengths differ and
    otherwise yielding tuples exactly as the built-in would.
    """

    if sys.version_info >= (3, 10):
        return zip(*iterables, strict=strict)

    if not strict:
        return zip(*iterables, strict=False)

    sentinel = object()

    def _generator() -> Iterator[Tuple[_T, ...]]:
        for combo in zip_longest(*iterables, fillvalue=sentinel):
            if sentinel in combo:
                if any(value is not sentinel for value in combo):
                    raise ValueError("zip() argument lengths differ")
                return
            yield combo  # type: ignore[return-value]

    return _generator()
