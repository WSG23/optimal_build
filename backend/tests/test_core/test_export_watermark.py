from datetime import datetime

from app.core.auth import PolicyContext, SignoffSnapshot, WorkspaceRole
import pytest

pytest.importorskip("sqlalchemy")

from app.core.export.watermark import ExportPayload, apply_watermark
from backend._compat.datetime import UTC


def approved_signoff() -> SignoffSnapshot:
    return SignoffSnapshot(
        project_id=2,
        overlay_version="v1",
        status="approved",
        architect_user_id=3,
        signed_at=datetime(2024, 1, 1, tzinfo=UTC),
    )


def test_watermark_applied_for_agency():
    context = PolicyContext(role=WorkspaceRole.AGENCY)
    payload = ExportPayload(content=b"data")
    result = apply_watermark(payload, context)
    assert result.watermark
    assert result.content == payload.content


def test_watermark_retained_if_already_applied():
    context = PolicyContext(role=WorkspaceRole.AGENCY)
    payload = ExportPayload(
        content=b"data",
        watermark="Marketing Feasibility Only – Not for Permit or Construction.",
    )
    result = apply_watermark(payload, context)
    assert result is payload


def test_no_watermark_for_architect_with_signoff():
    context = PolicyContext(role=WorkspaceRole.ARCHITECT, signoff=approved_signoff())
    payload = ExportPayload(content=b"data")
    result = apply_watermark(payload, context)
    assert result.watermark is None
