"""Postgres-backed regression test to verify overlay payload consistency."""

from __future__ import annotations

import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator

import pytest
import sqlalchemy as sa
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from app.core.database import get_session
from app.models.base import BaseModel
from app.models.overlay import OverlaySuggestion, OverlaySourceGeometry

# Lazy import to avoid loading the full app during test collection
app = None

SCHEMA_NAME = "__ob_overlay_test__"


@pytest.fixture(scope="module")
def event_loop() -> asyncio.AbstractEventLoop:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def database_url(pytestconfig: pytest.Config) -> str:
    url = pytestconfig.getoption("db_url")
    if not url:
        pytest.skip(
            "Postgres-backed tests require --db-url. "
            "Example: PYTHONPATH=. pytest unit_tests/test_overlay_missing_metric.py "
            "--db-url=postgresql://user:pass@localhost/dbname"
        )
    return url


@asynccontextmanager
async def _postgres_engine(database_url: str) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(database_url, future=True, pool_pre_ping=True)

    async with engine.begin() as conn:
        await conn.execute(sa.text(f'DROP SCHEMA IF EXISTS "{SCHEMA_NAME}" CASCADE'))
        await conn.execute(sa.text(f'CREATE SCHEMA "{SCHEMA_NAME}"'))
        await conn.execute(sa.text(f'SET search_path TO "{SCHEMA_NAME}"'))
        await conn.run_sync(BaseModel.metadata.create_all)

    try:
        yield engine
    finally:
        async with engine.begin() as conn:
            await conn.execute(
                sa.text(f'DROP SCHEMA IF EXISTS "{SCHEMA_NAME}" CASCADE')
            )
        await engine.dispose()


@pytest.fixture(scope="module")
async def engine(database_url: str) -> AsyncIterator[AsyncEngine]:
    async with _postgres_engine(database_url) as eng:
        yield eng


@pytest.fixture(scope="module")
def session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture(scope="module")
async def app_client(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncClient]:
    # Import app here to avoid loading during collection
    from app.main import app as fastapi_app

    async def _override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    fastapi_app.dependency_overrides[get_session] = _override_get_session
    async with AsyncClient(app=fastapi_app, base_url="http://testserver") as client:
        yield client
    fastapi_app.dependency_overrides.pop(get_session, None)


@pytest.fixture()
async def session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        try:
            await session.execute(sa.text(f'SET search_path TO "{SCHEMA_NAME}"'))
            yield session
        finally:
            await session.execute(
                sa.text(
                    f'TRUNCATE TABLE "{SCHEMA_NAME}"."overlay_suggestions", '
                    f'"{SCHEMA_NAME}"."overlay_source_geometries" RESTART IDENTITY CASCADE'
                )
            )
            await session.commit()


@pytest.mark.asyncio
async def test_overlay_missing_metric_payload_consistency(
    app_client: AsyncClient, session: AsyncSession
) -> None:
    project_id = uuid.uuid4().int % 1_000_000

    source_a = OverlaySourceGeometry(
        project_id=project_id,
        source_geometry_key="source-a",
        graph={"levels": []},
        metadata={"zone_code": "SG:residential"},
        checksum="checksum-a",
    )
    source_b = OverlaySourceGeometry(
        project_id=project_id,
        source_geometry_key="source-b",
        graph={"levels": []},
        metadata={"zone_code": "SG:residential"},
        checksum="checksum-b",
    )
    session.add_all([source_a, source_b])
    await session.flush()

    missing_metric_payload = {
        "missing_metric": "front_setback_m",
        "parameter_key": "zoning.setback.front_min_m",
        "zone_code": "SG:residential",
    }
    props_payload = {
        "metric": "front_setback_m",
        "parameter_key": "zoning.setback.front_min_m",
        "zone_code": "SG:residential",
    }

    suggestion_a = OverlaySuggestion(
        project_id=project_id,
        source_geometry_id=source_a.id,
        code="rule_data_missing_front_setback_m",
        type="data",
        title="Provide front setback data",
        rationale="Input needed",
        severity="low",
        status="pending",
        engine_version="2024.1",
        engine_payload=missing_metric_payload,
        target_ids=[],
        props=props_payload,
        rule_refs=["zoning.setback.front_min_m"],
        score=None,
        geometry_checksum="checksum-a",
    )
    suggestion_b = OverlaySuggestion(
        project_id=project_id,
        source_geometry_id=source_b.id,
        code="rule_data_missing_front_setback_m",
        type="data",
        title="Provide front setback data",
        rationale="Input needed",
        severity="low",
        status="pending",
        engine_version="2024.1",
        engine_payload=missing_metric_payload,
        target_ids=[],
        props=props_payload,
        rule_refs=["zoning.setback.front_min_m"],
        score=None,
        geometry_checksum="checksum-b",
    )
    session.add_all([suggestion_a, suggestion_b])
    await session.commit()

    response = await app_client.get(f"/api/v1/overlay/{project_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2
    engine_payloads = [item["engine_payload"] for item in payload["items"]]
    props_payloads = [item["props"] for item in payload["items"]]
    assert all(ep.get("missing_metric") == "front_setback_m" for ep in engine_payloads)
    assert all(props.get("metric") == "front_setback_m" for props in props_payloads)
