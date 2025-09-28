"""Declarative mapping tools backed by the in-memory SQLAlchemy stub."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .._memory import (
    MetaData,
    RelatedList,
    RelationshipDescriptor,
    Table,
    register_model,
)

__all__ = [
    "DeclarativeBase",
    "Mapped",
    "mapped_column",
    "relationship",
    "selectinload",
]


Mapped = Any


class DeclarativeBase:
    """Base class implementing minimal declarative mapping features."""

    metadata = MetaData()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__dict__.get("__abstract__", False):
            return
        cls.__abstract__ = False
        tablename = getattr(cls, "__tablename__", cls.__name__.lower())
        cls.__tablename__ = tablename
        cls.__table__ = Table(tablename, cls)  # type: ignore[attr-defined]
        cls.__mapped_columns__ = dict(getattr(cls, "__mapped_columns__", {}))
        cls.__relationships__ = dict(getattr(cls, "__relationships__", {}))
        DeclarativeBase.metadata.sorted_tables.append(cls.__table__)
        register_model(cls, tablename)

    def __init__(self, **kwargs: Any) -> None:
        columns = getattr(self, "__mapped_columns__", {})
        relationships = getattr(self, "__relationships__", {})
        for name, column in columns.items():
            if name in kwargs:
                setattr(self, name, kwargs.pop(name))
            else:
                getattr(self, name)
        for name, descriptor in relationships.items():
            if descriptor.uselist:
                if name not in self.__dict__ or not isinstance(
                    self.__dict__[name], RelatedList
                ):
                    self.__dict__[name] = RelatedList(self, descriptor)
            else:
                self.__dict__.setdefault(name, None)
        for key, value in kwargs.items():
            setattr(self, key, value)


def mapped_column(*args: Any, **kwargs: Any):  # noqa: D401 - thin wrapper
    from .. import Column

    return Column(*args, **kwargs)


def relationship(
    *args: Any,
    back_populates: str | None = None,
    cascade: str | None = None,  # noqa: ARG001 - unused, accepted for compatibility
    uselist: bool = True,
    **kwargs: Any,
) -> RelationshipDescriptor:
    return RelationshipDescriptor(back_populates=back_populates, uselist=uselist)


@dataclass
class _LoaderOption:
    name: str

    def __call__(self, *args: Any, **kwargs: Any) -> _LoaderOption:
        return self


def selectinload(*args: Any, **kwargs: Any) -> _LoaderOption:  # noqa: D401
    return _LoaderOption("selectinload")
