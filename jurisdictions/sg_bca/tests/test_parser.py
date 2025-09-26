"""Tests for the SG BCA plug-in."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select

from core import canonical_models
from core.mapping import load_and_apply_mappings
from core.util import create_session_factory, get_engine, session_scope
from jurisdictions.sg_bca.parse import PARSER
from jurisdictions.sg_bca import fetch


def test_parse_and_persist(monkeypatch):
    engine = get_engine("sqlite:///:memory:")
    canonical_models.RegstackBase.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    since = date(2025, 1, 1)
    raw_records = list(_run_fetch(monkeypatch, since))
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


def _run_fetch(monkeypatch, since: date):
    sample_rows = [
        {
            "circular_no": "2025-01",
            "circular_date": "2025-02-02",
            "subject": "Smoke detector requirements",
            "weblink": "https://www1.bca.gov.sg/circulars/2025-01",
            "description": "Section 1.1 Fire Safety - A smoke detector must be installed.",
        },
        {
            "circular_no": "2024-10",
            "circular_date": "2024-12-15",
            "subject": "Legacy guidance",
            "weblink": "https://www1.bca.gov.sg/circulars/2024-10",
            "description": "Archived guidance",
        },
    ]

    total = len(sample_rows)

    class DummyResponse:
        def __init__(self, payload: dict) -> None:
            self._payload = payload

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return self._payload

    class DummyClient:
        def __init__(self, *_, **__):
            self.calls: list[dict[str, object]] = []

        def __enter__(self) -> "DummyClient":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str, params: dict[str, object]):
            self.calls.append(params)
            offset = int(params.get("offset", 0) or 0)
            limit = int(params.get("limit", 100) or 100)
            page = sample_rows[offset : offset + limit]
            return DummyResponse(
                {
                    "result": {
                        "records": page,
                        "total": total,
                    }
                }
            )

    test_config = fetch.FetchConfig(
        resource_id="test-resource",
        page_size=1,
    )

    class MockedFetcher(fetch.Fetcher):
        def __init__(self, config: fetch.FetchConfig | None = None) -> None:
            super().__init__(config=config or test_config)

    monkeypatch.setattr(fetch, "Fetcher", MockedFetcher)
    monkeypatch.setattr(fetch.httpx, "Client", DummyClient, raising=False)

    return PARSER.fetch_raw(since)
