"""Tests for the SG BCA fetcher, parser, and ingestion pipeline."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import select

from core import canonical_models
from core.util import create_session_factory, get_engine, session_scope
from jurisdictions.sg_bca.fetch import FetchConfig, Fetcher
from jurisdictions.sg_bca.parse import PARSER
from scripts.ingest import upsert_regulations

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _load_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


class _MockResponse:
    def __init__(self, body: str, status_code: int) -> None:
        self._body = body
        self.status_code = status_code

    def json(self) -> dict:
        return json.loads(self._body)


class _MockClient:
    def __init__(self, body: str, status_code: int = 200) -> None:
        self._body = body
        self._status_code = status_code
        self.last_request: dict | None = None

    def get(self, url: str, *, params=None, auth=None):
        assert url.endswith("/regulations")
        self.last_request = {"url": url, "params": params, "auth": auth}
        return _MockResponse(self._body, self._status_code)

    def close(self) -> None:
        return None


def _mock_client(body: str, status_code: int = 200) -> _MockClient:
    return _MockClient(body, status_code)


@pytest.fixture()
def successful_records() -> list:
    client = _mock_client(_load_fixture("regulations_success.json"))
    fetcher = Fetcher(config=FetchConfig(base_url="https://example.gov.sg"), client=client)
    return fetcher.fetch_raw(date(2024, 1, 1))


def test_fetcher_returns_provenance_records(successful_records):
    assert len(successful_records) == 2
    first = successful_records[0]
    payload = json.loads(first.raw_content)

    assert first.regulation_external_id == "BCA-CP83-4-2"
    assert first.fetch_parameters == {"updated_after": "2024-01-01"}
    assert first.source_uri == payload["detail_url"]
    assert payload["title"] == "Clause 4.2 Fire Alarm Systems"


def test_parser_creates_expected_canonical_regs(successful_records):
    regs = list(PARSER.parse(successful_records))

    assert [reg.external_id for reg in regs] == ["BCA-CP83-4-2", "BCA-CP83-5-1"]
    assert regs[0].title == "Clause 4.2 Fire Alarm Systems"
    assert "interconnected smoke detectors" in regs[0].text
    assert regs[0].issued_on.isoformat() == "2024-06-01"
    assert regs[0].effective_on.isoformat() == "2024-09-01"
    assert regs[0].metadata["section"] == "4.2"
    assert regs[0].global_tags == ["fire_safety", "smoke_detection"]
    assert regs[1].global_tags == ["fire_safety"]


def test_fetcher_bad_credentials():
    client = _mock_client(_load_fixture("unauthorized.json"), status_code=401)
    fetcher = Fetcher(config=FetchConfig(base_url="https://example.gov.sg"), client=client)

    with pytest.raises(PermissionError):
        fetcher.fetch_raw(date(2024, 1, 1))


def test_fetcher_malformed_payload():
    client = _mock_client(_load_fixture("malformed_payload.json"))
    fetcher = Fetcher(config=FetchConfig(base_url="https://example.gov.sg"), client=client)

    with pytest.raises(ValueError):
        fetcher.fetch_raw(date(2024, 1, 1))


def test_ingestion_dedupes_regulations_and_provenance(successful_records):
    duplicated_records = successful_records + successful_records
    regs = list(PARSER.parse(duplicated_records))

    engine = get_engine("sqlite:///:memory:")
    canonical_models.RegstackBase.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_scope(session_factory) as session:
        session.add(canonical_models.JurisdictionORM(code=PARSER.code, name="SG BCA"))
        upsert_regulations(session, regs, duplicated_records)

    with session_scope(session_factory) as session:
        reg_total = len(
            session.execute(select(canonical_models.RegulationORM)).scalars().all()
        )
        provenance_total = len(
            session.execute(select(canonical_models.ProvenanceORM)).scalars().all()
        )

    assert reg_total == len(successful_records)
    assert provenance_total == len(successful_records)
