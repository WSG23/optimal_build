"""Rule pack catalogue and validation endpoints."""

from __future__ import annotations

import json
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.geometry import GeometrySerializer
from app.core.rules import RulesEngine
from app.models.rulesets import RulePack
from app.schemas.rulesets import (
    RuleEvaluationResult,
    RulePackSchema,
    RulePackSummary,
    RulesetEvaluationSummary,
    RulesetListResponse,
    RulesetValidationRequest,
    RulesetValidationResponse,
)


router = APIRouter()


async def _load_ruleset(
    session: AsyncSession, payload: RulesetValidationRequest
) -> Optional[RulePack]:
    """Retrieve the rule pack referenced by the validation request."""

    stmt: Select[RulePack]
    if payload.ruleset_id is not None:
        stmt = select(RulePack).where(RulePack.id == payload.ruleset_id)
    else:
        stmt = select(RulePack).where(RulePack.slug == payload.ruleset_slug)
        if payload.ruleset_version is not None:
            stmt = stmt.where(RulePack.version == payload.ruleset_version)
        else:
            stmt = stmt.order_by(RulePack.version.desc()).limit(1)
    result = await session.execute(stmt)
    return result.scalars().first()


@router.get("/rulesets", response_model=RulesetListResponse)
async def list_rulesets(session: AsyncSession = Depends(get_session)) -> RulesetListResponse:
    """Return stored rule packs ordered by slug and version."""

    stmt: Select[RulePack] = select(RulePack).order_by(RulePack.slug, RulePack.version.desc())
    result = await session.execute(stmt)
    packs = result.scalars().all()
    items = [RulePackSchema.model_validate(pack) for pack in packs]
    return RulesetListResponse(items=items, count=len(items))


@router.post("/rulesets/validate", response_model=RulesetValidationResponse)
async def validate_ruleset(
    payload: RulesetValidationRequest,
    session: AsyncSession = Depends(get_session),
) -> RulesetValidationResponse:
    """Validate a geometry payload against the requested rule pack."""

    ruleset = await _load_ruleset(session, payload)
    if ruleset is None:
        raise HTTPException(status_code=404, detail="Rule pack not found")

    if not payload.geometry:
        raise HTTPException(status_code=400, detail="Geometry payload is required")

    try:
        graph = GeometrySerializer.from_export(payload.geometry)
    except Exception as exc:  # pragma: no cover - defensive guard for invalid payloads
        raise HTTPException(status_code=400, detail=f"Invalid geometry payload: {exc}") from exc

    engine = RulesEngine(ruleset.definition)
    evaluation = engine.evaluate(graph)

    results = [RuleEvaluationResult.model_validate(item) for item in evaluation.get("results", [])]
    summary = RulesetEvaluationSummary.model_validate(evaluation.get("summary", {}))
    ruleset_summary = RulePackSummary.model_validate(ruleset)

    citations: List[Dict[str, object]] = []
    seen: set[str] = set()
    for item in results:
        citation = item.citation
        if citation:
            key = json.dumps(citation, sort_keys=True)
            if key not in seen:
                seen.add(key)
                citations.append(citation)

    return RulesetValidationResponse(
        ruleset=ruleset_summary,
        results=results,
        summary=summary,
        citations=citations,
    )


__all__ = ["router"]
