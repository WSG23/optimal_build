"""Tests for deals utility functions."""

from __future__ import annotations

from uuid import UUID, uuid4


from app.models.business_performance import AgentDeal
from app.services.deals.utils import audit_project_key


def test_audit_project_key_uses_project_id_first():
    """audit_project_key should prefer project_id over property_id and deal id."""
    project_id = uuid4()
    property_id = uuid4()
    deal_id = uuid4()

    deal = AgentDeal(
        id=str(deal_id),
        agent_id=str(uuid4()),
        title="Test Deal",
        project_id=str(project_id),
        property_id=str(property_id),
    )

    result = audit_project_key(deal)
    assert result is not None
    assert result > 0
    assert result <= 0x7FFFFFFF  # 31-bit positive integer


def test_audit_project_key_falls_back_to_property_id():
    """audit_project_key should use property_id when project_id is None."""
    property_id = uuid4()
    deal_id = uuid4()

    deal = AgentDeal(
        id=str(deal_id),
        agent_id=str(uuid4()),
        title="Test Deal",
        project_id=None,
        property_id=str(property_id),
    )

    result = audit_project_key(deal)
    assert result is not None
    assert result > 0


def test_audit_project_key_falls_back_to_deal_id():
    """audit_project_key should use deal id when project_id and property_id are None."""
    deal_id = uuid4()

    deal = AgentDeal(
        id=str(deal_id),
        agent_id=str(uuid4()),
        title="Test Deal",
        project_id=None,
        property_id=None,
    )

    result = audit_project_key(deal)
    assert result is not None
    assert result > 0


def test_audit_project_key_returns_none_when_all_none():
    """audit_project_key should return None when all candidate sources are None."""
    deal = AgentDeal(
        id=None,  # type: ignore[arg-type]
        agent_id=str(uuid4()),
        title="Test Deal",
        project_id=None,
        property_id=None,
    )

    result = audit_project_key(deal)
    assert result is None


def test_audit_project_key_handles_invalid_uuid_string():
    """audit_project_key should skip invalid UUID strings."""
    deal = AgentDeal(
        id="not-a-uuid",  # type: ignore[arg-type]
        agent_id=str(uuid4()),
        title="Test Deal",
        project_id="invalid-uuid",
        property_id="also-invalid",
    )

    result = audit_project_key(deal)
    assert result is None


def test_audit_project_key_masks_to_31_bits():
    """audit_project_key should ensure result is positive 31-bit integer."""
    # Use a UUID where the masked value would be zero
    zero_uuid = UUID("00000000-0000-0000-0000-000000000000")

    deal = AgentDeal(
        id=str(uuid4()),
        agent_id=str(uuid4()),
        title="Test Deal",
        project_id=str(zero_uuid),
    )

    result = audit_project_key(deal)
    # Zero is not positive, so should continue to next candidate
    assert result is not None
    assert result > 0


def test_audit_project_key_skips_empty_strings():
    """audit_project_key should skip empty string values."""
    deal = AgentDeal(
        id=str(uuid4()),
        agent_id=str(uuid4()),
        title="Test Deal",
        project_id="",
        property_id="",
    )

    result = audit_project_key(deal)
    # Should fall back to deal id
    assert result is not None
    assert result > 0
