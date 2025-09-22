"""Base model class utilities."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict

from sqlalchemy.orm import DeclarativeBase


class BaseModel(DeclarativeBase):
    """Declarative base class for SQLAlchemy models."""

    __abstract__ = True

    def as_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable representation of the model instance."""

        def normalise(value: Any) -> Any:
            if isinstance(value, Decimal):
                return float(value)
            if isinstance(value, (datetime, date)):
                return value.isoformat()
            return value

        data: Dict[str, Any] = {}
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

__all__ = ["Base", "BaseModel"]
