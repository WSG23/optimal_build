"""Lightweight SQLAlchemy compatibility layer for tests.

This stub implements the subset of the SQLAlchemy API exercised by the test
suite so that imports succeed without requiring the real dependency.  The goal
is not to provide full ORM behaviour—just enough structure for query builders,
metadata declarations, and async helpers that the tests interact with.
"""

from __future__ import annotations

from types import ModuleType
from typing import Any, Callable, Iterable, Sequence
import sys

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

    def with_name(self, name: str) -> "Column":
        self.name = name
        self.key = name
        return self


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


def asc(column: Any) -> tuple[str, Any]:
    return ("asc", column)


def desc(column: Any) -> tuple[str, Any]:
    return ("desc", column)


class Select:
    def __init__(self, entities: Sequence[Any]) -> None:
        self.entities = tuple(entities)

    def where(self, *args: Any, **kwargs: Any) -> Select:  # noqa: ARG002
        return self

    def join(self, *args: Any, **kwargs: Any) -> Select:  # noqa: ARG002
        return self

    def outerjoin(self, *args: Any, **kwargs: Any) -> Select:  # noqa: ARG002
        return self

    def order_by(self, *args: Any, **kwargs: Any) -> Select:  # noqa: ARG002
        return self

    def group_by(self, *args: Any, **kwargs: Any) -> Select:  # noqa: ARG002
        return self

    def having(self, *args: Any, **kwargs: Any) -> Select:  # noqa: ARG002
        return self

    def options(self, *args: Any, **kwargs: Any) -> Select:  # noqa: ARG002
        return self

    def limit(self, *args: Any, **kwargs: Any) -> Select:  # noqa: ARG002
        return self

    def offset(self, *args: Any, **kwargs: Any) -> Select:  # noqa: ARG002
        return self

    def distinct(self, *args: Any, **kwargs: Any) -> Select:  # noqa: ARG002
        return self


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
    def __init__(self, value: Any = None) -> None:
        self._value = value

    def scalar_one_or_none(self) -> Any:
        return self._value

    def scalar_one(self) -> Any:
        if self._value is None:
            raise LookupError("No result")
        return self._value

    def scalars(self) -> _Result:
        return self

    def all(self) -> list[Any]:
        return []

    def first(self) -> Any:
        return self._value


class AsyncSession:
    def __init__(self) -> None:
        self._objects: list[Any] = []

    async def execute(self, *_: Any, **__: Any) -> _Result:
        return _Result()

    async def scalar(self, *_: Any, **__: Any) -> Any:
        return None

    def add(self, obj: Any) -> None:
        self._objects.append(obj)

    def add_all(self, objs: Iterable[Any]) -> None:
        self._objects.extend(objs)

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None

    async def flush(self) -> None:
        return None

    async def close(self) -> None:
        return None


class _AsyncSessionContext:
    async def __aenter__(self) -> AsyncSession:
        return AsyncSession()

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None


class _AsyncSessionmaker:
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401, ANN001
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args: Any, **kwargs: Any) -> _AsyncSessionContext:  # noqa: ANN001
        return _AsyncSessionContext()

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


ext_module = ModuleType("sqlalchemy.ext")
asyncio_module = ModuleType("sqlalchemy.ext.asyncio")
asyncio_module.AsyncSession = AsyncSession  # type: ignore[attr-defined]
asyncio_module.async_sessionmaker = async_sessionmaker  # type: ignore[attr-defined]
asyncio_module.create_async_engine = create_async_engine  # type: ignore[attr-defined]
asyncio_module.AsyncEngine = AsyncEngine  # type: ignore[attr-defined]
ext_module.asyncio = asyncio_module  # type: ignore[attr-defined]

sys.modules["sqlalchemy.ext"] = ext_module
sys.modules["sqlalchemy.ext.asyncio"] = asyncio_module


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
            cls.__table__ = Table(tablename, metadata, *columns)
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
    pass


def mapped_column(*args: Any, **kwargs: Any) -> Column:  # noqa: ARG002
    return Column(*args, **kwargs)


def registry(*_: Any, **__: Any):
    reg = ModuleType("sqlalchemy.orm.registry")
    return reg


orm_module = ModuleType("sqlalchemy.orm")
orm_module.Session = Session  # type: ignore[attr-defined]
orm_module.sessionmaker = sessionmaker  # type: ignore[attr-defined]
orm_module.relationship = relationship  # type: ignore[attr-defined]
orm_module.selectinload = selectinload  # type: ignore[attr-defined]
orm_module.joinedload = joinedload  # type: ignore[attr-defined]
orm_module.DeclarativeBase = DeclarativeBase  # type: ignore[attr-defined]
orm_module.Mapped = Mapped  # type: ignore[attr-defined]
orm_module.mapped_column = mapped_column  # type: ignore[attr-defined]
orm_module.registry = registry  # type: ignore[attr-defined]

sys.modules["sqlalchemy.orm"] = orm_module


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
