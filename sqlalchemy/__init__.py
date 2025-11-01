"""Minimal SQLAlchemy compatibility layer for analytics unit tests."""

from __future__ import annotations

from decimal import Decimal as _Decimal
from types import ModuleType
from typing import Any, Callable, Iterable, Sequence
import sys
import types

__all__ = [
    "Boolean",
    "CHAR",
    "Column",
    "DateTime",
    "Float",
    "ForeignKey",
    "Integer",
    "Enum",
    "Date",
    "Numeric",
    "String",
    "Text",
    "cast",
    "literal",
    "select",
    "Select",
    "and_",
    "or_",
    "func",
    "create_engine",
    "event",
    "insert",
    "update",
    "delete",
    "UniqueConstraint",
    "Index",
    "CheckConstraint",
    "DECIMAL",
    "Decimal",
]

Decimal = _Decimal


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


def DECIMAL(*_: Any, **__: Any) -> _SQLType:
    return _SQLType(float)


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


class Column:
    def __init__(
        self,
        type_: _SQLType | None = None,
        primary_key: bool = False,
        default: Any = None,
        nullable: bool = True,
        unique: bool = False,
        **extras: Any,
    ) -> None:
        self.type_ = type_
        self.primary_key = primary_key
        self.default = default
        self.nullable = nullable
        self.unique = unique
        self.extras = extras


def UniqueConstraint(*columns: str, **_: Any) -> tuple[str, ...]:
    return tuple(columns)


def Index(name: str, *columns: str, **_: Any) -> tuple[str, tuple[str, ...]]:
    return (name, tuple(columns))


def CheckConstraint(expression: str, **_: Any) -> str:
    return expression


class ForeignKey:
    def __init__(self, target: str, **_: Any) -> None:
        self.target = target


def literal(value: Any, type_: _SQLType | None = None) -> Any:
    return value


def cast(value: Any, type_: _SQLType | None = None) -> Any:
    return value


def and_(*conditions: Any) -> tuple[str, tuple[Any, ...]]:
    return ("and", conditions)


def or_(*conditions: Any) -> tuple[str, tuple[Any, ...]]:
    return ("or", conditions)


class Select:
    def __init__(self, entities: Sequence[Any]) -> None:
        self.entities = tuple(entities)

    def where(self, *args: Any, **kwargs: Any) -> "Select":
        return self

    def join(self, *args: Any, **kwargs: Any) -> "Select":
        return self

    def outerjoin(self, *args: Any, **kwargs: Any) -> "Select":
        return self

    def order_by(self, *args: Any, **kwargs: Any) -> "Select":
        return self

    def group_by(self, *args: Any, **kwargs: Any) -> "Select":
        return self

    def having(self, *args: Any, **kwargs: Any) -> "Select":
        return self

    def options(self, *args: Any, **kwargs: Any) -> "Select":
        return self

    def limit(self, *args: Any, **kwargs: Any) -> "Select":
        return self

    def offset(self, *args: Any, **kwargs: Any) -> "Select":
        return self

    def distinct(self, *args: Any, **kwargs: Any) -> "Select":
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
    def __getattr__(self, name: str) -> "_FuncCall":
        return _FuncCall(name)


class _FuncCall:
    def __init__(self, name: str) -> None:
        self.name = name

    def __call__(self, *args: Any, **kwargs: Any) -> tuple[str, tuple[Any, ...], dict[str, Any]]:
        return (self.name, args, kwargs)


func = _FuncProxy()


