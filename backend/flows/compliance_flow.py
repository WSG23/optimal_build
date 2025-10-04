"""Prefect flow orchestrating property compliance checks."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any
from uuid import UUID

from app.models.singapore_property import ComplianceStatus, SingaporeProperty
from app.utils.singapore_compliance import update_property_compliance
from prefect import flow
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

DEFAULT_BATCH_SIZE = 50


def _build_property_query(
    property_ids: Iterable[UUID] | None,
) -> Select[tuple[SingaporeProperty]]:
    stmt = select(SingaporeProperty).order_by(SingaporeProperty.updated_at.desc())
    if property_ids:
        stmt = stmt.where(SingaporeProperty.id.in_(list(property_ids)))
    else:
        stmt = stmt.limit(DEFAULT_BATCH_SIZE)
    return stmt


@flow(name="singapore-compliance-refresh")
async def refresh_singapore_compliance(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    property_ids: Sequence[UUID] | None = None,
    commit: bool = True,
) -> list[dict[str, Any]]:
    """Run URA/BCA compliance checks and persist results.

    Parameters
    ----------
    session_factory:
        Async session factory used for database interaction.
    property_ids:
        Optional collection of Singapore property identifiers to refresh. When
        omitted, the flow processes a small batch of recently updated entries.
    commit:
        Controls whether the session is committed after processing. Disable when
        invoking the flow inside an existing transaction during tests.

    Returns
    -------
    list of dict
        Summary entries describing the compliance outcome for each processed
        property. Each entry contains the property identifier and the updated
        BCA/URA statuses.
    """

    results: list[dict[str, Any]] = []
    ids = list(property_ids or [])
    async with session_factory() as session:
        stmt = _build_property_query(ids)
        properties = (await session.execute(stmt)).scalars().all()

        for record in properties:
            updated = await update_property_compliance(record, session)
            bca_status = getattr(
                updated, "bca_compliance_status", ComplianceStatus.PENDING
            )
            ura_status = getattr(
                updated, "ura_compliance_status", ComplianceStatus.PENDING
            )
            results.append(
                {
                    "property_id": str(updated.id),
                    "bca_status": getattr(bca_status, "value", bca_status),
                    "ura_status": getattr(ura_status, "value", ura_status),
                }
            )

        if commit:
            await session.commit()
        else:  # pragma: no cover - safety for transactions managed by caller
            await session.flush()

    return results


__all__ = ["refresh_singapore_compliance"]
