"""Unicode handling in compliance summaries."""

import importlib
import sys
from datetime import datetime

from tests.helpers import ensure_sqlite_uuid, install_property_stub


def test_unicode_fields_round_trip(monkeypatch):
    ensure_sqlite_uuid(monkeypatch)
    install_property_stub(monkeypatch)
    sys.modules.pop("app.schemas.property", None)
    module = importlib.import_module("app.schemas.property")

    summary = module.PropertyComplianceSummary(
        bca_status="合格",
        ura_status="注意",
        notes="テスト",
        last_checked=datetime(2024, 6, 1),
        data={"結果": "良好"},
    )

    payload = summary.model_dump()
    assert payload["bca_status"] == "合格"
    assert payload["data"]["結果"] == "良好"
