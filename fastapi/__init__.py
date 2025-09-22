"""Minimal FastAPI stub used for offline API tests."""

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional, Tuple, Type, get_type_hints
from urllib.parse import parse_qs

from pydantic import BaseModel

from . import status
from .responses import Response

__all__ = [
    "FastAPI",
    "APIRouter",
    "Depends",
    "HTTPException",
    "Query",
    "File",
    "Form",
    "UploadFile",
    "status",
]


class HTTPException(Exception):
    """Exception raised to short-circuit request handling."""

    def __init__(self, status_code: int, detail: Any = None) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


@dataclass
class Depends:
    """Marker describing a dependency injection target."""

    dependency: Callable[..., Any]


class _ParameterInfo:
    def __init__(self, default: Any = None, **metadata: Any) -> None:
        self.default = default
        self.metadata = metadata


def Query(*args: Any, **kwargs: Any) -> _ParameterInfo:
    default = args[0] if args else kwargs.pop("default", None)
    return _ParameterInfo(default, **kwargs)


def Form(*args: Any, **kwargs: Any) -> _ParameterInfo:
    default = args[0] if args else kwargs.pop("default", None)
    return _ParameterInfo(default, **kwargs)


def File(*args: Any, **kwargs: Any) -> _ParameterInfo:
    default = args[0] if args else kwargs.pop("default", None)
    return _ParameterInfo(default, **kwargs)


class UploadFile:
    """Very small subset of :class:`fastapi.UploadFile`."""

    def __init__(self, filename: str | None = None, content_type: str | None = None, data: bytes | None = None) -> None:
        self.filename = filename
        self.content_type = content_type
        self._data = data or b""

    async def read(self) -> bytes:
        return self._data


