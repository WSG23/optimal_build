"""Main FastAPI application."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from threading import Lock
from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

try:  # pragma: no cover - prefer real slowapi when available
    from slowapi import Limiter
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    from slowapi.util import get_remote_address
except Exception:  # pragma: no cover - fallback for stubbed environments

    class RateLimitExceeded(RuntimeError):
        """Fallback exception used when slowapi is unavailable."""

        detail = "rate limit exceeded"

    class Limiter:
        """No-op limiter keeping API wiring intact during tests."""

        def __init__(self, *_: Any, **__: Any) -> None:
            pass

        def limit(self, *_: Any, **__: Any) -> Any:
            def decorator(func: Any) -> Any:
                return func

            return decorator

        def _inject_headers(self, response: Response, _rate_limit: Any) -> Response:
            return response

    class SlowAPIMiddleware:
        """Trivial middleware shim when slowapi is missing."""

        def __init__(self, app: Any, **_: Any) -> None:
            self.app = app

        async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
            await self.app(scope, receive, send)

    def get_remote_address(request: Request) -> str:
        client = getattr(request, "client", None)
        return getattr(client, "host", "127.0.0.1")


from app.api.deps import require_viewer
from app.api.error_handlers import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.api.v1 import TAGS_METADATA, build_api_router
from app.core.config import settings
from app.core.database import engine, get_session
from app.middleware.observability import (
    ApiErrorLoggingMiddleware,
    RequestMetricsMiddleware,
)
from app.middleware.request_guards import (
    CorrelationIdMiddleware,
    RequestSizeLimitMiddleware,
)
from app.middleware.security import SecurityHeadersMiddleware
from app.utils import metrics
from app.utils.logging import configure_logging, get_logger, log_event
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

configure_logging()
logger = get_logger(__name__)
_api_router_lock = Lock()
_api_router_loaded = False


@lru_cache(maxsize=1)
def _load_ref_rule_model() -> Any:
    """Import the RKP rule model only for endpoints that query it."""

    from app.models.rkp import RefRule

    return RefRule


@lru_cache(maxsize=1)
def _load_openapi_examples() -> dict[str, Any]:
    """Load heavyweight request/response examples only when generating OpenAPI."""

    from app.schemas.buildable import (
        BUILDABLE_REQUEST_EXAMPLE,
        BUILDABLE_RESPONSE_EXAMPLE,
    )
    from app.schemas.finance import (
        FINANCE_FEASIBILITY_REQUEST_EXAMPLE,
        FINANCE_FEASIBILITY_RESPONSE_EXAMPLE,
    )

    return {
        "buildable_request": BUILDABLE_REQUEST_EXAMPLE,
        "buildable_response": BUILDABLE_RESPONSE_EXAMPLE,
        "finance_request": FINANCE_FEASIBILITY_REQUEST_EXAMPLE,
        "finance_response": FINANCE_FEASIBILITY_RESPONSE_EXAMPLE,
    }


def _request_needs_api_router(path: str) -> bool:
    """Return whether the current path needs the API v1 router tree loaded."""

    if path == "/openapi.json":
        return True
    if path == "/docs" or path.startswith("/docs/"):
        return True
    if path == "/redoc" or path.startswith("/redoc/"):
        return True
    if path == settings.API_V1_STR:
        return True
    return path.startswith(f"{settings.API_V1_STR}/")


def _ensure_api_router_loaded() -> None:
    """Load and register the API v1 router once on first real use."""

    global _api_router_loaded

    if _api_router_loaded:
        return

    with _api_router_lock:
        if _api_router_loaded:
            return
        app.include_router(build_api_router(), prefix=settings.API_V1_STR)
        app.openapi_schema = None
        _api_router_loaded = True


class ApiRouterLoaderMiddleware:
    """Load API routes lazily so importing ``app.main`` stays cheap."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        path = str(scope.get("path", ""))
        if scope.get("type") in {"http", "websocket"} and _request_needs_api_router(
            path
        ):
            _ensure_api_router_loaded()
        await self.app(scope, receive, send)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""

    log_event(logger, "app_starting", environment=settings.ENVIRONMENT)

    # For SQLite dev mode, create all tables on startup
    if "sqlite" in str(engine.url):
        from app.models.base import BaseModel
        from app.models import load_model_modules

        load_model_modules()
        async with engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.create_all)
        log_event(logger, "sqlite_tables_created")

    try:
        yield
    finally:
        await engine.dispose()
        log_event(logger, "app_shutdown")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=TAGS_METADATA,
)

