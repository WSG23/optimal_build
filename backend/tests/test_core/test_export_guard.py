import pytest

from app.core.auth import PolicyContext, SignoffSnapshot, WorkspaceRole

pytest.importorskip("sqlalchemy")

from app.core.export.guard import ExportDecision, ExportRequest, evaluate_export


def build_signoff(status: str | None) -> SignoffSnapshot | None:
    if not status:
        return None
    return SignoffSnapshot(
        project_id=7,
        overlay_version="v2",
        status=status,  # type: ignore[arg-type]
        architect_user_id=88,
        signed_at=None,
    )


def test_non_permit_ready_requests_always_allowed():
    context = PolicyContext(role=WorkspaceRole.AGENCY)
    request = ExportRequest(project_id=1, overlay_version="v1", permit_ready=False)
    decision = evaluate_export(request, context)
    assert decision == ExportDecision(allowed=True, reason=None)


def test_developer_requires_signoff_for_permit_ready():
    context = PolicyContext(
        role=WorkspaceRole.DEVELOPER, signoff=build_signoff("pending")
    )
    request = ExportRequest(project_id=1, overlay_version="v1", permit_ready=True)
    decision = evaluate_export(request, context)
    assert not decision.allowed
    assert "sign-off" in (decision.reason or "")


def test_architect_with_signoff_is_allowed():
    signoff = build_signoff("approved")
    context = PolicyContext(role=WorkspaceRole.ARCHITECT, signoff=signoff)
    request = ExportRequest(project_id=1, overlay_version="v1", permit_ready=True)
    decision = evaluate_export(request, context)
    assert decision.allowed


def test_agency_never_permit_ready():
    context = PolicyContext(
        role=WorkspaceRole.AGENCY, signoff=build_signoff("approved")
    )
    request = ExportRequest(project_id=1, overlay_version="v1", permit_ready=True)
    decision = evaluate_export(request, context)
    assert not decision.allowed
    assert decision.reason == "Agency exports cannot be permit-ready"
