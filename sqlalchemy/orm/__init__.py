"""ORM related helpers for the SQLAlchemy stub."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

__all__ = [
    "DeclarativeBase",
    "Mapped",
    "mapped_column",
    "relationship",
    "selectinload",
]

T = TypeVar("T")


class _Statement:
    """Simple chainable object used to mimic SQL expressions."""

    def __init__(self, description: str) -> None:
        self.description = description

    def where(self, *args: Any, **kwargs: Any) -> "_Statement":  # noqa: D401 - fluent API
        return self

    def limit(self, *args: Any, **kwargs: Any) -> "_Statement":
        return self

    def order_by(self, *args: Any, **kwargs: Any) -> "_Statement":
        return self

    def options(self, *args: Any, **kwargs: Any) -> "_Statement":
        return self


class _MetaData:
    """Minimal metadata container tracking registered tables."""

    def __init__(self) -> None:
        self.sorted_tables: list[_Table] = []

    def create_all(self, *args: Any, **kwargs: Any) -> None:
        # No-op to satisfy test environments without SQLAlchemy.
        return None


@dataclass
class _Table:
    name: str

    def delete(self) -> _Statement:
        return _Statement(f"delete {self.name}")


class DeclarativeBase:
    """Very small subset of SQLAlchemy's declarative base."""

    metadata = _MetaData()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        table = _Table(cls.__name__)
        cls.__table__ = table  # type: ignore[attr-defined]
        DeclarativeBase.metadata.sorted_tables.append(table)


Mapped = Any


def mapped_column(*args: Any, **kwargs: Any) -> Any:
    """Return a placeholder for a mapped column attribute."""

    return None


def relationship(*args: Any, **kwargs: Any) -> Any:
    """Return a placeholder representing an ORM relationship."""

    return None


def selectinload(*args: Any, **kwargs: Any) -> _Statement:
    """Return a placeholder loader option."""

    return _Statement("selectinload")
