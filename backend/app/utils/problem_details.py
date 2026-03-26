"""Helpers for returning consistent RFC 7807-style API problem responses."""

from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


def _json_safe(value: Any) -> Any:
    """Convert nested payloads into JSON-serializable structures."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, BaseException):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return str(value)


def _default_title(status_code: int) -> str:
    """Return a human-readable title for the supplied HTTP status code."""

    try:
        return HTTPStatus(status_code).phrase
    except ValueError:
        return "Request failed"


def _normalise_code(code: str | None, status_code: int) -> str:
    """Return a stable machine-readable error code."""

    if code:
        return code
    try:
        status_name = HTTPStatus(status_code).name.lower()
    except ValueError:
        return "request_failed"
    return status_name


def _request_correlation_id(request: Request) -> str | None:
    """Return the correlation ID for the active request, if one exists."""

    scope_correlation_id = request.scope.get("correlation_id")
    if isinstance(scope_correlation_id, str) and scope_correlation_id.strip():
        return scope_correlation_id.strip()

    try:
        from app.middleware.request_guards import get_correlation_id
    except Exception:
        header_correlation_id = request.headers.get("X-Correlation-ID", "").strip()
        return header_correlation_id or None

    correlation_id_value = get_correlation_id()
    if isinstance(correlation_id_value, str):
        correlation_id = correlation_id_value.strip()
    else:
        correlation_id = str(correlation_id_value).strip()
    if correlation_id:
        return correlation_id
    header_correlation_id = request.headers.get("X-Correlation-ID", "").strip()
    return header_correlation_id or None


def build_problem_details(
    *,
    request: Request,
    status_code: int,
    detail: str,
    title: str | None = None,
    code: str | None = None,
    errors: list[dict[str, Any]] | dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a problem-details payload with trace context for clients."""

    payload: dict[str, Any] = {
        "type": "about:blank",
        "title": title or _default_title(status_code),
        "status": status_code,
        "detail": detail,
        "instance": request.url.path,
        "code": _normalise_code(code, status_code),
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    correlation_id = _request_correlation_id(request)
    if correlation_id is not None:
        payload["correlation_id"] = correlation_id
    if errors:
        payload["errors"] = _json_safe(errors)
    return payload


def problem_response(
    *,
    request: Request,
    status_code: int,
    detail: str,
    title: str | None = None,
    code: str | None = None,
    errors: list[dict[str, Any]] | dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Return a JSON response using the shared problem-details contract."""

    return JSONResponse(
        status_code=status_code,
        content=build_problem_details(
            request=request,
            status_code=status_code,
            detail=detail,
            title=title,
            code=code,
            errors=errors,
        ),
        headers=headers,
        media_type="application/problem+json",
    )


__all__ = ["build_problem_details", "problem_response"]
