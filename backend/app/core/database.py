"""Database configuration."""

from __future__ import annotations

import os
from importlib.util import find_spec
from pathlib import Path
from typing import AsyncGenerator

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
