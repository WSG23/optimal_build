"""Finance job tracking API endpoints.

This module handles:
- GET /jobs - List pending finance job metadata
- GET /scenarios/{scenario_id}/status - Expose job status for polling clients
- GET /scenarios/{scenario_id}/status-stream - SSE feed for job status
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import RequestIdentity, require_reviewer, require_viewer
from app.core.database import get_session
from app.models.finance import FinScenario
from app.schemas.finance import FinanceJobStatusSchema

from .finance_common import (
    project_uuid_from_scenario,
    scenario_job_statuses,
    status_payload,
)
from .finance_scenarios import _ensure_project_owner

router = APIRouter(prefix="/finance", tags=["finance"])


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


async def _load_scenario_for_status(
    session: AsyncSession,
    scenario_id: int,
    identity: RequestIdentity,
) -> FinScenario:
    """Load a scenario and verify ownership for status endpoints."""

    stmt = (
        select(FinScenario)
        .where(FinScenario.id == scenario_id)
        .options(selectinload(FinScenario.fin_project))
    )
    scenario = (await session.execute(stmt)).scalars().first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Finance scenario not found")
    await _ensure_project_owner(session, project_uuid_from_scenario(scenario), identity)
    return scenario


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/jobs", response_model=list[FinanceJobStatusSchema])
async def list_finance_jobs(
    scenario_id: int = Query(..., ge=1),
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_viewer),
) -> list[FinanceJobStatusSchema]:
    """Return pending finance job metadata for a persisted scenario."""

    stmt = (
        select(FinScenario)
        .where(FinScenario.id == scenario_id)
        .options(
            selectinload(FinScenario.fin_project),
            selectinload(FinScenario.asset_breakdowns),
        )
    )
    scenario = (await session.execute(stmt)).scalars().first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Finance scenario not found")
    await _ensure_project_owner(session, project_uuid_from_scenario(scenario), identity)
    return scenario_job_statuses(scenario)


@router.get("/scenarios/{scenario_id}/status")
async def finance_scenario_status(
    scenario_id: int,
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_viewer),
) -> dict[str, Any]:
    """Expose job status metadata for polling clients."""

    scenario = await _load_scenario_for_status(session, scenario_id, identity)
    return status_payload(scenario)


@router.get("/scenarios/{scenario_id}/status-stream")
async def finance_scenario_status_stream(
    scenario_id: int,
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_reviewer),
) -> StreamingResponse:
    """Server-sent events feed mirroring :func:`finance_scenario_status`."""

    scenario = await _load_scenario_for_status(session, scenario_id, identity)
    payload = status_payload(scenario)

    async def _event_stream() -> AsyncIterator[bytes]:
        data = json.dumps(payload, default=str)
        yield f"data: {data}\n\n".encode("utf-8")

    return StreamingResponse(_event_stream(), media_type="text/event-stream")


__all__ = ["router"]
