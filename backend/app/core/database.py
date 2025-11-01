"""Database configuration."""

from __future__ import annotations

import logging
import os
import time
from collections.abc import AsyncGenerator
from importlib.util import find_spec
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


def _sqlite_fallback_url() -> str:
    env_override = os.environ.get("DEV_SQLITE_URL")
    if env_override:
        return env_override
    repo_root = Path(__file__).resolve().parents[4]
    return f"sqlite+aiosqlite:///{repo_root / '.devstack' / 'app.db'}"


def _resolve_database_url() -> str:
    url = settings.SQLALCHEMY_DATABASE_URI
    if url.startswith("postgresql+asyncpg") and find_spec("asyncpg") is None:
        return _sqlite_fallback_url()
    return url


engine: AsyncEngine = create_async_engine(
    _resolve_database_url(),
    echo=True,
    future=True,
)

logger = logging.getLogger("app.database")
_SLOW_QUERY_THRESHOLD = settings.SLOW_QUERY_THRESHOLD_SECONDS

if _SLOW_QUERY_THRESHOLD > 0:

    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def _before_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ) -> None:
        context._query_start_time = time.perf_counter()

    @event.listens_for(engine.sync_engine, "after_cursor_execute")
    def _after_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ) -> None:
        start_time = getattr(context, "_query_start_time", None)
        if start_time is None:
            return
        elapsed = time.perf_counter() - start_time
        if elapsed >= _SLOW_QUERY_THRESHOLD:
            truncated = statement if len(statement) <= 500 else statement[:500] + "..."
            params_repr = repr(parameters)
            if len(params_repr) > 500:
                params_repr = params_repr[:500] + "..."
            logger.warning(
                "Slow query detected (%.2f ms): %s | params=%s",
                elapsed * 1000,
                truncated,
                params_repr,
            )


# Create session factory
AsyncSessionLocal = async_sessionmaker[AsyncSession](
    bind=engine,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""

    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
