"""Delegate to the repository-level SQLAlchemy stub when running from backend."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any, Iterable


def _load_installed_sqlalchemy() -> ModuleType | None:
    """Attempt to import the real SQLAlchemy package if it is installed."""

    stub_path = Path(__file__).resolve().parent
    backend_root = stub_path.parent
    repo_root = stub_path.parents[2]
    repo_stub_path = repo_root / "sqlalchemy"
    excluded_paths = {backend_root.resolve(), repo_root.resolve(), repo_stub_path.resolve()}

    search_paths = [
        entry
        for entry in sys.path
        if Path(entry).resolve() not in excluded_paths
    ]

    spec = importlib.machinery.PathFinder.find_spec(__name__, search_paths)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    sys.modules[__name__] = module
    spec.loader.exec_module(module)
    return module


def _load_repository_stub() -> ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    stub_init = repo_root / "sqlalchemy" / "__init__.py"
    if not stub_init.exists():
        raise ModuleNotFoundError

    spec = importlib.util.spec_from_file_location(
        __name__,
        stub_init,
        submodule_search_locations=[str(stub_init.parent)],
    )
    if spec is None or spec.loader is None:
        raise ModuleNotFoundError("Unable to load SQLAlchemy stub module")

    module = importlib.util.module_from_spec(spec)
    sys.modules[__name__] = module
    spec.loader.exec_module(module)
    return module


def _create_inline_stub() -> ModuleType:
    module = ModuleType(__name__)
    module.__dict__["__path__"] = [str(Path(__file__).parent)]

    class _MissingSQLAlchemy(RuntimeError):
        def __init__(self, feature: str) -> None:
            super().__init__(
                "SQLAlchemy is required for "
                f"{feature}. Install the 'sqlalchemy' package to enable full functionality."
            )

    class _Type:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.args = args
            self.kwargs = kwargs

    class Integer(_Type):
        pass

    class String(_Type):
        pass

    class Text(_Type):
        pass

    class DateTime(_Type):
        pass

    class Column:
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
        return Select(entities)

    def text(statement: str) -> _TextClause:
        return _TextClause(statement)

    class _FunctionCall:
        def __init__(self, name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
            self.name = name
            self.args = args
            self.kwargs = kwargs

        def label(self, _label: str) -> "_FunctionCall":
            return self

    class _SQLFunction:
        def __init__(self, name: str) -> None:
            self._name = name

        def __call__(self, *args: Any, **kwargs: Any) -> _FunctionCall:
            return _FunctionCall(self._name, args, kwargs)

    class _FuncProxy:
        def __getattr__(self, name: str) -> _SQLFunction:
            return _SQLFunction(name)

        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            raise _MissingSQLAlchemy("func")

    func = _FuncProxy()
    pool = SimpleNamespace(NullPool=object())

    class _GenericConstruct:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.args = args
            self.kwargs = kwargs

    _generated_constructs: dict[str, type[_GenericConstruct]] = {}

    def __getattr__(name: str) -> Any:
        if name in _generated_constructs:
            return _generated_constructs[name]
        if name and name[0].isupper():
            placeholder = type(name, (_GenericConstruct,), {})
            _generated_constructs[name] = placeholder
            return placeholder
        raise AttributeError(f"module 'sqlalchemy' has no attribute {name!r}")

    module.Column = Column
    module.DateTime = DateTime
    module.Integer = Integer
    module.Select = Select
    module.String = String
    module.Text = Text
    module.select = select
    module.text = text
    module.func = func
    module.pool = pool
    module.__getattr__ = __getattr__
    module.root_missing_error = _MissingSQLAlchemy

    module.__all__ = [
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

    # engine submodule
    engine_mod = ModuleType(f"{__name__}.engine")
    engine_mod.__all__ = ["Connection"]

    class Connection:
        def run_sync(self, _fn, *args: Any, **kwargs: Any) -> Any:
            raise _MissingSQLAlchemy("Connection.run_sync")

    engine_mod.Connection = Connection

    # ext.asyncio submodule
    ext_asyncio_mod = ModuleType(f"{__name__}.ext.asyncio")
    ext_asyncio_mod.__all__ = [
        "AsyncEngine",
        "AsyncSession",
        "AsyncResult",
        "async_sessionmaker",
        "create_async_engine",
    ]

    class AsyncResult:
        async def scalar_one_or_none(self) -> Any:
            raise _MissingSQLAlchemy("AsyncResult.scalar_one_or_none")

        async def scalars(self) -> "AsyncResult":
            raise _MissingSQLAlchemy("AsyncResult.scalars")

        def all(self) -> list[Any]:
            raise _MissingSQLAlchemy("AsyncResult.all")

    class AsyncSession:
        async def execute(self, *args: Any, **kwargs: Any) -> AsyncResult:
            raise _MissingSQLAlchemy("AsyncSession.execute")

        async def scalar(self, *args: Any, **kwargs: Any) -> Any:
            raise _MissingSQLAlchemy("AsyncSession.scalar")

        async def flush(self) -> None:
            raise _MissingSQLAlchemy("AsyncSession.flush")

        async def commit(self) -> None:
            raise _MissingSQLAlchemy("AsyncSession.commit")

        async def rollback(self) -> None:
            raise _MissingSQLAlchemy("AsyncSession.rollback")

        async def refresh(self, instance: Any) -> None:
            raise _MissingSQLAlchemy("AsyncSession.refresh")

        def add(self, instance: Any) -> None:
            raise _MissingSQLAlchemy("AsyncSession.add")

        def add_all(self, instances: Iterable[Any]) -> None:
            raise _MissingSQLAlchemy("AsyncSession.add_all")

        async def close(self) -> None:
            raise _MissingSQLAlchemy("AsyncSession.close")

        async def __aenter__(self) -> "AsyncSession":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            await self.close()

    class _AsyncEngineContext:
        async def __aenter__(self) -> Any:
            raise _MissingSQLAlchemy("AsyncEngine.begin")

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

    class AsyncEngine:
        def begin(self) -> _AsyncEngineContext:
            return _AsyncEngineContext()

        async def dispose(self) -> None:
            raise _MissingSQLAlchemy("AsyncEngine.dispose")

    class _AsyncSessionContext:
        async def __aenter__(self) -> AsyncSession:
            raise _MissingSQLAlchemy("AsyncSession")

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

    class _AsyncSessionFactory:
        def __call__(self, *args: Any, **kwargs: Any) -> _AsyncSessionContext:
            return _AsyncSessionContext()

    class _AsyncSessionmaker:
        def __call__(self, *args: Any, **kwargs: Any) -> _AsyncSessionFactory:
            return _AsyncSessionFactory()

        def __getitem__(self, _item: Any) -> "_AsyncSessionmaker":
            return self

    async_sessionmaker = _AsyncSessionmaker()

    def create_async_engine(*args: Any, **kwargs: Any) -> AsyncEngine:
        return AsyncEngine()

    ext_asyncio_mod.AsyncEngine = AsyncEngine
    ext_asyncio_mod.AsyncSession = AsyncSession
    ext_asyncio_mod.AsyncResult = AsyncResult
    ext_asyncio_mod.async_sessionmaker = async_sessionmaker
    ext_asyncio_mod.create_async_engine = create_async_engine

    ext_mod = ModuleType(f"{__name__}.ext")
    ext_mod.__all__ = ["asyncio"]
    ext_mod.asyncio = ext_asyncio_mod
    ext_mod.__dict__["__path__"] = []

    # orm submodule
    orm_mod = ModuleType(f"{__name__}.orm")
    orm_mod.__all__ = [
        "DeclarativeBase",
        "Mapped",
        "mapped_column",
        "relationship",
        "selectinload",
    ]

    class _Statement:
        def __init__(self, description: str) -> None:
            self.description = description

        def where(self, *args: Any, **kwargs: Any) -> "_Statement":
            return self

        def limit(self, *args: Any, **kwargs: Any) -> "_Statement":
            return self

        def order_by(self, *args: Any, **kwargs: Any) -> "_Statement":
            return self

        def options(self, *args: Any, **kwargs: Any) -> "_Statement":
            return self

    @dataclass
    class _Table:
        name: str

        def delete(self) -> _Statement:
            return _Statement(f"delete {self.name}")

    class _MetaData:
        def __init__(self) -> None:
            self.sorted_tables: list[_Table] = []

        def create_all(self, *args: Any, **kwargs: Any) -> None:
            return None

    class DeclarativeBase:
        metadata = _MetaData()

        def __init_subclass__(cls, **kwargs: Any) -> None:
            super().__init_subclass__(**kwargs)
            table = _Table(cls.__name__)
            cls.__table__ = table  # type: ignore[attr-defined]
            DeclarativeBase.metadata.sorted_tables.append(table)

    def mapped_column(*args: Any, **kwargs: Any) -> Any:
        return None

    def relationship(*args: Any, **kwargs: Any) -> Any:
        return None

    def selectinload(*args: Any, **kwargs: Any) -> _Statement:
        return _Statement("selectinload")

    orm_mod.DeclarativeBase = DeclarativeBase
    orm_mod.Mapped = Any
    orm_mod.mapped_column = mapped_column
    orm_mod.relationship = relationship
    orm_mod.selectinload = selectinload

    # sql submodule
    sql_mod = ModuleType(f"{__name__}.sql")
    sql_mod.__all__ = ["func"]
    sql_mod.func = func

    # types submodule
    types_mod = ModuleType(f"{__name__}.types")
    types_mod.__all__ = ["JSON", "TypeDecorator"]

    @dataclass
    class JSON:
        args: tuple[Any, ...] = ()
        kwargs: dict[str, Any] | None = None

    class TypeDecorator:
        impl = None
        cache_ok = False

        def process_bind_param(self, value: Any, dialect: Any) -> Any:
            return value

        def process_result_value(self, value: Any, dialect: Any) -> Any:
            return value

    types_mod.JSON = JSON
    types_mod.TypeDecorator = TypeDecorator

    # dialects submodule
    dialects_mod = ModuleType(f"{__name__}.dialects")
    dialects_mod.__all__ = ["postgresql"]

    postgresql_mod = ModuleType(f"{__name__}.dialects.postgresql")
    postgresql_mod.__all__ = ["JSONB"]

    @dataclass
    class JSONB:
        args: tuple[Any, ...] = ()
        kwargs: dict[str, Any] | None = None

    postgresql_mod.JSONB = JSONB
    dialects_mod.postgresql = postgresql_mod

    # register submodules
    submodules = {
        f"{__name__}.engine": engine_mod,
        f"{__name__}.ext": ext_mod,
        f"{__name__}.ext.asyncio": ext_asyncio_mod,
        f"{__name__}.orm": orm_mod,
        f"{__name__}.sql": sql_mod,
        f"{__name__}.types": types_mod,
        f"{__name__}.dialects": dialects_mod,
        f"{__name__}.dialects.postgresql": postgresql_mod,
    }

    for full_name, submodule in submodules.items():
        sys.modules.setdefault(full_name, submodule)

    module.engine = engine_mod
    module.ext = ext_mod
    module.orm = orm_mod
    module.sql = sql_mod
    module.types = types_mod
    module.dialects = dialects_mod

    module.__all__.extend(
        ["engine", "ext", "orm", "sql", "types", "dialects", "root_missing_error"]
    )

    return module


def _load_sqlalchemy() -> ModuleType:
    module = _load_installed_sqlalchemy()
    if module is not None:
        return module

    try:
        return _load_repository_stub()
    except ModuleNotFoundError:
        module = _create_inline_stub()
        sys.modules[__name__] = module
        return module


globals().update(_load_sqlalchemy().__dict__)