app.add_middleware(ApiRouterLoaderMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=500)
# CORS configuration - restrict headers in production
_ALLOWED_HEADERS = [
    "Authorization",
    "Content-Type",
    "Accept",
    "Origin",
    "X-Requested-With",
    "X-Role",  # Development role header
    "X-User-Id",  # Development user ID header
    "X-User-Email",  # Development email header
    "X-Correlation-ID",  # Request tracing
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=_ALLOWED_HEADERS,
)
app.add_middleware(ApiErrorLoggingMiddleware, logger=logger)
app.add_middleware(RequestMetricsMiddleware)
# Request size limit: 10 MB (DoS protection)
app.add_middleware(RequestSizeLimitMiddleware, max_size_bytes=10 * 1024 * 1024)
# Correlation ID for request tracing (outermost for full coverage)
app.add_middleware(CorrelationIdMiddleware)


def _build_rate_limiter() -> Limiter:
    """Construct the rate limiter using Redis storage when available."""

    try:
        limiter_instance = Limiter(
            key_func=get_remote_address,
            default_limits=[settings.API_RATE_LIMIT],
            storage_uri=settings.RATE_LIMIT_STORAGE_URI,
        )
        return limiter_instance
    except Exception as exc:  # pragma: no cover - fallback for misconfigured Redis
        log_event(
            logger,
            "rate_limiter_fallback_to_memory",
            storage_uri=settings.RATE_LIMIT_STORAGE_URI,
            error=str(exc),
        )
        return Limiter(
            key_func=get_remote_address,
            default_limits=[settings.API_RATE_LIMIT],
        )


