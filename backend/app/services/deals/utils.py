"""Shared utilities for deal pipeline services."""

from __future__ import annotations

from uuid import UUID

from app.models.business_performance import AgentDeal


def audit_key_from_value(value: object | None) -> int | None:
    """Derive a deterministic positive 31-bit audit key from a generic identifier."""

    if value in (None, ""):
        return None

    if isinstance(value, int):
        masked = value & 0x7FFFFFFF
        return masked if masked > 0 else None

    text = str(value).strip()
    if not text:
        return None

    try:
        numeric = int(text)
    except (TypeError, ValueError):
        numeric = None
    if numeric is not None:
        masked = numeric & 0x7FFFFFFF
        if masked > 0:
            return masked

    try:
        namespace = UUID(text)
    except (TypeError, ValueError):
        return None
    masked = namespace.int & 0x7FFFFFFF
    return masked if masked > 0 else None


def audit_project_key(deal: AgentDeal) -> int | None:
    """Derive a deterministic integer key for audit ledger chaining.

    Tries to extract a stable 31-bit integer from deal's project_id,
    property_id, or deal id (in that priority order).

    Args:
        deal: The agent deal record

    Returns:
        Positive 31-bit integer for audit linking, or None if no valid source
    """
    candidate_sources = [deal.project_id, deal.property_id, deal.id]
    for source in candidate_sources:
        value = audit_key_from_value(source)
        if value is not None:
            return value
    return None
