"""Shared Geometry column shim used by jurisdiction property models.

At type-check time ``Geometry`` is exposed as ``Any`` so mypy does not have to
reconcile the two runtime branches (real ``geoalchemy2.Geometry`` subclass vs
the inert ``UserDefinedType`` stub used in lightweight test environments). At
runtime we pick whichever is available without any suppression comments.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    Geometry: Any = Any
else:
    try:
        from geoalchemy2 import Geometry as _Geometry

        class Geometry(_Geometry):
            cache_ok = True

    except ModuleNotFoundError:  # pragma: no cover - optional dependency fallback
        from sqlalchemy.types import UserDefinedType

        class Geometry(UserDefinedType):
            """Minimal stub emulating geoalchemy2.Geometry when unavailable."""

            cache_ok = True

            def __init__(self, *args: object, **kwargs: object) -> None:
                self.args = args
                self.kwargs = kwargs

            def get_col_spec(self, **_: object) -> str:
                return "GEOMETRY"


__all__ = ["Geometry"]
