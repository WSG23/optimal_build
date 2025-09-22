"""ORM helpers for the in-memory SQLAlchemy stub."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Type

from .. import Column, _Table, register_table

__all__ = [
    "DeclarativeBase",
    "Mapped",
    "mapped_column",
    "relationship",
    "selectinload",
]


class _MetaData:
    """Minimal metadata container tracking registered tables."""

    def __init__(self) -> None:
        self.sorted_tables: list[_Table] = []

    def _register(self, table: _Table) -> None:
        if table not in self.sorted_tables:
            self.sorted_tables.append(table)

    def create_all(self, connection: Any | None = None) -> None:
        return None


class DeclarativeBase:
    """Very small subset of SQLAlchemy's declarative base."""

    metadata = _MetaData()
    __columns__: Dict[str, Column] = {}
    __primary_key__: str = "id"

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        columns: Dict[str, Column] = {}
        for base in reversed(cls.__mro__[1:]):
            base_columns = getattr(base, "__columns__", None)
            if isinstance(base_columns, dict):
                columns.update(base_columns)
        for name, attr in cls.__dict__.items():
            if isinstance(attr, Column):
                attr._bind(cls, name)
                columns[name] = attr
        cls.__columns__ = dict(columns)
        primary = next((name for name, column in columns.items() if column.primary_key), None)
        if primary is None and columns:
            primary = next(iter(columns.keys()))
        cls.__primary_key__ = primary or "id"
        table_name = getattr(cls, "__tablename__", cls.__name__)
        table = _Table(table_name, cls)
        cls.__table__ = table  # type: ignore[attr-defined]
        register_table(cls, table)
        DeclarativeBase.metadata._register(table)

    def __init__(self, **kwargs: Any) -> None:
        for name, column in self.__columns__.items():
            if name in kwargs:
                value = kwargs.pop(name)
            else:
                value = column._resolve_default() if hasattr(column, "_resolve_default") else None
            setattr(self, name, value)
        for key, value in kwargs.items():
            setattr(self, key, value)


Mapped = Any


def mapped_column(*args: Any, **kwargs: Any) -> Any:
    """Return a placeholder for a mapped column attribute."""

    return None


def relationship(*args: Any, **kwargs: Any) -> Any:
    """Return a placeholder representing an ORM relationship."""

    return None


@dataclass
class _LoaderOption:
    name: str

    def __call__(self, *args: Any, **kwargs: Any) -> "_LoaderOption":
        return self


def selectinload(*args: Any, **kwargs: Any) -> _LoaderOption:
    """Return a placeholder loader option."""

    return _LoaderOption("selectinload")


__all__ = ["DeclarativeBase", "Mapped", "mapped_column", "relationship", "selectinload"]
