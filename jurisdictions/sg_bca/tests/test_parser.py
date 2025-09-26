"""Tests for the SG BCA fetcher and parser."""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pytest
from sqlalchemy import select

from core import canonical_models
from core.mapping import load_and_apply_mappings
from core.util import create_session_factory, get_engine, session_scope
from jurisdictions.sg_bca import fetch
from jurisdictions.sg_bca.parse import PARSER, ParserError


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_fetcher_and_parser_against_recorded_fixtures(monkeypatch):
    since = date(2025, 1, 1)
    fixture_fetcher = _build_fixture_fetcher(monkeypatch)

    raw_records = fixture_fetcher.fetch_raw(since)

    assert [record.regulation_external_id for record in raw_records] == [
        "2025-04",
        "2025-03",
    ]
    assert all("resource_id" in record.fetch_parameters for record in raw_records)
    assert all(record.fetch_parameters["since"] == since.isoformat() for record in raw_records)

    first_payload = json.loads(raw_records[0].raw_content)
    assert first_payload["subject"] == "Revisions to accessible fire exits"

    canonical_regs = list(PARSER.parse(raw_records))
    assert [reg.external_id for reg in canonical_regs] == ["2025-04", "2025-03"]

    first = canonical_regs[0]
    assert first.title == "Revisions to accessible fire exits"
    assert first.text.startswith("Section 1.1 Fire Safety")
    assert first.issued_on == date(2025, 4, 10)
    assert first.effective_on == date(2025, 5, 1)
    assert first.metadata["source_uri"] == "https://www1.bca.gov.sg/circulars/2025-04"
    assert first.metadata["agency"] == "Building and Construction Authority"
    assert first.global_tags == ["accessibility", "fire_safety"]

    second = canonical_regs[1]
    assert second.title == "Updated inspection regime for mechanical ventilation"
    assert second.effective_on == date(2025, 3, 20)
    assert second.metadata["document_type"] == "Circular"
    assert second.metadata["source_uri"] == "https://www1.bca.gov.sg/circulars/2025-03"
    assert second.global_tags == ["fire_safety"]


def test_fetcher_raises_for_bad_credentials(monkeypatch):
    class UnauthorizedResponse:
        status_code = 401

        def raise_for_status(self) -> None:
            raise RuntimeError("HTTP 401")

        def json(self) -> dict:
            return {"success": False, "error": {"message": "Invalid API key"}}

    class UnauthorizedClient:
        def __init__(self, *_, **__):
            pass

        def __enter__(self) -> "UnauthorizedClient":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str, params: dict[str, object]):
            return UnauthorizedResponse()

    monkeypatch.setattr(fetch.httpx, "Client", UnauthorizedClient, raising=False)
    config = fetch.FetchConfig(
        resource_id="realistic-resource-id",
        max_retries=2,
        backoff_factor=0.0,
    )
    fixture_fetcher = fetch.Fetcher(config=config)

    with pytest.raises(fetch.FetchError) as excinfo:
        fixture_fetcher.fetch_raw(date(2025, 1, 1))

    assert "Failed to fetch" in str(excinfo.value)


def test_fetcher_rejects_malformed_payload(monkeypatch):
    class MalformedResponse:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"result": {"records": "not-a-list"}}

    class MalformedClient:
        def __init__(self, *_, **__):
            pass

        def __enter__(self) -> "MalformedClient":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str, params: dict[str, object]):
            return MalformedResponse()

    monkeypatch.setattr(fetch.httpx, "Client", MalformedClient, raising=False)
    config = fetch.FetchConfig(
        resource_id="realistic-resource-id",
        max_retries=1,
        backoff_factor=0.0,
    )

    fixture_fetcher = fetch.Fetcher(config=config)

    with pytest.raises(fetch.FetchError) as excinfo:
        fixture_fetcher.fetch_raw(date(2025, 1, 1))

    assert "json object" in str(excinfo.value).lower()


