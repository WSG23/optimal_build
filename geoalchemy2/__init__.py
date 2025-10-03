"""Minimal geoalchemy2 compatibility shim for test environments."""

from __future__ import annotations

from sqlalchemy.types import UserDefinedType


class Geometry(UserDefinedType):
    """Placeholder geometry column type."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.args = args
        self.kwargs = kwargs

    def get_col_spec(self, **_kwargs: object) -> str:
        return "GEOMETRY"


__all__ = ["Geometry"]
