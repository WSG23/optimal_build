"""Test configuration and shared fixtures."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import AsyncGenerator, Callable, Iterator
from contextlib import asynccontextmanager
import sys

from typing import TYPE_CHECKING, Any

import pytest

try:  # pragma: no cover - optional dependency
    import pytest_asyncio  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - shim for offline testing
    from types import ModuleType

    _pytest_asyncio = ModuleType("pytest_asyncio")

    def _async_fixture(*fixture_args: Any, **fixture_kwargs: Any):
        return pytest.fixture(*fixture_args, **fixture_kwargs)

    _pytest_asyncio.fixture = _async_fixture  # type: ignore[attr-defined]

    sys.modules.setdefault("pytest_asyncio", _pytest_asyncio)
    pytest_asyncio = _pytest_asyncio  # type: ignore[assignment]

    def _get_event_loop(request: pytest.FixtureRequest) -> asyncio.AbstractEventLoop:
        return request.getfixturevalue("event_loop")

    @pytest.hookimpl(tryfirst=True)
    def pytest_configure(config: pytest.Config) -> None:
        config.addinivalue_line(
            "markers",
            "asyncio: mark test coroutine for execution when pytest-asyncio is unavailable.",
        )

    @pytest.hookimpl(tryfirst=True)
    def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool | None:
        test_function = pyfuncitem.obj
        marker = pyfuncitem.get_closest_marker("asyncio")
        if inspect.iscoroutinefunction(test_function) or marker is not None:
            request = getattr(pyfuncitem, "_request", None)
            if request is None:
                return None
            loop = _get_event_loop(request)
            result = test_function(**pyfuncitem.funcargs)
            if inspect.isawaitable(result):
                loop.run_until_complete(result)
            return True
        return None

    @pytest.hookimpl(tryfirst=True)
    def pytest_fixture_setup(
        fixturedef: pytest.FixtureDef[Any], request: pytest.FixtureRequest
    ) -> Any:
        func = fixturedef.func
        if inspect.isasyncgenfunction(func):
            loop = _get_event_loop(request)
            dependencies = {
                name: request.getfixturevalue(name) for name in fixturedef.argnames
            }
            async_gen = func(**dependencies)
            value = loop.run_until_complete(async_gen.__anext__())

            def _finalize() -> None:
                loop.run_until_complete(async_gen.aclose())

            request.addfinalizer(_finalize)
            return value
        if inspect.iscoroutinefunction(func):
            loop = _get_event_loop(request)
            dependencies = {
                name: request.getfixturevalue(name) for name in fixturedef.argnames
            }
            return loop.run_until_complete(func(**dependencies))
        return None

try:  # pragma: no cover - optional dependency
    import httpx  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - shim for offline testing
    from types import ModuleType

    try:
        from fastapi.testclient import TestClient
    except ModuleNotFoundError:  # pragma: no cover - optional dependency missing
        pytest.skip(
            "HTTPX is unavailable and FastAPI's TestClient is required for the async client shim.",
            allow_module_level=True,
        )

    class _StubResponse:
        """Minimal shim compatible with the subset of httpx.Response used in tests."""

        def __init__(self, response: Any) -> None:
            self._response = response

        @property
        def status_code(self) -> int:
            return self._response.status_code

        @property
        def headers(self) -> Any:
            return self._response.headers

        @property
        def text(self) -> str:
            return self._response.text

        def json(self) -> Any:
            return self._response.json()

        def raise_for_status(self) -> None:
            self._response.raise_for_status()

        def __getattr__(self, name: str) -> Any:
            return getattr(self._response, name)

    class _AsyncClient:
        """Async-compatible facade over FastAPI's synchronous TestClient."""

        def __init__(
            self,
            *,
            app: Any,
            base_url: str | None = None,
            follow_redirects: bool | None = None,
            headers: Any | None = None,
            cookies: Any | None = None,
            raise_server_exceptions: bool | None = None,
            root_path: str | None = None,
            **_: Any,
        ) -> None:
            client_options: dict[str, Any] = {}
            if base_url is not None:
                client_options["base_url"] = base_url
            if follow_redirects is not None:
                client_options["follow_redirects"] = follow_redirects
            if headers is not None:
                client_options["headers"] = headers
            if cookies is not None:
                client_options["cookies"] = cookies
            if raise_server_exceptions is not None:
                client_options["raise_server_exceptions"] = raise_server_exceptions
            if root_path is not None:
                client_options["root_path"] = root_path

            self._client = TestClient(app=app, **client_options)
            self._entered = False

        async def __aenter__(self) -> "_AsyncClient":
            self._client.__enter__()
            self._entered = True
            return self

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            traceback: Any,
        ) -> None:
            self._exit(exc_type, exc, traceback)

        async def aclose(self) -> None:
            self._exit(None, None, None)

        def _exit(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            traceback: Any,
        ) -> None:
            if self._entered:
                self._client.__exit__(exc_type, exc, traceback)
                self._entered = False
            else:
                self._client.close()

        async def request(self, method: str, url: str, **kwargs: Any) -> _StubResponse:
            response = self._client.request(method, url, **kwargs)
            return _StubResponse(response)

        async def get(self, url: str, **kwargs: Any) -> _StubResponse:
            return await self.request("GET", url, **kwargs)

        async def post(self, url: str, **kwargs: Any) -> _StubResponse:
            return await self.request("POST", url, **kwargs)

        async def put(self, url: str, **kwargs: Any) -> _StubResponse:
            return await self.request("PUT", url, **kwargs)

        async def delete(self, url: str, **kwargs: Any) -> _StubResponse:
            return await self.request("DELETE", url, **kwargs)

        async def patch(self, url: str, **kwargs: Any) -> _StubResponse:
            return await self.request("PATCH", url, **kwargs)

        def __getattr__(self, name: str) -> Any:
            return getattr(self._client, name)

    _httpx = ModuleType("httpx")
    _httpx.AsyncClient = _AsyncClient  # type: ignore[attr-defined]
    _httpx.__all__ = ["AsyncClient"]  # type: ignore[attr-defined]

    sys.modules.setdefault("httpx", _httpx)
    httpx = _httpx  # type: ignore[assignment]

if TYPE_CHECKING:
    from httpx import AsyncClient  # pragma: no cover
else:
    AsyncClient = httpx.AsyncClient  # type: ignore[attr-defined]

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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

from app.core.database import get_session
from app.main import app
from app.models.base import BaseModel
from app.utils import metrics


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
