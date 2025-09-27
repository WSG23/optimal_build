"""In-memory data structures backing the lightweight SQLAlchemy stub."""

from __future__ import annotations

import copy
import inspect
from collections.abc import Callable, Iterable, Iterator, Sequence
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Type


def _callable(value: Any) -> bool:
    """Return ``True`` if ``value`` should be invoked to obtain a default."""

    return callable(value)


def _evaluate_default(value: Any) -> Any:
    """Return the default value for a column or relationship."""

    if value is None:
        return None
    if _callable(value):
        return value()
    name = getattr(value, "name", None)
    if isinstance(name, str) and name.lower() == "now":
        return datetime.now(timezone.utc)
    return copy.deepcopy(value)


class Condition:
    """Callable predicate used to filter in-memory query results."""

    def __init__(self, attribute: str, comparator: Callable[[Any], bool]) -> None:
        self.attribute = attribute
        self._comparator = comparator

    def evaluate(self, obj: Any) -> bool:
        value = getattr(obj, self.attribute, None)
        return self._comparator(value)


class OrderBy:
    """Ordering descriptor for query evaluation."""

    def __init__(self, attribute: str, *, reverse: bool = False) -> None:
        self.attribute = attribute
        self.reverse = reverse

    def key(self, obj: Any) -> Any:
        return getattr(obj, self.attribute, None)


class ColumnAccessor:
    """Proxy returned when column attributes are accessed from the class."""

    def __init__(self, attribute: str) -> None:
        self.attribute = attribute

    def __eq__(self, other: Any) -> Condition:  # type: ignore[override]
        return Condition(self.attribute, lambda value: value == other)

    def __ne__(self, other: Any) -> Condition:  # type: ignore[override]
        return Condition(self.attribute, lambda value: value != other)

    def in_(self, options: Iterable[Any]) -> Condition:
        values = set(options)
        return Condition(self.attribute, lambda value: value in values)

    def is_(self, other: Any) -> Condition:
        return Condition(self.attribute, lambda value: value is other)

    def isnot(self, other: Any) -> Condition:
        return Condition(self.attribute, lambda value: value is not other)

    def asc(self) -> OrderBy:
        return OrderBy(self.attribute, reverse=False)

    def desc(self) -> OrderBy:
        return OrderBy(self.attribute, reverse=True)


class ColumnDescriptor:
    """Descriptor implementing attribute behaviour for mapped columns."""

    def __init__(
        self,
        *,
        primary_key: bool = False,
        default: Any = None,
        server_default: Any = None,
        onupdate: Any = None,
    ) -> None:
        self.primary_key = primary_key
        self.default = default
        self.server_default = server_default
        self.onupdate = onupdate
        self.name: str | None = None

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name
        register_column(owner, name, self)

    def _default_value(self) -> Any:
        if self.default is not None:
            return _evaluate_default(self.default)
        if self.server_default is not None:
            return _evaluate_default(self.server_default)
        return None

    def __get__(self, instance: Any, owner: type | None = None) -> Any:
        if instance is None:
            if self.name is None:
                raise AttributeError("Unbound column descriptor")
            return ColumnAccessor(self.name)
        if self.name is None:
            raise AttributeError("Column descriptor missing name")
        if self.name not in instance.__dict__:
            instance.__dict__[self.name] = self._default_value()
        return instance.__dict__[self.name]

    def __set__(self, instance: Any, value: Any) -> None:
        if self.name is None:
            raise AttributeError("Column descriptor missing name")
        instance.__dict__[self.name] = value

    def apply_onupdate(self, instance: Any) -> None:
        if self.name is None or self.onupdate is None:
            return
        instance.__dict__[self.name] = _evaluate_default(self.onupdate)


class RelatedList(List[Any]):
    """List maintaining relationship back-references."""

    def __init__(self, owner: Any, descriptor: "RelationshipDescriptor") -> None:
        super().__init__()
        self._owner = owner
        self._descriptor = descriptor

    def append(self, value: Any) -> None:  # type: ignore[override]
        if value in self:
            return
        super().append(value)
        self._set_backref(value)

    def extend(self, values: Iterable[Any]) -> None:  # type: ignore[override]
        for value in values:
            self.append(value)

    def replace(self, values: Iterable[Any]) -> None:
        del self[:]
        for value in values:
            self.append(value)

    def _append_internal(self, value: Any) -> None:
        if value in self:
            return
        super().append(value)

    def _set_backref(self, value: Any) -> None:
        back_name = self._descriptor.back_populates
        if not back_name or value is None:
            return
        target_descriptor = getattr(type(value), back_name, None)
        if isinstance(target_descriptor, RelationshipDescriptor):
            target_descriptor._set_from_backref(value, self._owner)
        else:
            setattr(value, back_name, self._owner)


