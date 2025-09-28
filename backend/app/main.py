"""Main FastAPI application."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_viewer
from app.api.v1 import TAGS_METADATA, api_router
from app.core.config import settings
from app.core.database import engine, get_session
from app.middleware.security import SecurityHeadersMiddleware
from app.models.rkp import RefRule
from app.utils import metrics
from app.utils.logging import configure_logging, get_logger, log_event

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""

    log_event(logger, "app_starting", environment=settings.ENVIRONMENT)
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""

    metrics.REQUEST_COUNTER.labels(endpoint="root").inc()
    log_event(logger, "root_endpoint")
    return {
        "message": "Building Compliance Platform API",
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check(session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    """Health check endpoint with database connectivity."""

    metrics.REQUEST_COUNTER.labels(endpoint="health").inc()
    try:
        rules_count_result = await session.execute(
            select(func.count()).select_from(RefRule)
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

    metrics.REQUEST_COUNTER.labels(endpoint="test").inc()
    return {"message": "API is working", "version": settings.VERSION}


@app.get(f"{settings.API_V1_STR}/rules/count")
async def rules_count(
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> dict[str, Any]:
    """Get count of rules in database."""

    metrics.REQUEST_COUNTER.labels(endpoint="rules_count").inc()
    try:
        total_rules_result = await session.execute(
            select(func.count()).select_from(RefRule)
        )
        total_rules = int(total_rules_result.scalar_one() or 0)

        by_authority_result = await session.execute(
            select(RefRule.authority, func.count())
            .group_by(RefRule.authority)
            .order_by(RefRule.authority)
        )
        by_authority: dict[str, int] = {}
        for authority, count in by_authority_result.all():
            key = str(authority) if authority else "unknown"
            by_authority[key] = int(count or 0)

        sample_rule_result = await session.execute(
            select(RefRule.parameter_key, RefRule.value, RefRule.unit)
            .order_by(RefRule.id)
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

    metrics.REQUEST_COUNTER.labels(endpoint="database_status").inc()
    try:
        tables_result = await session.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        )
        tables = [row[0] for row in tables_result.fetchall()]

        rules_by_topic_result = await session.execute(
            select(RefRule.topic, func.count())
            .group_by(RefRule.topic)
            .order_by(RefRule.topic)
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
