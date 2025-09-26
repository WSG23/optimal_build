"""Tests for jurisdiction metadata handling during ingestion."""

from __future__ import annotations

from core import canonical_models
from core.registry import load_jurisdiction
from scripts.ingest import ensure_jurisdiction
from core.util import create_session_factory, get_engine
from sqlalchemy import select


def test_ensure_jurisdiction_uses_display_name() -> None:
    """Ensure friendly parser names are persisted to the database."""

    registered = load_jurisdiction("sg_bca")
    engine = get_engine("sqlite:///:memory:")
    session_factory = create_session_factory(engine)
    canonical_models.RegstackBase.metadata.create_all(engine)

    session = session_factory()
    try:
        ensure_jurisdiction(session, registered.parser)
        stored = session.execute(
            select(canonical_models.JurisdictionORM)
            .where(canonical_models.JurisdictionORM.code == registered.parser.code)
        ).scalar_one()
    finally:
        if hasattr(session, "close"):
            session.close()

    assert stored.name == getattr(registered.parser, "display_name")