class RelationshipDescriptor:
    """Descriptor providing minimal relationship semantics."""

    def __init__(
        self,
        *,
        back_populates: str | None = None,
        uselist: bool = True,
    ) -> None:
        self.back_populates = back_populates
        self.uselist = uselist
        self.name: str | None = None

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name
        register_relationship(owner, name, self)

    def __get__(self, instance: Any, owner: type | None = None) -> Any:
        if instance is None:
            return self
        if self.name is None:
            raise AttributeError("Relationship descriptor missing name")
        value = instance.__dict__.get(self.name)
        if value is None and self.uselist:
            value = RelatedList(instance, self)
            instance.__dict__[self.name] = value
        return value

    def __set__(self, instance: Any, value: Any) -> None:
        if self.name is None:
            raise AttributeError("Relationship descriptor missing name")
        if self.uselist:
            collection = instance.__dict__.get(self.name)
            if not isinstance(collection, RelatedList):
                collection = RelatedList(instance, self)
            if value is None:
                collection.replace([])
            elif isinstance(value, RelatedList):
                collection.replace(list(value))
            else:
                collection.replace(list(value))
            instance.__dict__[self.name] = collection
        else:
            instance.__dict__[self.name] = value
            if value is not None and self.back_populates:
                target_descriptor = getattr(type(value), self.back_populates, None)
                if isinstance(target_descriptor, RelationshipDescriptor):
                    target_descriptor._set_from_backref(value, instance)
                else:
                    setattr(value, self.back_populates, instance)

    def _set_from_backref(self, instance: Any, value: Any) -> None:
        if self.name is None:
            raise AttributeError("Relationship descriptor missing name")
        if self.uselist:
            collection = instance.__dict__.get(self.name)
            if not isinstance(collection, RelatedList):
                collection = RelatedList(instance, self)
                instance.__dict__[self.name] = collection
            collection._append_internal(value)
        else:
            instance.__dict__[self.name] = value


class DeleteStatement:
    """Descriptor representing ``table.delete()`` operations."""

    def __init__(self, model: type) -> None:
        self.model = model


class Table:
    """Placeholder table object stored on mapped models."""

    def __init__(self, name: str, model: type) -> None:
        self.name = name
        self.model = model

    def delete(self) -> DeleteStatement:
        return DeleteStatement(self.model)


