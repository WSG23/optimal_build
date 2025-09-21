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
from app.services.normalize import NormalizedRule, RuleNormalizer


router = APIRouter()


def _extract_zone_code(rule: RefRule) -> Optional[str]:
    applicability = rule.applicability or {}
    if isinstance(applicability, dict):
        zone = applicability.get("zone_code") or applicability.get("zone")
        if isinstance(zone, list):
            return next((str(item) for item in zone if item), None)
        if zone:
            return str(zone)
    return None


def _serialise_rule(
    rule: RefRule,
    normalizer: RuleNormalizer,
    zoning_lookup: Dict[str, List[RefZoningLayer]],
) -> Dict[str, object]:
    overlays: List[str] = []
    hints: List[str] = []
    normalized: List[NormalizedRule] = []

    if rule.notes:
        normalized = normalizer.normalize(rule.notes, context={"rule_id": rule.id})
    if not normalized:
        fragment = f"{rule.parameter_key} {rule.operator} {rule.value}"
        normalized = normalizer.normalize(fragment, context={"rule_id": rule.id})

    zone_code = _extract_zone_code(rule)
    if zone_code and zone_code in zoning_lookup:
        for layer in zoning_lookup[zone_code]:
            attributes = layer.attributes or {}
            overlays.extend(attributes.get("overlays", []))
            hints.extend(attributes.get("advisory_hints", []))

    hints.extend(hint for rule_match in normalized for hint in rule_match.hints)

    overlays = list(dict.fromkeys(filter(None, overlays)))
    hints = list(dict.fromkeys(filter(None, hints)))

    return {
        "id": rule.id,
        "parameter_key": rule.parameter_key,
        "operator": rule.operator,
        "value": rule.value,
        "unit": rule.unit,
        "jurisdiction": rule.jurisdiction,
        "authority": rule.authority,
        "topic": rule.topic,
        "review_status": rule.review_status,
        "review_notes": rule.review_notes,
        "is_published": rule.is_published,
        "overlays": overlays,
        "advisory_hints": hints,
        "normalized": [match.as_dict() for match in normalized],
    }


async def _load_zoning_lookup(
    session: AsyncSession, zone_codes: Iterable[str]
) -> Dict[str, List[RefZoningLayer]]:
    codes = [code for code in set(zone_codes) if code]
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
    zone_codes = [_extract_zone_code(rule) for rule in rules]
    zoning_lookup = await _load_zoning_lookup(session, zone_codes)
    normalizer = RuleNormalizer()
    items = [_serialise_rule(rule, normalizer, zoning_lookup) for rule in rules]
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

    now = datetime.now(timezone.utc)
    if payload.action == "approve":
        rule.review_status = "approved"
        rule.reviewed_at = now
    elif payload.action == "reject":
        rule.review_status = "rejected"
        rule.reviewed_at = now
    elif payload.action == "publish":
        rule.is_published = True
        rule.published_at = now
        rule.review_status = "approved"
        rule.reviewed_at = now

    if payload.reviewer:
        rule.reviewer = payload.reviewer
    if payload.notes is not None:
        rule.review_notes = payload.notes

    await session.commit()
    await session.refresh(rule)

    zoning_lookup = await _load_zoning_lookup(session, [_extract_zone_code(rule)])
    normalizer = RuleNormalizer()
    return {"item": _serialise_rule(rule, normalizer, zoning_lookup)}


@router.get("/review/queue")
async def review_queue(session: AsyncSession = Depends(get_session)) -> Dict[str, object]:
    stmt = select(RefRule).where(RefRule.review_status == "needs_review")
    rules = (await session.execute(stmt)).scalars().all()
    zoning_lookup = await _load_zoning_lookup(session, [_extract_zone_code(rule) for rule in rules])
    normalizer = RuleNormalizer()
    items = [_serialise_rule(rule, normalizer, zoning_lookup) for rule in rules]
    return {"items": items, "count": len(items)}


__all__ = ["router"]
