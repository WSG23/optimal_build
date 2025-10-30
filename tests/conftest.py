"""Shared fixtures for reference tests."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_ROOT = _PROJECT_ROOT / "backend"
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

# Ensure SQLAlchemy is loaded BEFORE attempting any imports
try:
    from backend._sqlalchemy_stub import ensure_sqlalchemy
    _SQLALCHEMY_AVAILABLE = ensure_sqlalchemy()
    if not _SQLALCHEMY_AVAILABLE:
        # Try importing directly if ensure_sqlalchemy didn't find it
        import importlib
        try:
            importlib.import_module("sqlalchemy")
            _SQLALCHEMY_AVAILABLE = True
        except Exception:
            pass
except (ModuleNotFoundError, ImportError):
    _SQLALCHEMY_AVAILABLE = False

# IMPORTANT: Patch SQLite type compiler BEFORE any other imports
# This ensures SQLite can handle PostgreSQL-specific types (UUID, JSONB)
if _SQLALCHEMY_AVAILABLE:
    try:
        from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
    except ImportError:
        SQLiteTypeCompiler = None
else:
    SQLiteTypeCompiler = None

if SQLiteTypeCompiler is not None:
    if not hasattr(SQLiteTypeCompiler, "visit_UUID"):

        def _visit_UUID(self, _type, **_):  # pragma: no cover
            return "CHAR(36)"

        SQLiteTypeCompiler.visit_UUID = _visit_UUID

    if not hasattr(SQLiteTypeCompiler, "visit_JSONB"):

        def _visit_JSONB(self, _type, **_):  # pragma: no cover
            return "TEXT"

        SQLiteTypeCompiler.visit_JSONB = _visit_JSONB

from types import ModuleType, SimpleNamespace

# Jose stubs
try:
    from jose import JWTError, jwt  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    jose_stub = ModuleType("jose")

    class JWTError(Exception):
        pass

    def _encode(payload, *_args, **_kwargs):
        return "token"

    def _decode(token, *_args, **_kwargs):
        return {}

    jose_stub.JWTError = JWTError
    jose_stub.jwt = SimpleNamespace(encode=_encode, decode=_decode)
    sys.modules.setdefault("jose", jose_stub)
else:
    JWTError = JWTError  # re-export for callers
    jwt = jwt  # re-export for callers

import importlib
from importlib import import_module

import pytest

if _SQLALCHEMY_AVAILABLE:
    try:
        from sqlalchemy.dialects.postgresql import UUID as PGUUID  # type: ignore
    except (ModuleNotFoundError, ImportError):  # pragma: no cover
        pg_module = ModuleType("sqlalchemy.dialects.postgresql")

        class _UUID:
            def __init__(self, *_, **__):
                pass

        pg_module.UUID = _UUID
        sys.modules.setdefault("sqlalchemy.dialects.postgresql", pg_module)
        PGUUID = _UUID
else:
    pg_module = ModuleType("sqlalchemy.dialects.postgresql")

    class _UUID:
        def __init__(self, *_, **__):
            pass

    pg_module.UUID = _UUID
    sys.modules.setdefault("sqlalchemy.dialects.postgresql", pg_module)
    PGUUID = _UUID

try:
    import geoalchemy2.admin.dialects.sqlite as _geo_sqlite
except ModuleNotFoundError:  # pragma: no cover
    _geo_sqlite = None

if _geo_sqlite is not None:

    def _noop_after_create(*_, **__):  # pragma: no cover
        return None

    class _NoopDialect:
        def after_create(self, *_, **__):  # pragma: no cover
            return None

    _geo_sqlite.select_dialect = lambda name: _NoopDialect()

try:  # pragma: no cover - optional dependency for async fixtures
    import pytest_asyncio
except ModuleNotFoundError:  # pragma: no cover - fallback stub when plugin missing
    pytest_asyncio = ModuleType("pytest_asyncio")
    pytest_asyncio.fixture = pytest.fixture  # type: ignore[attr-defined]
    sys.modules.setdefault("pytest_asyncio", pytest_asyncio)

if os.environ.get("ENABLE_BACKEND_TEST_FIXTURES") == "1":
    try:
        from backend.tests import (  # noqa: F401 - ensure fallback stubs are registered
            conftest as backend_conftest,
        )
    except Exception:  # pragma: no cover - fallback when backend fixtures unavailable
        backend_conftest = SimpleNamespace(
            flow_session_factory=None,
            async_session_factory=None,
            session=None,
            session_factory=None,
            reset_metrics=lambda *args, **kwargs: None,
            app_client=None,
            client_fixture=None,
        )
else:  # pragma: no cover - default to lightweight stubs
    backend_conftest = SimpleNamespace(
        flow_session_factory=None,
        async_session_factory=None,
        session=None,
        session_factory=None,
        reset_metrics=lambda *args, **kwargs: None,
        app_client=None,
        client_fixture=None,
    )


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Provide a session-scoped event loop compatible with session fixtures."""

    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()


