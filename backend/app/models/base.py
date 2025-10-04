"""Base model class utilities."""

from __future__ import annotations

import uuid as uuid_module
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import CHAR, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase


class UUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's UUID type when available, otherwise uses
    CHAR(36) storing UUIDs as strings for SQLite compatibility.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value
        else:
            if isinstance(value, uuid_module.UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value
        else:
            if not isinstance(value, uuid_module.UUID):
                return uuid_module.UUID(value)
            return value


class BaseModel(DeclarativeBase):
    """Declarative base class for SQLAlchemy models."""

    __abstract__ = True

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation of the model instance."""

        def normalise(value: Any) -> Any:
            if isinstance(value, Decimal):
                return float(value)
            if isinstance(value, (datetime, date)):
                return value.isoformat()
            return value

        data: dict[str, Any] = {}
        table = getattr(self, "__table__", None)
        columns = getattr(table, "columns", None)
        if columns:
            for column in columns:
                data[column.name] = normalise(getattr(self, column.name))
            return data

        for key, value in vars(self).items():
            if key.startswith("_"):
                continue
            data[key] = normalise(value)
        return data


# Re-export a `Base` alias for compatibility with migration tooling.
Base = BaseModel


class MetadataProxy:
    """Expose ``metadata_json`` via the conventional ``metadata`` attribute."""

    def __get__(self, instance, owner):
        if instance is None:
            return BaseModel.metadata
        value = getattr(instance, "metadata_json", None)
        if value is None:
            value = {}
            instance.metadata_json = value
        return value

    def __set__(self, instance, value):
        instance.metadata_json = value or {}


__all__ = ["Base", "BaseModel", "MetadataProxy", "UUID"]
