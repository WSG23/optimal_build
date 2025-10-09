"""Test configuration and shared fixtures."""

from __future__ import annotations

import asyncio
import importlib.machinery
import sys
import uuid
from collections.abc import AsyncGenerator, Callable, Iterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest
from backend._sqlalchemy_stub import ensure_sqlalchemy
from httpx import AsyncClient


def _find_repo_root(current: Path) -> Path:
    for parent in current.parents:
        if (parent / ".git").exists():
            return parent
    return current.parents[-1]


_REPO_ROOT = _find_repo_root(Path(__file__).resolve())

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _ensure_namespace_package(name: str, location: Path) -> None:
    """Register a namespace style package without mutating ``sys.path``."""

    if name in sys.modules:
        return

    package_dir = location / name.split(".")[-1]
    if not package_dir.exists():
        return

    spec = importlib.machinery.ModuleSpec(name, loader=None, is_package=True)
    module = ModuleType(name)
    module.__file__ = str(package_dir / "__init__.py")
    module.__path__ = [str(package_dir)]
    spec.submodule_search_locations = module.__path__
    module.__spec__ = spec
    sys.modules[name] = module


_ensure_namespace_package("backend", _REPO_ROOT)

try:
    from backend._stub_loader import load_optional_package
except ModuleNotFoundError:
    load_optional_package = None  # type: ignore[assignment]

if load_optional_package is not None:
    try:
        load_optional_package("fastapi", "fastapi", "FastAPI")
    except ModuleNotFoundError:
        import importlib.util
        import sys

        fastapi_path = _REPO_ROOT / "fastapi" / "__init__.py"
        if fastapi_path.exists():
            spec = importlib.util.spec_from_file_location("fastapi", fastapi_path)
            if spec and spec.loader is not None:
                module = importlib.util.module_from_spec(spec)
                sys.modules.setdefault("fastapi", module)
                spec.loader.exec_module(module)

try:  # pragma: no cover - async plugin is optional when running unit tests
    import pytest_asyncio  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - fallback to bundled shim
    pytest_asyncio = import_module("backend.pytest_asyncio")
    sys.modules.setdefault("pytest_asyncio", pytest_asyncio)

pytest_asyncio = cast(Any, pytest_asyncio)

ensure_sqlalchemy()

from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

try:  # pragma: no cover - StaticPool only exists in real SQLAlchemy
    from sqlalchemy.pool import StaticPool as _StaticPool
except (
    ImportError,
    AttributeError,
):  # pragma: no cover - fallback for stub implementation

    class _StaticPool:  # type: ignore[too-many-ancestors]
        """Placeholder used when running against the in-repo SQLAlchemy stub."""

        pass


StaticPool: type[Any] = _StaticPool

# isort: off
# Import app modules before sqlalchemy.orm to ensure proper initialization
import app.models as app_models
import app.utils.metrics as metrics
from app.core.database import get_session
from app.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column

# isort: on

try:
    from app.main import app
except Exception:  # pragma: no cover - fallback when FastAPI stub lacks features
    app = None
from sqlalchemy import Integer, String

# Importing ``app.models`` ensures all model metadata is registered.
_ = app_models


if "projects" not in getattr(BaseModel.metadata, "tables", {}):

    class _ProjectStub(BaseModel):
        """Minimal project table used for tests that only require an ID."""

        __tablename__ = "projects"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        name: Mapped[str] = mapped_column(
            String(120), nullable=False, default="Test Project"
        )


_SORTED_TABLES = tuple(BaseModel.metadata.sorted_tables)


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "no_db: skip database setup/teardown for lightweight tests"
    )


@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    """Create a dedicated event loop for the entire test session."""

    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()


async def _truncate_all(session: AsyncSession) -> None:
    """Remove all rows from every mapped table in metadata order."""

    await session.rollback()
    for table in reversed(_SORTED_TABLES):
        try:
            await session.execute(table.delete())
        except SQLAlchemyError:
            continue
    await session.commit()


async def _reset_database(factory: async_sessionmaker[AsyncSession]) -> None:
    """Clear all persisted data using a fresh session."""

    async with factory() as session:
        await _truncate_all(session)


@pytest_asyncio.fixture(scope="session")
async def flow_session_factory() -> AsyncGenerator[
    async_sessionmaker[AsyncSession],
    None,
]:
    """Provide a shared async session factory backed by in-memory SQLite."""

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _register_sqlite_functions(dbapi_connection, _) -> None:
        """Provide minimal SQLite stubs for Postgres-specific helpers."""

        def _gen_random_uuid() -> str:
            return str(uuid.uuid4())

        try:
            dbapi_connection.create_function("gen_random_uuid", 0, _gen_random_uuid)
        except Exception:
            # Some DBAPI implementations (or repeated registrations) may raise;
            # ignore so tests keep running on providers that already support it.
            pass

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _cleanup_flow_session_factory(
    flow_session_factory: async_sessionmaker[AsyncSession],
    request: pytest.FixtureRequest,
) -> AsyncGenerator[None, None]:
    """Ensure the shared flow database starts empty for every test."""

    if request.node.get_closest_marker("no_db"):
        yield
        return

    await _reset_database(flow_session_factory)
    try:
        yield
    finally:
        await _reset_database(flow_session_factory)


@pytest_asyncio.fixture(autouse=True)
async def _override_async_session_factory(
    flow_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncGenerator[None, None]:
    """Ensure application code reuses the in-memory test database."""

    targets = [
        import_module("app.core.database"),
        import_module("backend.flows.watch_fetch"),
        import_module("backend.flows.parse_segment"),
        import_module("backend.flows.sync_products"),
    ]

    for module in targets:
        monkeypatch.setattr(
            module,
            "AsyncSessionLocal",
            flow_session_factory,
            raising=False,
        )

    yield


@pytest_asyncio.fixture
async def async_session_factory(
    flow_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    """Yield the shared session factory with a clean database state."""

    await _reset_database(flow_session_factory)
    try:
        yield flow_session_factory
    finally:
        await _reset_database(flow_session_factory)


@pytest_asyncio.fixture
async def session(
    async_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session and clean up after each test."""

    async with async_session_factory() as db_session:
        try:
            yield db_session
        finally:
            await _truncate_all(db_session)


@pytest.fixture
def session_factory(
    async_session_factory: async_sessionmaker[AsyncSession],
) -> Callable[[], AbstractAsyncContextManager[AsyncSession]]:
    """Return an async context manager that yields a clean session."""

    @asynccontextmanager
    async def _factory() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory() as db_session:
            yield db_session

    return _factory


@pytest.fixture(autouse=True)
def reset_metrics() -> Iterator[None]:
    """Reset application metrics before and after every test."""

    metrics.reset_metrics()
    try:
        yield
    finally:
        metrics.reset_metrics()


@pytest_asyncio.fixture
async def app_client(
    async_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTPX client with the database dependency overridden."""

    async def _override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory() as db_session:
            yield db_session

    if app is None:
        pytest.skip("FastAPI app is unavailable in the current test environment")

    app.dependency_overrides[get_session] = _override_get_session
    async with AsyncClient(
        app=app,
        base_url="http://testserver",
        headers={"X-Role": "admin"},
    ) as client:
        yield client

    app.dependency_overrides.pop(get_session, None)
    await _reset_database(async_session_factory)


@pytest_asyncio.fixture(name="client")
async def client_fixture(
    app_client: AsyncClient,
) -> AsyncGenerator[AsyncClient, None]:
    """Compatibility alias exposing the app client under the traditional name."""

    yield app_client
