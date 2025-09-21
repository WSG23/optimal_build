"""Rules API routers."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas import RuleSearchResponse, RuleSnapshotResponse, RulesByClauseResponse
from app.services.rules import RuleService

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("/search", response_model=RuleSearchResponse)
async def search_rules(
    q: str | None = Query(default=None, alias="query"),
    authority: str | None = None,
    topic: str | None = None,
    parameter_key: str | None = None,
    limit: int = Query(default=25, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> RuleSearchResponse:
    service = RuleService(session)
    rules = await service.search(
        query=q,
        authority=authority,
        topic=topic,
        parameter_key=parameter_key,
        limit=limit,
    )
    return RuleSearchResponse(count=len(rules), rules=rules)


@router.get("/by-clause", response_model=RulesByClauseResponse)
async def rules_by_clause(
    clause_ref: str = Query(..., description="Clause reference to filter by"),
    session: AsyncSession = Depends(get_session),
) -> RulesByClauseResponse:
    service = RuleService(session)
    grouped = await service.rules_by_clause(clause_ref)
    if not grouped:
        raise HTTPException(status_code=404, detail="Clause not found")
    return RulesByClauseResponse(clause_ref=clause_ref, rules=grouped)


@router.get("/snapshot", response_model=RuleSnapshotResponse)
async def rules_snapshot(
    topic: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> RuleSnapshotResponse:
    service = RuleService(session)
    snapshot = await service.snapshot(topic=topic)
    return RuleSnapshotResponse(**snapshot)
