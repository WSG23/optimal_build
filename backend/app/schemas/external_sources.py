"""Schemas for external provider status metadata."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class ExternalSourceState(str, Enum):
    """Operational state for an external provider capability."""

    LIVE = "live"
    MOCK = "mock"
    UNAVAILABLE = "unavailable"


class ExternalSourceMetadata(BaseModel):
    """Machine-readable metadata for external provider provenance."""

    provider: str
    state: ExternalSourceState
    configured: bool
    synthetic: bool
    reason: str | None = None
