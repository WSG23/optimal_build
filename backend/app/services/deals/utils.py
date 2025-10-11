"""Shared utilities for deal pipeline services."""

from __future__ import annotations

from uuid import UUID

from app.models.business_performance import AgentDeal


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
        if not source:
            continue
        try:
            namespace = UUID(str(source))
        except (TypeError, ValueError):
            continue
        value = namespace.int & 0x7FFFFFFF
        if value > 0:
            return value
    return None
