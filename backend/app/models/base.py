"""Base model class utilities."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class BaseModel(DeclarativeBase):
    """Declarative base class for SQLAlchemy models."""

    __abstract__ = True


# Re-export a `Base` alias for compatibility with migration tooling.
Base = BaseModel

__all__ = ["Base", "BaseModel"]