def _missing_fixture(*_args, **_kwargs):
    raise RuntimeError("backend test fixtures unavailable")


# Re-export backend fixtures in this namespace for pytest discovery.
_backend_flow_session_factory = getattr(
    backend_conftest, "flow_session_factory", _missing_fixture
)

# Only define our own fixtures if backend fixtures are not available
if _backend_flow_session_factory in (None, _missing_fixture):
    pytest_plugins = []
    from collections.abc import AsyncGenerator
    from contextlib import asynccontextmanager

    # Only skip if we're supposed to use local fixtures AND SQLAlchemy is not available
    if not _SQLALCHEMY_AVAILABLE and os.environ.get("ENABLE_BACKEND_TEST_FIXTURES") != "1":
        pytest.skip("SQLAlchemy is required for test fixtures", allow_module_level=True)

    import app.utils.metrics as _metrics_module
    from app.core.database import get_session as _get_session
    from app.models.base import BaseModel as _FallbackBaseModel

    try:
        from app.main import app as _fastapi_app
    except Exception:  # pragma: no cover - FastAPI app unavailable
        _fastapi_app = None
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )

    from httpx import AsyncClient as _AsyncClient

    try:
        from sqlalchemy.pool import StaticPool as _StaticPool
    except (ImportError, AttributeError):  # pragma: no cover - stub fallback

        class _StaticPool:  # type: ignore[too-many-ancestors]
            """Fallback StaticPool used when SQLAlchemy pool is unavailable."""

            pass

    _SORTED_TABLES = tuple(_FallbackBaseModel.metadata.sorted_tables)

    async def _truncate_all(session: AsyncSession) -> None:
        await session.rollback()
        for table in reversed(_SORTED_TABLES):
            await session.execute(table.delete())
        await session.commit()

    async def _reset_database(factory: async_sessionmaker[AsyncSession]) -> None:
        async with factory() as db_session:
            await _truncate_all(db_session)

    @pytest_asyncio.fixture(scope="session")
    async def flow_session_factory() -> (
        AsyncGenerator[async_sessionmaker[AsyncSession], None]
    ):
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=_StaticPool,
            future=True,
        )
        async with engine.begin() as conn:
            await conn.run_sync(_FallbackBaseModel.metadata.create_all)

        factory = async_sessionmaker(engine, expire_on_commit=False)

        override_targets: list[tuple[ModuleType, object]] = []
        for module_name in (
            "app.core.database",
            "backend.flows.watch_fetch",
            "backend.flows.parse_segment",
            "backend.flows.sync_products",
        ):
            try:
                module = import_module(module_name)
            except ModuleNotFoundError:  # pragma: no cover - optional modules
                continue
            previous = getattr(module, "AsyncSessionLocal", None)
            module.AsyncSessionLocal = factory
            override_targets.append((module, previous))

        try:
            yield factory
        finally:
            for module, previous in override_targets:
                if previous is None:
                    try:
                        delattr(module, "AsyncSessionLocal")
                    except AttributeError:  # pragma: no cover - already absent
                        pass
                else:
                    module.AsyncSessionLocal = previous
            await engine.dispose()

    @pytest_asyncio.fixture(autouse=True)
    async def _cleanup_flow_session_factory(flow_session_factory):
        await _reset_database(flow_session_factory)
        try:
            yield
        finally:
            await _reset_database(flow_session_factory)

    @pytest_asyncio.fixture
    async def async_session_factory(flow_session_factory):
        await _reset_database(flow_session_factory)
        try:
            yield flow_session_factory
        finally:
            await _reset_database(flow_session_factory)

    @pytest_asyncio.fixture
    async def session(async_session_factory):
        async with async_session_factory() as db_session:
            try:
                yield db_session
            finally:
                await _truncate_all(db_session)

    @pytest.fixture
    def session_factory(async_session_factory):
        @asynccontextmanager
        async def _factory():
            async with async_session_factory() as db_session:
                yield db_session

        return _factory

    @pytest.fixture(autouse=True)
    def reset_metrics():
        _metrics_module.reset_metrics()
        try:
            yield
        finally:
            _metrics_module.reset_metrics()

    @pytest_asyncio.fixture
    async def app_client(async_session_factory):
        if _fastapi_app is None:
            pytest.skip("FastAPI app is unavailable in the current test environment")

        async def _override_get_session():
            async with async_session_factory() as db_session:
                yield db_session

        _fastapi_app.dependency_overrides[_get_session] = _override_get_session
        async with _AsyncClient(
            app=_fastapi_app,
            base_url="http://testserver",
            headers={"X-Role": "admin"},
        ) as client_instance:
            yield client_instance
        _fastapi_app.dependency_overrides.pop(_get_session, None)
        await _reset_database(async_session_factory)

    @pytest_asyncio.fixture(name="client")
    async def client_fixture(app_client):
        yield app_client

    client = client_fixture
