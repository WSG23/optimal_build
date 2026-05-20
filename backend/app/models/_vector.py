"""Vector embedding column shim for pgvector with SQLite fallback.

At type-check time ``Vector`` is exposed as ``Any`` so mypy does not have to
reconcile the two runtime branches (real ``pgvector.sqlalchemy.Vector`` vs the
inert ``UserDefinedType`` stub used in lightweight test environments). At
runtime we pick whichever is available without suppression comments.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    Vector: Any = Any
    HAS_PGVECTOR = False
else:
    try:
        from pgvector.sqlalchemy import Vector as _Vector

        class Vector(_Vector):
            cache_ok = True

        HAS_PGVECTOR = True

    except ModuleNotFoundError:  # pragma: no cover - optional dependency fallback
        from sqlalchemy.types import UserDefinedType

        class Vector(UserDefinedType):
            """Minimal stub emulating pgvector.Vector when unavailable.

            Stores as ``TEXT`` on non-Postgres backends; values pass through unchanged so
            tests do not need pgvector installed.
            """

            cache_ok = True

            def __init__(self, dim: int | None = None) -> None:
                self.dim = dim

            def get_col_spec(self, **_: object) -> str:
                return "TEXT"

        HAS_PGVECTOR = False


__all__ = ["Vector", "HAS_PGVECTOR"]
