"""Base model class utilities."""

from sqlalchemy.orm import DeclarativeBase


class BaseModel(DeclarativeBase):
    """Declarative base class for SQLAlchemy models."""

    pass


# Re-export a `Base` alias for compatibility with migration tooling.
Base = BaseModel