def test_ingestion_deduplicates_provenance_entries(monkeypatch):
    engine = get_engine("sqlite:///:memory:")
    canonical_models.RegstackBase.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    since = date(2025, 1, 1)

    first_fetcher = _build_fixture_fetcher(monkeypatch)
    first_records = first_fetcher.fetch_raw(since)
    first_regs = list(PARSER.parse(first_records))
    mapped_first = load_and_apply_mappings(first_regs, PARSER.map_overrides_path())

    with session_scope(session_factory) as session:
        session.add(canonical_models.JurisdictionORM(code=PARSER.code, name="SG BCA"))
        _persist(session, mapped_first, first_records)

    with session_scope(session_factory) as session:
        regs_in_db = session.execute(select(canonical_models.RegulationORM)).scalars().all()
        provenance_in_db = session.execute(
            select(canonical_models.ProvenanceORM)
        ).scalars().all()

    assert len(regs_in_db) == 2
    assert len(provenance_in_db) == 2

    second_fetcher = _build_fixture_fetcher(monkeypatch)
    second_records = second_fetcher.fetch_raw(since)
    second_regs = list(PARSER.parse(second_records))
    mapped_second = load_and_apply_mappings(second_regs, PARSER.map_overrides_path())

    with session_scope(session_factory) as session:
        _persist(session, mapped_second, second_records)

    with session_scope(session_factory) as session:
        regs_after_second = session.execute(
            select(canonical_models.RegulationORM)
        ).scalars().all()
        provenance_after_second = session.execute(
            select(canonical_models.ProvenanceORM)
        ).scalars().all()

    assert len(regs_after_second) == 2
    assert len(provenance_after_second) == 2


def test_ingestion_persists_multiple_sources_for_single_regulation():
    engine = get_engine("sqlite:///:memory:")
    canonical_models.RegstackBase.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    regulation = canonical_models.CanonicalReg(
        jurisdiction_code=PARSER.code,
        external_id="multi-source-reg", 
        title="Test regulation with multiple provenance sources",
        text="Example content",
        issued_on=date(2025, 1, 1),
        effective_on=date(2025, 1, 2),
        metadata={},
        global_tags=["example"],
    )

    provenance_records = [
        canonical_models.ProvenanceRecord(
            regulation_external_id="multi-source-reg",
            source_uri="https://example.invalid/source-a",
            fetched_at=datetime(2025, 1, 10, 12, 0, 0),
            fetch_parameters={"page": 1},
            raw_content=json.dumps({"id": "source-a", "payload": "first"}),
        ),
        canonical_models.ProvenanceRecord(
            regulation_external_id="multi-source-reg",
            source_uri="https://example.invalid/source-b",
            fetched_at=datetime(2025, 1, 11, 12, 0, 0),
            fetch_parameters={"page": 2},
            raw_content=json.dumps({"id": "source-b", "payload": "second"}),
        ),
    ]

    with session_scope(session_factory) as session:
        session.add(canonical_models.JurisdictionORM(code=PARSER.code, name="SG BCA"))
        _persist(session, [regulation], provenance_records)

    with session_scope(session_factory) as session:
        regulations_in_db = session.execute(
            select(canonical_models.RegulationORM).where(
                canonical_models.RegulationORM.external_id == "multi-source-reg"
            )
        ).scalars().all()
        assert len(regulations_in_db) == 1

        provenance_in_db = session.execute(
            select(canonical_models.ProvenanceORM).where(
                canonical_models.ProvenanceORM.regulation_id
                == regulations_in_db[0].id
            )
        ).scalars().all()

    assert len(provenance_in_db) == 2
    assert {
        provenance.source_uri for provenance in provenance_in_db
    } == {
        "https://example.invalid/source-a",
        "https://example.invalid/source-b",
    }


