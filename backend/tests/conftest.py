"""Test fixtures for backend services and API routes."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable, Iterable
import os
from typing import Any, AsyncGenerator

import pytest
from httpx import AsyncClient
from sqlalchemy import delete, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SQLALCHEMY_DISABLE_JSONB", "true")

from app.core.database import get_session
from app.main import app
from app.models import Base


class AsyncSessionStub:
    """Lightweight async facade over a synchronous SQLAlchemy session."""

    def __init__(self, session: Session) -> None:
        self._sync_session = session
        self.bind = session.bind

    # Context manager protocol -------------------------------------------------
    async def __aenter__(self) -> "AsyncSessionStub":  # pragma: no cover - used indirectly
        return self

    async def __aexit__(
        self,
        exc_type,
        exc: BaseException | None,
        _tb,
    ) -> None:
        if exc:
            await self.rollback()
        await self.close()

    # Mutation helpers ---------------------------------------------------------
    def add(self, instance: Any) -> None:
        self._sync_session.add(instance)

    def add_all(self, instances: Iterable[Any]) -> None:
        self._sync_session.add_all(list(instances))

    async def flush(self) -> None:
        self._sync_session.flush()

    async def commit(self) -> None:
        self._sync_session.commit()

    async def rollback(self) -> None:
        self._sync_session.rollback()

    async def close(self) -> None:
        self._sync_session.close()

    async def delete(self, instance: Any) -> None:
        self._sync_session.delete(instance)

    # Query helpers -------------------------------------------------------------
    async def execute(self, statement, params: Any | None = None):  # type: ignore[override]
        if params is None:
            return self._sync_session.execute(statement)
        return self._sync_session.execute(statement, params)

    async def scalar(self, statement):
        result = await self.execute(statement)
        return result.scalar_one_or_none()

    async def scalars(self, statement):
        result = await self.execute(statement)
        return result.scalars()

    async def get(self, entity, ident):
        return self._sync_session.get(entity, ident)


@pytest.fixture(scope="session")
def event_loop() -> AsyncIterator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def sync_engine() -> Engine:
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="session")
def session_maker(sync_engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=sync_engine, expire_on_commit=False, future=True)


@pytest.fixture
async def session(
    session_maker: sessionmaker[Session],
    sync_engine: Engine,
) -> AsyncIterator[AsyncSessionStub]:
    sync_session = session_maker()
    async_session = AsyncSessionStub(sync_session)
    try:
        yield async_session
    finally:
        await async_session.rollback()
        await async_session.close()
        with sync_engine.begin() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                conn.execute(delete(table))


@pytest.fixture
def session_factory(session_maker: sessionmaker[Session]) -> Callable[[], AsyncSessionStub]:
    def factory() -> AsyncSessionStub:
        return AsyncSessionStub(session_maker())

    return factory


@pytest.fixture
async def client(session: AsyncSessionStub) -> AsyncIterator[AsyncClient]:
    async def _get_session_override() -> AsyncGenerator[AsyncSessionStub, None]:
        yield session

    app.dependency_overrides[get_session] = _get_session_override
    async with AsyncClient(app=app, base_url="http://testserver") as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)

