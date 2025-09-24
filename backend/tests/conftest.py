"""Test configuration and shared fixtures."""

from __future__ import annotations

import asyncio
import sys
from collections.abc import AsyncGenerator, Callable, Iterator
from contextlib import asynccontextmanager
from importlib import import_module

import pytest
import pytest_asyncio
from httpx import AsyncClient


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
            sys.modules.setdefault(f"sqlalchemy.{name}", import_module(f"sqlalchemy_pkg_backup.{name}"))


_ensure_sqlalchemy()

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

try:  # pragma: no cover - StaticPool only exists in real SQLAlchemy
    from sqlalchemy.pool import StaticPool
except (ImportError, AttributeError):  # pragma: no cover - fallback for stub implementation
    class StaticPool:  # type: ignore[too-many-ancestors]
        """Placeholder used when running against the in-repo SQLAlchemy stub."""

        pass


from backend.app import models as app_models
from backend.app.core.database import get_session
from backend.app.main import app
from backend.app.models.base import BaseModel
from backend.app.utils import metrics

# Importing ``backend.app.models`` ensures all model metadata is registered.
_ = app_models

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

    app.dependency_overrides[get_session] = _override_get_session
    async with AsyncClient(
        app=app,
        base_url="http://testserver",
        headers={"X-Role": "admin"},
    ) as client:
        yield client

    app.dependency_overrides.pop(get_session, None)
    await _reset_database(async_session_factory)