def test_ingestion_deduplicates_identical_provenance_records():
    engine = get_engine("sqlite:///:memory:")
    canonical_models.RegstackBase.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    regulation = canonical_models.CanonicalReg(
        jurisdiction_code=PARSER.code,
        external_id="dedupe-provenance-reg",
        title="Regulation with duplicated provenance",
        text="Example content",
        issued_on=date(2025, 1, 3),
        effective_on=date(2025, 1, 4),
        metadata={},
        global_tags=["example"],
    )

    duplicate_payload = {"id": "source-a", "payload": "first"}
    provenance_records = [
        canonical_models.ProvenanceRecord(
            regulation_external_id="dedupe-provenance-reg",
            source_uri="https://example.invalid/source-a",
            fetched_at=datetime(2025, 1, 10, 12, 0, 0),
            fetch_parameters={"page": 1},
            raw_content=json.dumps(duplicate_payload),
        ),
        canonical_models.ProvenanceRecord(
            regulation_external_id="dedupe-provenance-reg",
            source_uri="https://example.invalid/source-a",
            fetched_at=datetime(2025, 1, 10, 12, 30, 0),
            fetch_parameters={"page": 1},
            raw_content=json.dumps(duplicate_payload),
        ),
    ]

    with session_scope(session_factory) as session:
        session.add(canonical_models.JurisdictionORM(code=PARSER.code, name="SG BCA"))
        _persist(session, [regulation], provenance_records)

    with session_scope(session_factory) as session:
        regulation_in_db = session.execute(
            select(canonical_models.RegulationORM).where(
                canonical_models.RegulationORM.external_id
                == "dedupe-provenance-reg"
            )
        ).scalar_one()

        provenance_in_db = session.execute(
            select(canonical_models.ProvenanceORM).where(
                canonical_models.ProvenanceORM.regulation_id == regulation_in_db.id
            )
        ).scalars().all()

    assert len(provenance_in_db) == 1
    assert provenance_in_db[0].source_uri == "https://example.invalid/source-a"


def test_parse_missing_title_raises():
    record = canonical_models.ProvenanceRecord(
        regulation_external_id="missing-title",
        source_uri="https://example.invalid/record",
        fetched_at=datetime(2025, 1, 1, 0, 0, 0),
        fetch_parameters={},
        raw_content=json.dumps({"description": "Content without a title."}),
    )

    with pytest.raises(ParserError) as excinfo:
        list(PARSER.parse([record]))

    assert "missing a title" in str(excinfo.value)
    assert "missing-title" in str(excinfo.value)


def _persist(
    session,
    regs: list[canonical_models.CanonicalReg],
    raw_records: list[canonical_models.ProvenanceRecord],
) -> None:
    from scripts.ingest import upsert_regulations

    upsert_regulations(session, regs, raw_records)


def _build_fixture_fetcher(monkeypatch) -> fetch.Fetcher:
    _patch_client_with_pages(
        monkeypatch,
        {
            0: "datastore_page_1.json",
            2: "datastore_page_2.json",
        },
    )
    config = fetch.FetchConfig(
        resource_id="realistic-resource-id",
        page_size=2,
        max_retries=1,
        backoff_factor=0.0,
    )
    return fetch.Fetcher(config=config)


def _patch_client_with_pages(
    monkeypatch: pytest.MonkeyPatch, fixtures_by_offset: dict[int, str]
) -> None:
    payloads = {
        offset: _load_fixture(filename)
        for offset, filename in fixtures_by_offset.items()
    }
    default_payload = {"result": {"records": []}}
    first_payload = next(iter(payloads.values()), None)
    if first_payload is not None:
        total = first_payload.get("result", {}).get("total")
        if total is not None:
            default_payload["result"]["total"] = total

    class FixtureResponse:
        def __init__(self, payload: dict, status_code: int = 200) -> None:
            self._payload = payload
            self.status_code = status_code

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise RuntimeError(f"HTTP {self.status_code}")

        def json(self) -> dict:
            return self._payload

    class FixtureClient:
        def __init__(self, *_, **__):
            pass

        def __enter__(self) -> "FixtureClient":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str, params: dict[str, object]):
            offset_raw = params.get("offset", 0)
            try:
                offset = int(offset_raw) if offset_raw is not None else 0
            except (TypeError, ValueError):
                offset = 0
            payload = payloads.get(offset, default_payload)
            return FixtureResponse(payload)

    monkeypatch.setattr(fetch.httpx, "Client", FixtureClient, raising=False)


def _load_fixture(name: str) -> dict:
    fixture_path = FIXTURES_DIR / name
    with fixture_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