class _Route:
    def __init__(
        self,
        path: str,
        methods: Iterable[str],
        endpoint: Callable[..., Any],
        default_status: int = 200,
    ) -> None:
        self.path = self._normalise_path(path)
        self.methods = {method.upper() for method in methods}
        self.endpoint = endpoint
        self.default_status = default_status
        self._parts, self._param_names = self._compile_path(self.path)

    @staticmethod
    def _normalise_path(path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        if len(path) > 1 and path.endswith("/"):
            path = path[:-1]
        return path

    @staticmethod
    def _compile_path(path: str) -> Tuple[List[Optional[str]], List[str]]:
        segments = [segment for segment in path.strip("/").split("/") if segment]
        parts: List[Optional[str]] = []
        params: List[str] = []
        for segment in segments:
            if segment.startswith("{") and segment.endswith("}"):
                params.append(segment[1:-1])
                parts.append(None)
            else:
                parts.append(segment)
        return parts, params

    def match(self, method: str, path: str) -> Optional[Dict[str, str]]:
        if method.upper() not in self.methods:
            return None
        path = self._normalise_path(path)
        if path == self.path:
            if not self._parts:
                return {}
        segments = [segment for segment in path.strip("/").split("/") if segment]
        if len(segments) != len(self._parts):
            return None
        params: Dict[str, str] = {}
        param_iter = iter(self._param_names)
        for expected, actual in zip(self._parts, segments):
            if expected is None:
                params[next(param_iter)] = actual
            elif expected != actual:
                return None
        return params

    def with_prefix(self, prefix: str) -> "_Route":
        new_path = _join_paths(prefix, self.path)
        return _Route(new_path, self.methods, self.endpoint, self.default_status)


def _join_paths(*parts: str) -> str:
    segments: List[str] = []
    for part in parts:
        if not part:
            continue
        if part.startswith("/"):
            part = part[1:]
        if part.endswith("/"):
            part = part[:-1]
        if part:
            segments.append(part)
    return "/" + "/".join(segments)


class APIRouter:
    """Router collecting routes before inclusion in an application."""

    def __init__(self, prefix: str = "", **_: Any) -> None:
        self.prefix = prefix
        self.routes: List[_Route] = []

    def add_api_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        methods: Iterable[str],
        status_code: int = 200,
    ) -> None:
        self.routes.append(_Route(_join_paths(self.prefix, path), methods, endpoint, status_code))

    def get(self, path: str, *, status_code: int = 200, **_: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._wrap(path, ["GET"], status_code)

    def post(self, path: str, *, status_code: int = 200, **_: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._wrap(path, ["POST"], status_code)

    def _wrap(
        self, path: str, methods: Iterable[str], status_code: int
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.add_api_route(path, func, methods=methods, status_code=status_code)
            return func

        return decorator

    def include_router(self, router: "APIRouter", prefix: str = "") -> None:
        for route in router.routes:
            combined = _join_paths(prefix, route.path)
            self.routes.append(_Route(combined, route.methods, route.endpoint, route.default_status))


class FastAPI:
    """Extremely small subset of :class:`fastapi.FastAPI`."""

    def __init__(self, *_, **__) -> None:
        self._routes: List[_Route] = []
        self.dependency_overrides: Dict[Callable[..., Any], Callable[..., Any]] = {}
        self.middleware: List[Tuple[Type[Any], Dict[str, Any]]] = []

    def add_middleware(self, middleware_class: Type[Any], **options: Any) -> None:
        self.middleware.append((middleware_class, options))

    def include_router(self, router: APIRouter, prefix: str = "") -> None:
        for route in router.routes:
            combined = _join_paths(prefix, route.path)
            self._routes.append(_Route(combined, route.methods, route.endpoint))

    def route(
        self,
        path: str,
        *,
        methods: Iterable[str],
        status_code: int = 200,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._routes.append(_Route(path, methods, func, status_code))
            return func

        return decorator

    def get(self, path: str, *, status_code: int = 200, **_: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.route(path, methods=["GET"], status_code=status_code)

    def post(self, path: str, *, status_code: int = 200, **_: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.route(path, methods=["POST"], status_code=status_code)

    async def __call__(self, scope: Dict[str, Any], receive: Callable[[], Awaitable[Dict[str, Any]]], send: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        if scope.get("type") != "http":
            raise RuntimeError("FastAPI stub only supports HTTP scopes")
        method = scope.get("method", "GET")
        path = scope.get("path", "/")
        route, params = self._find_route(method, path)
        if route is None:
            await _send_response(send, status_code=404, body=json.dumps({"detail": "Not Found"}).encode("utf-8"))
            return
        body_bytes = await _receive_body(receive)
        query_params = {key: values[0] for key, values in parse_qs(scope.get("query_string", b"").decode("utf-8")).items() if values}
        try:
            status_code, payload, headers = await self._execute(
                route.endpoint, route.default_status, params, query_params, body_bytes
            )
        except HTTPException as exc:
            payload = {"detail": exc.detail}
            await _send_response(send, status_code=exc.status_code, body=json.dumps(payload).encode("utf-8"))
            return
        await _send_response(send, status_code=status_code, body=payload, headers=headers)

    def _find_route(self, method: str, path: str) -> Tuple[Optional[_Route], Dict[str, str]]:
        for route in self._routes:
            match = route.match(method, path)
            if match is not None:
                return route, match
        return None, {}

    async def _execute(
        self,
        endpoint: Callable[..., Any],
        default_status: int,
        path_params: Dict[str, str],
        query_params: Dict[str, str],
        body: bytes,
    ) -> Tuple[int, bytes, List[Tuple[str, str]]]:
        cleanup_callbacks: List[Callable[[], Awaitable[None]]] = []
        try:
            kwargs = await self._resolve_parameters(endpoint, path_params, query_params, body, cleanup_callbacks)
            result = endpoint(**kwargs)
            if inspect.isawaitable(result):
                result = await result
            if isinstance(result, Response):
                return result.status_code, result.body, [("content-type", result.media_type)]
            payload = json.dumps(result).encode("utf-8") if result is not None else b""
            return default_status, payload, [("content-type", "application/json")]
        finally:
            for cleanup in cleanup_callbacks:
                await cleanup()

    async def _resolve_parameters(
        self,
        endpoint: Callable[..., Any],
        path_params: Dict[str, str],
        query_params: Dict[str, str],
        body: bytes,
        cleanup_callbacks: List[Callable[[], Awaitable[None]]],
    ) -> Dict[str, Any]:
        signature = inspect.signature(endpoint)
        body_data: Any = None
        if body:
            try:
                body_data = json.loads(body.decode("utf-8"))
            except json.JSONDecodeError:
                body_data = None
        kwargs: Dict[str, Any] = {}
        type_hints = get_type_hints(endpoint)
        for name, parameter in signature.parameters.items():
            annotation = type_hints.get(name, parameter.annotation)
            if isinstance(parameter.default, Depends):
                value, cleanup = await self._resolve_dependency(parameter.default.dependency)
                kwargs[name] = value
                if cleanup is not None:
                    cleanup_callbacks.append(cleanup)
            elif name in path_params:
                kwargs[name] = _convert_type(path_params[name], annotation)
            elif isinstance(parameter.default, _ParameterInfo):
                kwargs[name] = _convert_type(query_params.get(name, parameter.default.default), annotation)
            elif inspect.isclass(annotation) and issubclass(annotation, BaseModel):
                payload = body_data if isinstance(body_data, dict) else {}
                kwargs[name] = annotation(**payload)
            elif parameter.default is not inspect._empty:
                kwargs[name] = parameter.default
            else:
                kwargs[name] = None
        return kwargs

    async def _resolve_dependency(
        self, dependency: Callable[..., Any]
    ) -> Tuple[Any, Optional[Callable[[], Awaitable[None]]]]:
        override = self.dependency_overrides.get(dependency, dependency)
        if inspect.isasyncgenfunction(override):
            generator = override()
            value = await generator.__anext__()
            async def cleanup() -> None:
                await generator.aclose()
            return value, cleanup
        result = override()
        if inspect.isasyncgen(result):
            generator = result
            value = await generator.__anext__()
            async def cleanup() -> None:
                await generator.aclose()
            return value, cleanup
        if inspect.isawaitable(result):
            value = await result
            return value, None
        return result, None


async def _receive_body(receive: Callable[[], Awaitable[Dict[str, Any]]]) -> bytes:
    chunks: List[bytes] = []
    while True:
        message = await receive()
        if message.get("type") != "http.request":
            break
        chunks.append(message.get("body", b""))
        if not message.get("more_body"):
            break
    return b"".join(chunks)


async def _send_response(
    send: Callable[[Dict[str, Any]], Awaitable[None]],
    *,
    status_code: int,
    body: bytes,
    headers: Optional[List[Tuple[str, str]]] = None,
) -> None:
    header_list = [(b"content-length", str(len(body)).encode("utf-8"))]
    if headers:
        header_list.extend((name.encode("utf-8"), value.encode("utf-8")) for name, value in headers)
    await send({"type": "http.response.start", "status": status_code, "headers": header_list})
    await send({"type": "http.response.body", "body": body, "more_body": False})


def _convert_type(value: Any, annotation: Any) -> Any:
    if value is None or annotation in (inspect._empty, Any):
        return value
    try:
        if annotation is int:
            return int(value)
        if annotation is float:
            return float(value)
        if annotation is bool:
            return bool(value)
    except (TypeError, ValueError):
        return value
    return value


__all__.append("status")
