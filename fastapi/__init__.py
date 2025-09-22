"""Simplified FastAPI-compatible interface for the test environment."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
import inspect
import json
import re
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    Mapping,
    Optional,
    Tuple,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

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


class Query:
    def __init__(self, default: Any = None, *, description: str | None = None) -> None:
        self.default = default
        self.description = description


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
        headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        self.status_code = status_code
        self.media_type = media_type
        self._content = content
        self.headers: Dict[str, str] = dict(headers or {})

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
        headers: Optional[Mapping[str, str]] = None,
        background: Optional[Callable[[], Awaitable[None] | None]] = None,
    ) -> None:
        super().__init__(b"", status_code=status_code, media_type=media_type, headers=headers)
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
                payload += item if isinstance(item, bytes) else str(item).encode("utf-8")
        else:
            for item in stream:  # pragma: no cover - rarely exercised
                payload += item if isinstance(item, bytes) else str(item).encode("utf-8")
        if self._background is not None:
            result = self._background()
            if inspect.isawaitable(result):  # pragma: no cover - optional async background
                await result
        return payload


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return str(value)


class _Route:
    def __init__(
        self,
        path: str,
        *,
        endpoint: Callable[..., Any],
        methods: Iterable[str],
        response_model: Optional[type] = None,
        status_code: Optional[int] = None,
    ) -> None:
        self.path = path
        self.endpoint = endpoint
        self.methods = {method.upper() for method in methods}
        self.response_model = response_model
        self.status_code = status_code
        self.pattern, self.param_converters = _compile_path(path)

    def match(self, path: str) -> Optional[Dict[str, str]]:
        match = self.pattern.match(path)
        if not match:
            return None
        return match.groupdict()


def _compile_path(path: str) -> Tuple[re.Pattern[str], Dict[str, Callable[[str], Any]]]:
    pattern = "^"
    converters: Dict[str, Callable[[str], Any]] = {}
    for segment in filter(None, path.split("/")):
        if segment.startswith("{") and segment.endswith("}"):
            name = segment.strip("{}")
            converters[name] = _convert_path_value
            pattern += rf"/(?P<{name}>[^/]+)"
        else:
            pattern += "/" + re.escape(segment)
    if path.endswith("/"):
        pattern += "/"
    pattern += "$"
    return re.compile(pattern), converters


def _convert_path_value(value: str) -> str:
    return value


class APIRouter:
    """Collects routes prior to inclusion within an application."""

    def __init__(self, *, prefix: str = "", tags: Optional[Iterable[str]] = None) -> None:
        self.prefix = prefix.rstrip("/")
        self.routes: list[_Route] = []
        self.tags = list(tags or [])

    def add_api_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        methods: Iterable[str],
        response_model: Optional[type] = None,
        status_code: Optional[int] = None,
    ) -> None:
        full_path = f"{self.prefix}{path}" if path.startswith("/") else f"{self.prefix}/{path}"
        route = _Route(
            full_path or "/",
            endpoint=endpoint,
            methods=methods,
            response_model=response_model,
            status_code=status_code,
        )
        self.routes.append(route)

    def get(self, path: str, *, response_model: Optional[type] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._decorator(path, methods=["GET"], response_model=response_model)

    def post(
        self,
        path: str,
        *,
        response_model: Optional[type] = None,
        status_code: Optional[int] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._decorator(path, methods=["POST"], response_model=response_model, status_code=status_code)

    def include_router(self, router: "APIRouter") -> None:
        for route in router.routes:
            self.routes.append(route)

    def _decorator(
        self,
        path: str,
        *,
        methods: Iterable[str],
        response_model: Optional[type] = None,
        status_code: Optional[int] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
            self.add_api_route(path, func, methods=methods, response_model=response_model, status_code=status_code)
            return func

        return wrapper


class FastAPI:
    """Small subset of FastAPI used in the test suite."""

    def __init__(self, *, title: str | None = None, version: str | None = None, lifespan: Any = None, **_: Any) -> None:
        self.title = title
        self.version = version
        self.router = APIRouter()
        self.routes: list[_Route] = []
        self.dependency_overrides: Dict[Callable[..., Any], Callable[..., Any]] = {}
        self._middleware: list[tuple[Any, dict[str, Any]]] = []
        self._lifespan = lifespan

    def add_middleware(self, middleware_cls: Any, **options: Any) -> None:  # pragma: no cover - middleware ignored
        self._middleware.append((middleware_cls, options))

    def include_router(self, router: APIRouter, *, prefix: str = "") -> None:
        prefix = prefix.rstrip("/")
        for route in router.routes:
            combined_path = f"{prefix}{route.path}" if route.path.startswith("/") else f"{prefix}/{route.path}"
            combined = _Route(
                combined_path or "/",
                endpoint=route.endpoint,
                methods=route.methods,
                response_model=route.response_model,
                status_code=route.status_code,
            )
            self.routes.append(combined)

    def get(self, path: str, *, response_model: Optional[type] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.router.get(path, response_model=response_model)

    def post(
        self,
        path: str,
        *,
        response_model: Optional[type] = None,
        status_code: Optional[int] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.router.post(path, response_model=response_model, status_code=status_code)

    async def handle_request(
        self,
        *,
        method: str,
        path: str,
        query_params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        form_data: Mapping[str, Any] | None = None,
        files: Mapping[str, Tuple[str, bytes, str]] | None = None,
    ) -> Tuple[int, Dict[str, str], bytes]:
        route = self._match_route(method, path)
        if route is None:
            return status.HTTP_404_NOT_FOUND, {"content-type": "application/json"}, json.dumps({"detail": "Not Found"}).encode("utf-8")

        try:
            body = await _execute_route(
                self,
                route,
                method=method,
                path=path,
                query_params=query_params or {},
                json_body=json_body,
                form_data=form_data or {},
                files=files or {},
            )
            status_code, headers, payload = body
            return status_code, headers, payload
        except HTTPException as exc:
            payload = json.dumps({"detail": exc.detail}).encode("utf-8")
            headers = {"content-type": "application/json"}
            return exc.status_code, headers, payload

    def _match_route(self, method: str, path: str) -> Optional[_Route]:
        candidates = self.routes + self.router.routes
        for route in candidates:
            if method.upper() not in route.methods:
                continue
            if route.match(path) is not None:
                return route
        return None


async def _execute_route(
    app: FastAPI,
    route: _Route,
    *,
    method: str,
    path: str,
    query_params: Mapping[str, Any],
    json_body: Any,
    form_data: Mapping[str, Any],
    files: Mapping[str, Tuple[str, bytes, str]],
) -> Tuple[int, Dict[str, str], bytes]:
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
            cleanup_callbacks,
        )
        result = route.endpoint(**arguments)
        if inspect.isawaitable(result):
            result = await result

        response = await _serialise_response(route, result)
        return response
    finally:
        await _run_cleanups(cleanup_callbacks)


async def _run_cleanups(callbacks: Iterable[Callable[[], Awaitable[None] | None]]) -> None:
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
    files: Mapping[str, Tuple[str, bytes, str]],
    cleanup_callbacks: list[Callable[[], Awaitable[None] | None]],
) -> Dict[str, Any]:
    signature = inspect.signature(endpoint)
    arguments: Dict[str, Any] = {}

    body_consumed = False
    for name, parameter in signature.parameters.items():
        annotation = _resolve_annotation(endpoint, name, parameter.annotation)
        default = parameter.default

        if name in path_params:
            arguments[name] = _coerce_type(path_params[name], annotation)
            continue

        if isinstance(default, Depends):
            dependency = app.dependency_overrides.get(default.dependency, default.dependency)
            resolved, cleanup = await _resolve_dependency(dependency)
            arguments[name] = resolved
            if cleanup is not None:
                cleanup_callbacks.append(cleanup)
            continue

        if isinstance(default, Query):
            if default.default is ...:
                if name not in query_params:
                    raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Missing query parameter {name}")
            value = query_params.get(name, default.default)
            arguments[name] = _coerce_type(value, annotation)
            continue

        if isinstance(default, Form):
            if default.default is ... and name not in form_data:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Missing form field {name}")
            value = form_data.get(name, default.default)
            arguments[name] = _coerce_type(value, annotation)
            continue

        if isinstance(default, File):
            if name not in files:
                if default.default is ...:
                    raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Missing file field {name}")
                arguments[name] = default.default
                continue
            filename, payload, content_type = files[name]
            arguments[name] = UploadFile(filename=filename, content_type=content_type, _data=payload)
            continue

        if json_body is not None and not body_consumed:
            if name == "payload" or (inspect.isclass(annotation) and hasattr(annotation, "model_validate")):
                arguments[name] = _coerce_type(json_body, annotation)
                body_consumed = True
                continue
            if annotation in {dict, Mapping, Any} and parameter.default is inspect._empty:
                arguments[name] = json_body
                body_consumed = True
                continue

        if parameter.default is not inspect._empty:
            arguments[name] = parameter.default
            continue

        if name in query_params:
            arguments[name] = _coerce_type(query_params[name], annotation)
            continue

        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unable to resolve parameter {name}")

    return arguments


async def _resolve_dependency(
    dependency: Callable[..., Any]
) -> Tuple[Any, Optional[Callable[[], Awaitable[None] | None]]]:
    result = dependency()
    if inspect.isawaitable(result):
        result = await result
    if inspect.isasyncgen(result):
        agen = result
        value = await agen.__anext__()

        async def _cleanup() -> None:
            try:
                await agen.__anext__()
            except StopAsyncIteration:
                pass
            await agen.aclose()

        return value, _cleanup
    if inspect.isgenerator(result):  # pragma: no cover - rarely used
        gen = result
        value = next(gen)

        def _cleanup_sync() -> None:
            try:
                next(gen)
            except StopIteration:
                pass

        return value, _cleanup_sync
    return result, None


@lru_cache(maxsize=None)
def _type_hints_for(endpoint: Callable[..., Any]) -> Dict[str, Any]:
    try:
        return get_type_hints(endpoint)
    except Exception:
        return {}


def _resolve_annotation(endpoint: Callable[..., Any], name: str, default: Any) -> Any:
    hints = _type_hints_for(endpoint)
    return hints.get(name, default)


def _coerce_type(value: Any, annotation: Any) -> Any:
    if annotation is inspect._empty or value is None:
        return value
    origin = get_origin(annotation)
    if origin is Union and value is not None:
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if args:
            return _coerce_type(value, args[0])
        return value
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


async def _serialise_response(route: _Route, result: Any) -> Tuple[int, Dict[str, str], bytes]:
    status_code = route.status_code or status.HTTP_200_OK
    headers: Dict[str, str] = {"content-type": "application/json"}

    if isinstance(result, Response):
        payload = await result.render()
        if result.media_type:
            headers["content-type"] = result.media_type
        headers.update(result.headers)
        return result.status_code, headers, payload

    if route.response_model is not None and not isinstance(result, route.response_model):
        if hasattr(route.response_model, "model_validate"):
            result = route.response_model.model_validate(result)

    if hasattr(result, "model_dump"):
        payload = json.dumps(result.model_dump(mode="json"), default=_json_default).encode("utf-8")
    elif isinstance(result, (dict, list)):
        payload = json.dumps(result, default=_json_default).encode("utf-8")
    elif result is None:
        payload = b""
    else:
        payload = str(result).encode("utf-8")

    return status_code, headers, payload


__all__ = [
    "APIRouter",
    "Depends",
    "FastAPI",
    "File",
    "Form",
    "HTTPException",
    "Query",
    "Response",
    "StreamingResponse",
    "UploadFile",
    "status",
]
