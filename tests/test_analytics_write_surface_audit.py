from __future__ import annotations

from backend.scripts.audit_analytics_write_surfaces import build_inventory


def test_analytics_write_surface_audit_reports_capture_coverage() -> None:
    inventory = build_inventory()
    summary = inventory["summary"]

    assert summary["write_calls"] > 0
    assert summary["capture_calls"] > 0
    assert (
        "backend/app/api/v1/events.py"
        not in inventory["write_files_without_capture_helpers"]
    )
    assert (
        "backend/app/api/v1/listings.py"
        not in inventory["write_files_without_capture_helpers"]
    )
    assert (
        "backend/app/api/v1/singapore_properties.py"
        not in inventory["write_files_without_capture_helpers"]
    )
