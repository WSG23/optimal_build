"""Test configuration and shared fixtures."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Callable, Iterator
from contextlib import asynccontextmanager
from pathlib import Path
import importlib.util
import sys

import pytest

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
    _PROJECT_ROOT = Path(__file__).resolve().parents[2]
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))
    pytestmark = pytest.mark.skip(
        reason=f"Required dependencies missing: {', '.join(sorted(_MISSING_DEPS))}"
    )

try:  # pragma: no cover - exercised indirectly via tests
    import pytest_asyncio
except ModuleNotFoundError:  # pragma: no cover - fallback stub for offline testing
    import contextvars
    import inspect
    from typing import Any

    from _pytest.fixtures import call_fixture_func

    _ASYNC_FIXTURE_MARKER = "_pytest_asyncio_is_async_fixture"
    _CURRENT_LOOP: contextvars.ContextVar[asyncio.AbstractEventLoop | None] = (
        contextvars.ContextVar("pytest_asyncio_current_loop", default=None)
    )

    class _AsyncioStub:
        """Minimal stub of :mod:`pytest_asyncio` for offline test execution."""

        @staticmethod
        def fixture(*dargs: Any, **dkwargs: Any):
            def decorator(func: Callable[..., Any]):
                setattr(func, _ASYNC_FIXTURE_MARKER, True)
                return pytest.fixture(*dargs, **dkwargs)(func)

            return decorator

    pytest_asyncio = _AsyncioStub()

    def _ensure_loop(request: pytest.FixtureRequest) -> asyncio.AbstractEventLoop:
        try:
            loop = request.getfixturevalue("event_loop")
            created = False
        except pytest.FixtureLookupError:
            loop = _CURRENT_LOOP.get()
            created = False
            if loop is None:
                loop = asyncio.new_event_loop()
                created = True
        asyncio.set_event_loop(loop)
        if created:
            request.addfinalizer(loop.close)
        return loop

    @pytest.hookimpl
    def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool | None:
        test_function = pyfuncitem.obj
        if inspect.iscoroutinefunction(test_function):
            loop = pyfuncitem.funcargs.get("event_loop")
            created = False
            if loop is None:
                loop = _CURRENT_LOOP.get()
                if loop is None:
                    loop = asyncio.new_event_loop()
                    created = True
            asyncio.set_event_loop(loop)
            token = _CURRENT_LOOP.set(loop)
            try:
                loop.run_until_complete(test_function(**pyfuncitem.funcargs))
            finally:
                _CURRENT_LOOP.reset(token)
                if created:
                    loop.close()
            return True
        return None

    @pytest.hookimpl
    def pytest_fixture_setup(
        fixturedef: pytest.FixtureDef[Any], request: pytest.FixtureRequest
    ) -> Any:
        func = fixturedef.func
        if getattr(func, _ASYNC_FIXTURE_MARKER, False) or inspect.iscoroutinefunction(
            func
        ) or inspect.isasyncgenfunction(func):
            kwargs = {name: request.getfixturevalue(name) for name in fixturedef.argnames}
            result = call_fixture_func(func, request, kwargs)
            loop = _ensure_loop(request)
            token = _CURRENT_LOOP.set(loop)
            try:
                if inspect.iscoroutine(result):
                    return loop.run_until_complete(result)
                if inspect.isasyncgen(result):
                    async_gen = result
                    try:
                        value = loop.run_until_complete(async_gen.__anext__())
                    except StopAsyncIteration as exc:  # pragma: no cover - defensive
                        raise RuntimeError(
                            f"Async fixture {fixturedef.argname} did not yield a value"
                        ) from exc

                    def _finalizer() -> None:
                        try:
                            loop.run_until_complete(async_gen.aclose())
                        except RuntimeError:
                            pass

                    request.addfinalizer(_finalizer)
                    return value
                return result
            finally:
                _CURRENT_LOOP.reset(token)
        return None
if not _MISSING_DEPS:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
else:  # pragma: no cover - lightweight placeholders to satisfy type checkers
    from typing import Any

    class AsyncClient:  # type: ignore[no-redef]
        ...

    class AsyncSession:  # type: ignore[no-redef]
        ...

    def async_sessionmaker(*args: Any, **kwargs: Any):  # type: ignore[no-redef]
        raise RuntimeError("sqlalchemy is required for these tests")

    def create_async_engine(*args: Any, **kwargs: Any):  # type: ignore[no-redef]
        raise RuntimeError("sqlalchemy is required for these tests")

try:  # pragma: no cover - structlog is optional in the test environment
    import structlog  # type: ignore  # noqa: F401  (imported for side effects)
except ModuleNotFoundError:  # pragma: no cover - fallback stub for offline testing
    import json
    import logging
    from datetime import datetime, timezone
    from types import ModuleType
    from typing import Any

    _STRUCTLOG_CONFIG: dict[str, Any] = {
        "processors": [],
        "logger_factory": None,
        "wrapper_class": None,
    }

    class _StubBoundLogger:
        def __init__(
            self,
            name: str | None = None,
            context: dict[str, Any] | None = None,
            logger: logging.Logger | None = None,
        ) -> None:
            self.name = name or "structlog"
            self._context = dict(context or {})
            self._logger = logger or logging.getLogger(self.name)

        def bind(self, **kwargs: Any) -> "_StubBoundLogger":
            new_context = dict(self._context)
            new_context.update(kwargs)
            return _StubBoundLogger(self.name, new_context, self._logger)

        def info(self, event: str, **kwargs: Any) -> None:
            event_dict: dict[str, Any] = {"event": event, **self._context, **kwargs}
            result: Any = event_dict
            for processor in list(_STRUCTLOG_CONFIG.get("processors", [])):
                result = processor(self._logger, "info", result)
            if isinstance(result, dict):
                message = json.dumps(result)
            else:
                message = str(result)
            self._logger.info(message)

    class _StubLoggerFactory:
        def __call__(self, name: str | None = None, *args: Any, **kwargs: Any) -> logging.Logger:
            if name is None and args:
                name = args[0]
            if name is None:
                return logging.getLogger()
            return logging.getLogger(name)

    def _make_filtering_bound_logger(level: int):  # noqa: D401 - simple passthrough
        def _wrapper(logger: _StubBoundLogger) -> _StubBoundLogger:
            return logger

        return _wrapper

    def _configure(*, processors=None, wrapper_class=None, logger_factory=None, **_: Any) -> None:
        _STRUCTLOG_CONFIG["processors"] = list(processors or [])
        _STRUCTLOG_CONFIG["wrapper_class"] = wrapper_class
        _STRUCTLOG_CONFIG["logger_factory"] = logger_factory

    def _get_logger(name: str | None = None) -> _StubBoundLogger:
        factory = _STRUCTLOG_CONFIG.get("logger_factory")
        base_logger: logging.Logger | None = None
        if callable(factory):
            try:
                base_logger = factory(name)
            except TypeError:
                base_logger = factory()
        if base_logger is None:
            base_logger = logging.getLogger(name)
        bound: _StubBoundLogger = _StubBoundLogger(name or base_logger.name, logger=base_logger)
        wrapper = _STRUCTLOG_CONFIG.get("wrapper_class")
        if callable(wrapper):
            bound = wrapper(bound)
        return bound

    processors_module = ModuleType("structlog.processors")

    def _add_log_level(_: logging.Logger, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        event_dict.setdefault("level", method_name)
        return event_dict

    class _TimeStamper:
        def __init__(self, fmt: str, utc: bool = False) -> None:
            self.fmt = fmt
            self.utc = utc

        def __call__(self, _: logging.Logger, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
            now = datetime.now(timezone.utc if self.utc else None)
            if self.fmt == "iso":
                event_dict["timestamp"] = now.isoformat()
            else:
                event_dict["timestamp"] = now.strftime(self.fmt)
            return event_dict

    def _stack_info_renderer(_: logging.Logger, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        return event_dict

    def _format_exc_info(_: logging.Logger, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        return event_dict

    class _JSONRenderer:
        def __call__(self, _: logging.Logger, __: str, event_dict: dict[str, Any]) -> str:
            return json.dumps(event_dict)

    processors_module.add_log_level = _add_log_level  # type: ignore[attr-defined]
    processors_module.TimeStamper = _TimeStamper  # type: ignore[attr-defined]
    processors_module.StackInfoRenderer = lambda: _stack_info_renderer  # type: ignore[attr-defined]
    processors_module.format_exc_info = _format_exc_info  # type: ignore[attr-defined]
    processors_module.JSONRenderer = lambda: _JSONRenderer()  # type: ignore[attr-defined]

    stdlib_module = ModuleType("structlog.stdlib")
    stdlib_module.BoundLogger = _StubBoundLogger  # type: ignore[attr-defined]
    stdlib_module.LoggerFactory = _StubLoggerFactory  # type: ignore[attr-defined]

    structlog_module = ModuleType("structlog")
    structlog_module.configure = _configure  # type: ignore[attr-defined]
    structlog_module.get_logger = _get_logger  # type: ignore[attr-defined]
    structlog_module.make_filtering_bound_logger = _make_filtering_bound_logger  # type: ignore[attr-defined]
    structlog_module.processors = processors_module  # type: ignore[attr-defined]
    structlog_module.stdlib = stdlib_module  # type: ignore[attr-defined]
    structlog_module.BoundLogger = _StubBoundLogger  # type: ignore[attr-defined]

    sys.modules.setdefault("structlog", structlog_module)
    sys.modules.setdefault("structlog.processors", processors_module)
    sys.modules.setdefault("structlog.stdlib", stdlib_module)

if not _MISSING_DEPS:
    from app.core.database import get_session
    from app.main import app
    from app.models.base import BaseModel
    from app.services.storage import get_storage_service, reset_storage_service
else:  # pragma: no cover - fallback stubs for offline testing
    from typing import Any

    def get_session():  # type: ignore[no-redef]
        raise RuntimeError("sqlalchemy is required for these tests")

    class _StubApp:  # type: ignore[no-redef]
        dependency_overrides: dict[str, Any] = {}

    app = _StubApp()  # type: ignore[assignment]

    class _StubBaseModel:  # type: ignore[no-redef]
        metadata = type("Meta", (), {"create_all": staticmethod(lambda _: None), "sorted_tables": []})

    BaseModel = _StubBaseModel  # type: ignore[assignment]

    def get_storage_service():  # type: ignore[no-redef]
        raise RuntimeError("fastapi and sqlalchemy are required for these tests")

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
    if _MISSING_DEPS:
        pytest.skip("Storage service tests require fastapi, pydantic, and sqlalchemy")
    base_path = tmp_path / "storage"
    base_path.mkdir()
    monkeypatch.setenv("STORAGE_LOCAL_PATH", str(base_path))
    reset_storage_service()
    service = get_storage_service()
    try:
        yield service
    finally:
        reset_storage_service()


@pytest_asyncio.fixture
async def client(
    async_session_factory: async_sessionmaker[AsyncSession],
    storage_service,
) -> AsyncGenerator[AsyncClient, None]:
    if _MISSING_DEPS:
        pytest.skip("API client tests require fastapi, pydantic, and sqlalchemy")
    async def _get_session() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _get_session
    async with AsyncClient(app=app, base_url="http://testserver") as http_client:
        yield http_client
    app.dependency_overrides.pop(get_session, None)
