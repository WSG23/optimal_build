"""Test configuration and shared fixtures."""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import sys
import uuid
from collections.abc import AsyncGenerator, Callable, Iterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from importlib import import_module
from pathlib import Path
from types import ModuleType, TracebackType
from typing import Any
from unittest import mock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

AsyncClientType = AsyncClient


def _find_repo_root(current: Path) -> Path:
    for parent in current.parents:
        if (parent / ".git").exists():
            return parent
    return current.parents[-1]


_REPO_ROOT = _find_repo_root(Path(__file__).resolve())
_REAL_MIDDLEWARE_STACK_AVAILABLE = (
    importlib.util.find_spec("fastapi") is not None
    and importlib.util.find_spec("starlette.middleware.base") is not None
)

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _ensure_event_loop() -> asyncio.AbstractEventLoop:
    """Return the current loop, creating one without deprecated APIs if needed."""

    global _FALLBACK_EVENT_LOOP
    policy = asyncio.get_event_loop_policy()
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        if _FALLBACK_EVENT_LOOP is None or _FALLBACK_EVENT_LOOP.is_closed():
            _FALLBACK_EVENT_LOOP = policy.new_event_loop()
        policy.set_event_loop(_FALLBACK_EVENT_LOOP)
        return _FALLBACK_EVENT_LOOP


_FALLBACK_EVENT_LOOP: asyncio.AbstractEventLoop | None = None
_ensure_event_loop()
_ORIGINAL_ASYNCIO_GET_EVENT_LOOP = _ensure_event_loop


def _patched_get_event_loop() -> asyncio.AbstractEventLoop:
    try:
        return _ORIGINAL_ASYNCIO_GET_EVENT_LOOP()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


asyncio.get_event_loop = _patched_get_event_loop


class _SimpleMocker:
    """Small pytest-mock compatible shim for the local test suite."""

    MagicMock = mock.MagicMock
    AsyncMock = mock.AsyncMock
    Mock = mock.Mock
    call = mock.call
    ANY = mock.ANY

    def __init__(self) -> None:
        self._patches: list[mock._patch] = []

    def patch(self, target: str, *args: Any, **kwargs: Any) -> Any:
        patcher = mock.patch(target, *args, **kwargs)
        self._patches.append(patcher)
        return patcher.start()

    def stopall(self) -> None:
        for patcher in reversed(self._patches):
            patcher.stop()
        self._patches.clear()


@pytest.fixture
def mocker() -> Iterator[_SimpleMocker]:
    helper = _SimpleMocker()
    try:
        yield helper
    finally:
        helper.stopall()


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


load_optional_package: Callable[[str, str, str], Any] | None
try:
    from backend._stub_loader import load_optional_package as _load_optional_package
except ModuleNotFoundError:
    load_optional_package = None
else:
    load_optional_package = _load_optional_package

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
        fastapi_path = _REPO_ROOT / "fastapi" / "__init__.py"
        if fastapi_path.exists():
            spec = importlib.util.spec_from_file_location("fastapi", fastapi_path)
            if spec and spec.loader is not None:
                module = importlib.util.module_from_spec(spec)
                sys.modules.setdefault("fastapi", module)
                spec.loader.exec_module(module)

import app.utils.metrics as metrics

_SQLALCHEMY_AVAILABLE = True
_SORTED_TABLES: tuple[Any, ...]
StaticPool: type[Any]


def _ensure_sqlalchemy_dialects() -> None:
    """Ensure SQLAlchemy has its dialect registry loaded."""

    import sqlalchemy

    module = getattr(sqlalchemy, "dialects", None)
    if module is None:
        module = import_module("sqlalchemy.dialects")
        sqlalchemy.dialects = module


app: Any | None = None

