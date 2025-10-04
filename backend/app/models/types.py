"""Custom SQLAlchemy types for cross-database compatibility."""

from __future__ import annotations

from typing import Protocol, cast

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON, TypeDecorator


class _SupportsTypeDescriptor(Protocol):
    """Protocol representing the subset of dialect behaviour we rely on."""

    name: str

    def type_descriptor(self, type_: object) -> object:
        ...


class FlexibleJSONB(TypeDecorator):
    """JSONB type that falls back to SQLite's JSON implementation."""

    impl: object = JSONB
    cache_ok = True

    def load_dialect_impl(self, dialect: object) -> object:
        typed_dialect = cast(_SupportsTypeDescriptor, dialect)
        if typed_dialect.name == "sqlite":
            return typed_dialect.type_descriptor(JSON())
        return typed_dialect.type_descriptor(JSONB())


__all__ = ["FlexibleJSONB"]
