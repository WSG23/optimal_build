"""In-memory SQLAlchemy stub used for offline test execution."""

from __future__ import annotations

from dataclasses import dataclass
import inspect
from types import SimpleNamespace
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Type

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


class Condition:
    """Simple callable condition used to filter in-memory rows."""

    def __init__(self, predicate: Callable[[Any], bool]) -> None:
        self._predicate = predicate

    def evaluate(self, obj: Any) -> bool:
        try:
            return bool(self._predicate(obj))
        except Exception:
            return False


class Column:
    """Simplified representation of :class:`sqlalchemy.Column`."""

    def __init__(
        self,
        column_type: Any,
        *args: Any,
        primary_key: bool = False,
        default: Any = None,
        nullable: bool | None = None,
        index: bool | None = None,
        unique: bool | None = None,
        **kwargs: Any,
    ) -> None:
        self.type = column_type
        self.args = args
        self.kwargs = kwargs
        self.primary_key = primary_key
        self.default = default
        self.nullable = nullable
        self.index = index
        self.unique = unique
        self.name: str | None = None
        self.model: Type[Any] | None = None

    def _bind(self, model: Type[Any], name: str) -> None:
        self.model = model
        self.name = name

    def __get__(self, instance: Any, owner: Type[Any]) -> Any:
        if instance is None:
            if self.name is None:
                raise AttributeError("Column descriptor accessed before binding to a model")
            return ColumnExpression(owner, self.name)
        return instance.__dict__.get(self.name, self._resolve_default())

    def __set__(self, instance: Any, value: Any) -> None:
        if self.name is None:
            raise AttributeError("Column descriptor accessed before binding to a model")
        instance.__dict__[self.name] = value

    def _resolve_default(self) -> Any:
        if callable(self.default):
            return self.default()
        return self.default


class ColumnExpression:
    """Column bound to a declarative model used in ``Select`` statements."""

    def __init__(self, model: Type[Any], name: str) -> None:
        self.model = model
        self.name = name

    def get_value(self, obj: Any) -> Any:
        return getattr(obj, self.name, None)

    def __eq__(self, other: Any) -> Condition:  # type: ignore[override]
        return Condition(lambda obj: getattr(obj, self.name, None) == other)

    def in_(self, values: Iterable[Any]) -> Condition:
        values_set = {value for value in values}
        return Condition(lambda obj: getattr(obj, self.name, None) in values_set)


@dataclass
class _TextClause:
    text: str

    def bindparams(self, *args: Any, **kwargs: Any) -> "_TextClause":
        return self


@dataclass
class _DeleteStatement:
    model: Type[Any]


@dataclass
class _Table:
    name: str
    model: Type[Any]

    def delete(self) -> _DeleteStatement:
        return _DeleteStatement(self.model)


class Select:
    """In-memory representation of a ``SELECT`` statement."""

    def __init__(self, entities: Sequence[Any]) -> None:
        self.entities = tuple(entities)
        self._where: List[Any] = []
        self._limit: Optional[int] = None
        self._offset: int = 0
        self._from: Optional[Type[Any]] = None

    def _clone(self) -> "Select":
        clone = Select(self.entities)
        clone._where = list(self._where)
        clone._limit = self._limit
        clone._offset = self._offset
        clone._from = self._from
        return clone

    def where(self, *criteria: Any) -> "Select":
        stmt = self._clone()
        for criterion in criteria:
            if criterion is not None:
                stmt._where.append(criterion)
        return stmt

    def limit(self, value: int) -> "Select":
        stmt = self._clone()
        stmt._limit = value
        return stmt

    def offset(self, value: int) -> "Select":
        stmt = self._clone()
        stmt._offset = value
        return stmt

    def order_by(self, *criteria: Any) -> "Select":
        return self._clone()

    def options(self, *opts: Any) -> "Select":
        return self._clone()

    def join(self, *args: Any, **kwargs: Any) -> "Select":
        return self._clone()

    def outerjoin(self, *args: Any, **kwargs: Any) -> "Select":
        return self._clone()

    def select_from(self, model: Type[Any]) -> "Select":
        stmt = self._clone()
        stmt._from = model
        return stmt

    def _resolve_model(self) -> Optional[Type[Any]]:
        for entity in self.entities:
            if isinstance(entity, ColumnExpression):
                return entity.model
            if inspect.isclass(entity) and hasattr(entity, "__columns__"):
                return entity
        return self._from

    def _run(self, database: "_InMemoryDatabase") -> Tuple[List[Any], bool]:
        model = self._resolve_model()
        if model is None:
            return [], True
        rows = list(database.all(model))
        for criterion in self._where:
            if isinstance(criterion, Condition):
                rows = [row for row in rows if criterion.evaluate(row)]
            elif callable(criterion):
                rows = [row for row in rows if criterion(row)]
        if self._offset:
            rows = rows[self._offset :]
        if self._limit is not None:
            rows = rows[: self._limit]
        if len(self.entities) == 1:
            entity = self.entities[0]
            if isinstance(entity, ColumnExpression):
                values = [entity.get_value(row) for row in rows]
            else:
                values = rows
            return values, True
        data: List[Any] = []
        for row in rows:
            entry: List[Any] = []
            for entity in self.entities:
                if isinstance(entity, ColumnExpression):
                    entry.append(entity.get_value(row))
                elif isinstance(entity, type) and isinstance(row, entity):
                    entry.append(row)
                else:
                    entry.append(None)
            data.append(tuple(entry))
        return data, False


def select(*entities: Any) -> Select:
    """Return an in-memory ``Select`` construct."""

    return Select(entities)


def text(statement: str) -> _TextClause:
    """Return a lightweight text clause placeholder."""

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
        return _FunctionCall("func", args, kwargs)


func = _FuncProxy()


pool = SimpleNamespace(NullPool=object())


root_missing_error = None


_GENERATED_CONSTRUCTS: Dict[str, type] = {}
_MODEL_TABLES: Dict[Type[Any], _Table] = {}
_TABLE_NAME_MAP: Dict[str, Type[Any]] = {}


def register_table(model: Type[Any], table: _Table) -> None:
    """Register a model-to-table mapping for the in-memory database."""

    _MODEL_TABLES[model] = table
    _TABLE_NAME_MAP[table.name] = model


def get_table(model: Type[Any]) -> Optional[_Table]:
    return _MODEL_TABLES.get(model)


def get_model_from_table(name: str) -> Optional[Type[Any]]:
    return _TABLE_NAME_MAP.get(name)


def __getattr__(name: str) -> Any:  # noqa: D401 - module level dynamic fallback
    if name in _GENERATED_CONSTRUCTS:
        return _GENERATED_CONSTRUCTS[name]
    if name and name[0].isupper():
        placeholder = type(name, (_Type,), {})
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
