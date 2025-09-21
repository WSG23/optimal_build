"""Test configuration and shared fixtures."""

from __future__ import annotations

import asyncio
import contextvars
import inspect
from collections.abc import AsyncGenerator, Callable, Iterator
from contextlib import asynccontextmanager
import sys

import pytest
from _pytest.fixtures import TEST_OUTCOME

from pytest_asyncio import (
    _ASYNC_FIXTURE_MARKER,
    _consume_async_fixture as _pytest_asyncio_consume,
    fixture as _pytest_asyncio_fixture,
)


class _PytestAsyncioWrapper:
    fixture = staticmethod(_pytest_asyncio_fixture)


pytest_asyncio = _PytestAsyncioWrapper()


@pytest.hookimpl
def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addini(
        "asyncio_mode",
        "Default mode for pytest-asyncio compatibility shims",
        default="auto",
    )


@pytest.hookimpl
def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "asyncio: mark test as requiring an asyncio event loop"
    )


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
            test_args = {
                name: pyfuncitem.funcargs[name]
                for name in pyfuncitem._fixtureinfo.argnames
            }
            loop.run_until_complete(test_function(**test_args))
        finally:
            _CURRENT_LOOP.reset(token)
            if created:
                loop.close()
        return True
    return None


_CURRENT_LOOP: contextvars.ContextVar[asyncio.AbstractEventLoop | None] = (
    contextvars.ContextVar("pytest_asyncio_current_loop", default=None)
)


@pytest.hookimpl
def pytest_fixture_setup(
    fixturedef: pytest.FixtureDef[Any], request: pytest.FixtureRequest
) -> Any:
    func = fixturedef.func
    if getattr(func, _ASYNC_FIXTURE_MARKER, False) or inspect.iscoroutinefunction(
        func
    ) or inspect.isasyncgenfunction(func):
        kwargs = {name: request.getfixturevalue(name) for name in fixturedef.argnames}
        cache_key = fixturedef.cache_key(request)
        try:
            result = _pytest_asyncio_consume(func, request, kwargs)
        except TEST_OUTCOME as exc:
            fixturedef.cached_result = (None, cache_key, (exc, exc.__traceback__))
            raise
        fixturedef.cached_result = (result, cache_key, None)
        return result
    return None
try:  # pragma: no cover - prefer the real dependency when available
    from httpx import AsyncClient
