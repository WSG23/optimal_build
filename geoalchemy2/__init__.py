"""Minimal geoalchemy2 compatibility shim for test environments."""

from __future__ import annotations

from sqlalchemy.types import UserDefinedType


class Geometry(UserDefinedType):
    """Placeholder geometry column type."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.args = args
        self.kwargs = kwargs

    def get_col_spec(self, **_kwargs: object) -> str:
        # SQLite does not support GEOMETRY natively; fall back to TEXT so tests
        # using the shim can create tables without PostGIS.
        return "TEXT"


class Geography(UserDefinedType):
    """Placeholder geography column type."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.args = args
        self.kwargs = kwargs

    def get_col_spec(self, **_kwargs: object) -> str:
        # SQLite does not support GEOGRAPHY natively; fall back to TEXT so tests
        # using the shim can create tables without PostGIS.
        return "TEXT"


__all__ = ["Geometry", "Geography"]
