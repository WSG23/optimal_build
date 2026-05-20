"""Shared mixins for soft-delete and multi-tenant scoping."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime

from app.models.base import UUID


class SoftDeleteMixin:
    """Adds a nullable ``deleted_at`` timestamp for logical deletes.

    Queries must filter ``WHERE deleted_at IS NULL`` to exclude removed rows;
    the column is indexed so the filter stays cheap on hot paths.
    """

    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def mark_deleted(self, when: datetime | None = None) -> None:
        from backend._compat.datetime import utcnow

        self.deleted_at = when or utcnow()


class OrgScopedMixin:
    """Adds nullable ``organization_id`` FK so multi-tenant isolation is a row filter, not a forklift."""

    organization_id = Column(
        UUID(),
        nullable=True,
        index=True,
    )


__all__ = ["SoftDeleteMixin", "OrgScopedMixin"]
