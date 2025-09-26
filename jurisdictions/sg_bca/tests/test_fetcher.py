import json
from datetime import date

import pytest

from jurisdictions.sg_bca import fetch
from jurisdictions.sg_bca.tests._helpers import (
    install_fixture_client,
    load_fixture,
    make_response,
)


def test_fetcher_collects_recent_provenance_records(monkeypatch):
    page_one = load_fixture("circulars_page1.json")
    page_two = load_fixture("circulars_page2.json")
    empty_page = {"result": {"records": [], "total": page_one["result"]["total"]}}
    call_log: list[dict[str, str]] = []

    install_fixture_client(
        monkeypatch,
        [
            make_response(page_one),
            make_response(page_two),
            make_response(empty_page),
        ],
        call_log=call_log,
    )

    config = fetch.FetchConfig(resource_id="fixture-resource", page_size=2, max_retries=1)
    fetcher = fetch.Fetcher(config=config)

    since = date(2024, 1, 1)
    records = fetcher.fetch_raw(since)

    assert len(records) == 2
    assert {record.regulation_external_id for record in records} == {
        "BCA-2025-001",
        "BCA-2025-002",
    }

    for record in records:
        assert record.fetch_parameters == {
            "since": since.isoformat(),
            "resource_id": "fixture-resource",
        }
        raw_row = json.loads(record.raw_content)
        assert raw_row["circular_no"] == record.regulation_external_id
        assert raw_row["weblink"] == record.source_uri

    offsets = [int(params.get("offset", 0)) for params in call_log]
    assert offsets == [0, 2]


def test_fetcher_raises_fetch_error_on_bad_credentials(monkeypatch):
    call_log: list[dict[str, str]] = []
    install_fixture_client(
        monkeypatch,
        [
            make_response({"success": False, "error": "Forbidden"}, status_code=403),
            make_response({"success": False, "error": "Forbidden"}, status_code=403),
        ],
        call_log=call_log,
    )
    config = fetch.FetchConfig(resource_id="fixture-resource", max_retries=2)
    fetcher = fetch.Fetcher(config=config)

    with pytest.raises(fetch.FetchError):
        fetcher.fetch_raw(date(2024, 1, 1))

    assert len(call_log) == 2


def test_fetcher_handles_malformed_payload_gracefully(monkeypatch):
    install_fixture_client(monkeypatch, [make_response({"message": "upstream schema changed"})])

    config = fetch.FetchConfig(resource_id="fixture-resource", max_retries=1)
    fetcher = fetch.Fetcher(config=config)

    records = fetcher.fetch_raw(date(2024, 1, 1))
    assert records == []