limiter = _build_rate_limiter()
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return a standard response when clients exceed the configured rate limit."""

    log_event(
        logger,
        "rate_limit_exceeded",
        client_host=request.client.host if request.client else "unknown",
        path=request.url.path,
    )
    return await http_exception_handler(
        request,
        StarletteHTTPException(
            status_code=429,
            detail="Request rate limit exceeded. Please retry later.",
        ),
    )


app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

static_root = Path(__file__).resolve().parents[2] / "static"
if static_root.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(static_root), html=False),
        name="static",
    )


@app.get("/metrics", include_in_schema=False)
async def prometheus_metrics() -> Response:
    """Expose Prometheus metrics collected by the API."""

    payload = metrics.export_metrics()
    return Response(content=payload, media_type="text/plain; version=0.0.4")


def custom_openapi() -> dict[str, Any]:
    """Generate OpenAPI schema while injecting request/response examples."""

    _ensure_api_router_loaded()
    examples = _load_openapi_examples()

    if app.openapi_schema:
        schema = app.openapi_schema
    else:
        schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
            tags=TAGS_METADATA,
        )

    buildable_post = (
        schema.get("paths", {}).get("/api/v1/screen/buildable", {}).get("post", {})
    )

    request_content = (
        buildable_post.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
    )
    if isinstance(request_content, dict):
        request_content["example"] = examples["buildable_request"]

    response_content = (
        buildable_post.get("responses", {})
        .get("200", {})
        .get("content", {})
        .get("application/json", {})
    )
    if isinstance(response_content, dict):
        response_content["example"] = examples["buildable_response"]

    finance_post = (
        schema.get("paths", {}).get("/api/v1/finance/feasibility", {}).get("post", {})
    )
    finance_request = (
        finance_post.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
    )
    if isinstance(finance_request, dict):
        finance_request["example"] = examples["finance_request"]

    finance_response = (
        finance_post.get("responses", {})
        .get("200", {})
        .get("content", {})
        .get("application/json", {})
    )
    if isinstance(finance_response, dict):
        finance_response["example"] = examples["finance_response"]

    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi
app.openapi_schema = None


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""

    log_event(logger, "root_endpoint")
    return {
        "message": "Building Compliance Platform API",
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check(session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    """Health check endpoint with database connectivity."""

    ref_rule_model = _load_ref_rule_model()
    try:
        rules_count_result = await session.execute(
            select(func.count()).select_from(ref_rule_model)
        )
        rules_count = rules_count_result.scalar_one()
        payload = {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "database": "connected",
            "rules_count": int(rules_count or 0),
        }
        log_event(logger, "health_ok", rules_count=int(rules_count or 0))
        return payload
    except Exception as exc:  # pragma: no cover - defensive logging
        log_event(logger, "health_failed", error=str(exc))
        return {
            "status": "degraded",
            "service": settings.PROJECT_NAME,
            "database": "disconnected",
            "error": str(exc),
        }


@app.get("/health/metrics")
async def health_metrics() -> Response:
    """Expose Prometheus metrics."""

    metrics_output = metrics.render_latest_metrics()
    return Response(content=metrics_output, media_type="text/plain; version=0.0.4")


@app.get(f"{settings.API_V1_STR}/test")
async def test_endpoint(_: str = Depends(require_viewer)) -> dict[str, str]:
    """Test endpoint."""

    return {"message": "API is working", "version": settings.VERSION}


@app.get(f"{settings.API_V1_STR}/rules/count")
async def rules_count(
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> dict[str, Any]:
    """Get count of rules in database."""

    ref_rule_model = _load_ref_rule_model()
    try:
        total_rules_result = await session.execute(
            select(func.count()).select_from(ref_rule_model)
        )
        total_rules = int(total_rules_result.scalar_one() or 0)

        by_authority_result = await session.execute(
            select(ref_rule_model.authority, func.count())
            .group_by(ref_rule_model.authority)
            .order_by(ref_rule_model.authority)
        )
        by_authority: dict[str, int] = {}
        for authority, count in by_authority_result.all():
            key = str(authority) if authority else "unknown"
            by_authority[key] = int(count or 0)

        sample_rule_result = await session.execute(
            select(
                ref_rule_model.parameter_key,
                ref_rule_model.value,
                ref_rule_model.unit,
            )
            .order_by(ref_rule_model.id)
            .limit(1)
        )
        sample_rule = sample_rule_result.mappings().first()

        payload: dict[str, Any] = {
            "total_rules": total_rules,
            "by_authority": by_authority,
        }
        if sample_rule:
            payload["sample_rule"] = {
                "parameter_key": sample_rule["parameter_key"],
                "value": sample_rule["value"],
                "unit": sample_rule["unit"],
            }
        log_event(logger, "rules_count_report", total=total_rules)
        return payload
    except Exception as exc:  # pragma: no cover - defensive logging
        log_event(logger, "rules_count_failed", error=str(exc))
        return {"error": str(exc)}


@app.get(f"{settings.API_V1_STR}/database/status")
async def database_status(
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> dict[str, Any]:
    """Get database status and table information."""

    ref_rule_model = _load_ref_rule_model()
    try:
        tables_result = await session.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        )
        tables = [row[0] for row in tables_result.fetchall()]

        rules_by_topic_result = await session.execute(
            select(ref_rule_model.topic, func.count())
            .group_by(ref_rule_model.topic)
            .order_by(ref_rule_model.topic)
        )
        by_topic: dict[str, int] = {}
        total_rules = 0
        for topic, count in rules_by_topic_result.all():
            key = str(topic) if topic else "unknown"
            safe_count = int(count or 0)
            by_topic[key] = safe_count
            total_rules += safe_count

        payload = {
            "database_connected": True,
            "tables": sorted(tables),
            "rules_by_topic": by_topic,
            "total_rules": total_rules,
        }
        log_event(logger, "database_status_ok", table_count=len(tables))
        return payload
    except Exception as exc:  # pragma: no cover - defensive logging
        log_event(logger, "database_status_failed", error=str(exc))
        return {
            "database_connected": False,
            "error": str(exc),
        }


if __name__ == "__main__":  # pragma: no cover
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Application smoke test entry point.")
    parser.add_argument(
        "--dump-openapi",
        action="store_true",
        help="Output the generated OpenAPI schema and exit.",
    )
    args = parser.parse_args()

    if args.dump_openapi:
        schema = json.dumps(app.openapi(), indent=2, sort_keys=True)
        logger.info("openapi.schema", schema=schema)
    else:
        import uvicorn

        uvicorn.run(app, host="0.0.0.0", port=8000)
