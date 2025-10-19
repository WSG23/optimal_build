"""Test configuration and shared fixtures."""

from __future__ import annotations

# IMPORTANT: Patch SQLite type compiler BEFORE any other imports
# This ensures SQLite can handle PostgreSQL-specific types (UUID, JSONB)
try:
    from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler

    if not hasattr(SQLiteTypeCompiler, "visit_UUID"):

        def _visit_UUID(self, _type, **_):  # pragma: no cover
            return "CHAR(36)"

        SQLiteTypeCompiler.visit_UUID = _visit_UUID

    if not hasattr(SQLiteTypeCompiler, "visit_JSONB"):

        def _visit_JSONB(self, _type, **_):  # pragma: no cover
            return "TEXT"

        SQLiteTypeCompiler.visit_JSONB = _visit_JSONB
except ImportError:
    pass  # SQLAlchemy not installed

import asyncio
import importlib.machinery
import importlib.util
import sys
import uuid
from collections.abc import AsyncGenerator, Callable, Iterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any, Optional, Union, cast

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

_MINIMAL_APP_ERROR: Exception | None = None

try:
    from app.main import app  # type: ignore[assignment]
except (
    Exception
):  # pragma: no cover - build a minimal app when full stack is unavailable
    app = None
    try:
        from fastapi import FastAPI

        try:
            from fastapi import responses as fastapi_responses  # type: ignore
        except ImportError:
            fastapi_responses = None  # type: ignore[assignment]

        if fastapi_responses is None or not hasattr(fastapi_responses, "JSONResponse"):
            import json
            import types

            responses_module = types.ModuleType("fastapi.responses")

            class _Response:
                def __init__(
                    self,
                    content: Optional[Union[bytes, str]] = None,
                    status_code: int = 200,
                    headers: Optional[dict[str, str]] = None,
                    media_type: Optional[str] = None,
                ) -> None:
                    self.body = content
                    self.status_code = status_code
                    self.headers = headers or {}
                    self.media_type = media_type or "text/plain"

            class _JSONResponse(_Response):
                def __init__(
                    self,
                    content: object,
                    status_code: int = 200,
                    headers: dict[str, str] | None = None,
                ) -> None:
                    super().__init__(
                        json.dumps(content),
                        status_code=status_code,
                        headers=headers,
                        media_type="application/json",
                    )

            responses_module.Response = _Response  # type: ignore[attr-defined]
            responses_module.JSONResponse = _JSONResponse  # type: ignore[attr-defined]
            sys.modules["fastapi.responses"] = responses_module

        module_name = "test_app.api.v1.developers"
        developers_path = (
            _REPO_ROOT / "backend" / "app" / "api" / "v1" / "developers.py"
        )
        if not developers_path.exists():  # pragma: no cover - repository layout changed
            raise FileNotFoundError(
                f"Missing developers API module at {developers_path}"
            )

        spec = importlib.util.spec_from_file_location(module_name, developers_path)
        if spec is None or spec.loader is None:
            raise ImportError(
                f"Unable to load developers API module from {developers_path}"
            )
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        developers_router = module.router  # type: ignore[attr-defined]
    except Exception as import_error:  # pragma: no cover - FastAPI stub missing
        _MINIMAL_APP_ERROR = import_error
    else:
        minimal_app = FastAPI(title="Developer Checklist Test App")
        minimal_app.include_router(developers_router, prefix="/api/v1")
        app = minimal_app
        _MINIMAL_APP_ERROR = None
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
        # Create tables one by one, skipping those with PostgreSQL-specific DDL
        for table in BaseModel.metadata.sorted_tables:
            try:
                await conn.run_sync(table.create, checkfirst=True)
            except Exception:
                # Skip tables with PostgreSQL-specific syntax
                # (e.g., gen_random_uuid in DEFAULT)
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
        reason = "FastAPI app is unavailable in the current test environment"
        if _MINIMAL_APP_ERROR is not None:
            reason = f"{reason}: {_MINIMAL_APP_ERROR}"
        pytest.skip(reason)

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
    # Import inside fixture to avoid circular dependencies
    import uuid as uuid_module

    from app.models.property import Property, PropertyStatus, PropertyType, TenureType

    # Check if properties table exists, if not skip this fixture
    async with async_session_factory() as session:
        try:
            # Try to query the table to see if it exists
            from sqlalchemy import text as sql_text

            await session.execute(sql_text("SELECT 1 FROM properties LIMIT 1"))
        except Exception:
            # Table doesn't exist (likely due to PostgreSQL-specific DDL in SQLite tests)
            # Create it manually for SQLite
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

        # Create a demo property for advisory service testing
        demo_property = Property(
            id=uuid_module.uuid4(),  # Explicitly set ID for SQLite compatibility
            name="Market Demo Tower",
            address="123 Marina Boulevard",
            postal_code="018989",
            property_type=PropertyType.OFFICE,
            status=PropertyStatus.EXISTING,
            location="POINT(103.8535 1.2830)",  # Singapore coordinates
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

    # Cleanup happens automatically via _reset_database in async_session_factory
