"""Pytest fixtures for backend tests using a synchronous SQLite core."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Iterator
from dataclasses import dataclass
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import get_session
from app.main import app
from app.models import rkp  # noqa: F401  pylint: disable=unused-import
from app.models.base import Base
from app.utils import metrics


@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def sync_engine() -> Iterator[Engine]:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def sync_session_factory(sync_engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=sync_engine, expire_on_commit=False)


@dataclass
class AsyncSessionWrapper:
    """Lightweight asynchronous facade over a synchronous SQLAlchemy session."""

    sync_session: Session

    async def execute(self, statement: Any) -> Any:
        return self.sync_session.execute(statement)

    def add(self, instance: Any) -> None:
        self.sync_session.add(instance)

    def add_all(self, instances: Any) -> None:
        self.sync_session.add_all(instances)

    async def flush(self) -> None:
        self.sync_session.flush()

    async def commit(self) -> None:
        self.sync_session.commit()

    async def rollback(self) -> None:
        self.sync_session.rollback()

    async def close(self) -> None:
        self.sync_session.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self.sync_session, name)


class AsyncSessionContext:
    """Context manager that yields an AsyncSessionWrapper."""

    def __init__(self, sync_session_factory: sessionmaker[Session]) -> None:
        self._sync_session_factory = sync_session_factory
        self._wrapper: AsyncSessionWrapper | None = None

    async def __aenter__(self) -> AsyncSessionWrapper:
        sync_session = self._sync_session_factory()
        self._wrapper = AsyncSessionWrapper(sync_session)
        return self._wrapper

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        assert self._wrapper is not None
        if exc_type:
            self._wrapper.sync_session.rollback()
        else:
            self._wrapper.sync_session.commit()
        self._wrapper.sync_session.close()


@pytest.fixture(autouse=True)
def reset_metrics() -> Iterator[None]:
    metrics.reset_metrics()
    yield
    metrics.reset_metrics()


@pytest.fixture(autouse=True)
def override_session_dependency(sync_session_factory: sessionmaker[Session]) -> Iterator[None]:
    async def _get_session() -> AsyncGenerator[AsyncSessionWrapper, None]:
        sync_session = sync_session_factory()
        wrapper = AsyncSessionWrapper(sync_session)
        try:
            yield wrapper
            sync_session.commit()
        finally:
            sync_session.close()

    app.dependency_overrides[get_session] = _get_session
    yield
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture
async def session(sync_session_factory: sessionmaker[Session]) -> AsyncGenerator[AsyncSessionWrapper, None]:
    sync_session = sync_session_factory()
    wrapper = AsyncSessionWrapper(sync_session)
    try:
        yield wrapper
    finally:
        sync_session.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            sync_session.execute(table.delete())
        sync_session.commit()
        sync_session.close()


@pytest.fixture
def session_factory(sync_session_factory: sessionmaker[Session]) -> AsyncSessionContext:
    return lambda: AsyncSessionContext(sync_session_factory)


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://testserver") as http_client:
        yield http_client
