"""Test configuration and shared fixtures."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Callable, Iterator
from contextlib import asynccontextmanager
import sys

import pytest
from typing import Any

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
try:  # pragma: no cover - httpx may be unavailable in offline test environments
    from httpx import AsyncClient  # type: ignore  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - fallback stub for offline testing
    import json
    from dataclasses import dataclass
    from typing import Any, Dict, Mapping, Optional
    from urllib.parse import urlencode, urljoin, urlparse, urlunparse

    @dataclass
    class _StubResponse:
        status_code: int
        headers: list[tuple[str, str]]
        body: bytes

        def json(self) -> Any:
            if not self.body:
                return None
            return json.loads(self.body.decode("utf-8"))

        def text(self) -> str:
            return self.body.decode("utf-8")

    class AsyncClient:  # type: ignore[override]
        def __init__(
            self,
            *,
            app: Any,
            base_url: str = "http://testserver",
        ) -> None:
            if app is None:
                raise RuntimeError("AsyncClient stub requires an ASGI application.")
            parsed = urlparse(base_url.rstrip("/") or "http://testserver")
            self._app = app
            self._scheme = parsed.scheme or "http"
            self._netloc = parsed.netloc or "testserver"
            self._base_url = f"{self._scheme}://{self._netloc}"
            self._closed = False

        async def __aenter__(self) -> "AsyncClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            await self.aclose()

        async def aclose(self) -> None:
            self._closed = True

        async def get(
            self, url: str, params: Optional[Mapping[str, Any]] = None
        ) -> _StubResponse:
            return await self._request("GET", url, params=params)

        async def post(
            self,
            url: str,
            *,
            json: Any | None = None,
            params: Optional[Mapping[str, Any]] = None,
        ) -> _StubResponse:
            payload = b""
            headers: Dict[str, str] = {}
            if json is not None:
                payload = json_dumps(json)
                headers["content-type"] = "application/json"
            return await self._request(
                "POST",
                url,
                params=params,
                body=payload,
                headers=headers,
            )

        async def _request(
            self,
            method: str,
            url: str,
            *,
            params: Optional[Mapping[str, Any]] = None,
            body: bytes = b"",
            headers: Optional[Mapping[str, str]] = None,
        ) -> _StubResponse:
            if self._closed:
                raise RuntimeError("Client session is closed")

            full_url = self._merge_url(url, params)
            parsed = urlparse(full_url)

            header_items = [(b"host", self._netloc.encode("latin-1"))]
            if headers:
                for key, value in headers.items():
                    header_items.append((key.encode("latin-1"), str(value).encode("latin-1")))

            scope = {
                "type": "http",
                "asgi": {"version": "3.0"},
                "http_version": "1.1",
                "method": method.upper(),
                "scheme": parsed.scheme or self._scheme,
                "path": parsed.path or "/",
                "raw_path": (parsed.path or "/").encode("latin-1"),
                "query_string": (parsed.query or "").encode("latin-1"),
                "headers": header_items,
            }

            receive_called = False

            async def receive() -> Dict[str, Any]:
                nonlocal receive_called
                if not receive_called:
                    receive_called = True
                    return {"type": "http.request", "body": body, "more_body": False}
                await asyncio.sleep(0)
                return {"type": "http.disconnect"}

            status_code = 500
            response_headers: list[tuple[bytes, bytes]] = []
            body_parts: list[bytes] = []

            async def send(message: Mapping[str, Any]) -> None:
                nonlocal status_code, response_headers
                message_type = message.get("type")
                if message_type == "http.response.start":
                    status_code = int(message.get("status", 500))
                    response_headers = list(message.get("headers") or [])
                elif message_type == "http.response.body":
                    chunk = message.get("body", b"")
                    if chunk:
                        body_parts.append(chunk)

            await self._app(scope, receive, send)

            decoded_headers = [
                (key.decode("latin-1"), value.decode("latin-1"))
                for key, value in response_headers
            ]
            return _StubResponse(status_code, decoded_headers, b"".join(body_parts))

        def _merge_url(
            self, url: str, params: Optional[Mapping[str, Any]] = None
        ) -> str:
            if url.startswith("http://") or url.startswith("https://"):
                base = url
            else:
                base = urljoin(self._base_url + "/", url.lstrip("/"))
            parsed = urlparse(base)
            query_parts = [parsed.query]
            if params:
                query_parts.append(urlencode(params, doseq=True))
            merged_query = "&".join(filter(None, query_parts))
            return urlunparse(
                (
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    merged_query,
                    parsed.fragment,
                )
            )

    def json_dumps(payload: Any) -> bytes:
        return json.dumps(payload, separators=(",", ":")).encode("utf-8")
try:  # pragma: no cover - SQLAlchemy may be unavailable in offline test environments
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    _SQLALCHEMY_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - degrade gracefully without SQLAlchemy
    AsyncSession = Any  # type: ignore[assignment]
    async_sessionmaker = None  # type: ignore[assignment]
    create_async_engine = None  # type: ignore[assignment]
    _SQLALCHEMY_AVAILABLE = False

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

from app.utils import metrics

if _SQLALCHEMY_AVAILABLE:
    from app.core.database import get_session
    from app.main import app
    from app.models.base import BaseModel
else:  # pragma: no cover - lightweight ASGI app for offline testing
    try:
        from fastapi import FastAPI
    except ModuleNotFoundError:  # pragma: no cover - FastAPI unavailable
        class _FallbackApp:
            async def __call__(self, scope, receive, send) -> None:  # pragma: no cover
                raise RuntimeError("FastAPI is not installed in this environment")

        app = _FallbackApp()
    else:
        from app.api.v1.rulesets import router as rulesets_router

        app = FastAPI()
        app.include_router(rulesets_router, prefix="/api/v1")


@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


if _SQLALCHEMY_AVAILABLE:

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

else:  # pragma: no cover - fixtures skipped when SQLAlchemy unavailable

    @pytest.fixture
    def async_session_factory() -> AsyncGenerator[None, None]:
        raise pytest.SkipTest("SQLAlchemy is not available in the test environment")


@pytest.fixture(autouse=True)
def reset_metrics() -> Iterator[None]:
    metrics.reset_metrics()
    yield
    metrics.reset_metrics()


if _SQLALCHEMY_AVAILABLE:

    @pytest_asyncio.fixture
    async def session(
        async_session_factory: async_sessionmaker[AsyncSession],
    ) -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory() as session:
            try:
                yield session
            finally:
                await session.rollback()
                for table in reversed(BaseModel.metadata.sorted_tables):
                    await session.execute(table.delete())
                await session.commit()

    @pytest.fixture
    def session_factory(
        async_session_factory: async_sessionmaker[AsyncSession],
    ) -> Callable[[], AsyncGenerator[AsyncSession, None]]:
        @asynccontextmanager
        async def _context() -> AsyncGenerator[AsyncSession, None]:
            async with async_session_factory() as session:
                yield session

        def _factory() -> AsyncGenerator[AsyncSession, None]:
            return _context()

        return _factory

    @pytest_asyncio.fixture
    async def client(
        async_session_factory: async_sessionmaker[AsyncSession],
    ) -> AsyncGenerator[AsyncClient, None]:
        async def _get_session() -> AsyncGenerator[AsyncSession, None]:
            async with async_session_factory() as session:
                yield session

        app.dependency_overrides[get_session] = _get_session
        async with AsyncClient(app=app, base_url="http://testserver") as http_client:
            yield http_client
        app.dependency_overrides.pop(get_session, None)

else:  # pragma: no cover - fixtures skipped when SQLAlchemy unavailable

    @pytest.fixture
    def session() -> AsyncGenerator[None, None]:
        raise pytest.SkipTest("SQLAlchemy is not available in the test environment")

    @pytest.fixture
    def session_factory() -> Callable[[], AsyncGenerator[None, None]]:
        raise pytest.SkipTest("SQLAlchemy is not available in the test environment")

    @pytest_asyncio.fixture
    async def client() -> AsyncGenerator[AsyncClient, None]:
        raise pytest.SkipTest("SQLAlchemy is not available in the test environment")
