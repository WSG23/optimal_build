"""Rule review and catalogue endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Iterable, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.rkp import RefRule, RefZoningLayer
from app.services.normalize import RuleNormalizer
from app.services.rules_logic import (
    apply_review_action,
    get_rule_zone_code,
    serialise_rule,
)

router = APIRouter()


async def _load_zoning_lookup(
    session: AsyncSession, zone_codes: Iterable[str | None]
) -> Dict[str, List[RefZoningLayer]]:
    codes = [code for code in {code for code in zone_codes if code}]
    if not codes:
        return {}

    stmt = select(RefZoningLayer).where(RefZoningLayer.zone_code.in_(codes))
    result = await session.execute(stmt)
    lookup: Dict[str, List[RefZoningLayer]] = {}
    for layer in result.scalars().all():
        lookup.setdefault(layer.zone_code, []).append(layer)
    return lookup


@router.get("/rules")
async def list_rules(session: AsyncSession = Depends(get_session)) -> Dict[str, object]:
    result = await session.execute(select(RefRule))
    rules = result.scalars().all()
    zone_codes = [get_rule_zone_code(rule) for rule in rules]
    zoning_lookup = await _load_zoning_lookup(session, zone_codes)
    normalizer = RuleNormalizer()
    items = [serialise_rule(rule, normalizer, zoning_lookup) for rule in rules]
    return {"items": items, "count": len(items)}


class ReviewAction(BaseModel):
    action: Literal["approve", "reject", "publish"]
    reviewer: Optional[str] = None
    notes: Optional[str] = None


@router.post("/rules/{rule_id}/review")
async def review_rule(
    rule_id: int,
    payload: ReviewAction,
    session: AsyncSession = Depends(get_session),
) -> Dict[str, object]:
    rule = await session.get(RefRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")

    apply_review_action(
        rule,
        payload.action,
        reviewer=payload.reviewer,
        notes=payload.notes,
        timestamp=datetime.now(timezone.utc),
    )

    await session.commit()
    await session.refresh(rule)

    zoning_lookup = await _load_zoning_lookup(session, [get_rule_zone_code(rule)])
    normalizer = RuleNormalizer()
    return {"item": serialise_rule(rule, normalizer, zoning_lookup)}


@router.get("/review/queue")
async def review_queue(session: AsyncSession = Depends(get_session)) -> Dict[str, object]:
    stmt = select(RefRule).where(RefRule.review_status == "needs_review")
    rules = (await session.execute(stmt)).scalars().all()
    zoning_lookup = await _load_zoning_lookup(session, [get_rule_zone_code(rule) for rule in rules])
    normalizer = RuleNormalizer()
    items = [serialise_rule(rule, normalizer, zoning_lookup) for rule in rules]
    return {"items": items, "count": len(items)}


__all__ = ["router"]
