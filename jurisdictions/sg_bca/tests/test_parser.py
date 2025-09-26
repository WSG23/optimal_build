"""Tests for the SG BCA plug-in."""
from __future__ import annotations

import json
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import select

from core import canonical_models
from core.mapping import load_and_apply_mappings
from core.util import create_session_factory, get_engine, session_scope
from jurisdictions.sg_bca.parse import PARSER, ParserError


def test_parse_and_persist():
    engine = get_engine("sqlite:///:memory:")
    canonical_models.RegstackBase.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    since = date(2025, 1, 1)
    raw_records = list(PARSER.fetch_raw(since))
    regs = list(PARSER.parse(raw_records))

    assert len(regs) == 2

    fire = next(reg for reg in regs if reg.external_id == "sg-bca-2025-fire-safety")
    access = next(
        reg for reg in regs if reg.external_id == "sg-bca-2025-accessibility"
    )

    assert fire.title == "Fire Code 2025 Section 1.1 Smoke Detectors"
    assert fire.issued_on == date(2025, 1, 15)
    assert fire.effective_on == date(2025, 4, 1)
    assert fire.version == "2025 Edition"
    assert fire.metadata["division"] == "Fire Safety & Shelter Department"
    assert fire.metadata["source_uri"] == raw_records[0].source_uri
    assert fire.metadata["upstream_keywords"] == ["smoke detector", "residential"]
    assert fire.global_tags == ["fire_safety"]

    assert access.global_tags == ["accessibility"]

    mapped = load_and_apply_mappings(regs, PARSER.map_overrides_path())

    with session_scope(session_factory) as session:
        session.add(
            canonical_models.JurisdictionORM(code=PARSER.code, name="SG BCA")
        )
        _persist(session, mapped, raw_records)

    with session_scope(session_factory) as session:
        stored = session.execute(
            select(canonical_models.RegulationORM)
        ).scalars().all()

    assert len(stored) == 2
    tags_by_external = {row.external_id: row.global_tags for row in stored}
    assert tags_by_external["sg-bca-2025-fire-safety"] == ["fire_safety"]
    assert tags_by_external["sg-bca-2025-accessibility"] == ["accessibility"]


def _persist(
    session: Session,
    regs: list[canonical_models.CanonicalReg],
    raw_records: list[canonical_models.ProvenanceRecord],
) -> None:
    from scripts.ingest import upsert_regulations

    upsert_regulations(session, regs, raw_records)


def test_parse_missing_mandatory_field() -> None:
    payload = {"regulations": [{"external_id": "sg-bca-test", "body": "text"}]}
    record = canonical_models.ProvenanceRecord(
        regulation_external_id="batch",
        source_uri="https://example.gov.sg/bca/mock-regulation",
        fetched_at=datetime.now(UTC),
        fetch_parameters={},
        raw_content=json.dumps(payload),
    )

    with pytest.raises(ParserError) as excinfo:
        list(PARSER.parse([record]))

    assert "missing mandatory field 'title'" in str(excinfo.value)
