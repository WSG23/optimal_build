"""Compliance API endpoints."""

from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException

from app.core.database import AsyncSessionLocal
from app.schemas.compliance import ComplianceCheckRequest, ComplianceCheckResponse
from app.services.compliance import ComplianceService

router = APIRouter(prefix="/compliance", tags=["compliance"])


@lru_cache
def _service_factory() -> ComplianceService:
    return ComplianceService(AsyncSessionLocal)


async def get_compliance_service() -> ComplianceService:
    return _service_factory()


@router.post("/check", response_model=ComplianceCheckResponse)
async def check_property_compliance(
    payload: ComplianceCheckRequest,
    service: ComplianceService = Depends(get_compliance_service),
) -> ComplianceCheckResponse:
    try:
        result = await service.run_for_property(payload.property_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result.response


__all__ = ["router"]
