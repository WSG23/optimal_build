"""Supporting endpoints for the admin review UI."""

from __future__ import annotations

from typing import Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_viewer
from app.core.database import get_session
from app.models.rkp import RefClause, RefDocument, RefRule, RefSource
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

router = APIRouter(prefix="/review")


@router.get("/sources")
async def list_sources(
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> Dict[str, object]:
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


@router.get("/documents")
async def list_documents(
    session: AsyncSession = Depends(get_session),
    source_id: Optional[int] = Query(default=None),
    _: str = Depends(require_viewer),
) -> Dict[str, object]:
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
            "retrieved_at": document.retrieved_at.isoformat()
            if document.retrieved_at
            else None,
        }
        for document in result.scalars().all()
    ]
    return {"items": items, "count": len(items)}


@router.get("/clauses")
async def list_clauses(
    session: AsyncSession = Depends(get_session),
    document_id: Optional[int] = Query(default=None),
    _: str = Depends(require_viewer),
) -> Dict[str, object]:
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
    rule_id: Optional[int] = Query(default=None),
    _: str = Depends(require_viewer),
) -> Dict[str, object]:
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
