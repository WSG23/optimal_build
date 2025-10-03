from datetime import datetime
from backend._compat.datetime import UTC

import pytest
from app.core.auth import (
    PolicyContext,
    SignoffSnapshot,
    WorkspaceRole,
    can_export_permit_ready,
    can_invite_architect,
    requires_signoff,
    watermark_forced,
    watermark_text,
)


@pytest.fixture
def approved_signoff() -> SignoffSnapshot:
    return SignoffSnapshot(
        project_id=10,
        overlay_version="v1",
        status="approved",
        architect_user_id=42,
        signed_at=datetime(2024, 1, 1, tzinfo=UTC),
    )


@pytest.fixture
def pending_signoff() -> SignoffSnapshot:
    return SignoffSnapshot(
        project_id=10,
        overlay_version="v1",
        status="pending",
        architect_user_id=None,
        signed_at=None,
    )


@pytest.mark.parametrize(
    "role,expected",
    [
        (WorkspaceRole.AGENCY, True),
        (WorkspaceRole.DEVELOPER, True),
        (WorkspaceRole.ARCHITECT, False),
    ],
)
def test_requires_signoff(role, expected, approved_signoff):
    context = PolicyContext(role=role, signoff=approved_signoff)
    assert requires_signoff(context) is expected


@pytest.mark.parametrize(
    "role,signoff,expected",
    [
        (WorkspaceRole.AGENCY, None, False),
        (WorkspaceRole.DEVELOPER, None, False),
        (WorkspaceRole.DEVELOPER, "approved", True),
        (WorkspaceRole.ARCHITECT, "approved", True),
    ],
)
def test_can_export_permit_ready(
    role, signoff, expected, approved_signoff, pending_signoff
):
    snapshot = (
        approved_signoff
        if signoff == "approved"
        else pending_signoff if signoff else None
    )
    context = PolicyContext(role=role, signoff=snapshot)
    assert can_export_permit_ready(context) is expected


@pytest.mark.parametrize(
    "role,signoff,forced",
    [
        (WorkspaceRole.AGENCY, None, True),
        (WorkspaceRole.DEVELOPER, None, True),
        (WorkspaceRole.DEVELOPER, "approved", False),
        (WorkspaceRole.ARCHITECT, "approved", False),
    ],
)
def test_watermark_policies(role, signoff, forced, approved_signoff, pending_signoff):
    snapshot = (
        approved_signoff
        if signoff == "approved"
        else pending_signoff if signoff else None
    )
    context = PolicyContext(role=role, signoff=snapshot)
    assert watermark_forced(context) is forced
    if forced:
        assert watermark_text(context)
    else:
        assert watermark_text(context) == ""


def test_can_invite_architect_only_developer(approved_signoff):
    assert can_invite_architect(
        PolicyContext(role=WorkspaceRole.DEVELOPER, signoff=approved_signoff)
    )
    assert not can_invite_architect(PolicyContext(role=WorkspaceRole.AGENCY))
    assert not can_invite_architect(PolicyContext(role=WorkspaceRole.ARCHITECT))
