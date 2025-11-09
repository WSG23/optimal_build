"""Rule review and catalogue endpoints."""

from __future__ import annotations

import copy
import os
from collections.abc import Iterable
from datetime import datetime
from typing import Literal

from backend._compat.datetime import UTC
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.api.deps import require_reviewer, require_viewer
from app.core.database import get_session
from app.models.rkp import RefRule, RefZoningLayer
from app.services.normalize import NormalizedRule, RuleNormalizer
from app.utils.cache import TTLCache
from app.utils.logging import get_logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = get_logger(__name__)

_RULES_CACHE_TTL_SECONDS = int(os.getenv("RULES_CACHE_TTL_SECONDS", "120"))
_RULES_CACHE = TTLCache(
    ttl_seconds=_RULES_CACHE_TTL_SECONDS, copy=lambda payload: copy.deepcopy(payload)
)


def _extract_zone_code(rule: RefRule) -> str | None:
    applicability = rule.applicability or {}
    if isinstance(applicability, dict):
        zone = applicability.get("zone_code") or applicability.get("zone")
        if isinstance(zone, list):
            return next((str(item) for item in zone if item), None)
        if zone:
            return str(zone)
    return None


def _normalize_review_status(
    review_status: str | list[str] | None,
) -> list[str]:
    if not review_status:
        return []
    if isinstance(review_status, str):
        raw_tokens = [review_status]
    else:
        raw_tokens = list(review_status)

    statuses: list[str] = []
    seen: set[str] = set()
    for token in raw_tokens:
        for candidate in token.split(","):
            value = candidate.strip()
            if value and value not in seen:
                seen.add(value)
                statuses.append(value)
    return statuses


def _serialise_rule(
    rule: RefRule,
    normalizer: RuleNormalizer,
    zoning_lookup: dict[str, list[RefZoningLayer]],
) -> dict[str, object]:
    overlays: list[str] = []
    hints: list[str] = []
    normalized: list[NormalizedRule] = []

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

    provenance: dict[str, object]
    if isinstance(rule.source_provenance, dict):
        provenance = dict(rule.source_provenance)
    else:
        provenance = {}

    if rule.review_status == "approved":
        provenance.setdefault("document_id", rule.document_id)
        provenance.setdefault("clause_id", None)
        provenance.setdefault("pages", [])

    return {
        "id": rule.id,
        "source_id": rule.source_id,
        "document_id": rule.document_id,
        "parameter_key": rule.parameter_key,
        "operator": rule.operator,
        "value": rule.value,
        "unit": rule.unit,
        "jurisdiction": rule.jurisdiction,
        "authority": rule.authority,
        "topic": rule.topic,
        "clause_ref": rule.clause_ref,
        "review_status": rule.review_status,
        "review_notes": rule.review_notes,
        "is_published": rule.is_published,
        "source_provenance": provenance,
        "overlays": overlays,
        "advisory_hints": hints,
        "normalized": [match.as_dict() for match in normalized],
    }


async def _load_zoning_lookup(
    session: AsyncSession, zone_codes: Iterable[str]
) -> dict[str, list[RefZoningLayer]]:
    codes = [code for code in set(zone_codes) if code]
    if not codes:
        return {}

    stmt = select(RefZoningLayer).where(RefZoningLayer.zone_code.in_(codes))
    result = await session.execute(stmt)
    lookup: dict[str, list[RefZoningLayer]] = {}
    for layer in result.scalars().all():
        lookup.setdefault(layer.zone_code, []).append(layer)
    return lookup


@router.get("/rules")
async def list_rules(
    jurisdiction: str | None = Query(None),
    parameter_key: str | None = Query(None),
    authority: str | None = Query(None),
    topic: str | None = Query(None),
    review_status: str | list[str] | None = Query(None),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> dict[str, object]:
    statuses = _normalize_review_status(review_status)
    cache_key = (
        jurisdiction or "",
        parameter_key or "",
        authority or "",
        topic or "",
        tuple(statuses),
    )

    cached_payload = await _RULES_CACHE.get(cache_key)
    if cached_payload is not None:
        return cached_payload

    stmt = select(RefRule)
    filter_conditions: list[object] = []
    if jurisdiction:
        condition = RefRule.jurisdiction == jurisdiction
        stmt = stmt.where(condition)
        filter_conditions.append(condition)
    if parameter_key:
        condition = RefRule.parameter_key == parameter_key
        stmt = stmt.where(condition)
        filter_conditions.append(condition)
    if authority:
        condition = RefRule.authority == authority
        stmt = stmt.where(condition)
        filter_conditions.append(condition)
    if topic:
        condition = RefRule.topic == topic
        stmt = stmt.where(condition)
        filter_conditions.append(condition)

    fallback_stmt = select(RefRule)
    for condition in filter_conditions:
        fallback_stmt = fallback_stmt.where(condition)

    base_stmt = stmt
    rules: list[RefRule]

    if statuses:
        seen_ids: set[int] = set()
        collected: list[RefRule] = []
        for status in statuses:
            subset_stmt = base_stmt.where(RefRule.review_status == status)
            result = await session.execute(subset_stmt)
            subset_rules = result.scalars().all()
            logger.debug(
                "rules_filter_subset",
                review_status=status,
                subset_count=len(subset_rules),
            )
            for rule in subset_rules:
                if rule.id not in seen_ids:
                    seen_ids.add(rule.id)
                    collected.append(rule)
        rules = collected
        logger.debug(
            "rules_filter_combined",
            requested_statuses=statuses,
            total=len(rules),
        )
    else:
        filtered_stmt = base_stmt.where(RefRule.review_status == "approved")
        result = await session.execute(filtered_stmt)
        rules = result.scalars().all()
        if not rules and not filter_conditions:
            fallback_filtered = fallback_stmt.where(RefRule.review_status == "approved")
            result = await session.execute(fallback_filtered)
            rules = result.scalars().all()

    zone_codes = [_extract_zone_code(rule) for rule in rules]
    zoning_lookup = await _load_zoning_lookup(session, zone_codes)
    normalizer = RuleNormalizer()
    items = [_serialise_rule(rule, normalizer, zoning_lookup) for rule in rules]
    payload = {"items": items, "count": len(items)}
    await _RULES_CACHE.set(cache_key, payload)
    return payload


class ReviewAction(BaseModel):
    action: Literal["approve", "reject", "publish"]
    reviewer: str | None = None
    notes: str | None = None


@router.post("/rules/{rule_id}/review")
async def review_rule(
    rule_id: int,
    payload: ReviewAction,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_reviewer),
) -> dict[str, object]:
    rule = await session.get(RefRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")

    now = datetime.now(UTC)
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
    await _RULES_CACHE.clear()

    zoning_lookup = await _load_zoning_lookup(session, [_extract_zone_code(rule)])
    normalizer = RuleNormalizer()
    return {"item": _serialise_rule(rule, normalizer, zoning_lookup)}


@router.get("/review/queue")
async def review_queue(
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> dict[str, object]:
    stmt = select(RefRule).where(RefRule.review_status == "needs_review")
    rules = (await session.execute(stmt)).scalars().all()
    zoning_lookup = await _load_zoning_lookup(
        session, [_extract_zone_code(rule) for rule in rules]
    )
    normalizer = RuleNormalizer()
    items = [_serialise_rule(rule, normalizer, zoning_lookup) for rule in rules]
    return {"items": items, "count": len(items)}


__all__ = ["router"]
