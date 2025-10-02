"""Business logic for regulatory compliance checks."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.singapore_property import SingaporeProperty, ComplianceStatus
from app.schemas.compliance import ComplianceCheckResponse
from app.schemas.property import PropertyComplianceSummary, SingaporePropertySchema
from app.utils.singapore_compliance import update_property_compliance


@dataclass(slots=True)
class ComplianceResult:
    """Outcome emitted by the compliance service."""

    property: SingaporePropertySchema
    response: ComplianceCheckResponse


class ComplianceService:
    """Coordinator responsible for running compliance assessments."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def run_for_property(self, property_id: UUID) -> ComplianceResult:
        """Execute compliance checks for a single property identifier."""

        async with self._session_factory() as session:
            record = await session.get(SingaporeProperty, property_id)
            if record is None:
                raise ValueError(f"Property {property_id} not found")
            updated = await update_property_compliance(record, session)
            await session.commit()
            return _build_result(updated)

    async def run_batch(
        self,
        *,
        property_ids: Sequence[UUID] | None = None,
        limit: int = 100,
    ) -> list[ComplianceResult]:
        """Refresh a batch of properties awaiting compliance validation."""

        async with self._session_factory() as session:
            stmt = self._build_query(property_ids, limit)
            properties = (await session.execute(stmt)).scalars().all()
            results: list[ComplianceResult] = []
            for record in properties:
                updated = await update_property_compliance(record, session)
                results.append(_build_result(updated))
            await session.commit()
        return results

    def _build_query(
        self,
        property_ids: Sequence[UUID] | None,
        limit: int,
    ) -> Select[tuple[SingaporeProperty]]:
        stmt = select(SingaporeProperty).order_by(SingaporeProperty.updated_at.desc())
        ids = list(property_ids or [])
        if ids:
            stmt = stmt.where(SingaporeProperty.id.in_(ids))
        else:
            stmt = stmt.limit(limit)
        return stmt


def _build_result(record: SingaporeProperty) -> ComplianceResult:
    compliance = PropertyComplianceSummary(
        bca_status=_to_string(record.bca_compliance_status),
        ura_status=_to_string(record.ura_compliance_status),
        notes=record.compliance_notes,
        last_checked=record.compliance_last_checked,
        data=record.compliance_data or {},
    )
    response = ComplianceCheckResponse(
        property_id=record.id,
        compliance=compliance,
        updated_at=record.updated_at,
        metadata={"jurisdiction": "SG"},
    )
    return ComplianceResult(
        property=SingaporePropertySchema.model_validate(record),
        response=response,
    )


def _to_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, ComplianceStatus):
        return value.value
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


__all__ = ["ComplianceResult", "ComplianceService"]