class _EventAPI:
    def listen(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - no-op hook
        return None

    def listens_for(self, target: Any, identifier: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            return fn

        return decorator


event = _EventAPI()


class Engine:
    def __init__(self, url: str, **_: Any) -> None:
        self.url = url

    def dispose(self) -> None:  # pragma: no cover - compatibility hook
        return None


def create_engine(url: str, **kwargs: Any) -> Engine:
    return Engine(url, **kwargs)


# ---------------------------------------------------------------------------
# Submodules: sqlalchemy.ext.asyncio
# ---------------------------------------------------------------------------
ext_module = ModuleType("sqlalchemy.ext")
asyncio_module = ModuleType("sqlalchemy.ext.asyncio")


class _Result:
    def __init__(self, value: Any = None) -> None:
        self._value = value

    def scalar_one_or_none(self) -> Any:
        return self._value

    def scalars(self) -> "_Result":
        return self

    def all(self) -> list[Any]:
        return []

    def first(self) -> Any:
        return self._value


class AsyncSession:
    async def execute(self, *_: Any, **__: Any) -> _Result:
        return _Result()

    async def scalar(self, *_: Any, **__: Any) -> Any:
        return None

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

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class _AsyncSessionmaker:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args: Any, **kwargs: Any) -> _AsyncSessionContext:
        return _AsyncSessionContext()

    @classmethod
    def __class_getitem__(cls, item: Any) -> "_AsyncSessionmaker":  # pragma: no cover - typing helper
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
            async def __aenter__(self_inner):
                return self_inner

            async def __aexit__(self_inner, exc_type, exc, tb) -> None:
                return None

            async def run_sync(self_inner, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
                return func(*args, **kwargs)

        return _TxnContext()


def create_async_engine(url: str, **kwargs: Any) -> _AsyncEngine:
    return _AsyncEngine(url, **kwargs)


class AsyncEngine(_AsyncEngine):
    pass


asyncio_module.AsyncSession = AsyncSession  # type: ignore[attr-defined]
asyncio_module.async_sessionmaker = async_sessionmaker  # type: ignore[attr-defined]
asyncio_module.create_async_engine = create_async_engine  # type: ignore[attr-defined]
asyncio_module.AsyncEngine = AsyncEngine  # type: ignore[attr-defined]

sys.modules["sqlalchemy.ext"] = ext_module
sys.modules["sqlalchemy.ext.asyncio"] = asyncio_module

# ---------------------------------------------------------------------------
# Submodules: sqlalchemy.orm
# ---------------------------------------------------------------------------
orm_module = ModuleType("sqlalchemy.orm")


class Session:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def add(self, obj: Any) -> None:
        setattr(obj, "_added", True)

    def commit(self) -> None:
        return None

    def refresh(self, *_: Any) -> None:
        return None


def sessionmaker(*_: Any, **__: Any):
    def factory(*args: Any, **kwargs: Any) -> Session:
        return Session(*args, **kwargs)

    return factory


def relationship(*_: Any, **__: Any) -> list[Any]:
    return []


def selectinload(*_: Any, **__: Any) -> str:
    return "selectinload"


def joinedload(*_: Any, **__: Any) -> str:
    return "joinedload"


class _MetaData:
    def __init__(self) -> None:
        self.tables: dict[str, Any] = {}

    def create_all(self, *args: Any, **kwargs: Any) -> None:
        return None

    def drop_all(self, *args: Any, **kwargs: Any) -> None:
        return None

    @property
    def sorted_tables(self) -> list[Any]:
        return list(self.tables.values())


class DeclarativeBase:
    metadata = _MetaData()


class Mapped:
    pass


def mapped_column(*args: Any, **kwargs: Any) -> Column:
    type_ = kwargs.get("type_")
    return Column(type_, **{k: v for k, v in kwargs.items() if k in {"primary_key", "default", "nullable", "unique"}})


def registry() -> ModuleType:
    reg = ModuleType("sqlalchemy.orm.registry")
    return reg


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

# ---------------------------------------------------------------------------
# Submodules: sqlalchemy.ext.declarative
# ---------------------------------------------------------------------------
declarative_module = ModuleType("sqlalchemy.ext.declarative")


def declarative_base() -> type:
    class Base:
        metadata = _MetaData()

    return Base


declarative_module.declarative_base = declarative_base  # type: ignore[attr-defined]

sys.modules["sqlalchemy.ext.declarative"] = declarative_module

# ---------------------------------------------------------------------------
# Submodules: sqlalchemy.dialects.postgresql
# ---------------------------------------------------------------------------
postgresql_module = ModuleType("sqlalchemy.dialects.postgresql")


class JSONB(_SQLType):
    pass


class UUID(_SQLType):
    pass


def insert(table: Any) -> Select:
    return Select((table,))


postgresql_module.JSONB = JSONB  # type: ignore[attr-defined]
postgresql_module.UUID = UUID  # type: ignore[attr-defined]
postgresql_module.insert = insert  # type: ignore[attr-defined]

sys.modules["sqlalchemy.dialects.postgresql"] = postgresql_module

# ---------------------------------------------------------------------------
# Submodules: sqlalchemy.types
# ---------------------------------------------------------------------------
types_module = ModuleType("sqlalchemy.types")


class JSON(_SQLType):
    pass


class TypeDecorator:
    impl = _SQLType()

    def process_bind_param(self, value: Any, dialect: Any) -> Any:  # pragma: no cover - compatibility stub
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Any:  # pragma: no cover - compatibility stub
        return value


class UserDefinedType:
    pass


types_module.JSON = JSON  # type: ignore[attr-defined]
types_module.TypeDecorator = TypeDecorator  # type: ignore[attr-defined]
types_module.UserDefinedType = UserDefinedType  # type: ignore[attr-defined]
types_module.Enum = Enum  # type: ignore[attr-defined]
types_module.Numeric = Numeric  # type: ignore[attr-defined]

sys.modules["sqlalchemy.types"] = types_module

# Expose selected types at the package root for compatibility with imports
JSON = types_module.JSON
TypeDecorator = types_module.TypeDecorator
UserDefinedType = types_module.UserDefinedType
Enum = types_module.Enum
Numeric = types_module.Numeric

# ---------------------------------------------------------------------------
# Submodules: sqlalchemy.sql
# ---------------------------------------------------------------------------
sql_module = ModuleType("sqlalchemy.sql")


def text(statement: str) -> str:
    return statement


sql_module.func = func  # type: ignore[attr-defined]
sql_module.text = text  # type: ignore[attr-defined]

sys.modules["sqlalchemy.sql"] = sql_module

# ---------------------------------------------------------------------------
# Submodules: sqlalchemy.exc
# ---------------------------------------------------------------------------
exc_module = ModuleType("sqlalchemy.exc")


class SQLAlchemyError(Exception):
    pass


class IntegrityError(SQLAlchemyError):
    pass


exc_module.SQLAlchemyError = SQLAlchemyError  # type: ignore[attr-defined]
exc_module.IntegrityError = IntegrityError  # type: ignore[attr-defined]

sys.modules["sqlalchemy.exc"] = exc_module