except ModuleNotFoundError:  # pragma: no cover - lightweight ASGI stub for offline tests
    import inspect
    import json
    from types import ModuleType
    from typing import Any, Iterable, Mapping, MutableMapping, Sequence
    from urllib.parse import parse_qsl, urlencode, urlsplit

    class HTTPStatusError(RuntimeError):
        """Simplified stand-in for :class:`httpx.HTTPStatusError`."""

        def __init__(self, message: str, *, status_code: int) -> None:
            super().__init__(message)
            self.status_code = status_code

    def _encode_headers(headers: Mapping[str, Any]) -> list[tuple[bytes, bytes]]:
        encoded: list[tuple[bytes, bytes]] = []
        for key, value in headers.items():
            name = str(key).lower().encode("latin-1")
            if isinstance(value, (list, tuple, set)):
                values: Iterable[Any]
                values = value
            else:
                values = (value,)
            for item in values:
                encoded.append((name, str(item).encode("latin-1")))
        return encoded

    def _decode_headers(headers: Iterable[tuple[bytes, bytes]]) -> dict[str, str]:
        decoded: dict[str, str] = {}
        for name, value in headers:
            key = name.decode("latin-1")
            text = value.decode("latin-1")
            if key in decoded:
                decoded[key] = f"{decoded[key]}, {text}"
            else:
                decoded[key] = text
        return decoded

    class _StubResponse:
        """Minimal response object mimicking :class:`httpx.Response`."""

        def __init__(self, status_code: int, headers: Mapping[str, str], content: bytes) -> None:
            self.status_code = status_code
            self.headers = dict(headers)
            self._content = content

        @property
        def content(self) -> bytes:
            return self._content

        @property
        def text(self) -> str:
            try:
                return self._content.decode("utf-8")
            except UnicodeDecodeError:
                return self._content.decode("latin-1", errors="replace")

        def json(self) -> Any:
            return json.loads(self.text or "null")

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise HTTPStatusError(
                    f"Request failed with status code {self.status_code}",
                    status_code=self.status_code,
                )

    class AsyncClient:
        """Very small subset of :class:`httpx.AsyncClient` for tests."""

        def __init__(
            self,
            *args: Any,
            app: Any | None = None,
            base_url: str = "http://testserver",
            headers: Mapping[str, str] | None = None,
            **kwargs: Any,
        ) -> None:
            if app is None:
                raise TypeError("httpx.AsyncClient stub requires an 'app' argument")
            self._app = app
            self._base_url = base_url.rstrip("/") or "http://testserver"
            self._headers = dict(headers or {})
            self._default_request_kwargs = dict(kwargs)
            self._closed = False

        async def __aenter__(self) -> "AsyncClient":
            self._closed = False
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            self._closed = True

        async def aclose(self) -> None:
            self._closed = True

        def _build_url(self, url: str) -> str:
            if url.startswith("http://") or url.startswith("https://"):
                return url
            if url.startswith("/"):
                return f"{self._base_url}{url}"
            return f"{self._base_url}/{url}"

        async def request(self, method: str, url: str, **kwargs: Any) -> _StubResponse:
            if self._closed:
                raise RuntimeError("AsyncClient context has been closed")

            request_kwargs = dict(self._default_request_kwargs)
            request_kwargs.update(kwargs)

            json_payload = request_kwargs.pop("json", None)
            data = request_kwargs.pop("data", None)
            params = request_kwargs.pop("params", None)
            headers_override = request_kwargs.pop("headers", None)

            if request_kwargs:
                # Ignore unsupported parameters silently to stay lightweight.
                request_kwargs.clear()

            target_url = self._build_url(url)
            parsed = urlsplit(target_url)
            query_items = list(parse_qsl(parsed.query, keep_blank_values=True))

            if params:
                if isinstance(params, Mapping):
                    items: Iterable[tuple[Any, Any]] = params.items()
                else:
                    items = params  # type: ignore[assignment]
                for key, value in items:
                    if isinstance(value, (list, tuple)):
                        for item in value:
                            query_items.append((str(key), str(item)))
                    else:
                        query_items.append((str(key), str(value)))

            query_string = urlencode(query_items, doseq=True)

            headers: MutableMapping[str, Any] = dict(self._headers)
            if headers_override:
                if isinstance(headers_override, Mapping):
                    headers.update(headers_override)
                else:
                    headers.update(dict(headers_override))

            host = parsed.hostname or urlsplit(self._base_url).hostname or "testserver"
            if "host" not in {key.lower() for key in headers}:
                port = parsed.port
                if port and port not in (80, 443):
                    headers["host"] = f"{host}:{port}"
                else:
                    headers["host"] = host

            body: bytes = b""
            if json_payload is not None:
                body = json.dumps(json_payload).encode("utf-8")
                if "content-type" not in {key.lower() for key in headers}:
                    headers["content-type"] = "application/json"
            elif data is not None:
                if isinstance(data, bytes):
                    body = data
                elif isinstance(data, str):
                    body = data.encode("utf-8")
                elif isinstance(data, Mapping):
                    body = urlencode(data, doseq=True).encode("utf-8")
                elif isinstance(data, Sequence):
                    body = urlencode(data, doseq=True).encode("utf-8")
                else:
                    body = bytes(data)
                if "content-type" not in {key.lower() for key in headers}:
                    headers["content-type"] = "application/x-www-form-urlencoded"

            if body and "content-length" not in {key.lower() for key in headers}:
                headers["content-length"] = str(len(body))

            scope = {
                "type": "http",
                "asgi": {"version": "3.0", "spec_version": "2.3"},
                "http_version": "1.1",
                "method": method.upper(),
                "scheme": parsed.scheme or urlsplit(self._base_url).scheme or "http",
                "path": parsed.path or "/",
                "raw_path": (parsed.path or "/").encode("utf-8"),
                "query_string": query_string.encode("ascii"),
                "headers": _encode_headers(headers),
                "client": ("testclient", 50000),
                "server": (
                    host,
                    parsed.port
                    or (443 if (parsed.scheme or "http") == "https" else 80),
                ),
            }

            body_sent = False

            async def receive() -> dict[str, Any]:
                nonlocal body_sent
                if not body_sent:
                    body_sent = True
                    return {
                        "type": "http.request",
                        "body": body,
                        "more_body": False,
                    }
                return {"type": "http.disconnect"}

            response_status: int | None = None
            response_headers: list[tuple[bytes, bytes]] = []
            response_body: list[bytes] = []

            async def send(message: Mapping[str, Any]) -> None:
                nonlocal response_status, response_headers
                msg_type = message.get("type")
                if msg_type == "http.response.start":
                    response_status = int(message.get("status", 500))
                    response_headers = list(message.get("headers", []))
                elif msg_type == "http.response.body":
                    response_body.append(message.get("body", b""))

            result = self._app(scope, receive, send)
            if inspect.isawaitable(result):
                await result
            else:  # pragma: no cover - defensive guard for misconfigured apps
                raise TypeError("ASGI application did not return an awaitable")

            content = b"".join(response_body)
            status_code = response_status or 500
            decoded_headers = _decode_headers(response_headers)
            return _StubResponse(status_code, decoded_headers, content)

        async def get(self, url: str, **kwargs: Any) -> _StubResponse:
            return await self.request("GET", url, **kwargs)

        async def post(self, url: str, **kwargs: Any) -> _StubResponse:
            return await self.request("POST", url, **kwargs)

        async def put(self, url: str, **kwargs: Any) -> _StubResponse:
            return await self.request("PUT", url, **kwargs)

        async def delete(self, url: str, **kwargs: Any) -> _StubResponse:
            return await self.request("DELETE", url, **kwargs)

    _httpx_stub = ModuleType("httpx")
    _httpx_stub.AsyncClient = AsyncClient
    _httpx_stub.Response = _StubResponse
    _httpx_stub.HTTPStatusError = HTTPStatusError
    _httpx_stub.__all__ = ["AsyncClient", "Response", "HTTPStatusError"]
    sys.modules.setdefault("httpx", _httpx_stub)
try:  # pragma: no cover - prefer the real dependency when available
    from fastapi import APIRouter, Depends, FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import Response
