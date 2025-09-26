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


def test_ensure_jurisdiction_falls_back_to_uppercase_code() -> None:
    """Parsers without display names should fall back to uppercase codes."""

    class DummyParser:
        code = "xx"
        display_name = None

        def fetch_raw(self, since):  # pragma: no cover - not used in test
            raise NotImplementedError

        def parse(self, records):  # pragma: no cover - not used in test
            raise NotImplementedError

        def map_overrides_path(self):  # pragma: no cover - not used in test
            return None

    engine = get_engine("sqlite:///:memory:")
    session_factory = create_session_factory(engine)
    canonical_models.RegstackBase.metadata.create_all(engine)

    session = session_factory()
    try:
        ensure_jurisdiction(session, DummyParser())
        stored = session.execute(
            select(canonical_models.JurisdictionORM).where(
                canonical_models.JurisdictionORM.code == "xx"
            )
        ).scalar_one()
    finally:
        if hasattr(session, "close"):
            session.close()

    assert stored.name == "XX"


def test_ensure_jurisdiction_treats_none_display_name_as_missing() -> None:
    """Explicit ``None`` values should also trigger the uppercase fallback."""

    class DummyParser:
        code = "zz"

        def __init__(self) -> None:
            self.display_name = None

        def fetch_raw(self, since):  # pragma: no cover - not used in test
            raise NotImplementedError

        def parse(self, records):  # pragma: no cover - not used in test
            raise NotImplementedError

        def map_overrides_path(self):  # pragma: no cover - not used in test
            return None

    engine = get_engine("sqlite:///:memory:")
    session_factory = create_session_factory(engine)
    canonical_models.RegstackBase.metadata.create_all(engine)

    session = session_factory()
    try:
        ensure_jurisdiction(session, DummyParser())
        stored = session.execute(
            select(canonical_models.JurisdictionORM).where(
                canonical_models.JurisdictionORM.code == "zz"
            )
        ).scalar_one()
    finally:
        if hasattr(session, "close"):
            session.close()

    assert stored.name == "ZZ"


def test_ensure_jurisdiction_handles_missing_display_name_attribute() -> None:
    """Parsers that omit ``display_name`` should still be uppercased."""

    class DummyParser:
        code = "yy"

        def fetch_raw(self, since):  # pragma: no cover - not used in test
            raise NotImplementedError

        def parse(self, records):  # pragma: no cover - not used in test
            raise NotImplementedError

        def map_overrides_path(self):  # pragma: no cover - not used in test
            return None

    engine = get_engine("sqlite:///:memory:")
    session_factory = create_session_factory(engine)
    canonical_models.RegstackBase.metadata.create_all(engine)

    session = session_factory()
    try:
        ensure_jurisdiction(session, DummyParser())
        stored = session.execute(
            select(canonical_models.JurisdictionORM).where(
                canonical_models.JurisdictionORM.code == "yy"
            )
        ).scalar_one()
    finally:
        if hasattr(session, "close"):
            session.close()

    assert stored.name == "YY"
