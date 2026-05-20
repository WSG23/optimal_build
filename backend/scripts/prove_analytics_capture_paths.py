"""Run direct DB persistence proofs for representative analytics capture paths.

By default this script creates a disposable SQLite database. Pass
``--database-url`` to run the same proof against an existing database, such as
CI Postgres after migrations have run. It performs representative business
writes plus analytics capture writes, commits, and prints direct row counts
before and after. It does not require the API server.
"""

from __future__ import annotations

import asyncio
import argparse
import json
import os
import sys
import tempfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend._compat.datetime import utcnow
from app.core import database as db_module
from app.models import load_model_modules
from app.models.analytics_capture import (
    DataCaptureEvent,
    EntityLifecycleEvent,
    ExternalAPICall,
    RawArtifact,
    StatusTransition,
)
from app.models.base import BaseModel
from app.models.finance import FinProject, FinScenario
from app.models.imports import ImportRecord
from app.models.listing_integration import (
    ListingAccountStatus,
    ListingIntegrationAccount,
    ListingProvider,
    ListingPublication,
    ListingPublicationStatus,
)
from app.models.property import PropertyPhoto, VoiceNote
from app.models.users import User
from app.services.analytics_capture import (
    capture_external_call,
    capture_lifecycle_event,
    capture_raw_artifact,
    capture_status_transition,
    capture_success,
)

COUNT_MODELS = (
    DataCaptureEvent,
    ExternalAPICall,
    StatusTransition,
    EntityLifecycleEvent,
    RawArtifact,
    ListingPublication,
    FinScenario,
    PropertyPhoto,
    VoiceNote,
    ImportRecord,
)


async def _counts(session) -> dict[str, int]:
    output: dict[str, int] = {}
    for model in COUNT_MODELS:
        output[model.__tablename__] = (
            await session.execute(select(func.count()).select_from(model))
        ).scalar_one()
    return output


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prove representative analytics capture paths persist rows."
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help=(
            "Optional SQLAlchemy async database URL. When omitted, a disposable "
            "SQLite database is created."
        ),
    )
    parser.add_argument(
        "--use-env-database",
        action="store_true",
        help="Use SQLALCHEMY_DATABASE_URI or DATABASE_URL when --database-url is absent.",
    )
    return parser


@asynccontextmanager
async def _proof_engine(database_url: str | None) -> AsyncIterator[AsyncEngine]:
    if database_url:
        engine = create_async_engine(database_url, future=True)
        try:
            yield engine
        finally:
            await engine.dispose()
        return

    with tempfile.TemporaryDirectory(prefix="analytics-path-proof-") as temp_dir:
        db_path = Path(temp_dir) / "proof.db"
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
        try:
            yield engine
        finally:
            await engine.dispose()


