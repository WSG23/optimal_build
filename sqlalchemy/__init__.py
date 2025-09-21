"""Minimal SQLAlchemy stub used for test environments without the dependency."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Iterable

__all__ = [
    "Column",
    "DateTime",
    "Integer",
    "Select",
    "String",
    "Text",
    "select",
    "text",
    "func",
    "pool",
]


class _MissingSQLAlchemy(RuntimeError):
    """Error raised when a SQLAlchemy feature is used without the dependency."""

    def __init__(self, feature: str) -> None:
        super().__init__(
            "SQLAlchemy is required for "
            f"{feature}. Install the 'sqlalchemy' package to enable full functionality."
        )


class _Type:
    """Lightweight placeholder for SQLAlchemy type objects."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs


class Integer(_Type):
    """Placeholder for :class:`sqlalchemy.Integer`."""


class String(_Type):
    """Placeholder for :class:`sqlalchemy.String`."""


class Text(_Type):
    """Placeholder for :class:`sqlalchemy.Text`."""


class DateTime(_Type):
    """Placeholder for :class:`sqlalchemy.DateTime`."""


class Column:
    """Simplified representation of :class:`sqlalchemy.Column`."""

    def __init__(self, column_type: Any, *args: Any, **kwargs: Any) -> None:
        self.type = column_type
        self.args = args
        self.kwargs = kwargs


@dataclass
class _TextClause:
    text: str

    def bindparams(self, *args: Any, **kwargs: Any) -> "_TextClause":
        return self


class Select:
    """Chainable stub mimicking :class:`sqlalchemy.sql.Select`."""

    def __init__(self, entities: Iterable[Any]) -> None:
        self.entities = tuple(entities)
        self._modifiers: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def _clone(self) -> "Select":
        clone = Select(self.entities)
        clone._modifiers = list(self._modifiers)
        return clone

    def where(self, *criteria: Any) -> "Select":
        stmt = self._clone()
        stmt._modifiers.append(("where", criteria, {}))
        return stmt

    def limit(self, value: int) -> "Select":
        stmt = self._clone()
        stmt._modifiers.append(("limit", (value,), {}))
        return stmt

    def offset(self, value: int) -> "Select":
        stmt = self._clone()
        stmt._modifiers.append(("offset", (value,), {}))
        return stmt

    def order_by(self, *criteria: Any) -> "Select":
        stmt = self._clone()
        stmt._modifiers.append(("order_by", criteria, {}))
        return stmt

    def options(self, *opts: Any) -> "Select":
        stmt = self._clone()
        stmt._modifiers.append(("options", opts, {}))
        return stmt

    def join(self, *args: Any, **kwargs: Any) -> "Select":
        stmt = self._clone()
        stmt._modifiers.append(("join", args, kwargs))
        return stmt

    def outerjoin(self, *args: Any, **kwargs: Any) -> "Select":
        stmt = self._clone()
        stmt._modifiers.append(("outerjoin", args, kwargs))
        return stmt


def select(*entities: Any) -> Select:
    """Return a chainable :class:`Select` stub."""

    return Select(entities)


def text(statement: str) -> _TextClause:
    """Return a placeholder for :func:`sqlalchemy.text`."""

    return _TextClause(statement)


class _FunctionCall:
    """Placeholder representing a lazily evaluated SQL function call."""

    def __init__(self, name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
        self.name = name
        self.args = args
        self.kwargs = kwargs

    def label(self, _label: str) -> "_FunctionCall":  # noqa: D401 - fluent API
        return self


class _SQLFunction:
    """Callable proxy returned for attributes accessed via :data:`func`."""

    def __init__(self, name: str) -> None:
        self._name = name

    def __call__(self, *args: Any, **kwargs: Any) -> _FunctionCall:
        return _FunctionCall(self._name, args, kwargs)


class _FuncProxy:
    """Object returning lightweight SQL function call placeholders."""

    def __getattr__(self, name: str) -> _SQLFunction:  # noqa: D401 - simple factory
        return _SQLFunction(name)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        raise _MissingSQLAlchemy("func")


func = _FuncProxy()


pool = SimpleNamespace(NullPool=object())


root_missing_error = _MissingSQLAlchemy

class _GenericConstruct:
    """Generic stand-in for SQLAlchemy constructs instantiated at import time."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs


_GENERATED_CONSTRUCTS: dict[str, type[_GenericConstruct]] = {}


def __getattr__(name: str) -> Any:  # noqa: D401 - module level dynamic fallback
    if name in _GENERATED_CONSTRUCTS:
        return _GENERATED_CONSTRUCTS[name]
    if name and name[0].isupper():
        placeholder = type(name, (_GenericConstruct,), {})
        _GENERATED_CONSTRUCTS[name] = placeholder
        return placeholder
    raise AttributeError(f"module 'sqlalchemy' has no attribute {name!r}")


# Re-export commonly imported submodules so that ``import sqlalchemy.ext.asyncio`` works
from . import engine  # noqa: E402  (imported for side effects)
from . import ext  # noqa: E402  (imported for side effects)
from . import orm  # noqa: E402  (imported for side effects)
from . import sql  # noqa: E402  (imported for side effects)
from . import types  # noqa: E402  (imported for side effects)
from . import dialects  # noqa: E402  (imported for side effects)

__all__.extend(["engine", "ext", "orm", "sql", "types", "dialects", "root_missing_error"])
