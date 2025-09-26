"""Minimal SQLAlchemy-compatible interface backed by an in-memory store."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Iterable

from ._memory import (
    ColumnDescriptor,
    MetaData,
    SelectStatement,
    TextClause,
)

__all__ = [
    "Boolean",
    "Column",
    "DateTime",
    "Float",
    "ForeignKey",
    "Index",
    "Integer",
    "SelectStatement",
    "String",
    "Text",
    "UniqueConstraint",
    "select",
    "text",
    "func",
    "pool",
]


class _Type:
    """Lightweight placeholder for SQLAlchemy type objects."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs


class Integer(_Type):
    """Placeholder representing :class:`sqlalchemy.Integer`."""


class Float(_Type):
    """Placeholder representing :class:`sqlalchemy.Float`."""


class Boolean(_Type):
    """Placeholder representing :class:`sqlalchemy.Boolean`."""


class String(_Type):
    """Placeholder representing :class:`sqlalchemy.String`."""


class Text(_Type):
    """Placeholder representing :class:`sqlalchemy.Text`."""


class DateTime(_Type):
    """Placeholder representing :class:`sqlalchemy.DateTime`."""


class Column:
    """Factory mirroring :func:`sqlalchemy.Column` behaviour."""

    def __new__(
        cls,
        *args: Any,
        primary_key: bool = False,
        default: Any = None,
        server_default: Any = None,
        onupdate: Any = None,
        **_: Any,
    ) -> ColumnDescriptor:
        return ColumnDescriptor(
            primary_key=primary_key,
            default=default,
            server_default=server_default,
            onupdate=onupdate,
        )


class ForeignKey:
    """Placeholder for :func:`sqlalchemy.ForeignKey`."""

    def __init__(self, target: str, *args: Any, **kwargs: Any) -> None:
        self.target = target
        self.args = args
        self.kwargs = kwargs


class UniqueConstraint:
    """Placeholder for :func:`sqlalchemy.UniqueConstraint`."""

    def __init__(self, *columns: Any, **kwargs: Any) -> None:
        self.columns = columns
        self.kwargs = kwargs


class Index:
    """Placeholder for :func:`sqlalchemy.Index`."""

    def __init__(self, name: str, *columns: Any, **kwargs: Any) -> None:
        self.name = name
        self.columns = columns
        self.kwargs = kwargs


@dataclass
class _Text:
    statement: str

    def bindparams(self, *args: Any, **kwargs: Any) -> "_Text":  # noqa: D401 - passthrough
        return self


def select(*entities: Any) -> SelectStatement:
    """Return a selectable over ``entities`` evaluated against the in-memory store."""

    return SelectStatement(entities)


def text(statement: str) -> TextClause:
    """Return a :class:`TextClause` compatible object."""

    return TextClause(statement)


class _FunctionCall:
    """Placeholder object representing ``func.<name>(...)`` expressions."""

    def __init__(self, name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
        self.name = name
        self.args = args
        self.kwargs = kwargs

    def label(self, _label: str) -> "_FunctionCall":  # noqa: D401 - fluent API
        return self


class _SQLFunction:
    def __init__(self, name: str) -> None:
        self._name = name

    def __call__(self, *args: Any, **kwargs: Any) -> _FunctionCall:
        return _FunctionCall(self._name, args, kwargs)


class _FuncProxy:
    def __getattr__(self, name: str) -> _SQLFunction:  # noqa: D401 - factory proxy
        return _SQLFunction(name)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover - defensive
        raise RuntimeError("SQL function objects cannot be called directly")


func = _FuncProxy()


pool = SimpleNamespace(NullPool=object())


root_missing_error = None


__metadata__ = MetaData()


class _GenericPlaceholder:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs


_DYNAMIC_TYPES: dict[str, type] = {}


def __getattr__(name: str) -> Any:
    if name in _DYNAMIC_TYPES:
        return _DYNAMIC_TYPES[name]
    if name and name[0].isupper():
        placeholder = type(name, (_GenericPlaceholder,), {})
        _DYNAMIC_TYPES[name] = placeholder
        return placeholder
    raise AttributeError(f"module 'sqlalchemy' has no attribute {name!r}")

