"""Custom SQLAlchemy types for cross-database compatibility."""

from __future__ import annotations

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON, TypeDecorator


class FlexibleJSONB(TypeDecorator):
    """JSONB type that falls back to SQLite's JSON implementation."""

    impl = JSONB
    cache_ok = True

    def load_dialect_impl(self, dialect):  # type: ignore[override]
        if dialect.name == "sqlite":
            return dialect.type_descriptor(JSON())
        return dialect.type_descriptor(JSONB())


__all__ = ["FlexibleJSONB"]
