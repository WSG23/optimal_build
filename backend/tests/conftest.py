"""Test configuration and shared fixtures."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Callable, Iterator
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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
