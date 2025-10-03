"""Stub geoalchemy2 elements module."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WKTElement:
    """Minimal WKT element used for geometry inserts."""

    data: str
    srid: int | None = None

    def __str__(self) -> str:  # pragma: no cover - simple helper
        return self.data


__all__ = ["WKTElement"]
