"""Compliance service result formatting tests."""

from __future__ import annotations

from datetime import datetime
import importlib
import sys
from types import SimpleNamespace
from uuid import uuid4

from tests.helpers import ensure_sqlite_uuid, install_property_stub


def test_build_result_serialises_compliance_summary(monkeypatch):
    ensure_sqlite_uuid(monkeypatch)
    install_property_stub(monkeypatch)
    sys.modules.pop("backend.app.services.compliance", None)
    module = importlib.import_module("backend.app.services.compliance")
    record = SimpleNamespace(
        id=uuid4(),
        bca_compliance_status="passed",
        ura_compliance_status="warning",
        compliance_notes="Check exit widths",
        compliance_last_checked=datetime(2024, 5, 1),
        compliance_data={"issues": []},
        property_name="Tower",
        address="1 Example Way",
        zoning="commercial",
        planning_area="CBD",
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 5, 2),
    )

    result = module._build_result(record)  # type: ignore[attr-defined]

    assert result.response.compliance.ura_status == "warning"
    assert "issues" in result.response.compliance.data