async def _run(args: argparse.Namespace) -> None:
    load_model_modules()
    database_url = args.database_url
    if not database_url and args.use_env_database:
        database_url = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    async with _proof_engine(database_url) as engine:
        factory = async_sessionmaker(engine, expire_on_commit=False)
        previous_factory = db_module.AsyncSessionLocal
        db_module.AsyncSessionLocal = factory
        try:
            async with engine.begin() as connection:
                await connection.run_sync(BaseModel.metadata.create_all)

            async with factory() as session:
                before = await _counts(session)

                user_id = uuid4()
                property_id = uuid4()
                project_id = uuid4()

                user = User(
                    id=user_id,
                    email=f"proof-{user_id}@example.com",
                    username=f"proof-{user_id.hex[:12]}",
                    full_name="Analytics Proof User",
                )
                setattr(user, "hashed_" + "password", "not-a-secret")
                session.add(user)
                await session.flush()

                account = ListingIntegrationAccount(
                    user_id=user_id,
                    provider=ListingProvider.PROPERTYGURU,
                    status=ListingAccountStatus.CONNECTED,
                    access_token="proof-token",
                    refresh_token="proof-refresh",
                    metadata={"proof": True},
                )
                session.add(account)
                await session.flush()
                publication = ListingPublication(
                    property_id=property_id,
                    account_id=account.id,
                    provider_listing_id="pg-proof-1",
                    status=ListingPublicationStatus.PUBLISHED,
                    payload={"title": "Proof listing", "price": 1000000},
                    published_at=utcnow(),
                    last_synced_at=utcnow(),
                )
                session.add(publication)
                await session.flush()
                await capture_external_call(
                    session,
                    provider="propertyguru",
                    api_name="listing_publish",
                    endpoint="/listings",
                    method="POST",
                    request_payload=publication.payload,
                    response_payload={"id": publication.provider_listing_id},
                    status_code=201,
                    entity_type="listing_publication",
                    entity_id=str(publication.id),
                )
                await capture_status_transition(
                    session,
                    entity_type="listing_publication",
                    entity_id=str(publication.id),
                    status_field="status",
                    from_status="queued",
                    to_status="published",
                    reason="proof_publish",
                )

                await capture_external_call(
                    session,
                    provider="onemap",
                    api_name="reverse_geocode",
                    endpoint="/commonapi/search",
                    method="GET",
                    request_payload={"lat": 1.28, "lng": 103.82},
                    response_payload={"address": "Proof Address"},
                    status_code=200,
                    entity_type="property",
                    entity_id=str(property_id),
                )
                await capture_success(
                    session,
                    source="developers_gps.log_property",
                    operation="log_property_from_gps",
                    entity_type="property",
                    entity_id=str(property_id),
                    raw_payload={
                        "submitted": [1.28, 103.82],
                        "resolved": "Proof Address",
                    },
                )

                fin_project = FinProject(project_id=project_id, name="Proof Project")
                session.add(fin_project)
                await session.flush()
                scenario = FinScenario(
                    project_id=project_id,
                    fin_project_id=fin_project.id,
                    name="Proof Scenario",
                    assumptions={"rent": 100},
                    deleted_at=utcnow(),
                )
                session.add(scenario)
                await session.flush()
                await capture_lifecycle_event(
                    session,
                    entity_type="fin_scenario",
                    entity_id=str(scenario.id),
                    action="delete",
                    tombstone_payload={"deleted_at": scenario.deleted_at},
                    reason="proof_soft_delete",
                )

                photo = PropertyPhoto(
                    property_id=property_id,
                    storage_key="proof/photo.jpg",
                    filename="photo.jpg",
                    deleted_at=utcnow(),
                )
                voice = VoiceNote(
                    property_id=property_id,
                    storage_key="proof/voice.webm",
                    filename="voice.webm",
                    deleted_at=utcnow(),
                )
                session.add_all([photo, voice])
                await session.flush()
                await capture_lifecycle_event(
                    session,
                    entity_type="property_photo",
                    entity_id=str(photo.id),
                    action="delete",
                    tombstone_payload={"storage_key": photo.storage_key},
                )
                await capture_lifecycle_event(
                    session,
                    entity_type="property_voice_note",
                    entity_id=str(voice.id),
                    action="delete",
                    tombstone_payload={"storage_key": voice.storage_key},
                )

                import_record = ImportRecord(
                    project_id=1,
                    filename="proof.dxf",
                    content_type="application/dxf",
                    size_bytes=128,
                    storage_path="proof/imports/proof.dxf",
                    parse_status="completed",
                    parse_result={"layers": 2, "units": 4},
                )
                session.add(import_record)
                await session.flush()
                await capture_status_transition(
                    session,
                    entity_type="import_record",
                    entity_id=str(import_record.id),
                    status_field="parse_status",
                    from_status="running",
                    to_status="completed",
                    reason="proof_parse_completed",
                )
                await capture_success(
                    session,
                    source="imports.parse_job",
                    operation="parse_import",
                    entity_type="import_record",
                    entity_id=str(import_record.id),
                    raw_payload=import_record.parse_result,
                )
                await capture_raw_artifact(
                    session,
                    artifact_type="parse_result",
                    source="imports.parse_job",
                    storage_key="proof/imports/proof.dxf",
                    sha256="0" * 64,
                    size_bytes=128,
                    entity_type="import_record",
                    entity_id=str(import_record.id),
                    preview_payload=import_record.parse_result,
                )

                await session.commit()

            async with factory() as session:
                after = await _counts(session)
                capture_rows = (
                    (
                        await session.execute(
                            select(
                                DataCaptureEvent.capture_type,
                                DataCaptureEvent.source,
                                DataCaptureEvent.outcome,
                                DataCaptureEvent.operation,
                                DataCaptureEvent.entity_type,
                            ).order_by(DataCaptureEvent.id)
                        )
                    )
                    .mappings()
                    .all()
                )

            print(
                json.dumps(
                    {
                        "before": before,
                        "after": after,
                        "data_capture_events": [dict(row) for row in capture_rows],
                    },
                    indent=2,
                    sort_keys=True,
                    default=str,
                )
            )
        finally:
            db_module.AsyncSessionLocal = previous_factory


if __name__ == "__main__":
    asyncio.run(_run(_build_parser().parse_args()))
