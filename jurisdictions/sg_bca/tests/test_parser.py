import json
from datetime import timedelta

from sqlalchemy import select

from core import canonical_models
from core.mapping import load_and_apply_mappings
from core.util import create_session_factory, get_engine, session_scope
from jurisdictions.sg_bca.parse import PARSER
from jurisdictions.sg_bca.tests._helpers import fetch_records_from_fixtures


def test_parser_produces_expected_canonical_regs(monkeypatch):
    provenance_records = fetch_records_from_fixtures(monkeypatch)
    regulations = list(PARSER.parse(provenance_records))

    assert len(regulations) == 2
    assert {reg.external_id for reg in regulations} == {"BCA-2025-001", "BCA-2025-002"}

    for reg in regulations:
        assert reg.jurisdiction_code == PARSER.code
        assert reg.title == "Smoke detector requirements"
        raw_row = json.loads(
            next(
                record.raw_content
                for record in provenance_records
                if record.regulation_external_id == reg.external_id
            )
        )
        assert reg.metadata == {"source_uri": raw_row["weblink"]}
        assert reg.global_tags == ["fire_safety"]


def test_ingestion_upsert_deduplicates_provenance_entries(monkeypatch):
    provenance_records = fetch_records_from_fixtures(monkeypatch)
    regulations = load_and_apply_mappings(
        list(PARSER.parse(provenance_records)), PARSER.map_overrides_path()
    )

    engine = get_engine("sqlite:///:memory:")
    canonical_models.RegstackBase.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_scope(session_factory) as session:
        session.add(canonical_models.JurisdictionORM(code=PARSER.code, name="SG BCA"))
        from scripts.ingest import upsert_regulations

        upsert_regulations(session, regulations, provenance_records)

    with session_scope(session_factory) as session:
        regs = session.execute(select(canonical_models.RegulationORM)).scalars().all()
        provenance = session.execute(select(canonical_models.ProvenanceORM)).scalars().all()

    assert len(regs) == 2
    assert len(provenance) == 2

    later_records = [
        record.model_copy(update={"fetched_at": record.fetched_at + timedelta(hours=1)})
        for record in provenance_records
    ]
    later_regs = load_and_apply_mappings(
        list(PARSER.parse(later_records)), PARSER.map_overrides_path()
    )

    with session_scope(session_factory) as session:
        from scripts.ingest import upsert_regulations

        upsert_regulations(session, later_regs, later_records)

    with session_scope(session_factory) as session:
        regs = session.execute(select(canonical_models.RegulationORM)).scalars().all()
        provenance = session.execute(select(canonical_models.ProvenanceORM)).scalars().all()

    assert len(regs) == 2
    assert len(provenance) == 2
    fetched_at_values = {entry.fetched_at for entry in provenance}
    expected_times = {record.fetched_at for record in later_records}
    assert fetched_at_values == expected_times
