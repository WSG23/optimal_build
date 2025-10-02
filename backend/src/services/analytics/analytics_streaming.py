"""Utilities for streaming analytics."""

from __future__ import annotations

from typing import Iterable, Iterator, Tuple


def stream_events(source: Iterable[Tuple[str, float]]) -> Iterator[Tuple[str, float]]:
    """Yield events from ``source`` while normalising to lowercase keys."""

    for key, value in source:
        yield key.lower(), float(value)
