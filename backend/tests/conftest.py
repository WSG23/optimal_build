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

# Import AsyncClient from httpx, but we'll wrap it for FastAPI testing
try:
    from httpx import AsyncClient as _RealAsyncClient
except ImportError:
    _RealAsyncClient = None  # type: ignore[assignment]


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
        # Try loading the shadow stub first
        shadow_dirs = [
            d
            for d in _REPO_ROOT.iterdir()
            if d.is_dir() and d.name.startswith("fastapi_shadow_")
        ]
        if shadow_dirs:
            load_optional_package("fastapi", shadow_dirs[0].name, "FastAPI")
        else:
            load_optional_package("fastapi", "fastapi", "FastAPI")
    except ModuleNotFoundError:
        import importlib.util

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

import app.utils.metrics as metrics

_SQLALCHEMY_AVAILABLE = ensure_sqlalchemy()

# Import AsyncTestClient from FastAPI stub for testing
try:
    from fastapi.testclient import AsyncTestClient

    AsyncClient = AsyncTestClient  # type: ignore[misc,assignment]
except ImportError:
    if _RealAsyncClient is not None:
        AsyncClient = _RealAsyncClient  # type: ignore[misc,assignment]
    else:
        AsyncClient = None  # type: ignore[assignment]

app: Any | None = None

if _SQLALCHEMY_AVAILABLE:
    from sqlalchemy import Integer, String, event
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )
    from sqlalchemy.orm import Mapped, mapped_column
    from sqlalchemy.util import concurrency

    if not concurrency.have_greenlet:  # pragma: no cover - environment specific

        class _AsyncLock:
            def __init__(self) -> None:
                self._lock = asyncio.Lock()

            async def __aenter__(self) -> "_AsyncLock":
                await self._lock.acquire()
                return self

            async def __aexit__(self, exc_type, exc, tb) -> None:
                self._lock.release()

        async def _await_only(value):
            if asyncio.iscoroutine(value):
                return await value
            return value

        async def _greenlet_spawn(func, *args, **kwargs):
            return await asyncio.to_thread(func, *args, **kwargs)

        concurrency.AsyncAdaptedLock = lambda *_, **__: _AsyncLock()
        concurrency.await_only = _await_only
        concurrency.await_fallback = _await_only
        concurrency.greenlet_spawn = _greenlet_spawn
        concurrency.have_greenlet = True

        from sqlalchemy.ext.asyncio import engine as _async_engine
        from sqlalchemy.ext.asyncio import result as _async_result
        from sqlalchemy.ext.asyncio import session as _async_session

        _async_engine.greenlet_spawn = _greenlet_spawn
        _async_session.greenlet_spawn = _greenlet_spawn
        _async_result.greenlet_spawn = _greenlet_spawn

    try:  # pragma: no cover - StaticPool only exists in real SQLAlchemy
        from sqlalchemy.pool import StaticPool as _StaticPool
    except (ImportError, AttributeError):  # pragma: no cover

        class _StaticPool:  # type: ignore[too-many-ancestors]
            """Placeholder used when running against the in-repo SQLAlchemy stub."""

            pass

    StaticPool: type[Any] = _StaticPool

    # isort: off
    # Import app modules before sqlalchemy.orm to ensure proper initialization
    import app.models as app_models
    from app.core.database import get_session
    from app.models.base import BaseModel

    # isort: on

    try:
        from app.main import app as _app
    except Exception:  # pragma: no cover - fallback when FastAPI stub lacks features
        _app = None

    app = _app

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
else:
    SQLAlchemyError = RuntimeError
    StaticPool = type("StaticPool", (), {})  # type: ignore[assignment]


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


