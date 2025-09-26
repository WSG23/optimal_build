from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Iterable, List

from core.canonical_models import ProvenanceRecord
from jurisdictions.sg_bca import fetch


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if not (200 <= self.status_code < 300):
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> dict:
        return json.loads(json.dumps(self._payload))


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def make_response(payload: dict, status_code: int = 200) -> FakeResponse:
    return FakeResponse(payload, status_code=status_code)


def install_fixture_client(
    monkeypatch, responses: Iterable[FakeResponse], call_log: List[dict[str, str]] | None = None
) -> None:
    responses_list = list(responses)

    class FixtureClient:
        def __init__(self, *args, **kwargs) -> None:
            self._responses = iter(responses_list.copy())

        def __enter__(self) -> "FixtureClient":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str, params: dict[str, object]):
            if call_log is not None:
                call_log.append({k: str(v) for k, v in params.items()})
            try:
                return next(self._responses)
            except StopIteration:
                return FakeResponse({"result": {"records": [], "total": 0}})

    monkeypatch.setattr(fetch, "httpx", type("HttpxModule", (), {"Client": FixtureClient}))


def fetch_records_from_fixtures(
    monkeypatch, *, since: date = date(2024, 1, 1)
) -> list[ProvenanceRecord]:
    page_one = load_fixture("circulars_page1.json")
    page_two = load_fixture("circulars_page2.json")
    empty_page = {"result": {"records": [], "total": page_one["result"]["total"]}}

    install_fixture_client(
        monkeypatch,
        [
            make_response(page_one),
            make_response(page_two),
            make_response(empty_page),
        ],
    )
    config = fetch.FetchConfig(resource_id="fixture-resource", page_size=2, max_retries=1)
    fetcher = fetch.Fetcher(config=config)
    return fetcher.fetch_raw(since)
