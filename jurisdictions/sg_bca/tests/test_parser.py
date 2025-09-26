"""Tests for the SG BCA plug-in."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select

from core import canonical_models
from core.mapping import load_and_apply_mappings
from core.util import create_session_factory, get_engine, session_scope
from jurisdictions.sg_bca.parse import PARSER


def test_parse_and_persist():
    engine = get_engine("sqlite:///:memory:")
    canonical_models.RegstackBase.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    since = date(2025, 1, 1)
    raw_records = list(PARSER.fetch_raw(since))
    regs = list(PARSER.parse(raw_records))
    mapped = load_and_apply_mappings(regs, PARSER.map_overrides_path())

    with session_scope(session_factory) as session:
        session.add(
            canonical_models.JurisdictionORM(code=PARSER.code, name="SG BCA")
        )
        _persist(session, mapped, raw_records)

    with session_scope(session_factory) as session:
        stored = session.execute(
            select(canonical_models.RegulationORM).limit(1)
        ).scalar_one()
        count = len(
            session.execute(select(canonical_models.RegulationORM)).all()
        )

    assert count == 1
    assert stored.global_tags == ["fire_safety"]


def _persist(
    session: Session,
    regs: list[canonical_models.CanonicalReg],
    raw_records: list[canonical_models.ProvenanceRecord],
) -> None:
    from scripts.ingest import upsert_regulations

    upsert_regulations(session, regs, raw_records)
