"""Simplified FastAPI-compatible interface for the test environment."""

from __future__ import annotations

import asyncio
import inspect
import json
import re
from collections.abc import Awaitable, Callable, Iterable
from collections.abc import Mapping
from collections.abc import Mapping as MappingABC
from collections.abc import Sequence as SequenceABC
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from functools import cache, lru_cache
from types import SimpleNamespace
from typing import (
    Any,
    Dict,
    Literal,
    Optional,
    Tuple,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)
from urllib.parse import parse_qsl

from pydantic import BaseModel

from . import status  # noqa: F401  (re-exported)


class HTTPException(Exception):
    """Raised by route handlers to signal an HTTP error."""

    def __init__(self, status_code: int, detail: Any = None) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class Depends:
    """Marker specifying that a parameter should be resolved via dependency injection."""

    def __init__(self, dependency: Callable[..., Any]) -> None:
        self.dependency = dependency


@dataclass
class Request:
    """Minimal request object exposing headers and state."""

    scope: Mapping[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    state: SimpleNamespace = field(default_factory=SimpleNamespace)

    async def body(self) -> bytes:  # pragma: no cover - rarely used in tests
        return b""

    def __getattr__(self, name: str) -> Any:  # pragma: no cover - simple proxy
        return self.scope.get(name)


class Query:
    def __init__(
        self,
        default: Any = None,
        *,
        description: str | None = None,
        **_: Any,
    ) -> None:
        self.default = default
        self.description = description


class Path(Query):
    """Marker used for path parameters."""

    pass


class Header:
    def __init__(self, default: Any = None) -> None:
        self.default = default


class Body:
    """Marker used for request body parameters."""

    def __init__(
        self,
        default: Any = None,
        *,
        embed: bool = False,
        media_type: str = "application/json",
        **kwargs: Any,
    ) -> None:
        self.default = default
        self.embed = embed
        self.media_type = media_type


class Form:
    def __init__(self, default: Any = None) -> None:
        self.default = default


class File:
    def __init__(self, default: Any = None) -> None:
        self.default = default


@dataclass
class UploadFile:
    """Minimal representation of an uploaded file."""

    filename: str
    content_type: str
    _data: bytes

    async def read(self) -> bytes:
        return self._data

    def read_sync(self) -> bytes:
        return self._data


class Response:
    """Base HTTP response object."""

    def __init__(
        self,
        content: Any = b"",
        *,
        status_code: int = status.HTTP_200_OK,
        media_type: str | None = "application/json",
        headers: Mapping[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.media_type = media_type
        self._content = content
        self.headers: dict[str, str] = dict(headers or {})

    async def render(self) -> bytes:
        content = self._content
        if content is None:
            return b""
        if isinstance(content, bytes):
            return content
        if isinstance(content, str):
            return content.encode("utf-8")
        if isinstance(content, (dict, list)):
            return json.dumps(content, default=_json_default).encode("utf-8")
        return str(content).encode("utf-8")


class StreamingResponse(Response):
    """Response that streams content, used for export endpoints."""

    def __init__(
        self,
        content: Any,
        *,
        media_type: str | None = None,
        status_code: int = status.HTTP_200_OK,
        headers: Mapping[str, str] | None = None,
        background: Callable[[], Awaitable[None] | None] | None = None,
    ) -> None:
        super().__init__(
            b"", status_code=status_code, media_type=media_type, headers=headers
        )
        self._stream = content
        self._background = background

    async def render(self) -> bytes:
        payload = b""
        stream = self._stream
        if hasattr(stream, "read"):
            chunk = stream.read()
            if inspect.isawaitable(chunk):
                chunk = await chunk
            payload = chunk or b""
        elif hasattr(stream, "__aiter__"):
            async for item in stream:  # pragma: no cover - rarely exercised
                payload += (
                    item if isinstance(item, bytes) else str(item).encode("utf-8")
                )
        else:
            for item in stream:  # pragma: no cover - rarely exercised
                payload += (
                    item if isinstance(item, bytes) else str(item).encode("utf-8")
                )
        if self._background is not None:
            result = self._background()
            if inspect.isawaitable(
                result
            ):  # pragma: no cover - optional async background
                await result
        return payload


class JSONResponse(Response):
    """Static JSON response wrapper used for schema endpoints."""

    def __init__(
        self,
        content: Any,
        *,
        status_code: int = status.HTTP_200_OK,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(
            content,
            status_code=status_code,
            media_type="application/json",
            headers=headers,
        )


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return str(value)


def _is_undefined(value: Any) -> bool:
    """Return True when a value corresponds to pydantic's undefined sentinel."""

    return getattr(value.__class__, "__name__", "") == "_Undefined"


def _normalise_example(value: Any) -> Any:
    """Convert example values into JSON-friendly types."""

    if isinstance(value, BaseModel):
        return _normalise_example(value.model_dump(mode="json"))
    if isinstance(value, dict):
        return {str(key): _normalise_example(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_normalise_example(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Enum):
        return getattr(value, "value", value.name)
    return value


def _build_model_example(annotation: Any) -> Any:
    """Return a representative example for the supplied type annotation."""

    if annotation is inspect._empty or annotation is Any:
        return None

    origin = get_origin(annotation)
    if origin is Union:
        for arg in get_args(annotation):
            if arg is type(None):
                continue
            example = _build_model_example(arg)
            if example is not None:
                return example
        return None
    if origin is not None:
        if (
            isinstance(origin, type)
            and issubclass(origin, SequenceABC)
            and not issubclass(origin, (str, bytes))
        ) or origin in {list, set, tuple}:
            args = get_args(annotation)
            item_type = args[0] if args else Any
            item_example = _build_model_example(item_type)
            if item_example is None:
                return []
            return _normalise_example([item_example])
        if (isinstance(origin, type) and issubclass(origin, MappingABC)) or origin in {
            dict,
            dict,
            Mapping,
        }:
            args = get_args(annotation)
            key_type = args[0] if len(args) >= 1 else str
            value_type = args[1] if len(args) >= 2 else Any
            key_example = _build_model_example(key_type)
            if isinstance(key_example, (dict, list, set, tuple)) or key_example is None:
                key_example = "key"
            value_example = _build_model_example(value_type)
            return {str(key_example): _normalise_example(value_example)}
    if origin is Literal:
        values = get_args(annotation)
        if values:
            return _normalise_example(values[0])

    if inspect.isclass(annotation):
        if issubclass(annotation, BaseModel):
            return _build_base_model_example(annotation)
        if issubclass(annotation, Enum):
            try:
                first = next(iter(annotation))  # type: ignore[arg-type]
            except StopIteration:
                return None
            return _normalise_example(getattr(first, "value", first))
        if annotation is str:
            return "string"
        if annotation is int:
            return 0
        if annotation is float:
            return 0.0
        if annotation is bool:
            return True
        if annotation is datetime:
            return datetime.now().isoformat()
        if annotation is date:
            return date.today().isoformat()
        if annotation is Decimal:
            return "0"

    return None


def _build_base_model_example(model: type[BaseModel]) -> Any:
    """Create a JSON-serialisable example for a pydantic model."""

    data: dict[str, Any] = {}
    for name, field in getattr(model, "model_fields", {}).items():
        annotation = getattr(field, "annotation", Any)
        value: Any
        default_factory = getattr(field, "default_factory", None)
        default = getattr(field, "default", None)
        if callable(default_factory):
            try:
                value = default_factory()
            except Exception:
                value = None
        elif default is not None and not _is_undefined(default):
            value = default
        elif getattr(field, "required", False):
            value = _build_model_example(annotation)
        else:
            value = _build_model_example(annotation)
        data[name] = value

    try:
        instance = model(**data)
        payload = instance.model_dump(mode="json")
    except Exception:
        payload = data
    return _normalise_example(payload)


def _is_pydantic_model_type(annotation: Any) -> bool:
    """Determine whether an annotation represents a pydantic model."""

    if annotation is inspect._empty:
        return False
    if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
        return True

    origin = get_origin(annotation)
    if origin is Union:
        return any(
            _is_pydantic_model_type(arg)
            for arg in get_args(annotation)
            if arg is not type(None)
        )
    if origin is not None:
        if (
            isinstance(origin, type)
            and issubclass(origin, SequenceABC)
            and not issubclass(origin, (str, bytes))
        ) or origin in {list, set, tuple}:
            return any(_is_pydantic_model_type(arg) for arg in get_args(annotation))
        if (isinstance(origin, type) and issubclass(origin, MappingABC)) or origin in {
            dict,
            dict,
            Mapping,
        }:
            args = get_args(annotation)
            if len(args) >= 2:
                return _is_pydantic_model_type(args[1])
    return False


def _extract_request_model(route: _Route) -> Any:
    """Return the request body model associated with the route if present."""

    endpoint = route.endpoint
    signature = inspect.signature(endpoint)
    for name, parameter in signature.parameters.items():
        if route.path and f"{{{name}}}" in route.path:
            continue
        default = parameter.default
        if isinstance(default, (Depends, Query, Header, Form, File)):
            continue
        annotation = _resolve_annotation(endpoint, name, parameter.annotation)
        if _is_pydantic_model_type(annotation):
            return annotation
    return None


class _Route:
    def __init__(
        self,
        path: str,
        *,
        endpoint: Callable[..., Any],
        methods: Iterable[str],
        response_model: type | None = None,
        status_code: int | None = None,
    ) -> None:
        self.path = path
        self.endpoint = endpoint
        self.methods = {method.upper() for method in methods}
        self.response_model = response_model
        self.status_code = status_code
        self.pattern, self.param_converters = _compile_path(path)

    def match(self, path: str) -> dict[str, str] | None:
        match = self.pattern.match(path)
        if not match:
            return None
        return match.groupdict()


def _compile_path(path: str) -> tuple[re.Pattern[str], dict[str, Callable[[str], Any]]]:
    pattern = "^"
    converters: dict[str, Callable[[str], Any]] = {}
    for segment in filter(None, path.split("/")):
        if segment.startswith("{") and segment.endswith("}"):
            name = segment.strip("{}")
            converters[name] = _convert_path_value
            pattern += rf"/(?P<{name}>[^/]+)"
        else:
            pattern += "/" + re.escape(segment)
    pattern = pattern.rstrip("/")
    pattern += "/?"
    pattern += "$"
    return re.compile(pattern), converters


def _convert_path_value(value: str) -> str:
    return value


class APIRouter:
    """Collects routes prior to inclusion within an application."""

    def __init__(
        self, *, prefix: str = "", tags: Iterable[str] | None = None
    ) -> None:
        self.prefix = prefix.rstrip("/")
        self.routes: list[_Route] = []
        self.tags = list(tags or [])

    def add_api_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        methods: Iterable[str],
        response_model: type | None = None,
        status_code: int | None = None,
    ) -> None:
        full_path = (
            f"{self.prefix}{path}" if path.startswith("/") else f"{self.prefix}/{path}"
        )
        route = _Route(
            full_path or "/",
            endpoint=endpoint,
            methods=[method.upper() for method in methods],
            response_model=response_model,
            status_code=status_code,
        )
        self.routes.append(route)

    def api_route(
        self,
        path: str,
        *,
        methods: Iterable[str] | None = None,
        response_model: type | None = None,
        status_code: int | None = None,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        resolved_methods = [method.upper() for method in (methods or ["GET"])]
        return self._decorator(
            path,
            methods=resolved_methods,
            response_model=response_model,
            status_code=status_code,
            **kwargs,
        )

    def get(
        self,
        path: str,
        *,
        response_model: type | None = None,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._decorator(
            path, methods=["GET"], response_model=response_model, **kwargs
        )

    def post(
        self,
        path: str,
        *,
        response_model: type | None = None,
        status_code: int | None = None,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.api_route(
            path,
            methods=["POST"],
            response_model=response_model,
            status_code=status_code,
            **kwargs,
        )

    def put(
        self,
        path: str,
        *,
        response_model: type | None = None,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._decorator(
            path, methods=["PUT"], response_model=response_model, **kwargs
        )

    def patch(
        self,
        path: str,
        *,
        response_model: type | None = None,
        status_code: int | None = None,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._decorator(
            path,
            methods=["PATCH"],
            response_model=response_model,
            status_code=status_code,
            **kwargs,
        )

    def delete(
        self,
        path: str,
        *,
        response_model: type | None = None,
        status_code: int | None = None,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._decorator(
            path,
            methods=["DELETE"],
            response_model=response_model,
            status_code=status_code,
            **kwargs,
        )

    def include_router(self, router: APIRouter) -> None:
        for route in router.routes:
            self.routes.append(route)

    def _decorator(
        self,
        path: str,
        *,
        methods: Iterable[str],
        response_model: type | None = None,
        status_code: int | None = None,
        **_: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
            self.add_api_route(
                path,
                func,
                methods=methods,
                response_model=response_model,
                status_code=status_code,
            )
            return func

        return wrapper


class FastAPI:
    """Small subset of FastAPI used in the test suite."""

    def __init__(
        self,
        *,
        title: str | None = None,
        version: str | None = None,
        lifespan: Any = None,
        openapi_url: str | None = "/openapi.json",
        **extra: Any,
    ) -> None:
        self.title = title or "FastAPI"
        self.version = version or "0.1.0"
        self.router = APIRouter()
        self.routes: list[_Route] = []
        self.dependency_overrides: dict[Callable[..., Any], Callable[..., Any]] = {}
        self._middleware: list[tuple[Any, dict[str, Any]]] = []
        self._lifespan = lifespan
        self.openapi_tags: list[dict[str, Any]] = list(extra.get("openapi_tags", []))
        self._openapi_schema: dict[str, Any] | None = None
        self.openapi_url = openapi_url
        self.state = SimpleNamespace()  # Application state for storing arbitrary data

        if self.openapi_url:
            openapi_path = (
                self.openapi_url
                if self.openapi_url.startswith("/")
                else f"/{self.openapi_url}"
            )

            async def _openapi_handler() -> JSONResponse:
                return JSONResponse(self.openapi())

            self.routes.append(
                _Route(openapi_path, endpoint=_openapi_handler, methods=["GET"])
            )

    def add_middleware(
        self, middleware_cls: Any, **options: Any
    ) -> None:  # pragma: no cover - middleware ignored
        self._middleware.append((middleware_cls, options))

    def exception_handler(self, exc_class: type[Exception]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Register an exception handler for a specific exception type.

        This is a stub implementation that returns a no-op decorator.
        """
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func
        return decorator

    def include_router(self, router: APIRouter, *, prefix: str = "") -> None:
        prefix = prefix.rstrip("/")
        for route in router.routes:
            combined_path = (
                f"{prefix}{route.path}"
                if route.path.startswith("/")
                else f"{prefix}/{route.path}"
            )
            combined = _Route(
                combined_path or "/",
                endpoint=route.endpoint,
                methods=route.methods,
                response_model=route.response_model,
                status_code=route.status_code,
            )
            self.routes.append(combined)
            self.router.routes.append(combined)
        self._openapi_schema = None

    def get(
        self, path: str, *, response_model: type | None = None
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        decorator = self.router.get(path, response_model=response_model)

        def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
            result = decorator(func)
            self._openapi_schema = None
            return result

        return wrapper

    def post(
        self,
        path: str,
        *,
        response_model: type | None = None,
        status_code: int | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        decorator = self.router.post(
            path,
            response_model=response_model,
            status_code=status_code,
        )

        def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
            result = decorator(func)
            self._openapi_schema = None
            return result

        return wrapper

    async def handle_request(
        self,
        *,
        method: str,
        path: str,
        query_params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        form_data: Mapping[str, Any] | None = None,
        files: Mapping[str, tuple[str, bytes, str]] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        route = self._match_route(method, path)
        if route is None:
            return (
                status.HTTP_404_NOT_FOUND,
                {"content-type": "application/json"},
                json.dumps({"detail": "Not Found"}).encode("utf-8"),
            )

        try:
            header_map = {key.lower(): value for key, value in (headers or {}).items()}
            body = await _execute_route(
                self,
                route,
                method=method,
                path=path,
                query_params=query_params or {},
                json_body=json_body,
                form_data=form_data or {},
                files=files or {},
                headers=header_map,
            )
            status_code, headers, payload = body
            return status_code, headers, payload
        except HTTPException as exc:
            payload = json.dumps({"detail": exc.detail}).encode("utf-8")
            headers = {"content-type": "application/json"}
            return exc.status_code, headers, payload

    def _match_route(self, method: str, path: str) -> _Route | None:
        candidates = self.routes + self.router.routes
        for route in candidates:
            if method.upper() not in route.methods:
                continue
            if route.match(path) is not None:
                return route
        return None

    def openapi(self) -> dict[str, Any]:
        """Return a cached OpenAPI representation of the registered routes."""

        if self._openapi_schema is not None:
            return self._openapi_schema

        schema: dict[str, Any] = {
            "openapi": "3.1.0",
            "info": {"title": self.title, "version": self.version},
            "paths": {},
        }
        if self.openapi_tags:
            schema["tags"] = self.openapi_tags

        for route in self.routes + self.router.routes:
            path_item = schema["paths"].setdefault(route.path, {})
            request_model = _extract_request_model(route)
            summary = inspect.getdoc(route.endpoint)
            for method in sorted(route.methods):
                operation: dict[str, Any] = {}
                if summary:
                    operation["summary"] = summary.splitlines()[0]

                if request_model is not None:
                    request_example = _build_model_example(request_model)
                    if request_example is not None:
                        operation["requestBody"] = {
                            "content": {
                                "application/json": {"example": request_example}
                            }
                        }

                status_code = route.status_code or status.HTTP_200_OK
                responses: dict[str, Any] = {
                    str(status_code): {"description": "Successful Response"}
                }
                response_model = route.response_model
                if response_model is not None:
                    response_example = _build_model_example(response_model)
                    if response_example is not None:
                        responses[str(status_code)]["content"] = {
                            "application/json": {"example": response_example}
                        }

                operation["responses"] = responses
                path_item[method.lower()] = operation

        self._openapi_schema = schema
        return schema

    async def __call__(self, scope, receive, send) -> None:
        """Minimal ASGI entrypoint supporting httpx.AsyncClient."""

        scope_type = scope.get("type")
        if scope_type == "lifespan":
            await self._handle_lifespan(receive, send)
            return

        if scope_type != "http":  # pragma: no cover - non-http scopes unused
            raise RuntimeError(f"Unsupported ASGI scope: {scope_type}")

        method = scope.get("method", "GET")
        path = scope.get("path", "/")
        raw_query = scope.get("query_string", b"")
        query_params = dict(parse_qsl(raw_query.decode("utf-8"))) if raw_query else {}
        headers = {
            key.decode("latin-1"): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }

        body = b""
        more_body = True
        json_payload: Any | None = None
        form_data: dict[str, Any] = {}

        while more_body:
            message = await receive()
            if message["type"] != "http.request":
                continue
            body += message.get("body", b"")
            more_body = message.get("more_body", False)

        if body:
            content_type = headers.get("content-type", "")
            try:
                if "application/json" in content_type or not content_type:
                    json_payload = json.loads(body.decode("utf-8"))
                elif "application/x-www-form-urlencoded" in content_type:
                    form_data = dict(parse_qsl(body.decode("utf-8")))
            except (ValueError, UnicodeDecodeError):  # pragma: no cover - fallback
                json_payload = None

        status_code, response_headers, payload = await self.handle_request(
            method=method,
            path=path,
            query_params=query_params,
            json_body=json_payload,
            form_data=form_data,
            files={},
            headers=headers,
        )

        await send(
            {
                "type": "http.response.start",
                "status": status_code,
                "headers": [
                    (key.encode("latin-1"), value.encode("latin-1"))
                    for key, value in response_headers.items()
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": payload,
                "more_body": False,
            }
        )

    async def _handle_lifespan(self, receive, send) -> None:
        """Process lifespan startup/shutdown events."""

        async def _emit(message_type: str) -> None:
            await send({"type": f"lifespan.{message_type}.complete"})

        if self._lifespan is None:
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await _emit("startup")
                elif message["type"] == "lifespan.shutdown":
                    await _emit("shutdown")
                    break
            return

        async with self._lifespan(self):
            started = False
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    if not started:
                        await _emit("startup")
                        started = True
                elif message["type"] == "lifespan.shutdown":
                    await _emit("shutdown")
                    break


async def _execute_route(
    app: FastAPI,
    route: _Route,
    *,
    method: str,
    path: str,
    query_params: Mapping[str, Any],
    json_body: Any,
    form_data: Mapping[str, Any],
    files: Mapping[str, tuple[str, bytes, str]],
    headers: Mapping[str, str],
) -> tuple[int, dict[str, str], bytes]:
    path_params = route.match(path) or {}
    converted_params = {
        key: _convert_path_param(value, route.endpoint, key)
        for key, value in path_params.items()
    }
    cleanup_callbacks: list[Callable[[], Awaitable[None] | None]] = []
    try:
        arguments = await _build_arguments(
            app,
            route.endpoint,
            converted_params,
            query_params,
            json_body,
            form_data,
            files,
            headers,
            cleanup_callbacks,
        )
        result = route.endpoint(**arguments)
        if inspect.isawaitable(result):
            result = await result

        response = await _serialise_response(route, result)
        return response
    finally:
        await _run_cleanups(cleanup_callbacks)


async def _run_cleanups(
    callbacks: Iterable[Callable[[], Awaitable[None] | None]],
) -> None:
    for callback in callbacks:
        try:
            result = callback()
            if inspect.isawaitable(result):
                await result
        except Exception:  # pragma: no cover - defensive cleanup
            continue


async def _build_arguments(
    app: FastAPI,
    endpoint: Callable[..., Any],
    path_params: Mapping[str, Any],
    query_params: Mapping[str, Any],
    json_body: Any,
    form_data: Mapping[str, Any],
    files: Mapping[str, tuple[str, bytes, str]],
    headers: Mapping[str, str],
    cleanup_callbacks: list[Callable[[], Awaitable[None] | None]],
) -> dict[str, Any]:
    signature = inspect.signature(endpoint)
    arguments: dict[str, Any] = {}

    body_consumed = False
    for name, parameter in signature.parameters.items():
        annotation = _resolve_annotation(endpoint, name, parameter.annotation)
        default = parameter.default

        if name in path_params:
            arguments[name] = _coerce_type(path_params[name], annotation)
            continue

        if isinstance(default, Depends):
            dependency = app.dependency_overrides.get(
                default.dependency, default.dependency
            )
            resolved = await _resolve_dependency(
                app,
                dependency,
                path_params,
                query_params,
                json_body,
                form_data,
                files,
                headers,
                cleanup_callbacks,
            )
            arguments[name] = resolved
            continue

        if isinstance(default, Header):
            header_name = name.replace("_", "-")
            header_key = header_name.lower()
            value = headers.get(header_key)
            if value is None:
                value = headers.get(name.lower())
            if value is None:
                if default.default is ...:
                    raise HTTPException(
                        status.HTTP_422_UNPROCESSABLE_ENTITY,
                        f"Missing required header {header_name}",
                    )
                value = default.default
            arguments[name] = _coerce_type(value, annotation)
            continue

        if isinstance(default, Query):
            if default.default is ...:
                if name not in query_params:
                    raise HTTPException(
                        status.HTTP_422_UNPROCESSABLE_ENTITY,
                        f"Missing query parameter {name}",
                    )
            value = query_params.get(name, default.default)
            arguments[name] = _coerce_type(value, annotation)
            continue

        if isinstance(default, Form):
            if default.default is ... and name not in form_data:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY, f"Missing form field {name}"
                )
            value = form_data.get(name, default.default)
            arguments[name] = _coerce_type(value, annotation)
            continue

        if isinstance(default, File):
            if name not in files:
                if default.default is ...:
                    raise HTTPException(
                        status.HTTP_422_UNPROCESSABLE_ENTITY,
                        f"Missing file field {name}",
                    )
                arguments[name] = default.default
                continue
            filename, payload, content_type = files[name]
            arguments[name] = UploadFile(
                filename=filename, content_type=content_type, _data=payload
            )
            continue

        if (
            name == "request"
            and (annotation is Request or annotation is inspect._empty)
        ):
            arguments[name] = Request(headers=dict(headers))
            continue

        if json_body is not None and not body_consumed:
            if name == "payload" or (
                inspect.isclass(annotation) and hasattr(annotation, "model_validate")
            ):
                arguments[name] = _coerce_type(json_body, annotation)
                body_consumed = True
                continue
            if (
                annotation in {dict, Mapping, Any}
                and parameter.default is inspect._empty
            ):
                arguments[name] = json_body
                body_consumed = True
                continue

        if parameter.default is not inspect._empty:
            arguments[name] = parameter.default
            continue

        if name in query_params:
            arguments[name] = _coerce_type(query_params[name], annotation)
            continue

        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unable to resolve parameter {name}"
        )

    return arguments


async def _resolve_dependency(
    app: FastAPI,
    dependency: Callable[..., Any],
    path_params: Mapping[str, Any],
    query_params: Mapping[str, Any],
    json_body: Any,
    form_data: Mapping[str, Any],
    files: Mapping[str, tuple[str, bytes, str]],
    headers: Mapping[str, str],
    cleanup_callbacks: list[Callable[[], Awaitable[None] | None]],
) -> Any:
    nested_cleanups: list[Callable[[], Awaitable[None] | None]] = []
    signature = inspect.signature(dependency)
    if signature.parameters:
        arguments = await _build_arguments(
            app,
            dependency,
            path_params,
            query_params,
            json_body,
            form_data,
            files,
            headers,
            nested_cleanups,
        )
    else:
        arguments = {}

    result = dependency(**arguments)
    if inspect.isawaitable(result):
        result = await result
    if inspect.isasyncgen(result):
        agen = result
        value = await agen.__anext__()

        async def _cleanup_async_gen() -> None:
            try:
                await agen.__anext__()
            except StopAsyncIteration:
                pass
            await agen.aclose()

        cleanup_callbacks.extend(nested_cleanups)
        cleanup_callbacks.append(_cleanup_async_gen)
        return value
    if inspect.isgenerator(result):  # pragma: no cover - rarely used
        gen = result
        value = next(gen)

        def _cleanup_sync() -> None:
            try:
                next(gen)
            except StopIteration:
                pass

        cleanup_callbacks.extend(nested_cleanups)
        cleanup_callbacks.append(_cleanup_sync)
        return value

    cleanup_callbacks.extend(nested_cleanups)
    return result


@cache
def _type_hints_for(endpoint: Callable[..., Any]) -> dict[str, Any]:
    try:
        return get_type_hints(endpoint)
    except Exception:
        return {}


def _resolve_annotation(endpoint: Callable[..., Any], name: str, default: Any) -> Any:
    hints = _type_hints_for(endpoint)
    if name in hints:
        return hints[name]
    if isinstance(default, str):
        module = inspect.getmodule(endpoint)
        if module is not None and hasattr(module, default):
            return getattr(module, default)
    return default


def _coerce_type(value: Any, annotation: Any) -> Any:
    if annotation is inspect._empty or value is None:
        return value
    origin = get_origin(annotation)
    if origin is Union and value is not None:
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if args:
            return _coerce_type(value, args[0])
        return value
    if inspect.isclass(annotation) and issubclass(annotation, Enum):
        if isinstance(value, annotation):
            return value
        return annotation(value)
    if inspect.isclass(annotation) and hasattr(annotation, "model_validate"):
        if isinstance(value, annotation):
            return value
        if isinstance(value, Mapping):
            return annotation.model_validate(value)
    if annotation is bool and isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
    if annotation in {int, float, str, bool}:
        return annotation(value)
    if annotation is datetime and isinstance(value, str):
        return datetime.fromisoformat(value)
    if annotation is date and isinstance(value, str):
        return date.fromisoformat(value)
    return value


def _convert_path_param(value: str, endpoint: Callable[..., Any], name: str) -> Any:
    signature = inspect.signature(endpoint)
    parameter = signature.parameters.get(name)
    if parameter:
        annotation = _resolve_annotation(endpoint, name, parameter.annotation)
        if annotation in {int, float}:
            return annotation(value)
    return value


async def _serialise_response(
    route: _Route, result: Any
) -> tuple[int, dict[str, str], bytes]:
    status_code = route.status_code or status.HTTP_200_OK
    headers: dict[str, str] = {"content-type": "application/json"}

    if isinstance(result, Response):
        payload = await result.render()
        if result.media_type:
            headers["content-type"] = result.media_type
        headers.update(result.headers)
        return result.status_code, headers, payload

    if route.response_model is not None:
        try:
            model_type = route.response_model
            origin = get_origin(model_type)
            check_type = origin or model_type
            needs_conversion = not isinstance(result, check_type)
        except TypeError:
            needs_conversion = True
        if needs_conversion and hasattr(route.response_model, "model_validate"):
            result = route.response_model.model_validate(result)

    if hasattr(result, "model_dump"):
        payload = json.dumps(
            result.model_dump(mode="json"), default=_json_default
        ).encode("utf-8")
    elif isinstance(result, (dict, list)):
        payload = json.dumps(result, default=_json_default).encode("utf-8")
    elif result is None:
        payload = b""
    else:
        payload = str(result).encode("utf-8")

    return status_code, headers, payload


__all__ = [
    "APIRouter",
    "Body",
    "Depends",
    "FastAPI",
    "File",
    "Form",
    "Header",
    "HTTPException",
    "JSONResponse",
    "Path",
    "Query",
    "Request",
    "Response",
    "StreamingResponse",
    "UploadFile",
    "status",
]
