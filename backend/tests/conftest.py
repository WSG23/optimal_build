"""Test configuration and shared fixtures."""

from __future__ import annotations

import asyncio
import sys
from collections.abc import AsyncGenerator, Callable, Iterator
from contextlib import asynccontextmanager
from importlib import import_module
from pathlib import Path

import pytest
from httpx import AsyncClient


def _find_repo_root(current: Path) -> Path:
    for parent in current.parents:
        if (parent / ".git").exists():
            return parent
    return current.parents[-1]


_REPO_ROOT = _find_repo_root(Path(__file__).resolve())
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:  # pragma: no cover - async plugin is optional when running unit tests
    import pytest_asyncio
except ModuleNotFoundError:  # pragma: no cover - fallback to bundled shim
    pytest_asyncio = import_module("backend.pytest_asyncio")
    sys.modules.setdefault("pytest_asyncio", pytest_asyncio)


def _ensure_sqlalchemy() -> None:
    """Expose the bundled lightweight SQLAlchemy implementation if needed."""

    try:  # pragma: no cover - exercised implicitly when SQLAlchemy is available
        import sqlalchemy  # noqa: F401
    except ModuleNotFoundError:
        pkg = import_module("sqlalchemy_pkg_backup")
        sys.modules.setdefault("sqlalchemy", pkg)

        for name in (
            "ext",
            "ext.asyncio",
            "orm",
            "engine",
            "sql",
            "dialects",
            "dialects.postgresql",
            "types",
            "pool",
        ):
            try:
                module = import_module(f"sqlalchemy_pkg_backup.{name}")
            except ModuleNotFoundError:
                continue
            sys.modules.setdefault(f"sqlalchemy.{name}", module)


_ensure_sqlalchemy()

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

try:  # pragma: no cover - StaticPool only exists in real SQLAlchemy
    from sqlalchemy.pool import StaticPool
except (ImportError, AttributeError):  # pragma: no cover - fallback for stub implementation
    class StaticPool:  # type: ignore[too-many-ancestors]
        """Placeholder used when running against the in-repo SQLAlchemy stub."""

        pass


from app import models as app_models
from app.core import database as database_module
from app.core.database import get_session
from app.main import app
from app.models.base import BaseModel
from app.utils import metrics
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

# Importing ``app.models`` ensures all model metadata is registered.
_ = app_models


if "projects" not in getattr(BaseModel.metadata, "tables", {}):
    class _ProjectStub(BaseModel):
        """Minimal project table used for tests that only require an ID."""

        __tablename__ = "projects"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        name: Mapped[str] = mapped_column(String(120), nullable=False, default="Test Project")

_SORTED_TABLES = tuple(BaseModel.metadata.sorted_tables)


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
        await session.execute(table.delete())
    await session.commit()


async def _reset_database(factory: async_sessionmaker[AsyncSession]) -> None:
    """Clear all persisted data using a fresh session."""

    async with factory() as session:
        await _truncate_all(session)


@pytest_asyncio.fixture(scope="session")
async def flow_session_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    """Provide a shared async session factory backed by SQLite."""

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def async_session_factory(
    flow_session_factory: async_sessionmaker[AsyncSession],
) -> async_sessionmaker[AsyncSession]:
    """Alias for the shared async session factory."""

    return flow_session_factory


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
) -> Callable[[], AsyncGenerator[AsyncSession, None]]:
    """Return an async context manager that yields a clean session."""

    @asynccontextmanager
    async def _factory() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory() as db_session:
            try:
                yield db_session
            finally:
                await _truncate_all(db_session)

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

    original_session_factory = database_module.AsyncSessionLocal
    database_module.AsyncSessionLocal = async_session_factory
    app.dependency_overrides[get_session] = _override_get_session
    try:
        async with AsyncClient(
            app=app,
            base_url="http://testserver",
            headers={"X-Role": "admin"},
        ) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_session, None)
        database_module.AsyncSessionLocal = original_session_factory
        await _reset_database(async_session_factory)

