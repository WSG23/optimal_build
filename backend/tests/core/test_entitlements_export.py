from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.export import entitlements as export_module


class _Page:
    def __init__(self, items):
        self.items = items
        self.total = len(items)


class _SessionStub:
    pass


@pytest.mark.asyncio
async def test_build_snapshot_and_generate_export(monkeypatch):
    roadmap_item = SimpleNamespace(
        sequence_order=1,
        status=SimpleNamespace(value="planned"),
        approval_type_id=10,
        target_submission_date=None,
        target_decision_date=None,
        actual_submission_date=None,
        actual_decision_date=None,
        notes="First step",
    )
    study = SimpleNamespace(
        name="Traffic",
        study_type=SimpleNamespace(value="traffic"),
        status=SimpleNamespace(value="draft"),
        consultant="Consultant",
        due_date=None,
        completed_at=None,
    )
    engagement = SimpleNamespace(
        name="URA",
        organisation="URA",
        engagement_type=SimpleNamespace(value="agency"),
        status=SimpleNamespace(value="active"),
        contact_email="planner@example.com",
        contact_phone=None,
    )
    legal = SimpleNamespace(
        name="Lease",
        instrument_type=SimpleNamespace(value="agreement"),
        status=SimpleNamespace(value="draft"),
        reference_code="REF-1",
        effective_date=None,
        expiry_date=None,
    )

    class _ServiceStub:
        def __init__(self, session):
            self.session = session

        async def all_roadmap_items(self, project_id: int):
            return [roadmap_item]

        async def list_studies(self, **kwargs):
            return _Page([study])

        async def list_engagements(self, **kwargs):
            return _Page([engagement])

        async def list_legal_instruments(self, **kwargs):
            return _Page([legal])

    monkeypatch.setattr(export_module, "EntitlementsService", _ServiceStub)
    monkeypatch.setattr(export_module, "render_html_to_pdf", lambda html: b"%PDF-1.4")

    snapshot = await export_module.build_snapshot(_SessionStub(), project_id=21)
    assert snapshot.project_id == 21
    assert snapshot.roadmap[0]["sequence"] == 1
    assert snapshot.studies[0]["name"] == "Traffic"
    assert snapshot.engagements[0]["organisation"] == "URA"
    assert snapshot.legal[0]["instrument_type"] == "agreement"

    payload, media_type, filename = await export_module.generate_entitlements_export(
        _SessionStub(), project_id=21, fmt=export_module.EntitlementsExportFormat.PDF
    )
    assert media_type == "application/pdf"
    assert filename.endswith(".pdf")
    assert payload.startswith(b"%PDF")


def test_render_export_payload_falls_back_to_html(monkeypatch):
    snapshot = export_module.EntitlementsSnapshot(
        project_id=7,
        roadmap=[
            {
                "sequence": 1,
                "status": "planned",
                "approval_type_id": 5,
                "target_submission": None,
                "target_decision": None,
                "actual_submission": None,
                "actual_decision": None,
                "notes": "note",
            }
        ],
        studies=[],
        engagements=[],
        legal=[],
        generated_at=export_module.datetime.now(export_module.UTC),
    )
    monkeypatch.setattr(export_module, "render_html_to_pdf", lambda html: None)
    payload, media_type = export_module.render_export_payload(
        snapshot, export_module.EntitlementsExportFormat.PDF
    )
    assert media_type == export_module.EntitlementsExportFormat.HTML.media_type
    assert payload.startswith(b"<html")
