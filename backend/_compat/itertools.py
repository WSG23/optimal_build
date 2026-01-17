"""Compatibility helpers for itertools across Python versions."""

from __future__ import annotations

from itertools import zip_longest
from typing import Iterable, Iterator, Tuple, TypeVar

_T = TypeVar("_T")

__all__ = ["compat_zip"]


def compat_zip(
    *iterables: Iterable[_T], strict: bool = False
) -> Iterator[Tuple[_T, ...]]:
    """Mirror :func:`zip` with an optional ``strict`` parameter."""

    if not strict:
        return zip(*iterables, strict=False)

    sentinel = object()

    def _generator() -> Iterator[Tuple[_T, ...]]:
        for combo in zip_longest(*iterables, fillvalue=sentinel):
            if sentinel in combo:
                if any(value is not sentinel for value in combo):
                    raise ValueError("zip() argument lengths differ")
                return
            yield combo  # type: ignore[misc]

    return _generator()