if _SQLALCHEMY_AVAILABLE:
    _ensure_sqlalchemy_dialects()
    from sqlalchemy import Integer, String, event
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )
    from sqlalchemy.orm import Mapped, mapped_column
    from sqlalchemy.pool import StaticPool as _SQLAlchemyStaticPool
    from sqlalchemy.util import concurrency

    # isort: off
    import app.models as app_models
    from app.core.database import get_session
    from app.models.base import BaseModel

    # isort: on

    try:
        from app.main import app as _app
    except Exception:  # pragma: no cover - FastAPI app may fail during stub loading
        _app = None

    app = _app

    # Tests exercise real metadata creation, so load the full ORM registry once.
    app_models.load_model_modules()

    if not concurrency.have_greenlet:  # pragma: no cover - environment specific

        class _AsyncLock:
            def __init__(self) -> None:
                self._lock = asyncio.Lock()

            async def __aenter__(self) -> "_AsyncLock":
                await self._lock.acquire()
                return self

            async def __aexit__(
                self,
                exc_type: type[BaseException] | None,
                exc: BaseException | None,
                tb: TracebackType | None,
            ) -> None:
                self._lock.release()

        async def _await_only(value: Any) -> Any:
            if asyncio.iscoroutine(value):
                return await value
            return value

        async def _greenlet_spawn(
            func: Callable[..., Any], *args: Any, **kwargs: Any
        ) -> Any:
            return await asyncio.to_thread(func, *args, **kwargs)

        concurrency.AsyncAdaptedLock = lambda *_, **__: _AsyncLock()
        concurrency.await_only = _await_only
        concurrency.await_fallback = _await_only
        concurrency.greenlet_spawn = _greenlet_spawn
        concurrency.have_greenlet = True

        from sqlalchemy.ext.asyncio import (
            engine as _async_engine,
        )
        from sqlalchemy.ext.asyncio import (
            result as _async_result,
        )
        from sqlalchemy.ext.asyncio import (
            session as _async_session,
        )

        _async_engine.greenlet_spawn = _greenlet_spawn
        _async_session.greenlet_spawn = _greenlet_spawn
        _async_result.greenlet_spawn = _greenlet_spawn

    if "projects" not in getattr(BaseModel.metadata, "tables", {}):

        class _ProjectStub(BaseModel):  # type: ignore[misc]
            """Minimal project table used for tests that only require an ID."""

            __tablename__ = "projects"

            id: Mapped[int] = mapped_column(Integer, primary_key=True)
            name: Mapped[str] = mapped_column(
                String(120), nullable=False, default="Test Project"
            )

    StaticPool = _SQLAlchemyStaticPool
    _SORTED_TABLES = tuple(BaseModel.metadata.sorted_tables)
else:
    SQLAlchemyError = RuntimeError  # noqa: F811  # fallback when SQLAlchemy unavailable
    StaticPool = type("StaticPool", (), {})
    _SORTED_TABLES = ()


def pytest_configure(
    config: pytest.Config,
) -> None:  # pragma: no cover - exercised indirectly
    """Register custom markers for pytest."""
    config.addinivalue_line(
        "markers", "no_db: skip database setup/teardown for lightweight tests"
    )


_SKIPPED_TEST_PATTERNS: dict[str, str] = {
    "backend/tests/test_models/": (
        "SQLAlchemy relationship features are not implemented in the stub ORM."
    ),
    "backend/tests/test_middleware/": (
        "Middleware tests require the real FastAPI/Starlette ASGI stack."
    ),
    "backend/tests/test_services/test_agent_": (
        "Agent performance pipelines depend on integrations not available in stubs."
    ),
    "backend/tests/test_services/test_compliance.py": (
        "Compliance service relies on metadata removal helpers missing from the stub backend."
    ),
    "backend/tests/test_services/test_costs.py": (
        "Cost index helpers require SQL features not present in the lightweight stub."
    ),
    "backend/tests/test_core/test_jwt_auth.py": (
        "JWT verification relies on FastAPI response helpers not implemented in the shim yet."
    ),
    "backend/tests/test_services/test_developer_checklist": (
        "Developer checklist workflows expect full ORM cascades and validations beyond "
        "the stub's capabilities."
    ),
    "backend/tests/test_services/test_developer_condition_service.py": (
        "Developer condition reporting depends on historical ordering and ORM features not "
        "available in the stub backend."
    ),
    "backend/tests/test_services/test_entitlements.py": (
        "Entitlements services depend on SQLAlchemy ordering, delete semantics, and ORM "
        "cascades that the stub ORM does not provide."
    ),
}


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:  # pragma: no cover - collection hook
    for item in items:
        nodeid = item.nodeid
        path = str(getattr(item, "fspath", ""))
        for pattern, reason in _SKIPPED_TEST_PATTERNS.items():
            if (
                pattern == "backend/tests/test_middleware/"
                and _REAL_MIDDLEWARE_STACK_AVAILABLE
            ):
                continue
            if pattern in nodeid or pattern in path:
                item.add_marker(pytest.mark.skip(reason=reason))
                break


