"""Test configuration and shared fixtures."""

from __future__ import annotations

import asyncio
import importlib
import sys
from collections.abc import AsyncGenerator, Callable, Iterator
from contextlib import asynccontextmanager
from types import ModuleType
from typing import Any

import pytest

_sqlalchemy_asyncio = pytest.importorskip(
    "sqlalchemy.ext.asyncio",
    reason=(
        "SQLAlchemy is required for database integration tests; install optional test dependencies to run these checks."
    ),
)

AsyncSession = _sqlalchemy_asyncio.AsyncSession
async_sessionmaker = _sqlalchemy_asyncio.async_sessionmaker
create_async_engine = _sqlalchemy_asyncio.create_async_engine

try:
    from httpx import AsyncClient
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal test envs
    class AsyncClient:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401 - simple stub
            raise RuntimeError("httpx is required for HTTP client tests")

from app.core.database import get_session
from app.main import app
from app.models.base import BaseModel
from app.utils import metrics


_PYTEST_ASYNCIO_STUB_INSTALLED = False
try:
    import pytest_asyncio  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal test envs
    pytest_asyncio = ModuleType("pytest_asyncio")  # type: ignore[assignment]
    pytest_asyncio.fixture = pytest.fixture  # type: ignore[attr-defined]
    sys.modules["pytest_asyncio"] = pytest_asyncio
    _PYTEST_ASYNCIO_STUB_INSTALLED = True


def _noop_prefect_flow(
    *args: Any, **kwargs: Any
) -> Callable[[Callable[..., Any]], Callable[..., Any]] | Callable[..., Any]:
    """Provide a lightweight stand-in for ``prefect.flow`` during tests."""

    if args and callable(args[0]) and len(args) == 1 and not kwargs:
        return args[0]

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return func

    return decorator


@pytest.fixture(autouse=True)
def _ensure_prefect_flow(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Provide a minimal ``prefect.flow`` decorator when Prefect isn't installed."""

    try:
        prefect_module = importlib.import_module("prefect")
    except ModuleNotFoundError:  # pragma: no cover - exercised when Prefect isn't installed
        prefect_module = ModuleType("prefect")
        monkeypatch.setitem(sys.modules, "prefect", prefect_module)
    if not hasattr(prefect_module, "flow"):
        monkeypatch.setattr(prefect_module, "flow", _noop_prefect_flow, raising=False)
    yield


def pytest_unconfigure(config: pytest.Config) -> None:  # pragma: no cover - test cleanup
    if _PYTEST_ASYNCIO_STUB_INSTALLED and sys.modules.get("pytest_asyncio") is pytest_asyncio:
        sys.modules.pop("pytest_asyncio", None)


@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_session_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest.fixture(autouse=True)
def reset_metrics() -> Iterator[None]:
    metrics.reset_metrics()
    yield
    metrics.reset_metrics()


@pytest_asyncio.fixture
async def session(async_session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            for table in reversed(BaseModel.metadata.sorted_tables):
                await session.execute(table.delete())
            await session.commit()


@pytest.fixture
def session_factory(async_session_factory: async_sessionmaker[AsyncSession]) -> Callable[[], AsyncGenerator[AsyncSession, None]]:
    @asynccontextmanager
    async def _context() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory() as session:
            yield session

    def _factory() -> AsyncGenerator[AsyncSession, None]:
        return _context()

    return _factory


@pytest_asyncio.fixture
async def client(async_session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncClient, None]:
    async def _get_session() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _get_session
    async with AsyncClient(app=app, base_url="http://testserver") as http_client:
        yield http_client
    app.dependency_overrides.pop(get_session, None)
