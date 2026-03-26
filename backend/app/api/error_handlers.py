"""Central API exception handlers."""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.utils.logging import get_logger, log_event
from app.utils.problem_details import problem_response

logger = get_logger(__name__)


def _extract_http_exception_detail(
    detail: Any,
) -> tuple[str, list[dict[str, Any]] | dict[str, Any] | None]:
    """Normalise FastAPI exception detail into a client-friendly payload."""

    if isinstance(detail, str):
        return detail, None
    if isinstance(detail, (list, dict)):
        return "Request failed", detail
    if detail is None:
        return "Request failed", None
    return str(detail), None


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Render application HTTP exceptions using a shared error schema."""

    detail, errors = _extract_http_exception_detail(exc.detail)
    return problem_response(
        request=request,
        status_code=exc.status_code,
        detail=detail,
        errors=errors,
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Render request validation failures as problem responses."""

    return problem_response(
        request=request,
        status_code=422,
        detail="Request validation failed",
        code="request_validation_failed",
        errors=exc.errors(),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Render unexpected errors using the shared problem schema."""

    log_event(
        logger,
        "unhandled_exception",
        client_host=request.client.host if request.client else "unknown",
        path=request.url.path,
        error=str(exc),
        error_type=type(exc).__name__,
        correlation_id=request.scope.get("correlation_id"),
    )
    return problem_response(
        request=request,
        status_code=500,
        detail="Internal server error",
        code="internal_server_error",
    )


__all__ = [
    "http_exception_handler",
    "unhandled_exception_handler",
    "validation_exception_handler",
]
