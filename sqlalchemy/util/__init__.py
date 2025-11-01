"""Minimal ``sqlalchemy.util`` stub used in the test suite."""

from __future__ import annotations


class _ConcurrencyNamespace:
    """Namespace mirroring the subset of ``sqlalchemy.util.concurrency`` used."""

    def __init__(self) -> None:
        self.have_greenlet = False


concurrency = _ConcurrencyNamespace()


__all__ = ["concurrency"]