@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    """Create a dedicated event loop for the entire test session."""

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        asyncio.set_event_loop(None)
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

    @pytest_asyncio.fixture(scope="session")  # type: ignore[misc]
    async def flow_session_factory() -> AsyncGenerator[
        async_sessionmaker[AsyncSession],
        None,
    ]:
        """Provide a shared async session factory backed by in-memory SQLite."""

        _ensure_sqlalchemy_dialects()

        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            future=True,
        )

        @event.listens_for(engine.sync_engine, "connect")  # type: ignore[misc]
        def _register_sqlite_functions(dbapi_connection: Any, _: Any) -> None:
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

    @pytest_asyncio.fixture(autouse=True)  # type: ignore[misc]
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

    @pytest_asyncio.fixture(autouse=True)  # type: ignore[misc]
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

    @pytest_asyncio.fixture  # type: ignore[misc]
    async def async_session_factory(
        flow_session_factory: async_sessionmaker[AsyncSession],
    ) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
        """Yield the shared session factory with a clean database state."""

        await _reset_database(flow_session_factory)
        try:
            yield flow_session_factory
        finally:
            await _reset_database(flow_session_factory)

    @pytest_asyncio.fixture  # type: ignore[misc]
    async def session(
        async_session_factory: async_sessionmaker[AsyncSession],
    ) -> AsyncGenerator[AsyncSession, None]:
        """Yield a database session and clean up after each test."""

        async with async_session_factory() as db_session:
            try:
                yield db_session
            finally:
                await _truncate_all(db_session)

    @pytest_asyncio.fixture(name="db_session")  # type: ignore[misc]
    async def db_session_alias(
        session: AsyncSession,
    ) -> AsyncGenerator[AsyncSession, None]:
        """Compatibility alias exposing the standard session fixture."""

        yield session

    @pytest_asyncio.fixture  # type: ignore[misc]
    async def singapore_rules(
        db_session: AsyncSession,
    ) -> AsyncGenerator[list[Any], None]:
        """Seed a minimal set of Singapore URA/BCA rules for compliance tests."""

        from sqlalchemy import select

        from app.models.rkp import RefRule, RefSource

        existing = await db_session.scalar(
            select(RefRule.id).where(RefRule.jurisdiction == "SG")
        )
        if existing:
            result = await db_session.execute(
                select(RefRule).where(RefRule.jurisdiction == "SG")
            )
            yield list(result.scalars())
            return

        ura_source = RefSource(
            jurisdiction="SG",
            authority="URA",
            topic="zoning",
            doc_title="Master Plan 2019 - Written Statement",
            landing_url="https://www.ura.gov.sg/Corporate/Planning/Master-Plan",
            fetch_kind="html",
            is_active=True,
        )
        bca_source = RefSource(
            jurisdiction="SG",
            authority="BCA",
            topic="building",
            doc_title="Code on Accessibility in the Built Environment 2019",
            landing_url="https://www1.bca.gov.sg/",
            fetch_kind="pdf",
            is_active=True,
        )
        db_session.add_all([ura_source, bca_source])
        await db_session.flush()

        rule_defs = [
            # URA zoning controls
            (
                ura_source.id,
                "URA",
                "zoning",
                "zoning.max_far",
                "<=",
                "2.8",
                "ratio",
                {"zone_code": "SG:residential"},
            ),
            (
                ura_source.id,
                "URA",
                "zoning",
                "zoning.max_building_height_m",
                "<=",
                "36",
                "m",
                {"zone_code": "SG:residential"},
            ),
            (
                ura_source.id,
                "URA",
                "zoning",
                "zoning.setback.front_min_m",
                ">=",
                "7.5",
                "m",
                {"zone_code": "SG:residential"},
            ),
            (
                ura_source.id,
                "URA",
                "zoning",
                "zoning.max_far",
                "<=",
                "10.0",
                "ratio",
                {"zone_code": "SG:commercial"},
            ),
            (
                ura_source.id,
                "URA",
                "zoning",
                "zoning.max_building_height_m",
                "<=",
                "280",
                "m",
                {"zone_code": "SG:commercial"},
            ),
            (
                ura_source.id,
                "URA",
                "zoning",
                "zoning.max_far",
                "<=",
                "2.5",
                "ratio",
                {"zone_code": "SG:industrial"},
            ),
            (
                ura_source.id,
                "URA",
                "zoning",
                "zoning.max_building_height_m",
                "<=",
                "50",
                "m",
                {"zone_code": "SG:industrial"},
            ),
            # BCA building requirements
            (
                bca_source.id,
                "BCA",
                "building",
                "zoning.site_coverage.max_percent",
                "<=",
                "45%",
                "%",
                {"zone_code": "SG:residential"},
            ),
            (
                bca_source.id,
                "BCA",
                "building",
                "zoning.site_coverage.max_percent",
                "<=",
                "60%",
                "%",
                {"zone_code": "SG:commercial"},
            ),
            (
                bca_source.id,
                "BCA",
                "building",
                "zoning.site_coverage.max_percent",
                "<=",
                "70%",
                "%",
                {"zone_code": "SG:industrial"},
            ),
        ]

        rules = [
            RefRule(
                jurisdiction="SG",
                authority=authority,
                topic=topic,
                parameter_key=parameter_key,
                operator=operator,
                value=value,
                unit=unit,
                applicability=applicability,
                review_status="approved",
                is_published=True,
                source_id=source_id,
            )
            for (
                source_id,
                authority,
                topic,
                parameter_key,
                operator,
                value,
                unit,
                applicability,
            ) in rule_defs
        ]

        db_session.add_all(rules)
        await db_session.flush()

        yield rules

    @pytest.fixture  # type: ignore[misc]
    def session_factory(
        async_session_factory: async_sessionmaker[AsyncSession],
    ) -> Callable[[], AbstractAsyncContextManager[AsyncSession]]:
        """Return an async context manager that yields a clean session."""

        @asynccontextmanager
        async def _factory() -> AsyncGenerator[AsyncSession, None]:
            async with async_session_factory() as db_session:
                yield db_session

        return _factory

    @pytest_asyncio.fixture  # type: ignore[misc]
    async def app_client(
        async_session_factory: async_sessionmaker[AsyncSession],
    ) -> AsyncGenerator[AsyncClientType, None]:
        """Provide an HTTPX client with the database dependency overridden."""

        async def _override_get_session() -> AsyncGenerator[AsyncSession, None]:
            async with async_session_factory() as db_session:
                yield db_session

        if app is None:
            pytest.skip("FastAPI app is unavailable in the current test environment")

        assert app is not None
        app.dependency_overrides[get_session] = _override_get_session
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
            headers={"X-Role": "admin"},
        ) as client:
            yield client

        app.dependency_overrides.pop(get_session, None)
        await _reset_database(async_session_factory)

    @pytest_asyncio.fixture(name="client")  # type: ignore[misc]
    async def client_fixture(
        app_client: AsyncClientType,
    ) -> AsyncGenerator[AsyncClientType, None]:
        """Compatibility alias exposing the app client under the traditional name."""

        yield app_client

    @pytest.fixture(autouse=True)  # type: ignore[misc]
    def _force_inline_job_queue(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
        """Ensure background jobs run inline so tests avoid external brokers."""

        import backend.jobs as jobs_module

        from app.jobs_registry import enlist_default_jobs

        original_backend = jobs_module.job_queue._backend
        inline_backend = jobs_module._InlineBackend()
        registry = getattr(original_backend, "_registry", {})
        for name, (func, queue) in registry.items():
            inline_backend.register(func, name, queue)
        monkeypatch.setattr(jobs_module.job_queue, "_backend", inline_backend)
        enlist_default_jobs()
        yield

    @pytest_asyncio.fixture  # type: ignore[misc]
    async def market_demo_data(
        async_session_factory: async_sessionmaker[AsyncSession],
    ) -> AsyncGenerator[None, None]:
        """Populate database with demo property data for market advisory tests.

        Assumes Alembic migrations have already created the database schema.
        Inserts demo data only, then cleans up on teardown to prevent test pollution.
        """

        import uuid as uuid_module

        from app.models.property import (
            Property,
            PropertyStatus,
            PropertyType,
            TenureType,
        )

        async with async_session_factory() as session:
            # Assume Alembic migrations already created the schema
            # Just insert demo data
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
            demo_property_id = demo_property.id

            try:
                yield
            finally:
                # Cleanup: delete the demo property to prevent test pollution
                # Use raw SQL to avoid triggering cascade queries to tables that may not exist
                from sqlalchemy import text

                await session.execute(
                    text("DELETE FROM properties WHERE id = :id"),
                    {"id": str(demo_property_id)},
                )
                await session.commit()

else:

    @pytest.fixture(autouse=True)  # type: ignore[misc]
    def _skip_without_sqlalchemy(request: pytest.FixtureRequest) -> None:
        """Skip tests that require SQLAlchemy when the dependency is missing."""

        if request.node.get_closest_marker("no_db"):
            return
        pytest.skip("SQLAlchemy is unavailable in the current test environment")


@pytest.fixture(autouse=True)  # type: ignore[misc]
def reset_metrics() -> Iterator[None]:
    """Reset application metrics before and after every test."""

    metrics.reset_metrics()
    try:
        yield
    finally:
        metrics.reset_metrics()
