"""Test configuration and shared fixtures."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Callable, Iterator
from contextlib import asynccontextmanager
from pathlib import Path
import importlib.util
import sys
from typing import Any

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[2]

if importlib.util.find_spec("structlog") is None and str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

_MISSING_DEPS = [
    name
    for name in ("fastapi", "pydantic", "sqlalchemy")
    if importlib.util.find_spec(name) is None
]

if "sqlalchemy" not in _MISSING_DEPS:
    try:  # pragma: no cover - only exercised when the stub is present
        import sqlalchemy as _sqlalchemy
    except ModuleNotFoundError:  # pragma: no cover - defensive
        pass
    else:
        if getattr(_sqlalchemy, "root_missing_error", None) is not None:
            _MISSING_DEPS.append("sqlalchemy")

if _MISSING_DEPS:  # pragma: no cover - offline test fallback
    pytestmark = pytest.mark.skip(
        reason=f"Required dependencies missing: {', '.join(sorted(_MISSING_DEPS))}"
    )

try:  # pragma: no cover - exercised indirectly via tests
    import pytest_asyncio
except ModuleNotFoundError:  # pragma: no cover - fallback stub for offline testing
    from types import ModuleType

    _pytest_asyncio_stub = ModuleType("pytest_asyncio")
    _pytest_asyncio_stub.fixture = pytest.fixture  # type: ignore[attr-defined]
    sys.modules.setdefault("pytest_asyncio", _pytest_asyncio_stub)
    pytest_asyncio = _pytest_asyncio_stub  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency for API tests
    from httpx import AsyncClient
except ModuleNotFoundError:  # pragma: no cover - fallback stub for offline testing
    class AsyncClient:  # type: ignore[no-redef]
        """Fallback stub used when httpx is not installed."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401 - simple stub
            self._error = ModuleNotFoundError(
                "The optional dependency 'httpx' is required for AsyncClient fixtures. "
                "Install httpx to run API client tests."
            )

        async def __aenter__(self) -> "AsyncClient":  # pragma: no cover - invoked in tests
            raise self._error

        async def __aexit__(self, exc_type, exc, tb) -> bool:  # pragma: no cover - invoked in tests
            return False

try:  # pragma: no cover - optional dependency for database fixtures
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
except ModuleNotFoundError as exc:  # pragma: no cover - fallback stub for offline testing
    class AsyncSession:  # type: ignore[no-redef]
        """Stub used when SQLAlchemy is unavailable."""

    def async_sessionmaker(*args: Any, **kwargs: Any):  # type: ignore[no-redef]
        raise ModuleNotFoundError(
            "SQLAlchemy is required for database fixtures. Install 'sqlalchemy' to run database tests."
        )

    def create_async_engine(*args: Any, **kwargs: Any):  # type: ignore[no-redef]
        raise ModuleNotFoundError(
            "SQLAlchemy is required for database fixtures. Install 'sqlalchemy' to run database tests."
        )

    structlog_module.processors = processors_module  # type: ignore[attr-defined]
    structlog_module.stdlib = stdlib_module  # type: ignore[attr-defined]
    structlog_module.BoundLogger = _StubBoundLogger  # type: ignore[attr-defined]

    sys.modules.setdefault("structlog", structlog_module)
    sys.modules.setdefault("structlog.processors", processors_module)
    sys.modules.setdefault("structlog.stdlib", stdlib_module)

_APP_IMPORT_ERROR: ModuleNotFoundError | None = None

try:  # pragma: no cover - optional dependency for database fixtures
    from app.core.database import get_session
except ModuleNotFoundError as exc:  # pragma: no cover - fallback stub for offline testing
    _APP_IMPORT_ERROR = exc

    async def get_session(*args: Any, **kwargs: Any):  # type: ignore[no-redef]
        raise exc

try:  # pragma: no cover - optional dependency for API fixtures
    from app.main import app
except ModuleNotFoundError as exc:  # pragma: no cover - fallback stub for offline testing
    if _APP_IMPORT_ERROR is None:
        _APP_IMPORT_ERROR = exc
    app = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency for database fixtures
    from app.models.base import BaseModel
except ModuleNotFoundError as exc:  # pragma: no cover - fallback stub for offline testing
    if _APP_IMPORT_ERROR is None:
        _APP_IMPORT_ERROR = exc

    class _BaseModelMetadataStub:
        sorted_tables: list = []

        def create_all(self, *args: Any, **kwargs: Any) -> None:
            raise exc

    class BaseModel:  # type: ignore[no-redef]
        metadata = _BaseModelMetadataStub()

try:  # pragma: no cover - optional dependency for storage fixtures
    from app.services.storage import get_storage_service, reset_storage_service
except ModuleNotFoundError:  # pragma: no cover - fallback stubs for offline testing
    def get_storage_service():  # type: ignore[no-redef]
        raise ModuleNotFoundError(
            "Storage service dependencies are unavailable. Install optional dependencies to run storage tests."
        )

    def reset_storage_service():  # type: ignore[no-redef]
        return None

from app.utils import metrics


@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


if _MISSING_DEPS:
    @pytest.fixture
    def async_session_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
        pytest.skip("Database fixtures require fastapi, pydantic, and sqlalchemy")
        yield  # pragma: no cover
else:

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


if _MISSING_DEPS:
    @pytest.fixture
    def session(async_session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
        pytest.skip("Database fixtures require fastapi, pydantic, and sqlalchemy")
        yield  # pragma: no cover
else:

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


@pytest.fixture
def storage_service(tmp_path, monkeypatch):
    try:
        base_path = tmp_path / "storage"
        base_path.mkdir()
        monkeypatch.setenv("STORAGE_LOCAL_PATH", str(base_path))
        reset_storage_service()
        service = get_storage_service()
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency missing
        pytest.skip(str(exc))
        return None
    try:
        yield service
    finally:
        reset_storage_service()


@pytest_asyncio.fixture
async def client(async_session_factory: async_sessionmaker[AsyncSession], storage_service) -> AsyncGenerator[AsyncClient, None]:
    if app is None:  # pragma: no cover - triggered only when optional deps missing
        raise ModuleNotFoundError(
            "FastAPI application dependencies are unavailable. Install optional dependencies to run API tests."
        ) from _APP_IMPORT_ERROR

    async def _get_session() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _get_session
    async with AsyncClient(app=app, base_url="http://testserver") as http_client:
        yield http_client
    app.dependency_overrides.pop(get_session, None)
