"""Lightweight SQLAlchemy compatibility layer for tests.

This stub implements the subset of the SQLAlchemy API exercised by the test
suite so that imports succeed without requiring the real dependency.  The goal
is not to provide full ORM behaviour—just enough structure for query builders,
metadata declarations, and async helpers that the tests interact with.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import ModuleType
from typing import Any, Callable, Iterable, Sequence
import sys

_DATABASE: dict[type, list[Any]] = {}
_PK_COUNTER: dict[type, int] = {}

__all__ = [
    "AsyncEngine",
    "AsyncSession",
    "Boolean",
    "CHAR",
    "CheckConstraint",
    "Column",
    "DECIMAL",
    "Date",
    "DateTime",
    "Decimal",
    "Enum",
    "Engine",
    "Float",
    "ForeignKey",
    "Index",
    "Integer",
    "MetaData",
    "Select",
    "Session",
    "String",
    "Table",
    "Text",
    "TypeDecorator",
    "UniqueConstraint",
    "UserDefinedType",
    "and_",
    "asc",
    "async_sessionmaker",
    "cast",
    "create_async_engine",
    "create_engine",
    "declarative_base",
    "delete",
    "desc",
    "engine_from_config",
    "event",
    "func",
    "inspect",
    "insert",
    "joinedload",
    "literal",
    "literal_column",
    "make_url",
    "mapped_column",
    "or_",
    "registry",
    "relationship",
    "select",
    "selectinload",
    "sessionmaker",
    "text",
    "update",
]

Decimal = float


class _SQLType:
    def __init__(self, python_type: type | None = None, **_: Any) -> None:
        self.python_type = python_type

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"SQLType({self.python_type!r})"


class String(_SQLType):
    pass


class Integer(_SQLType):
    pass


class Float(_SQLType):
    pass


class Boolean(_SQLType):
    pass


class Text(_SQLType):
    pass


class DateTime(_SQLType):
    pass


class CHAR(_SQLType):
    pass


class Enum(_SQLType):
    pass


class Date(_SQLType):
    pass


def Numeric(*_: Any, **__: Any) -> _SQLType:
    return _SQLType(float)


def DECIMAL(*_: Any, **__: Any) -> _SQLType:
    return _SQLType(float)


class _ColumnExpression:
    def __init__(self, column: "Column", owner: type | None) -> None:
        self.column = column
        self.owner = owner

    def _comparison(self, operator: str, value: Any) -> tuple[str, str, Any]:
        return (operator, self.column.name, value)

    def __eq__(self, other: Any) -> tuple[str, str, Any]:  # type: ignore[override]
        return self._comparison("eq", other)

    def __ne__(self, other: Any) -> tuple[str, str, Any]:  # type: ignore[override]
        return self._comparison("ne", other)

    def in_(self, values: Iterable[Any]) -> tuple[str, str, tuple[Any, ...]]:
        return ("in", self.column.name, tuple(values))

    def is_(self, value: Any) -> tuple[str, str, Any]:
        return self._comparison("is", value)

    def isnot(self, value: Any) -> tuple[str, str, Any]:
        return self._comparison("isnot", value)

    def desc(self) -> tuple[str, str]:
        return ("desc", self.column.name)

    def asc(self) -> tuple[str, str]:
        return ("asc", self.column.name)


class Column:
    def __init__(
        self,
        *args: Any,
        type_: _SQLType | None = None,
        primary_key: bool = False,
        default: Any = None,
        nullable: bool = True,
        unique: bool = False,
        **extras: Any,
    ) -> None:
        """Lightweight approximation of ``sqlalchemy.Column``.

        The real SQLAlchemy ``Column`` constructor accepts a wide variety of
        positional and keyword arguments.  The tests that exercise this stub
        stick to the common patterns of passing an optional column name as the
        first positional argument followed by a type, so we emulate just enough
        of that behaviour to keep model declarations working.
        """

        name: str | None = None
        inferred_type: _SQLType | None = None
        remaining = list(args)
        if remaining and isinstance(remaining[0], str):
            name = remaining.pop(0)
        if remaining:
            inferred_type = remaining.pop(0)

        self.name = name
        self.type_ = type_ if type_ is not None else inferred_type
        self.primary_key = primary_key
        self.default = default
        self.nullable = nullable
        self.unique = unique
        self.extras = extras
        self.table: "Table | None" = None
        self.key: str | None = None
        self._owner: type | None = None
        self.model: type | None = None

    def __set_name__(self, owner: type, name: str) -> None:  # pragma: no cover - descriptor protocol
        self._owner = owner
        if self.name is None:
            self.name = name
        self.key = name

    def __get__(self, instance: Any, owner: type | None = None) -> Any:
        if instance is None:
            return _ColumnExpression(self, owner)
        if self.name in instance.__dict__:
            return instance.__dict__[self.name]
        value = self._default_value()
        instance.__dict__[self.name] = value
        return value

    def __set__(self, instance: Any, value: Any) -> None:
        instance.__dict__[self.name] = value

    def with_name(self, name: str) -> "Column":
        self.name = name
        self.key = name
        return self

    def _default_value(self) -> Any:
        default = self.default
        if callable(default):  # pragma: no cover - rarely exercised in tests
            try:
                return default()
            except TypeError:
                return default
        return default


class _MetaData:
    def __init__(self) -> None:
        self.tables: dict[str, Table] = {}

    def create_all(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - stub
        return None

    def drop_all(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - stub
        return None

    @property
    def sorted_tables(self) -> list[Table]:
        return [self.tables[key] for key in sorted(self.tables.keys())]


class Table:
    def __init__(
        self,
        name: str,
        metadata: _MetaData,
        *columns: Column,
        **options: Any,
    ) -> None:
        self.name = name
        self.metadata = metadata
        self.model: type | None = options.pop("model", None)
        bound_columns: list[Column] = []
        for index, column in enumerate(columns):
            if not isinstance(column, Column):
                continue
            if column.name is None:
                column.with_name(column.key or f"column_{index}")
            column.table = self
            bound_columns.append(column)
        self.columns = tuple(bound_columns)
        self.c = {column.name: column for column in self.columns}
        self.options = options
        metadata.tables[name] = self

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Table({self.name!r})"

    def delete(self) -> tuple[str, "Table"]:
        return ("delete", self)

    def insert(self) -> tuple[str, "Table"]:
        return ("insert", self)

    def update(self) -> tuple[str, "Table"]:
        return ("update", self)


MetaData = _MetaData


def UniqueConstraint(*columns: str, **_: Any) -> tuple[str, ...]:
    return tuple(columns)


def Index(name: str, *columns: str, **_: Any) -> tuple[str, tuple[str, ...]]:
    return (name, tuple(columns))


def CheckConstraint(expression: str, **_: Any) -> str:
    return expression


class ForeignKey:
    def __init__(self, target: str, **_: Any) -> None:
        self.target = target


def literal(value: Any, type_: _SQLType | None = None) -> Any:  # noqa: ARG001
    return value


def literal_column(name: str) -> str:
    return name


def cast(value: Any, type_: _SQLType | None = None) -> Any:  # noqa: ARG001
    return value


def and_(*conditions: Any) -> tuple[str, tuple[Any, ...]]:
    return ("and", conditions)


def or_(*conditions: Any) -> tuple[str, tuple[Any, ...]]:
    return ("or", conditions)


def _evaluate_condition(record: Any, condition: Any) -> bool:
    if isinstance(condition, tuple):
        operator = condition[0]
        if operator in {"eq", "ne", "is", "isnot", "in"}:
            column_name = condition[1]
            value = condition[2]
            current = getattr(record, column_name, None)
            if operator == "eq":
                return current == value
            if operator == "ne":
                return current != value
            if operator == "is":
                return current is value or current == value
            if operator == "isnot":
                return not (current is value or current == value)
            if operator == "in":
                return current in value
        if operator == "and":
            return all(_evaluate_condition(record, item) for item in condition[1])
        if operator == "or":
            return any(_evaluate_condition(record, item) for item in condition[1])
    return True


def _apply_filters(records: list[Any], filters: list[Any]) -> list[Any]:
    if not filters:
        return list(records)
    return [record for record in records if all(_evaluate_condition(record, cond) for cond in filters)]


def asc(column: Any) -> tuple[str, Any]:
    return ("asc", column)


def desc(column: Any) -> tuple[str, Any]:
    return ("desc", column)


class Select:
    def __init__(self, entities: Sequence[Any]) -> None:
        self.entities = tuple(entities)
        self._where: list[Any] = []
        self._limit: int | None = None
        self._offset: int | None = None
        self._order_by: list[Any] = []

    def _clone(self) -> "Select":
        clone = Select(self.entities)
        clone._where = list(self._where)
        clone._limit = self._limit
        clone._offset = self._offset
        clone._order_by = list(self._order_by)
        return clone

    def where(self, *conditions: Any, **_: Any) -> Select:
        new = self._clone()
        for condition in conditions:
            if condition is not None:
                new._where.append(condition)
        return new

    def join(self, *args: Any, **kwargs: Any) -> Select:  # noqa: ARG002
        return self

    def outerjoin(self, *args: Any, **kwargs: Any) -> Select:  # noqa: ARG002
        return self

    def order_by(self, *args: Any, **kwargs: Any) -> Select:  # noqa: ARG002
        new = self._clone()
        new._order_by.extend(args)
        return new

    def group_by(self, *args: Any, **kwargs: Any) -> Select:  # noqa: ARG002
        return self

    def having(self, *args: Any, **kwargs: Any) -> Select:  # noqa: ARG002
        return self

    def options(self, *args: Any, **kwargs: Any) -> Select:  # noqa: ARG002
        return self

    def limit(self, value: int | None) -> Select:
        new = self._clone()
        new._limit = value
        return new

    def offset(self, value: int | None) -> Select:
        new = self._clone()
        new._offset = value
        return new

    def distinct(self, *args: Any, **kwargs: Any) -> Select:  # noqa: ARG002
        return self

    def add_columns(self, *columns: Any) -> Select:
        new = self._clone()
        new.entities = tuple(list(new.entities) + list(columns))
        return new


def select(*entities: Any) -> Select:
    return Select(entities)


def insert(entity: Any) -> Select:
    return Select((entity,))


def update(entity: Any) -> Select:
    return Select((entity,))


def delete(entity: Any) -> Select:
    return Select((entity,))


class _FuncProxy:
    def __getattr__(self, name: str) -> Callable[..., tuple[str, tuple[Any, ...], dict[str, Any]]]:
        def _call(*args: Any, **kwargs: Any) -> tuple[str, tuple[Any, ...], dict[str, Any]]:
            return (name, args, kwargs)

        return _call


func = _FuncProxy()


class _EventAPI:
    def listen(self, target: Any, identifier: str, fn: Callable[..., Any]) -> None:  # noqa: ARG002
        setattr(target, identifier, fn)

    def listens_for(self, target: Any, identifier: str, **__: Any):
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.listen(target, identifier, fn)
            return fn

        return decorator


event = _EventAPI()


class Engine:
    def __init__(self, url: str, **_: Any) -> None:
        self.url = url

    def dispose(self) -> None:  # pragma: no cover - compatibility hook
        return None

    def connect(self):
        class _Connection:
            def __enter__(self_inner) -> _Connection:
                return self_inner

            def __exit__(self_inner, exc_type, exc, tb) -> None:  # noqa: ANN001
                return None

            def begin(self_inner):
                class _Txn:
                    def __enter__(self_txn) -> _Txn:  # pragma: no cover - debug helper
                        return self_txn

                    def __exit__(self_txn, exc_type, exc, tb) -> None:  # noqa: ANN001
                        return None

                return _Txn()

        return _Connection()


def create_engine(url: str, **kwargs: Any) -> Engine:  # noqa: ARG001
    return Engine(url, **kwargs)


def engine_from_config(config: dict[str, Any], prefix: str = "sqlalchemy.", **kwargs: Any) -> Engine:
    url = config.get(f"{prefix}url", "sqlite://")
    return create_engine(url, **kwargs)


class _Inspector:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def has_table(self, name: str) -> bool:  # pragma: no cover - diagnostic helper
        return name in getattr(getattr(self.engine, "metadata", None), "tables", {})

    def get_table_names(self) -> list[str]:  # pragma: no cover - diagnostic helper
        metadata = getattr(self.engine, "metadata", None)
        if metadata and hasattr(metadata, "tables"):
            return list(metadata.tables.keys())
        return []


def inspect(engine: Engine) -> _Inspector:
    return _Inspector(engine)


class _Result:
    def __init__(self, values: Iterable[Any] | None = None) -> None:
        self._values = list(values or [])

    def __iter__(self):  # pragma: no cover - iteration helper
        return iter(self._values)

    def scalar_one_or_none(self) -> Any:
        return self._values[0] if self._values else None

    def scalar_one(self) -> Any:
        if not self._values:
            raise LookupError("No result")
        return self._values[0]

    def one(self) -> Any:
        if not self._values:
            raise LookupError("No row was returned")
        if len(self._values) > 1:
            raise LookupError("Multiple rows were returned")
        return self._values[0]

    def scalars(self) -> _Result:
        return self

    def all(self) -> list[Any]:
        return list(self._values)

    def first(self) -> Any:
        return self._values[0] if self._values else None

    def unique(self) -> "_Result":
        return self


class AsyncSession:
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401, ANN001, ARG002
        self._pending: list[Any] = []

    async def execute(self, statement: Any, *args: Any, **kwargs: Any) -> _Result:  # noqa: ARG002
        await self.flush()

        if isinstance(statement, Select):
            results: list[Any] = []
            for entity in statement.entities:
                if isinstance(entity, type):
                    records = list(_DATABASE.get(entity, []))
                    filtered = _apply_filters(records, statement._where)
                    if statement._offset:
                        filtered = filtered[statement._offset :]
                    if statement._limit is not None:
                        filtered = filtered[: statement._limit]
                    results.extend(filtered)
            return _Result(results)

        if isinstance(statement, tuple) and len(statement) == 2:
            op, target = statement
            if isinstance(target, Table) and op == "delete":
                model = getattr(target, "model", None)
                if model is not None:
                    _DATABASE[model] = []
                    _PK_COUNTER.pop(model, None)
            return _Result()

        return _Result()

    async def scalar(self, statement: Any, *args: Any, **kwargs: Any) -> Any:  # noqa: ARG002
        result = await self.execute(statement, *args, **kwargs)
        return result.scalar_one_or_none()

    def add(self, obj: Any) -> None:
        if obj not in self._pending:
            self._pending.append(obj)

    def add_all(self, objs: Iterable[Any]) -> None:
        for obj in objs:
            self.add(obj)

    async def commit(self) -> None:
        await self.flush()

    async def rollback(self) -> None:  # pragma: no cover - compatibility hook
        self._pending.clear()

    async def flush(self) -> None:
        if not self._pending:
            return
        pending = list(self._pending)
        self._pending.clear()
        for obj in pending:
            model = obj.__class__
            store = _DATABASE.setdefault(model, [])
            table = getattr(model, "__table__", None)
            pk_column = None
            if table is not None:
                for column in getattr(table, "columns", []):
                    if getattr(column, "primary_key", False):
                        pk_column = column
                        break
            if pk_column is not None:
                attr = pk_column.name
                if getattr(obj, attr, None) is None:
                    default = getattr(pk_column, "default", None)
                    if callable(default):
                        value = default()
                    elif default is not None:
                        value = default
                    else:
                        next_id = _PK_COUNTER.get(model, 0) + 1
                        _PK_COUNTER[model] = next_id
                        value = next_id
                    setattr(obj, attr, value)
            if obj not in store:
                store.append(obj)
            now = datetime.now(timezone.utc)
            if hasattr(obj, "created_at") and getattr(obj, "created_at", None) is None:
                setattr(obj, "created_at", now)
            if hasattr(obj, "updated_at"):
                setattr(obj, "updated_at", now)
            if hasattr(obj, "recorded_at") and getattr(obj, "recorded_at", None) is None:
                setattr(obj, "recorded_at", now)

    async def close(self) -> None:  # pragma: no cover - compatibility hook
        await self.flush()

    async def refresh(
        self,
        instance: Any,
        attribute_names: Sequence[str] | None = None,
    ) -> None:
        await self.flush()
        if attribute_names:
            for name in attribute_names:
                getattr(instance, name, None)

    async def get(
        self,
        model: type,
        ident: Any,
        *,
        options: Sequence[Any] | None = None,
    ) -> Any | None:
        await self.flush()
        store = _DATABASE.get(model, [])
        pk_attr = None
        table = getattr(model, "__table__", None)
        if table is not None:
            for column in getattr(table, "columns", []):
                if getattr(column, "primary_key", False):
                    pk_attr = column.name
                    break
        pk_attr = pk_attr or "id"
        target = str(ident)
        for obj in store:
            value = getattr(obj, pk_attr, None)
            if value == ident or str(value) == target:
                return obj
        return None


class _AsyncSessionContext:
    def __init__(self, args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
        self._args = args
        self._kwargs = kwargs
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> AsyncSession:
        self._session = AsyncSession(*self._args, **self._kwargs)
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        if self._session is not None:
            await self._session.close()
        self._session = None


class _AsyncSessionmaker:
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401, ANN001
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args: Any, **kwargs: Any) -> _AsyncSessionContext:  # noqa: ANN001
        if args or kwargs:
            combined_kwargs = dict(self.kwargs)
            combined_kwargs.update(kwargs)
            combined_args = tuple(self.args) + tuple(args)
        else:
            combined_args = tuple(self.args)
            combined_kwargs = dict(self.kwargs)
        return _AsyncSessionContext(combined_args, combined_kwargs)

    @classmethod
    def __class_getitem__(cls, item: Any) -> _AsyncSessionmaker:  # noqa: ANN001, pragma: no cover - typing helper
        return cls


class AsyncSessionmaker(_AsyncSessionmaker):
    pass


async_sessionmaker = AsyncSessionmaker


class _AsyncEngine:
    def __init__(self, url: str, **_: Any) -> None:
        self.url = url
        self.sync_engine = self

    async def dispose(self) -> None:
        return None

    def begin(self):
        class _TxnContext:
            async def __aenter__(self_inner):  # noqa: ANN001
                return self_inner

            async def __aexit__(self_inner, exc_type, exc, tb) -> None:  # noqa: ANN001
                return None

            async def run_sync(self_inner, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
                return func(*args, **kwargs)

        return _TxnContext()


def create_async_engine(url: str, **kwargs: Any) -> _AsyncEngine:  # noqa: ARG001
    return _AsyncEngine(url, **kwargs)


class AsyncEngine(_AsyncEngine):
    pass


class Session:
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
        pass

    def add(self, obj: Any) -> None:
        setattr(obj, "_added", True)

    def commit(self) -> None:
        return None

    def refresh(self, *_: Any) -> None:
        return None


def sessionmaker(*_: Any, **__: Any):  # noqa: ANN001
    def factory(*args: Any, **kwargs: Any) -> Session:  # noqa: ANN001
        return Session(*args, **kwargs)

    return factory


def relationship(*_: Any, **__: Any) -> list[Any]:
    return []


def selectinload(*_: Any, **__: Any) -> str:
    return "selectinload"


def joinedload(*_: Any, **__: Any) -> str:
    return "joinedload"


class _DeclarativeMeta(type):
    def __new__(mcls, name: str, bases: tuple[type, ...], attrs: dict[str, Any]):
        column_attrs = {
            key: value for key, value in attrs.items() if isinstance(value, Column)
        }
        cls = super().__new__(mcls, name, bases, attrs)

        metadata = getattr(cls, "metadata", None)
        if metadata is None:
            for base in bases:
                metadata = getattr(base, "metadata", None)
                if metadata is not None:
                    break
        if metadata is None:
            metadata = MetaData()
        cls.metadata = metadata

        if attrs.get("__abstract__", False):
            return cls

        tablename = getattr(cls, "__tablename__", None)
        if not tablename:
            return cls

        columns = []
        for key, column in column_attrs.items():
            column.with_name(column.name or key)
            columns.append(column)

        if columns:
            cls.__table__ = Table(tablename, metadata, *columns, model=cls)
            for column in columns:
                column.model = cls
            if "__init__" not in attrs:
                def __init__(self, **kwargs: Any) -> None:
                    for key, value in kwargs.items():
                        setattr(self, key, value)

                cls.__init__ = __init__  # type: ignore[assignment]
        return cls


class DeclarativeBase(metaclass=_DeclarativeMeta):
    metadata = MetaData()
    __abstract__ = True


class Mapped:
    def __class_getitem__(cls, item: Any) -> type["Mapped"]:  # noqa: D401
        return cls



def mapped_column(*args: Any, **kwargs: Any) -> Column:  # noqa: ARG002
    return Column(*args, **kwargs)


def registry(*_: Any, **__: Any):
    reg = ModuleType("sqlalchemy.orm.registry")
    return reg


def declarative_base() -> type:
    class Base(DeclarativeBase):
        pass

    return Base


declarative_module = ModuleType("sqlalchemy.ext.declarative")
declarative_module.declarative_base = declarative_base  # type: ignore[attr-defined]

sys.modules["sqlalchemy.ext.declarative"] = declarative_module


class JSON(_SQLType):
    pass


class TypeDecorator:
    impl = _SQLType()

    def process_bind_param(self, value: Any, dialect: Any) -> Any:  # pragma: no cover - stub
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Any:  # pragma: no cover - stub
        return value


class UserDefinedType:
    pass


types_module = ModuleType("sqlalchemy.types")
types_module.JSON = JSON  # type: ignore[attr-defined]
types_module.TypeDecorator = TypeDecorator  # type: ignore[attr-defined]
types_module.UserDefinedType = UserDefinedType  # type: ignore[attr-defined]
types_module.Enum = Enum  # type: ignore[attr-defined]
types_module.Numeric = Numeric  # type: ignore[attr-defined]

sys.modules["sqlalchemy.types"] = types_module


JSON = types_module.JSON
TypeDecorator = types_module.TypeDecorator
UserDefinedType = types_module.UserDefinedType
Enum = types_module.Enum
Numeric = types_module.Numeric


postgresql_module = ModuleType("sqlalchemy.dialects.postgresql")


class JSONB(_SQLType):
    pass


class UUID(_SQLType):
    pass


postgresql_module.JSONB = JSONB  # type: ignore[attr-defined]
postgresql_module.UUID = UUID  # type: ignore[attr-defined]
postgresql_module.insert = insert  # type: ignore[attr-defined]

sys.modules["sqlalchemy.dialects.postgresql"] = postgresql_module


sqlite_module = ModuleType("sqlalchemy.dialects.sqlite")
sqlite_base_module = ModuleType("sqlalchemy.dialects.sqlite.base")


class SQLiteTypeCompiler:
    pass


sqlite_base_module.SQLiteTypeCompiler = SQLiteTypeCompiler  # type: ignore[attr-defined]

sys.modules["sqlalchemy.dialects.sqlite"] = sqlite_module
sys.modules["sqlalchemy.dialects.sqlite.base"] = sqlite_base_module


sql_module = ModuleType("sqlalchemy.sql")


def text(statement: str) -> str:
    return statement


sql_module.func = func  # type: ignore[attr-defined]
sql_module.text = text  # type: ignore[attr-defined]

sys.modules["sqlalchemy.sql"] = sql_module


schema_module = ModuleType("sqlalchemy.sql.schema")
schema_module.Column = Column  # type: ignore[attr-defined]
schema_module.Table = Table  # type: ignore[attr-defined]
schema_module.MetaData = MetaData  # type: ignore[attr-defined]
schema_module.ForeignKey = ForeignKey  # type: ignore[attr-defined]
schema_module.UniqueConstraint = UniqueConstraint  # type: ignore[attr-defined]
schema_module.CheckConstraint = CheckConstraint  # type: ignore[attr-defined]
schema_module.Index = Index  # type: ignore[attr-defined]

sys.modules["sqlalchemy.sql.schema"] = schema_module


exc_module = ModuleType("sqlalchemy.exc")


class SQLAlchemyError(Exception):
    pass


class IntegrityError(SQLAlchemyError):
    pass


exc_module.SQLAlchemyError = SQLAlchemyError  # type: ignore[attr-defined]
exc_module.IntegrityError = IntegrityError  # type: ignore[attr-defined]

sys.modules["sqlalchemy.exc"] = exc_module


engine_module = ModuleType("sqlalchemy.engine")


class URL:
    def __init__(self, raw: str) -> None:
        self.raw = raw

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return self.raw


def make_url(url: str) -> URL:
    return URL(url)


engine_module.Engine = Engine  # type: ignore[attr-defined]
engine_module.URL = URL  # type: ignore[attr-defined]
engine_module.make_url = make_url  # type: ignore[attr-defined]

sys.modules["sqlalchemy.engine"] = engine_module


pool_module = ModuleType("sqlalchemy.pool")


class NullPool:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs


class StaticPool(NullPool):
    pass


pool_module.NullPool = NullPool  # type: ignore[attr-defined]
pool_module.StaticPool = StaticPool  # type: ignore[attr-defined]

sys.modules["sqlalchemy.pool"] = pool_module
