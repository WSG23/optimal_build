"""Supporting endpoints for the admin review UI."""

from __future__ import annotations

from collections import Counter
from fastapi import APIRouter, Depends, Query

from app.api.deps import require_viewer
from app.core.database import get_session
from app.models.rkp import RefClause, RefDocument, RefRule, RefSource
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/review")


def _coverage_state(*, total_rules: int, approved_published: int) -> str:
    if total_rules == 0:
        return "missing"
    if approved_published == 0:
        return "review_pending"
    if approved_published < total_rules:
        return "partial"
    return "approved"


def _confidence(*, approved_published: int, traceable: int) -> str:
    if approved_published == 0:
        return "low"
    if traceable < approved_published:
        return "medium"
    return "high"


def _freshness_state(
    *,
    is_active: bool,
    total_documents: int,
    suspected_updates: int,
) -> str:
    if not is_active:
        return "inactive"
    if total_documents == 0:
        return "no_documents"
    if suspected_updates > 0:
        return "suspected_update"
    return "current"


@router.get("/sources")
async def list_sources(
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> dict[str, object]:
    result = await session.execute(select(RefSource))
    items = [
        {
            "id": source.id,
            "jurisdiction": source.jurisdiction,
            "authority": source.authority,
            "topic": source.topic,
            "doc_title": source.doc_title,
            "landing_url": source.landing_url,
        }
        for source in result.scalars().all()
    ]
    return {"items": items, "count": len(items)}


@router.get("/corpus-status")
async def list_corpus_status(
    session: AsyncSession = Depends(get_session),
    jurisdiction: str | None = Query(default=None),
    authority: str | None = Query(default=None),
    topic: str | None = Query(default=None),
    _: str = Depends(require_viewer),
) -> dict[str, object]:
    """Summarise corpus freshness and review readiness by source."""

    source_stmt = select(RefSource)
    if jurisdiction is not None:
        source_stmt = source_stmt.where(RefSource.jurisdiction == jurisdiction)
    if authority is not None:
        source_stmt = source_stmt.where(RefSource.authority == authority)
    if topic is not None:
        source_stmt = source_stmt.where(RefSource.topic == topic)

    sources = (await session.execute(source_stmt)).scalars().all()
    if not sources:
        return {"items": [], "count": 0}

    source_ids = [source.id for source in sources]
    documents = (
        (
            await session.execute(
                select(RefDocument).where(RefDocument.source_id.in_(source_ids))
            )
        )
        .scalars()
        .all()
    )
    rules = (
        (
            await session.execute(
                select(RefRule).where(RefRule.source_id.in_(source_ids))
            )
        )
        .scalars()
        .all()
    )

    docs_by_source: dict[int, list[RefDocument]] = {}
    for document in documents:
        docs_by_source.setdefault(document.source_id, []).append(document)

    rules_by_source: dict[int, list[RefRule]] = {}
    for rule in rules:
        if rule.source_id is None:
            continue
        rules_by_source.setdefault(rule.source_id, []).append(rule)

    items: list[dict[str, object]] = []
    for source in sources:
        source_documents = docs_by_source.get(source.id, [])
        source_rules = rules_by_source.get(source.id, [])
        latest_document = max(
            source_documents,
            key=lambda item: (
                item.retrieved_at is not None,
                item.retrieved_at.isoformat() if item.retrieved_at else "",
            ),
            default=None,
        )
        review_counts = Counter(
            str(rule.review_status or "unknown") for rule in source_rules
        )
        approved_published = sum(
            1
            for rule in source_rules
            if rule.review_status == "approved" and bool(rule.is_published)
        )
        traceable = sum(
            1
            for rule in source_rules
            if rule.review_status == "approved"
            and bool(rule.is_published)
            and any(
                (
                    rule.document_id,
                    rule.source_id,
                    isinstance(rule.source_provenance, dict),
                )
            )
        )
        suspected_updates = sum(
            1 for document in source_documents if bool(document.suspected_update)
        )
        item = {
            "source_id": source.id,
            "jurisdiction": source.jurisdiction,
            "authority": source.authority,
            "topic": source.topic,
            "doc_title": source.doc_title,
            "landing_url": source.landing_url,
            "fetch_kind": source.fetch_kind,
            "update_freq_hint": source.update_freq_hint,
            "is_active": bool(source.is_active),
            "latest_document": (
                {
                    "id": latest_document.id,
                    "version_label": latest_document.version_label,
                    "retrieved_at": (
                        latest_document.retrieved_at.isoformat()
                        if latest_document.retrieved_at
                        else None
                    ),
                    "suspected_update": bool(latest_document.suspected_update),
                }
                if latest_document is not None
                else None
            ),
            "document_counts": {
                "total": len(source_documents),
                "suspected_updates": suspected_updates,
            },
            "rule_counts": {
                "total": len(source_rules),
                "approved": review_counts.get("approved", 0),
                "published": approved_published,
                "traceable": traceable,
                "needs_review": review_counts.get("needs_review", 0),
                "rejected": review_counts.get("rejected", 0),
            },
            "coverage_state": _coverage_state(
                total_rules=len(source_rules),
                approved_published=approved_published,
            ),
            "confidence": _confidence(
                approved_published=approved_published,
                traceable=traceable,
            ),
            "freshness_state": _freshness_state(
                is_active=bool(source.is_active),
                total_documents=len(source_documents),
                suspected_updates=suspected_updates,
            ),
            "review_queue_size": review_counts.get("needs_review", 0),
        }
        items.append(item)

    items.sort(
        key=lambda item: (
            str(item["jurisdiction"]),
            str(item["authority"]),
            str(item["topic"]),
        )
    )
    return {"items": items, "count": len(items)}


@router.get("/documents")
async def list_documents(
    session: AsyncSession = Depends(get_session),
    source_id: int | None = Query(default=None),
    _: str = Depends(require_viewer),
) -> dict[str, object]:
    stmt = select(RefDocument)
    if source_id is not None:
        stmt = stmt.where(RefDocument.source_id == source_id)
    result = await session.execute(stmt)
    items = [
        {
            "id": document.id,
            "source_id": document.source_id,
            "version_label": document.version_label,
            "storage_path": document.storage_path,
            "retrieved_at": (
                document.retrieved_at.isoformat() if document.retrieved_at else None
            ),
        }
        for document in result.scalars().all()
    ]
    return {"items": items, "count": len(items)}


@router.get("/clauses")
async def list_clauses(
    session: AsyncSession = Depends(get_session),
    document_id: int | None = Query(default=None),
    _: str = Depends(require_viewer),
) -> dict[str, object]:
    stmt = select(RefClause)
    if document_id is not None:
        stmt = stmt.where(RefClause.document_id == document_id)
    result = await session.execute(stmt)
    items = [
        {
            "id": clause.id,
            "document_id": clause.document_id,
            "clause_ref": clause.clause_ref,
            "section_heading": clause.section_heading,
            "text_span": clause.text_span,
            "page_from": clause.page_from,
            "page_to": clause.page_to,
        }
        for clause in result.scalars().all()
    ]
    return {"items": items, "count": len(items)}


@router.get("/diffs")
async def list_diffs(
    session: AsyncSession = Depends(get_session),
    rule_id: int | None = Query(default=None),
    _: str = Depends(require_viewer),
) -> dict[str, object]:
    stmt = select(RefRule)
    if rule_id is not None:
        stmt = stmt.where(RefRule.id == rule_id)
    result = await session.execute(stmt)
    items = []
    for rule in result.scalars().all():
        baseline = rule.notes or "No previous note available."
        updated = f"{rule.parameter_key} {rule.operator} {rule.value}"
        items.append(
            {
                "rule_id": rule.id,
                "baseline": baseline,
                "updated": updated,
            }
        )
    return {"items": items, "count": len(items)}


__all__ = ["router"]