else:
    pytest_plugins = ["backend.tests.conftest"]
    flow_session_factory = _backend_flow_session_factory
    async_session_factory = getattr(
        backend_conftest, "async_session_factory", _missing_fixture
    )
    session = getattr(backend_conftest, "session", _missing_fixture)
    session_factory = getattr(backend_conftest, "session_factory", _missing_fixture)
    reset_metrics = getattr(backend_conftest, "reset_metrics", _missing_fixture)
    app_client = getattr(backend_conftest, "app_client", _missing_fixture)
    client = getattr(backend_conftest, "client_fixture", _missing_fixture)


from backend.app.core import database as app_database

base_module = importlib.import_module("backend.app.models.base")
app_base_module = importlib.import_module("app.models.base")
if not hasattr(base_module, "TimestampMixin"):

    class TimestampMixin:  # pragma: no cover - compatibility stub
        created_at = None
        updated_at = None

    base_module.TimestampMixin = TimestampMixin
    if not hasattr(app_base_module, "TimestampMixin"):
        app_base_module.TimestampMixin = TimestampMixin


base_module = sys.modules.get("backend.app.models.base")
app_base_module = sys.modules.get("app.models.base")
if base_module is not None and not hasattr(base_module, "TimestampMixin"):

    class _TimestampMixin:
        created_at = None
        updated_at = None

    base_module.TimestampMixin = _TimestampMixin
    if app_base_module is not None and not hasattr(app_base_module, "TimestampMixin"):
        app_base_module.TimestampMixin = _TimestampMixin

from app.models.base import BaseModel as _BaseModel

if not hasattr(_BaseModel.__class__, "metadata"):
    _BaseModel = _BaseModel  # pragma: no cover
if not hasattr(_BaseModel, "TimestampMixin") and "TimestampMixin" not in globals():

    class TimestampMixinStub:
        created_at = None
        updated_at = None

    backend_base_module = sys.modules.get("backend.app.models.base")
    if backend_base_module is not None:
        backend_base_module.TimestampMixin = TimestampMixinStub
    app_base_module = sys.modules.get("app.models.base")
    if app_base_module is not None and not hasattr(app_base_module, "TimestampMixin"):
        app_base_module.TimestampMixin = TimestampMixinStub
from backend.scripts.seed_market_demo import seed_market_demo
from backend.scripts.seed_nonreg import seed_nonregulated_reference_data


def pytest_configure(config: pytest.Config) -> None:
    """Register project-specific markers to silence pytest warnings."""

    config.addinivalue_line(
        "markers", "asyncio: mark test as requiring asyncio event loop support"
    )


@pytest_asyncio.fixture(autouse=True)
async def _override_app_database(monkeypatch):
    async_session_factory = getattr(backend_conftest, "async_session_factory", None)
    if async_session_factory in (None, _missing_fixture):
        yield
        return
    """Ensure application session factories use the in-memory test database."""

    monkeypatch.setattr(
        app_database, "AsyncSessionLocal", async_session_factory, raising=False
    )

    sync_products = import_module("backend.flows.sync_products")
    watch_fetch = import_module("backend.flows.watch_fetch")
    parse_segment = import_module("backend.flows.parse_segment")

    for module in (sync_products, watch_fetch, parse_segment):
        monkeypatch.setattr(
            module, "AsyncSessionLocal", async_session_factory, raising=False
        )
    try:
        yield
    except Exception:  # pragma: no cover - best-effort fallback
        return


@pytest_asyncio.fixture
async def reference_data(async_session_factory):
    """Populate non-regulated reference data for tests that require it."""

    if async_session_factory in (None, _missing_fixture):  # pragma: no cover - safety
        yield None
        return

    async with async_session_factory() as session:
        await seed_nonregulated_reference_data(session, commit=True)
    yield True


@pytest_asyncio.fixture
async def market_demo_data(async_session_factory):
    """Populate representative market intelligence demo data."""

    if async_session_factory in (None, _missing_fixture):  # pragma: no cover - safety
        yield None
        return

    async with async_session_factory() as session:
        await seed_market_demo(session, reset_existing=True)
    yield True