class MetaData:
    """Simplified metadata container mimicking SQLAlchemy's interface."""

    def __init__(self) -> None:
        self.sorted_tables: List[Table] = []

    def create_all(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401 - no-op
        return None


class SelectStatement:
    """Representation of a ``select`` statement evaluated in memory."""

    def __init__(self, entities: Sequence[Any]) -> None:
        self.entities = tuple(entities)
        self._conditions: List[Condition] = []
        self._ordering: List[OrderBy] = []
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None

    def where(self, *conditions: Condition) -> "SelectStatement":
        for condition in conditions:
            if condition is not None:
                self._conditions.append(condition)
        return self

    def order_by(self, *orderings: OrderBy | ColumnAccessor) -> "SelectStatement":
        for ordering in orderings:
            if isinstance(ordering, ColumnAccessor):
                self._ordering.append(OrderBy(ordering.attribute))
            elif isinstance(ordering, OrderBy):
                self._ordering.append(ordering)
        return self

    def limit(self, value: int) -> "SelectStatement":
        self._limit = value
        return self

    def offset(self, value: int) -> "SelectStatement":
        self._offset = value
        return self

    def options(self, *args: Any, **kwargs: Any) -> "SelectStatement":  # noqa: D401
        return self

    def join(
        self, *args: Any, **kwargs: Any
    ) -> "SelectStatement":  # pragma: no cover - unused
        return self

    def outerjoin(
        self, *args: Any, **kwargs: Any
    ) -> "SelectStatement":  # pragma: no cover - unused
        return self

    def _apply(self, database: "InMemoryDatabase") -> List[Any]:
        if not self.entities:
            return []
        primary = self.entities[0]
        rows = list(database.select_all(primary))
        for condition in self._conditions:
            rows = [row for row in rows if condition.evaluate(row)]
        for ordering in reversed(self._ordering):
            rows.sort(key=ordering.key, reverse=ordering.reverse)
        if self._offset:
            rows = rows[self._offset :]
        if self._limit is not None:
            rows = rows[: self._limit]
        return rows


class TextClause:
    """Representation of ``text()`` statements."""

    def __init__(self, statement: str) -> None:
        self.statement = statement


class Result:
    """Container returned from ``AsyncSession.execute``."""

    def __init__(self, rows: Sequence[Any]) -> None:
        self._rows = list(rows)

    def scalars(self) -> "ScalarResult":
        return ScalarResult(self._rows)

    def all(self) -> List[Any]:
        return list(self._rows)

    def first(self) -> Any:
        return self._rows[0] if self._rows else None

    def fetchall(self) -> List[Any]:
        return self.all()

    def scalar_one(self) -> Any:
        if len(self._rows) != 1:
            raise RuntimeError("Expected exactly one row")
        return self._rows[0]

    def scalar_one_or_none(self) -> Any:
        if not self._rows:
            return None
        if len(self._rows) > 1:
            raise RuntimeError("Expected zero or one row")
        return self._rows[0]

    def mappings(self) -> "MappingResult":
        return MappingResult(self._rows)


class ScalarResult:
    """Wrapper exposing scalar-centric helpers."""

    def __init__(self, rows: Sequence[Any]) -> None:
        self._rows = list(rows)

    def unique(self) -> "ScalarResult":
        seen: set[int] = set()
        unique_rows: List[Any] = []
        for row in self._rows:
            identifier = id(row)
            if identifier in seen:
                continue
            seen.add(identifier)
            unique_rows.append(row)
        return ScalarResult(unique_rows)

    def all(self) -> List[Any]:
        return list(self._rows)

    def first(self) -> Any:
        return self._rows[0] if self._rows else None

    def one(self) -> Any:
        if len(self._rows) != 1:
            raise RuntimeError("Expected exactly one result")
        return self._rows[0]

    def one_or_none(self) -> Any:
        if not self._rows:
            return None
        if len(self._rows) > 1:
            raise RuntimeError("Expected at most one result")
        return self._rows[0]

    def __iter__(self) -> Iterator[Any]:
        return iter(self._rows)


class MappingResult:
    """Convert row tuples into dictionaries for mapping-style access."""

    def __init__(self, rows: Sequence[Any]) -> None:
        self._rows = list(rows)

    def first(self) -> Optional[Dict[str, Any]]:
        return self._rows[0] if self._rows else None


class InMemoryDatabase:
    """Simple store maintaining data for mapped models."""

    def __init__(self) -> None:
        self._data: Dict[type, List[Any]] = {}
        self._pk_sequence: Dict[type, int] = {}
        self._columns: Dict[type, List[ColumnDescriptor]] = {}
        self._table_map: Dict[str, type] = {}

    def register_model(self, model: type, table_name: str) -> None:
        self._data.setdefault(model, [])
        self._pk_sequence.setdefault(model, 1)
        self._columns.setdefault(model, [])
        self._table_map.setdefault(table_name, model)

    def register_column(self, model: type, column: ColumnDescriptor) -> None:
        self._columns.setdefault(model, [])
        if column not in self._columns[model]:
            self._columns[model].append(column)

    def select_all(self, model: type) -> Sequence[Any]:
        return list(self._data.get(model, []))

    def add(self, instance: Any) -> None:
        model = type(instance)
        if model not in self._data:
            self.register_model(
                model, getattr(model, "__tablename__", model.__name__.lower())
            )
        pk_name = getattr(model, "__primary_key__", None)
        if pk_name:
            pk_value = getattr(instance, pk_name, None)
            if pk_value is None:
                pk_value = self._pk_sequence[model]
                self._pk_sequence[model] += 1
                setattr(instance, pk_name, pk_value)
        if instance not in self._data[model]:
            self._data[model].append(instance)

    def add_all(self, instances: Iterable[Any]) -> None:
        for instance in instances:
            self.add(instance)

    def get(self, model: type, pk: Any) -> Any:
        pk_name = getattr(model, "__primary_key__", None)
        if not pk_name:
            return None
        for row in self._data.get(model, []):
            if getattr(row, pk_name, None) == pk:
                return row
        return None

    def delete_all(self, model: type) -> None:
        self._data[model] = []
        self._pk_sequence[model] = 1

    def apply_onupdate(self) -> None:
        for model, columns in self._columns.items():
            for row in self._data.get(model, []):
                for column in columns:
                    if column.onupdate is not None:
                        column.apply_onupdate(row)

    def resolve_table(self, table_name: str) -> Optional[type]:
        return self._table_map.get(table_name)


GLOBAL_DATABASE = InMemoryDatabase()


def register_model(model: type, table_name: str) -> None:
    GLOBAL_DATABASE.register_model(model, table_name)


def register_column(model: type, name: str, column: ColumnDescriptor) -> None:
    if column.primary_key:
        setattr(model, "__primary_key__", name)
    mapped = getattr(model, "__mapped_columns__", None)
    if mapped is None:
        mapped = {}
        setattr(model, "__mapped_columns__", mapped)
    mapped[name] = column
    GLOBAL_DATABASE.register_column(model, column)


def register_relationship(
    model: type, name: str, descriptor: RelationshipDescriptor
) -> None:
    relationships = getattr(model, "__relationships__", None)
    if relationships is None:
        relationships = {}
        setattr(model, "__relationships__", relationships)
    relationships[name] = descriptor
