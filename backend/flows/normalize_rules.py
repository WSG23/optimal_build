"""Flow for normalising reference clauses into structured rules."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from prefect import flow
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models.rkp import RefClause, RefDocument, RefRule, RefSource
from app.services.normalize import NormalizedRule, RuleNormalizer


@flow(name="normalize-reference-rules")
async def normalize_reference_rules(
    session_factory: "async_sessionmaker[AsyncSession]",
    *,
    clause_ids: Optional[Sequence[int]] = None,
    normalizer: Optional[RuleNormalizer] = None,
) -> List[Dict[str, Any]]:
    """Generate structured rules from stored ``RefClause`` entries.

    Parameters
    ----------
    session_factory:
        Async SQLAlchemy session factory used for database interaction.
    clause_ids:
        Optional collection of clause identifiers to restrict processing to a
        subset of records. When omitted, all clauses are considered.
    normalizer:
        Optional :class:`RuleNormalizer` instance. A default instance is created
        when not provided so that callers can inject custom behaviour during
        tests.

    Returns
    -------
    list of dict
        A summary of the rules detected for each processed clause. Each entry
        contains the ``clause_id`` and the extracted ``parameter_key``.
    """

    normalizer = normalizer or RuleNormalizer()
    clause_filter = list(clause_ids) if clause_ids is not None else []
    results: List[Dict[str, Any]] = []

    async with session_factory() as session:
        stmt = _build_clause_query(clause_filter)
        clauses = (await session.execute(stmt)).scalars().all()

        for clause in clauses:
            if not clause.text_span:
                continue

            document = await session.get(RefDocument, clause.document_id)
            if document is None:
                continue

            source = await session.get(RefSource, document.source_id)
            if source is None:
                continue

            matches = normalizer.normalize(clause.text_span)
            if not matches:
                continue

            for match in matches:
                rule = await _upsert_rule(session, clause, document, source, match)
                results.append({
                    "clause_id": clause.id,
                    "parameter_key": rule.parameter_key,
                })

        await session.commit()

    return results


def _build_clause_query(clause_filter: Iterable[int]) -> Select[tuple[RefClause]]:
    stmt = select(RefClause).order_by(RefClause.id)
    ids = list(clause_filter)
    if ids:
        stmt = stmt.where(RefClause.id.in_(ids))
    return stmt


def _format_rule_value(value: Any) -> str:
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return format(value, "g")
    return str(value)


def _collect_pages(clause: RefClause) -> List[int]:
    pages: List[int] = []
    for page in (clause.page_from, clause.page_to):
        if page is None:
            continue
        page_int = int(page)
        if page_int not in pages:
            pages.append(page_int)
    return pages


def _build_provenance(clause: RefClause, document: RefDocument) -> Dict[str, Any]:
    provenance: Dict[str, Any] = {
        "document_id": document.id,
        "clause_id": clause.id,
        "document_hash": getattr(document, "file_hash", None),
    }
    pages = _collect_pages(clause)
    if pages:
        provenance["pages"] = pages
    if clause.clause_ref:
        provenance["clause_ref"] = clause.clause_ref
    if getattr(document, "version_label", None):
        provenance["document_version"] = document.version_label
    return {key: value for key, value in provenance.items() if value not in (None, [], "")}


async def _upsert_rule(
    session: AsyncSession,
    clause: RefClause,
    document: RefDocument,
    source: RefSource,
    match: NormalizedRule,
) -> RefRule:
    stmt = (
        select(RefRule)
        .where(RefRule.document_id == document.id)
        .where(RefRule.clause_ref == clause.clause_ref)
        .where(RefRule.parameter_key == match.parameter_key)
        .limit(1)
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    value = _format_rule_value(match.value)
    provenance = _build_provenance(clause, document)

    if existing:
        existing.source_id = source.id
        existing.document_id = document.id
        existing.jurisdiction = source.jurisdiction
        existing.authority = source.authority
        existing.topic = source.topic
        existing.clause_ref = clause.clause_ref
        existing.operator = match.operator
        existing.value = value
        existing.unit = match.unit
        existing.applicability = match.context or {}
        existing.source_provenance = provenance
        return existing

    rule = RefRule(
        source_id=source.id,
        document_id=document.id,
        jurisdiction=source.jurisdiction,
        authority=source.authority,
        topic=source.topic,
        clause_ref=clause.clause_ref,
        parameter_key=match.parameter_key,
        operator=match.operator,
        value=value,
        unit=match.unit,
        applicability=match.context or {},
        source_provenance=provenance,
        review_status="needs_review",
    )
    session.add(rule)
    return rule


__all__ = ["normalize_reference_rules"]