except ModuleNotFoundError:  # pragma: no cover - minimal FastAPI stub
    import inspect
    import json
    from types import ModuleType
    from typing import (
        Any,
        Awaitable,
        Callable,
        Dict,
        List,
        Optional,
        Sequence,
        Tuple,
        Union,
        get_args,
        get_origin,
        get_type_hints,
    )

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: Any = None) -> None:
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

    class Response:
        def __init__(
            self,
            content: Any = b"",
            *,
            status_code: int = 200,
            media_type: str = "application/json",
            headers: Optional[Dict[str, str]] = None,
        ) -> None:
            if isinstance(content, bytes):
                self.body = content
            elif isinstance(content, str):
                self.body = content.encode("utf-8")
            else:
                self.body = json.dumps(content).encode("utf-8")
            self.status_code = status_code
            self.media_type = media_type
            self.headers = dict(headers or {})

    class Depends:
        def __init__(self, dependency: Optional[Callable[..., Any]] = None) -> None:
            self.dependency = dependency

    def Query(default: Any = None, **kwargs: Any) -> Any:
        return default

    class CORSMiddleware:  # pragma: no cover - middleware no-op
        def __init__(self, app: Callable[..., Awaitable[Any]], **kwargs: Any) -> None:
            self.app = app
            self.options = kwargs

        async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
            await self.app(scope, receive, send)

    def _join_paths(*segments: str) -> str:
        parts: List[str] = []
        for segment in segments:
            if not segment:
                continue
            stripped = segment.strip("/")
            if stripped:
                parts.append(stripped)
        if not parts:
            return "/"
        return "/" + "/".join(parts)

    def _split_path(path: str) -> List[str]:
        if not path or path == "/":
            return []
        return [segment for segment in path.strip("/").split("/") if segment]

    def _convert_path_value(value: str, annotation: Any) -> Any:
        if annotation is inspect.Signature.empty or annotation is Any:
            return value
        origin = get_origin(annotation)
        if origin is Union:
            args = [arg for arg in get_args(annotation) if arg is not type(None)]
            if args:
                return _convert_path_value(value, args[0])
            return value
        if annotation is int:
            return int(value)
        if annotation is float:
            return float(value)
        if annotation is bool:
            return value.lower() in {"1", "true", "yes", "on"}
        return value

    def _convert_body_value(value: Any, annotation: Any) -> Any:
        if annotation is inspect.Signature.empty or annotation is Any:
            return value
        origin = get_origin(annotation)
        if origin is Union:
            args = [arg for arg in get_args(annotation) if arg is not type(None)]
            if args:
                return _convert_body_value(value, args[0])
            return value
        if inspect.isclass(annotation):
            try:
                if isinstance(value, dict):
                    return annotation(**value)
                return annotation(value)
            except Exception:  # pragma: no cover - fallback to raw value
                return value
        return value

    async def _call_endpoint(endpoint: Callable[..., Any], kwargs: Dict[str, Any]) -> Any:
        result = endpoint(**kwargs)
        if inspect.isawaitable(result):
            return await result  # type: ignore[return-value]
        return result

    async def _resolve_dependency(
        app: "FastAPI", dependency: Callable[..., Any]
    ) -> Tuple[Any, Optional[Callable[[], Awaitable[None]]]]:
        target = app.dependency_overrides.get(dependency, dependency)
        if inspect.isasyncgenfunction(target):
            generator = target()
            value = await generator.__anext__()

            async def _cleanup() -> None:
                try:
                    await generator.aclose()
                except RuntimeError:  # pragma: no cover - defensive
                    pass

            return value, _cleanup
        if inspect.isgeneratorfunction(target):
            generator = target()
            value = next(generator)

            async def _cleanup_sync() -> None:
                try:
                    next(generator)
                except StopIteration:
                    pass

            return value, _cleanup_sync
        result = target()
        if inspect.isawaitable(result):
            return await result, None  # type: ignore[return-value]
        return result, None

    async def _receive_body(receive: Callable[[], Awaitable[Dict[str, Any]]]) -> bytes:
        body = b""
        while True:
            message = await receive()
            if message.get("type") != "http.request":
                break
            body += message.get("body", b"")
            if not message.get("more_body"):
                break
        return body

    class _Route:
        def __init__(self, path: str, endpoint: Callable[..., Any], methods: Sequence[str]) -> None:
            self.path = path or "/"
            self.endpoint = endpoint
            self.methods = {method.upper() for method in methods}
            self.signature = inspect.signature(endpoint)
            try:
                type_hints = get_type_hints(endpoint)
            except Exception:
                type_hints = {}
            self.param_order = list(self.signature.parameters.keys())
            self.param_annotations: Dict[str, Any] = {}
            self.dependencies: Dict[str, Callable[..., Any]] = {}
            self.body_params: List[str] = []
            segments = _split_path(self.path)
            self.path_params = [
                segment[1:-1]
                for segment in segments
                if segment.startswith("{") and segment.endswith("}")
            ]
            for name, param in self.signature.parameters.items():
                annotation = type_hints.get(name, param.annotation)
                self.param_annotations[name] = annotation
                default = param.default
                if isinstance(default, Depends):
                    if default.dependency is None:
                        raise TypeError("Depends requires a dependency")
                    self.dependencies[name] = default.dependency
                elif name in self.path_params:
                    continue
                else:
                    self.body_params.append(name)

        def clone(self, path: str) -> "_Route":
            return _Route(path, self.endpoint, self.methods)

        def matches(self, path: str) -> Optional[Dict[str, str]]:
            template = _split_path(self.path)
            actual = _split_path(path)
            if len(template) != len(actual):
                return None
            params: Dict[str, str] = {}
            for tmpl, value in zip(template, actual):
                if tmpl.startswith("{") and tmpl.endswith("}"):
                    params[tmpl[1:-1]] = value
                elif tmpl != value:
                    return None
            return params

        async def execute(
            self, app: "FastAPI", path_params: Dict[str, str], body: bytes
        ) -> Any:
            values: Dict[str, Any] = {}
            cleanups: List[Callable[[], Awaitable[None]]] = []
            for name, dependency in self.dependencies.items():
                resolved, cleanup = await _resolve_dependency(app, dependency)
                values[name] = resolved
                if cleanup:
                    cleanups.append(cleanup)
            try:
                for name, raw in path_params.items():
                    annotation = self.param_annotations.get(name, inspect.Signature.empty)
                    values[name] = _convert_path_value(raw, annotation)
                if self.body_params:
                    parsed: Any = None
                    if body:
                        try:
                            parsed = json.loads(body.decode("utf-8"))
                        except json.JSONDecodeError:
                            parsed = body.decode("utf-8") or None
                    if len(self.body_params) == 1:
                        name = self.body_params[0]
                        annotation = self.param_annotations.get(name, inspect.Signature.empty)
                        values[name] = _convert_body_value(parsed, annotation)
                    else:
                        payload = parsed if isinstance(parsed, dict) else {}
                        for name in self.body_params:
                            annotation = self.param_annotations.get(name, inspect.Signature.empty)
                            values[name] = _convert_body_value(payload.get(name), annotation)
                kwargs = {name: values[name] for name in self.param_order if name in values}
                return await _call_endpoint(self.endpoint, kwargs)
            finally:
                for cleanup in reversed(cleanups):
                    await cleanup()

    class _RouterBase:
        def __init__(self, *, prefix: str = "") -> None:
            self.prefix = prefix
            self.routes: List[_Route] = []

        def add_api_route(
            self, path: str, endpoint: Callable[..., Any], *, methods: Sequence[str]
        ) -> Callable[..., Any]:
            route = _Route(path or "/", endpoint, methods)
            self.routes.append(route)
            return endpoint

        def get(self, path: str, **_: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                self.add_api_route(path, func, methods=["GET"])
                return func

            return decorator

        def post(self, path: str, **_: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                self.add_api_route(path, func, methods=["POST"])
                return func

            return decorator

        def include_router(self, router: "APIRouter", *, prefix: str = "") -> None:
            combined_prefix = _join_paths(self.prefix, prefix, router.prefix)
            for route in router.routes:
                new_path = _join_paths(combined_prefix, route.path)
                self.routes.append(route.clone(new_path))

    class APIRouter(_RouterBase):
        def __init__(self, *, prefix: str = "", **_: Any) -> None:
            super().__init__(prefix=prefix)

    class FastAPI(_RouterBase):
        def __init__(
            self,
            *,
            title: str = "FastAPI",
            version: str = "0.1.0",
            docs_url: Optional[str] = None,
            redoc_url: Optional[str] = None,
            lifespan: Optional[Callable[..., Any]] = None,
        ) -> None:
            super().__init__(prefix="")
            self.title = title
            self.version = version
            self.docs_url = docs_url
            self.redoc_url = redoc_url
            self._lifespan = lifespan
            self.dependency_overrides: Dict[Callable[..., Any], Callable[..., Any]] = {}
            self._middlewares: List[Tuple[Callable[..., Any], Dict[str, Any]]] = []
            self.router = self

        def add_middleware(self, middleware: Callable[..., Any], **options: Any) -> None:
            self._middlewares.append((middleware, options))

        def include_router(self, router: "APIRouter", *, prefix: str = "") -> None:
            super().include_router(router, prefix=prefix)

        async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
            if scope.get("type") != "http":  # pragma: no cover - limited ASGI support
                raise RuntimeError("FastAPI stub only supports HTTP scopes")
            method = scope.get("method", "GET").upper()
            path = scope.get("path", "/")
            body = await _receive_body(receive)
            for route in self.routes:
                if method not in route.methods:
                    continue
                params = route.matches(path)
                if params is None:
                    continue
                try:
                    result = await route.execute(self, params, body)
                except HTTPException as exc:
                    payload = {"detail": exc.detail}
                    response = Response(payload, status_code=exc.status_code)
                except Exception as exc:  # pragma: no cover - defensive handling
                    response = Response({"detail": str(exc)}, status_code=500)
                else:
                    if isinstance(result, Response):
                        response = result
                    else:
                        response = Response(result)
                headers = [(b"content-type", response.media_type.encode("latin-1"))]
                for key, value in response.headers.items():
                    headers.append((key.lower().encode("latin-1"), str(value).encode("latin-1")))
                await send({"type": "http.response.start", "status": response.status_code, "headers": headers})
                await send({"type": "http.response.body", "body": response.body, "more_body": False})
                return
            not_found = Response({"detail": "Not Found"}, status_code=404)
            headers = [(b"content-type", not_found.media_type.encode("latin-1"))]
            await send({"type": "http.response.start", "status": not_found.status_code, "headers": headers})
            await send({"type": "http.response.body", "body": not_found.body, "more_body": False})

    fastapi_module = ModuleType("fastapi")
    fastapi_module.APIRouter = APIRouter  # type: ignore[attr-defined]
    fastapi_module.Depends = Depends  # type: ignore[attr-defined]
    fastapi_module.Query = Query  # type: ignore[attr-defined]
    fastapi_module.FastAPI = FastAPI  # type: ignore[attr-defined]
    fastapi_module.HTTPException = HTTPException  # type: ignore[attr-defined]

    responses_module = ModuleType("fastapi.responses")
    responses_module.Response = Response  # type: ignore[attr-defined]

    cors_module = ModuleType("fastapi.middleware.cors")
    cors_module.CORSMiddleware = CORSMiddleware  # type: ignore[attr-defined]

    middleware_module = ModuleType("fastapi.middleware")
    middleware_module.cors = cors_module  # type: ignore[attr-defined]

    fastapi_module.responses = responses_module  # type: ignore[attr-defined]
    fastapi_module.middleware = middleware_module  # type: ignore[attr-defined]

    import sys

    sys.modules.setdefault("fastapi", fastapi_module)
    sys.modules.setdefault("fastapi.responses", responses_module)
    sys.modules.setdefault("fastapi.middleware", middleware_module)
    sys.modules.setdefault("fastapi.middleware.cors", cors_module)

    from fastapi import APIRouter, Depends, FastAPI, HTTPException  # type: ignore[assignment]
    from fastapi.middleware.cors import CORSMiddleware  # type: ignore[assignment]
    from fastapi.responses import Response  # type: ignore[assignment]

try:  # pragma: no cover - prefer the real dependency when available
    from pydantic import BaseModel, field_validator, model_validator
except ModuleNotFoundError:  # pragma: no cover - minimal Pydantic stub
    from collections import defaultdict
    from types import ModuleType
    from typing import Any, Callable, Dict, List, Optional

    def model_validator(*, mode: str = "after") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            if isinstance(func, classmethod):
                target = func.__func__
                setattr(target, "_model_validator_flag", mode)
                return func
            setattr(func, "_model_validator_flag", mode)
            return classmethod(func)

        return decorator

    def field_validator(*fields: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            if isinstance(func, classmethod):
                target = func.__func__
                setattr(target, "_field_validator_fields", fields)
                return func
            setattr(func, "_field_validator_fields", fields)
            return classmethod(func)

        return decorator

    class BaseModel:
        __field_names__: List[str] = []
        __field_defaults__: Dict[str, Any] = {}
        __field_validators__: Dict[str, List[Callable[..., Any]]] = {}
        __model_validators__: List[Callable[..., Any]] = []

        def __init_subclass__(cls, **kwargs: Any) -> None:
            super().__init_subclass__(**kwargs)
            annotations: Dict[str, Any] = {}
            for base in reversed(cls.__mro__[1:]):
                annotations.update(getattr(base, "__annotations__", {}))
            annotations.update(getattr(cls, "__annotations__", {}))
            cls.__field_names__ = list(annotations.keys())
            defaults: Dict[str, Any] = {}
            for name in cls.__field_names__:
                defaults[name] = getattr(cls, name, None)
            cls.__field_defaults__ = defaults
            field_validators: Dict[str, List[Callable[..., Any]]] = defaultdict(list)
            model_validators: List[Callable[..., Any]] = []
            for base in reversed(cls.__mro__[1:]):
                for field, validators in getattr(base, "__field_validators__", {}).items():
                    field_validators[field].extend(validators)
                model_validators.extend(getattr(base, "__model_validators__", []))
            for attr in cls.__dict__.values():
                bound: Optional[Callable[..., Any]] = None
                func: Optional[Callable[..., Any]] = None
                if isinstance(attr, classmethod):
                    func = attr.__func__
                    bound = attr.__get__(None, cls)
                elif callable(attr):
                    func = attr
                    bound = attr
                if func is None or bound is None:
                    continue
                fields = getattr(func, "_field_validator_fields", None)
                if fields:
                    for field in fields:
                        field_validators[field].append(bound)
                if hasattr(func, "_model_validator_flag"):
                    model_validators.append(bound)
            cls.__field_validators__ = {key: list(value) for key, value in field_validators.items()}
            cls.__model_validators__ = list(model_validators)

        def __init__(self, **data: Any) -> None:
            cls = self.__class__
            for name in cls.__field_names__:
                if name in data:
                    value = data.pop(name)
                else:
                    default = cls.__field_defaults__.get(name)
                    value = default() if callable(default) else default
                for validator in cls.__field_validators__.get(name, []):
                    result = validator(value)
                    if result is not None:
                        value = result
                setattr(self, name, value)
            for key, value in data.items():
                setattr(self, key, value)
            for validator in cls.__model_validators__:
                result = validator(self)
                if isinstance(result, dict):
                    for key, value in result.items():
                        setattr(self, key, value)

        def model_dump(self, mode: str = "python") -> Dict[str, Any]:
            payload: Dict[str, Any] = {}
            for name in self.__class__.__field_names__:
                value = getattr(self, name, None)
                if isinstance(value, BaseModel):
                    payload[name] = value.model_dump(mode=mode)
                elif isinstance(value, list):
                    payload[name] = [
                        item.model_dump(mode=mode) if isinstance(item, BaseModel) else item
                        for item in value
                    ]
                else:
                    payload[name] = value
            return payload

    pydantic_module = ModuleType("pydantic")
    pydantic_module.BaseModel = BaseModel  # type: ignore[attr-defined]
    pydantic_module.field_validator = field_validator  # type: ignore[attr-defined]
    pydantic_module.model_validator = model_validator  # type: ignore[attr-defined]

    import sys

    sys.modules.setdefault("pydantic", pydantic_module)

    from pydantic import BaseModel, field_validator, model_validator  # type: ignore[assignment]
try:  # pragma: no cover - prefer the real dependency when available
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
except ModuleNotFoundError:  # pragma: no cover - lightweight ORM stub for offline tests
    import operator
    from collections import defaultdict
    from copy import deepcopy
    from datetime import datetime, timezone
    from types import ModuleType
    from typing import (
        Any,
        Callable,
        Dict,
        Generic,
        Iterable,
        Iterator,
        List,
        Optional,
        Sequence,
        Tuple,
        Type,
        TypeVar,
    )

    _T = TypeVar("_T")

    def _clone(value: Any) -> Any:
        if callable(value):
            return value()
        try:
            return deepcopy(value)
        except Exception:  # pragma: no cover - fallback for non-copyable values
            return value

    class _SimpleType:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.args = args
            self.kwargs = kwargs

        def __repr__(self) -> str:  # pragma: no cover - debugging aid
            return f"{self.__class__.__name__}{self.args!r}{self.kwargs!r}"

    class Boolean(_SimpleType):
        ...

    class DateTime(_SimpleType):
        ...

    class Date(_SimpleType):
        ...

    class Float(_SimpleType):
        ...

    class Integer(_SimpleType):
        ...

    class Numeric(_SimpleType):
        ...

    class String(_SimpleType):
        ...

    class Text(_SimpleType):
        ...

    class CheckConstraint:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.args = args
            self.kwargs = kwargs

    class UniqueConstraint:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.args = args
            self.kwargs = kwargs

    class ForeignKey:
        def __init__(self, target: str, **kwargs: Any) -> None:
            self.target = target
            self.kwargs = kwargs

    class Index:
        def __init__(self, name: str, *columns: Any) -> None:
            self.name = name
            self.columns = columns

    class _FunctionExpression:
        def __init__(self, name: str) -> None:
            self.name = name

        def evaluate(self, rows: Sequence[Any]) -> Any:
            if self.name == "count":
                return len(rows)
            return None

    class _TextClause:
        def __init__(self, text: str) -> None:
            self.text = text

    def text(value: str) -> _TextClause:
        return _TextClause(value)

    class Column:
        def __init__(
            self,
            type_: Any = None,
            *args: Any,
            default: Any = None,
            server_default: Any = None,
            primary_key: bool = False,
            nullable: bool = True,
            index: bool = False,
            unique: bool = False,
            **kwargs: Any,
        ) -> None:
            self.type_ = type_
            self.args = args
            self.kwargs = kwargs
            self.default = default
            self.server_default = server_default
            self.primary_key = primary_key
            self.nullable = nullable
            self.index = index
            self.unique = unique
            self.name: str | None = None
            self.model: Type["_DeclarativeBase"] | None = None

        def __set_name__(self, owner: Type["_DeclarativeBase"], name: str) -> None:
            self.name = name
            self.model = owner

        def _initial_value(self) -> Any:
            if self.default is not None:
                return _clone(self.default)
            if self.server_default is not None:
                return _clone(self.server_default)
            return None

        def __get__(self, instance: Any, owner: Type[Any]) -> Any:
            if instance is None:
                return self
            if self.name not in instance.__dict__:
                instance.__dict__[self.name] = self._initial_value()
            return instance.__dict__[self.name]

        def __set__(self, instance: Any, value: Any) -> None:
            instance.__dict__[self.name] = value

        def _compare(self, op: Callable[[Any, Any], bool], other: Any) -> "_Criterion":
            return _Comparison(self, op, other)

        def __eq__(self, other: Any) -> "_Criterion":  # type: ignore[override]
            return self._compare(operator.eq, other)

        def __ne__(self, other: Any) -> "_Criterion":  # pragma: no cover - rarely used
            return self._compare(operator.ne, other)

        def __lt__(self, other: Any) -> "_Criterion":  # pragma: no cover - rarely used
            return self._compare(operator.lt, other)

        def __le__(self, other: Any) -> "_Criterion":  # pragma: no cover - rarely used
            return self._compare(operator.le, other)

        def __gt__(self, other: Any) -> "_Criterion":  # pragma: no cover - rarely used
            return self._compare(operator.gt, other)

        def __ge__(self, other: Any) -> "_Criterion":  # pragma: no cover - rarely used
            return self._compare(operator.ge, other)

        def in_(self, values: Iterable[Any]) -> "_Criterion":
            return _InComparison(self, list(values))

        def default_value(self) -> Any:
            value = self._initial_value()
            return _clone(value)

    class _Criterion:
        def evaluate(self, instance: Any) -> bool:
            return True

    class _Comparison(_Criterion):
        def __init__(
            self, column: Column, op: Callable[[Any, Any], bool], other: Any
        ) -> None:
            self.column = column
            self.op = op
            self.other = other

        def evaluate(self, instance: Any) -> bool:
            left = getattr(instance, self.column.name)
            right = self.other
            if self.op is operator.eq and right is None:
                return left is None
            if self.op is operator.ne and right is None:
                return left is not None
            return self.op(left, right)

    class _InComparison(_Criterion):
        def __init__(self, column: Column, values: Sequence[Any]) -> None:
            self.column = column
            self.values = list(values)

        def evaluate(self, instance: Any) -> bool:
            left = getattr(instance, self.column.name)
            return left in self.values

    class _Table:
        def __init__(self, model: Type["_DeclarativeBase"]) -> None:
            self.model = model
            self.name = getattr(model, "__tablename__", model.__name__)

        def delete(self) -> "_DeleteStatement":
            return _DeleteStatement(self.model)

    class _DeleteStatement:
        def __init__(self, model: Type["_DeclarativeBase"]) -> None:
            self.model = model

    class Metadata:
        def __init__(self) -> None:
            self._models: List[Type["_DeclarativeBase"]] = []

        def register_model(self, model: Type["_DeclarativeBase"]) -> None:
            if model not in self._models:
                self._models.append(model)

        def create_all(self, engine: "AsyncEngine" | None = None) -> None:
            if engine is None:
                return
            for model in self._models:
                engine._ensure_storage(model)

        @property
        def sorted_tables(self) -> List[_Table]:
            return [
                _Table(model)
                for model in self._models
                if not getattr(model, "__abstract__", False)
            ]

    class _Relationship:
        def __init__(self, target: Any, **kwargs: Any) -> None:
            self.target = target

        def __set_name__(self, owner: Type[Any], name: str) -> None:
            self.name = name

        def __get__(self, instance: Any, owner: Type[Any]) -> Any:
            if instance is None:
                return self
            return instance.__dict__.setdefault(self.name, [])

        def __set__(self, instance: Any, value: Any) -> None:
            instance.__dict__[self.name] = value

    class _DeclarativeBase:
        metadata = Metadata()
        __abstract__ = True

        def __init_subclass__(cls, **kwargs: Any) -> None:
            super().__init_subclass__(**kwargs)
            columns: Dict[str, Column] = {}
            for base in cls.__mro__[1:]:
                columns.update(getattr(base, "__columns__", {}))
            for name, value in cls.__dict__.items():
                if isinstance(value, Column):
                    columns[name] = value
                    value.model = cls
            cls.__columns__ = columns
            cls.__primary_key__ = next(
                (name for name, col in columns.items() if col.primary_key),
                None,
            )
            if not getattr(cls, "__abstract__", False):
                _DeclarativeBase.metadata.register_model(cls)

        def __init__(self, **kwargs: Any) -> None:
            columns: Dict[str, Column] = getattr(self, "__columns__", {})
            for name, column in columns.items():
                if name in kwargs:
                    value = kwargs.pop(name)
                else:
                    value = column.default_value()
                setattr(self, name, value)
            for key, value in kwargs.items():
                setattr(self, key, value)

    DeclarativeBase = _DeclarativeBase

    class Mapped(Generic[_T]):  # type: ignore[misc]
        ...

    def mapped_column(*args: Any, **kwargs: Any) -> Column:
        return Column(*args, **kwargs)

    relationship = _Relationship

    class _Select:
        def __init__(self, *entities: Any) -> None:
            if not entities:
                raise ValueError("select() requires at least one entity")
            self._entities = entities
            self._where: List[_Criterion] = []
            self._limit: Optional[int] = None
            self._select_from: Any | None = None

        def _clone(self) -> "_Select":
            clone = _Select(*self._entities)
            clone._where = list(self._where)
            clone._limit = self._limit
            clone._select_from = self._select_from
            return clone

        def where(self, criterion: _Criterion) -> "_Select":
            clone = self._clone()
            clone._where.append(criterion)
            return clone

        def limit(self, value: int) -> "_Select":  # pragma: no cover - unused in tests
            clone = self._clone()
            clone._limit = value
            return clone

        def select_from(self, entity: Any) -> "_Select":  # pragma: no cover
            clone = self._clone()
            clone._select_from = entity
            return clone

        def group_by(self, *args: Any) -> "_Select":  # pragma: no cover
            return self

        def order_by(self, *args: Any) -> "_Select":  # pragma: no cover
            return self

        @property
        def entities(self) -> Tuple[Any, ...]:
            return self._entities

    def select(*entities: Any) -> _Select:
        return _Select(*entities)

    class Result:
        def __init__(self, rows: Sequence[Any]) -> None:
            self._rows = list(rows)

        def __iter__(self) -> Iterator[Any]:
            return iter(self._rows)

        def all(self) -> List[Any]:  # pragma: no cover - compatibility helper
            return list(self._rows)

        def fetchall(self) -> List[Any]:  # pragma: no cover - compatibility helper
            return self.all()

        def first(self) -> Any | None:  # pragma: no cover - compatibility helper
            return self._rows[0] if self._rows else None

        def scalars(self) -> "ScalarResult":
            return ScalarResult(self._rows)

        def scalar_one(self) -> Any:
            values = self.scalars().all()
            if len(values) != 1:
                raise RuntimeError("Expected exactly one row")
            return values[0]

        def scalar_one_or_none(self) -> Any:
            values = self.scalars().all()
            if not values:
                return None
            if len(values) > 1:
                raise RuntimeError("Expected at most one row")
            return values[0]

        def mappings(self) -> "_MappingResult":  # pragma: no cover - unused in tests
            return _MappingResult(self._rows)

    class ScalarResult:
        def __init__(self, values: Sequence[Any]) -> None:
            self._values = list(values)

        def __iter__(self) -> Iterator[Any]:
            return iter(self._values)

        def all(self) -> List[Any]:
            return list(self._values)

        def first(self) -> Any | None:  # pragma: no cover - compatibility helper
            return self._values[0] if self._values else None

        def one(self) -> Any:  # pragma: no cover - compatibility helper
            if len(self._values) != 1:
                raise RuntimeError("Expected exactly one row")
            return self._values[0]

        def one_or_none(self) -> Any:  # pragma: no cover - compatibility helper
            if not self._values:
                return None
            if len(self._values) > 1:
                raise RuntimeError("Expected at most one row")
            return self._values[0]

    class _MappingResult:  # pragma: no cover - compatibility helper
        def __init__(self, rows: Sequence[Any]) -> None:
            self._rows = []
            for row in rows:
                if isinstance(row, dict):
                    self._rows.append(dict(row))
                elif isinstance(row, tuple):
                    self._rows.append({str(index): value for index, value in enumerate(row)})
                else:
                    self._rows.append({"value": row})

        def first(self) -> Dict[str, Any] | None:
            return self._rows[0] if self._rows else None

        def all(self) -> List[Dict[str, Any]]:
            return list(self._rows)

    class AsyncEngine:
        def __init__(self) -> None:
            self._data: Dict[Type[_DeclarativeBase], List[_DeclarativeBase]] = defaultdict(list)
            self._identity: Dict[Type[_DeclarativeBase], int] = defaultdict(int)

        def _ensure_storage(self, model: Type[_DeclarativeBase]) -> None:
            self._data.setdefault(model, [])
            self._identity.setdefault(model, 0)

        def begin(self) -> "_EngineContext":
            return _EngineContext(self)

        async def dispose(self) -> None:
            self._data.clear()
            self._identity.clear()

    class _EngineContext:
        def __init__(self, engine: AsyncEngine) -> None:
            self._engine = engine

        async def __aenter__(self) -> "_EngineConnection":
            return _EngineConnection(self._engine)

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

    class _EngineConnection:
        def __init__(self, engine: AsyncEngine) -> None:
            self._engine = engine

        async def run_sync(self, fn: Callable[[Any], Any]) -> Any:
            return fn(self._engine)

    class AsyncSession:
        def __init__(self, engine: AsyncEngine) -> None:
            self._engine = engine
            self._closed = False

        async def __aenter__(self) -> "AsyncSession":
            self._closed = False
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            await self.close()

        async def close(self) -> None:
            self._closed = True

        async def aclose(self) -> None:  # pragma: no cover - compatibility helper
            await self.close()

        def _ensure_open(self) -> None:
            if self._closed:
                raise RuntimeError("Session is closed")

        def _assign_identity(self, instance: _DeclarativeBase) -> None:
            model = type(instance)
            self._engine._ensure_storage(model)
            pk_name = getattr(model, "__primary_key__", None)
            if pk_name:
                current = getattr(instance, pk_name)
                if current is None:
                    self._engine._identity[model] += 1
                    setattr(instance, pk_name, self._engine._identity[model])

        def add(self, instance: _DeclarativeBase) -> None:
            self._ensure_open()
            model = type(instance)
            self._engine._ensure_storage(model)
            if instance not in self._engine._data[model]:
                self._assign_identity(instance)
                self._engine._data[model].append(instance)

        def add_all(self, instances: Iterable[_DeclarativeBase]) -> None:  # pragma: no cover
            for item in instances:
                self.add(item)

        async def flush(self) -> None:
            return None

        async def commit(self) -> None:
            return None

        async def rollback(self) -> None:
            return None

        async def refresh(self, instance: _DeclarativeBase) -> None:
            return None

        async def execute(self, statement: Any) -> Result:
            self._ensure_open()
            if isinstance(statement, _Select):
                return Result(self._run_select(statement))
            if isinstance(statement, _DeleteStatement):
                model = statement.model
                self._engine._ensure_storage(model)
                self._engine._data[model] = []
                self._engine._identity[model] = 0
                return Result([])
            if isinstance(statement, _TextClause):
                return Result([])
            raise TypeError(f"Unsupported statement type: {type(statement)!r}")

        def _filtered_rows(
            self, model: Type[_DeclarativeBase], criteria: Sequence[_Criterion]
        ) -> List[_DeclarativeBase]:
            self._engine._ensure_storage(model)
            rows = []
            for instance in list(self._engine._data[model]):
                if all(criterion.evaluate(instance) for criterion in criteria):
                    rows.append(instance)
            return rows

        def _select_model(self, statement: _Select) -> Optional[Type[_DeclarativeBase]]:
            if statement._select_from is not None:
                entity = statement._select_from
                if isinstance(entity, Column) and entity.model is not None:
                    return entity.model
                if isinstance(entity, type) and issubclass(entity, _DeclarativeBase):
                    return entity
            first = statement.entities[0]
            if isinstance(first, Column) and first.model is not None:
                return first.model
            if isinstance(first, type) and issubclass(first, _DeclarativeBase):
                return first
            return None

        def _run_select(self, statement: _Select) -> List[Any]:
            model = self._select_model(statement)
            if model is None:
                return []
            rows = self._filtered_rows(model, statement._where)
            if statement.entities and isinstance(statement.entities[0], _FunctionExpression):
                return [statement.entities[0].evaluate(rows)]
            results: List[Any] = []
            for instance in rows:
                if len(statement.entities) == 1:
                    entity = statement.entities[0]
                    if isinstance(entity, Column):
                        results.append(getattr(instance, entity.name))
                    else:
                        results.append(instance)
                else:  # pragma: no cover - unused in current tests
                    row: List[Any] = []
                    for entity in statement.entities:
                        if isinstance(entity, Column):
                            row.append(getattr(instance, entity.name))
                        else:
                            row.append(instance)
                    results.append(tuple(row))
            if statement._limit is not None:
                results = results[: statement._limit]
            return results

        async def get(
            self, model: Type[_DeclarativeBase], identity: Any
        ) -> Optional[_DeclarativeBase]:
            self._engine._ensure_storage(model)
            pk_name = getattr(model, "__primary_key__", None)
            for instance in self._engine._data[model]:
                if pk_name is None:
                    continue
                if getattr(instance, pk_name) == identity:
                    return instance
            return None

    class _AsyncSessionFactory:
        def __init__(self, engine: AsyncEngine) -> None:
            self._engine = engine

        def __call__(self, **kwargs: Any) -> AsyncSession:
            return AsyncSession(self._engine)

    class async_sessionmaker:  # type: ignore[override]
        def __new__(cls, *args: Any, **kwargs: Any) -> _AsyncSessionFactory:
            if args:
                engine = args[0]
            else:
                engine = kwargs.get("bind")
            if engine is None:
                raise TypeError("async_sessionmaker requires an engine")
            return _AsyncSessionFactory(engine)

        @classmethod
        def __class_getitem__(cls, item: Any) -> Type["async_sessionmaker"]:
            return cls

    def create_async_engine(*args: Any, **kwargs: Any) -> AsyncEngine:
        return AsyncEngine()

    class TypeDecorator:
        cache_ok = False

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            ...

        def load_dialect_impl(self, dialect: Any) -> Any:
            return getattr(self, "impl", None)

    class JSON(TypeDecorator):  # pragma: no cover - simple placeholder
        impl = dict

    class JSONB(JSON):  # pragma: no cover - simple placeholder
        ...

    class DialectModule(ModuleType):
        def __init__(self) -> None:
            super().__init__("sqlalchemy.dialects.postgresql")
            self.JSONB = JSONB  # type: ignore[attr-defined]

    class TypesModule(ModuleType):
        def __init__(self) -> None:
            super().__init__("sqlalchemy.types")
            self.JSON = JSON  # type: ignore[attr-defined]
            self.TypeDecorator = TypeDecorator  # type: ignore[attr-defined]

    class OrmModule(ModuleType):
        def __init__(self) -> None:
            super().__init__("sqlalchemy.orm")
            self.DeclarativeBase = DeclarativeBase  # type: ignore[attr-defined]
            self.relationship = relationship  # type: ignore[attr-defined]
            self.mapped_column = mapped_column  # type: ignore[attr-defined]
            self.Mapped = Mapped  # type: ignore[attr-defined]
            self.selectinload = lambda *args, **kwargs: None  # type: ignore[attr-defined]

    class ExtAsyncioModule(ModuleType):
        def __init__(self) -> None:
            super().__init__("sqlalchemy.ext.asyncio")
            self.AsyncSession = AsyncSession  # type: ignore[attr-defined]
            self.async_sessionmaker = async_sessionmaker  # type: ignore[attr-defined]
            self.create_async_engine = create_async_engine  # type: ignore[attr-defined]
            self.AsyncEngine = AsyncEngine  # type: ignore[attr-defined]

    class ExtModule(ModuleType):
        def __init__(self, asyncio_module: ModuleType) -> None:
            super().__init__("sqlalchemy.ext")
            self.asyncio = asyncio_module

    class SqlalchemyModule(ModuleType):
        def __init__(self) -> None:
            super().__init__("sqlalchemy")
            self.Boolean = Boolean  # type: ignore[attr-defined]
            self.CheckConstraint = CheckConstraint  # type: ignore[attr-defined]
            self.UniqueConstraint = UniqueConstraint  # type: ignore[attr-defined]
            self.Column = Column  # type: ignore[attr-defined]
            self.Date = Date  # type: ignore[attr-defined]
            self.DateTime = DateTime  # type: ignore[attr-defined]
            self.Float = Float  # type: ignore[attr-defined]
            self.ForeignKey = ForeignKey  # type: ignore[attr-defined]
            self.Index = Index  # type: ignore[attr-defined]
            self.Integer = Integer  # type: ignore[attr-defined]
            self.Numeric = Numeric  # type: ignore[attr-defined]
            self.String = String  # type: ignore[attr-defined]
            self.Text = Text  # type: ignore[attr-defined]
            self.Select = _Select  # type: ignore[attr-defined]
            self.select = select  # type: ignore[attr-defined]
            self.func = _Func()  # type: ignore[attr-defined]
            self.text = text  # type: ignore[attr-defined]

    class _Func:
        def now(self) -> Callable[[], datetime]:
            return lambda: datetime.now(timezone.utc)

        def count(self) -> _FunctionExpression:  # pragma: no cover - seldom used
            return _FunctionExpression("count")

    sqlalchemy_module = SqlalchemyModule()
    asyncio_module = ExtAsyncioModule()
    ext_module = ExtModule(asyncio_module)
    orm_module = OrmModule()
    types_module = TypesModule()
    dialect_module = DialectModule()
    sql_module = ModuleType("sqlalchemy.sql")
    sql_module.func = sqlalchemy_module.func  # type: ignore[attr-defined]
    sql_module.text = text  # type: ignore[attr-defined]

    sqlalchemy_module.orm = orm_module  # type: ignore[attr-defined]
    sqlalchemy_module.types = types_module  # type: ignore[attr-defined]
    sqlalchemy_module.ext = ext_module  # type: ignore[attr-defined]
    sqlalchemy_module.dialects = ModuleType("sqlalchemy.dialects")
    sqlalchemy_module.dialects.postgresql = dialect_module  # type: ignore[attr-defined]

    sys.modules.setdefault("sqlalchemy", sqlalchemy_module)
    sys.modules.setdefault("sqlalchemy.ext", ext_module)
    sys.modules.setdefault("sqlalchemy.ext.asyncio", asyncio_module)
    sys.modules.setdefault("sqlalchemy.orm", orm_module)
    sys.modules.setdefault("sqlalchemy.types", types_module)
    sys.modules.setdefault("sqlalchemy.dialects", sqlalchemy_module.dialects)
    sys.modules.setdefault("sqlalchemy.dialects.postgresql", dialect_module)
    sys.modules.setdefault("sqlalchemy.sql", sql_module)

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