if _SQLALCHEMY_AVAILABLE:

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
            for table in BaseModel.metadata.sorted_tables:
                try:
                    await conn.run_sync(table.create, checkfirst=True)
                except Exception:
                    # Skip tables with PostgreSQL-specific syntax (e.g., gen_random_uuid)
                    pass

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
        request: pytest.FixtureRequest,
    ) -> AsyncGenerator[None, None]:
        """Ensure application code reuses the in-memory test database."""

        if request.node.get_closest_marker("no_db"):
            yield
            return

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

    @pytest_asyncio.fixture
    async def market_demo_data(
        async_session_factory: async_sessionmaker[AsyncSession],
    ) -> AsyncGenerator[None, None]:
        """Populate database with demo property data for market advisory tests."""

        import uuid as uuid_module

        from app.models.property import (
            Property,
            PropertyStatus,
            PropertyType,
            TenureType,
        )

        async with async_session_factory() as session:
            try:
                from sqlalchemy import text as sql_text

                await session.execute(sql_text("SELECT 1 FROM properties LIMIT 1"))
            except Exception:
                await session.execute(
                    sql_text(
                        """
                        CREATE TABLE IF NOT EXISTS properties (
                            id TEXT PRIMARY KEY,
                            name VARCHAR(255) NOT NULL,
                            address VARCHAR(500) NOT NULL,
                            postal_code VARCHAR(20),
                            property_type VARCHAR(50) NOT NULL,
                            status VARCHAR(50),
                            location TEXT NOT NULL,
                            district VARCHAR(50),
                            subzone VARCHAR(100),
                            planning_area VARCHAR(100),
                            land_area_sqm DECIMAL(10, 2),
                            gross_floor_area_sqm DECIMAL(12, 2),
                            net_lettable_area_sqm DECIMAL(12, 2),
                            building_height_m DECIMAL(6, 2),
                            floors_above_ground INTEGER,
                            floors_below_ground INTEGER,
                            units_total INTEGER,
                            year_built INTEGER,
                            year_renovated INTEGER,
                            developer VARCHAR(255),
                            architect VARCHAR(255),
                            tenure_type VARCHAR(50),
                            lease_start_date DATE,
                            lease_expiry_date DATE,
                            zoning_code VARCHAR(50),
                            plot_ratio DECIMAL(4, 2),
                            is_conservation BOOLEAN,
                            conservation_status VARCHAR(100),
                            heritage_constraints JSON,
                            ura_property_id VARCHAR(50) UNIQUE,
                            data_source VARCHAR(50),
                            external_references JSON
                        )
                        """
                    )
                )
                await session.commit()

            demo_property = Property(
                id=uuid_module.uuid4(),
                name="Market Demo Tower",
                address="123 Marina Boulevard",
                postal_code="018989",
                property_type=PropertyType.OFFICE,
                status=PropertyStatus.EXISTING,
                location="POINT(103.8535 1.2830)",
                district="Downtown Core",
                subzone="Marina Centre",
                planning_area="Downtown Core",
                land_area_sqm=5000.0,
                gross_floor_area_sqm=25000.0,
                net_lettable_area_sqm=22000.0,
                building_height_m=120.0,
                floors_above_ground=30,
                floors_below_ground=2,
                units_total=150,
                year_built=2015,
                developer="Demo Developer Pte Ltd",
                architect="Demo Architects",
                tenure_type=TenureType.LEASEHOLD_99,
                plot_ratio=5.0,
                is_conservation=False,
                data_source="demo",
            )
            session.add(demo_property)
            await session.commit()

        yield

else:

    @pytest.fixture(autouse=True)
    def _skip_without_sqlalchemy(request: pytest.FixtureRequest) -> None:
        """Skip tests that require SQLAlchemy when the dependency is missing."""

        if request.node.get_closest_marker("no_db"):
            return
        pytest.skip("SQLAlchemy is unavailable in the current test environment")


@pytest.fixture(autouse=True)
def reset_metrics() -> Iterator[None]:
    """Reset application metrics before and after every test."""

    metrics.reset_metrics()
    try:
        yield
    finally:
        metrics.reset_metrics()
