"""Rule normalization and query helpers."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

import importlib.util
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rkp import RefClause, RefDocument, RefRule, RefSource
from app.utils.logging import get_logger

_PINT_SPEC = importlib.util.find_spec("pint")
if _PINT_SPEC is not None:  # pragma: no cover
    from pint import UnitRegistry  # type: ignore
else:  # pragma: no cover
    UnitRegistry = None  # type: ignore

logger = get_logger(__name__)


class RuleService:
    """High-level read service for rules and clauses."""

    def __init__(self, session: AsyncSession, unit_registry: Optional[UnitRegistry] = None) -> None:
        self._session = session
        if UnitRegistry is not None:
            self._ureg = unit_registry or UnitRegistry()
        else:
            self._ureg = None

    async def search(
        self,
        *,
        query: Optional[str] = None,
        authority: Optional[str] = None,
        topic: Optional[str] = None,
        parameter_key: Optional[str] = None,
        limit: int = 25,
    ) -> List[Dict[str, object]]:
        stmt = select(RefRule).order_by(RefRule.parameter_key).limit(limit)
        if authority:
            stmt = stmt.where(RefRule.authority == authority)
        if topic:
            stmt = stmt.where(RefRule.topic == topic)
        if parameter_key:
            stmt = stmt.where(RefRule.parameter_key == parameter_key)
        if query:
            like = f"%{query.lower()}%"
            stmt = stmt.where(func.lower(RefRule.parameter_key).like(like))

        result = await self._session.scalars(stmt)
        rules = result.all()
        logger.info("rule_search", query=query, authority=authority, topic=topic, count=len(rules))
        return [await self._normalize(rule) for rule in rules]

    async def rules_by_clause(self, clause_ref: str) -> Dict[str, List[Dict[str, object]]]:
        stmt = select(RefRule).where(RefRule.clause_ref == clause_ref)
        result = await self._session.scalars(stmt)
        grouped: Dict[str, List[Dict[str, object]]] = defaultdict(list)
        for rule in result:
            grouped[rule.parameter_key].append(await self._normalize(rule))
        return grouped

    async def snapshot(self, *, topic: Optional[str] = None) -> Dict[str, object]:
        stmt = select(RefRule)
        if topic:
            stmt = stmt.where(RefRule.topic == topic)
        result = await self._session.scalars(stmt)
        rules = result.all()

        by_authority: Dict[str, int] = defaultdict(int)
        for rule in rules:
            by_authority[rule.authority] += 1

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "total_rules": len(rules),
            "by_authority": dict(by_authority),
            "rules": [await self._normalize(rule) for rule in rules],
        }

    async def _normalize(self, rule: RefRule) -> Dict[str, object]:
        normalized_value = self._normalize_value(rule.value, rule.unit)
        source = None
        if rule.source_id:
            source = await self._session.get(RefSource, rule.source_id)
        document = None
        if rule.document_id:
            document = await self._session.get(RefDocument, rule.document_id)
        clause = None
        if rule.document_id and rule.clause_ref:
            clause = await self._session.scalar(
                select(RefClause).where(
                    RefClause.document_id == rule.document_id, RefClause.clause_ref == rule.clause_ref
                )
            )

        provenance = {
            "source_id": rule.source_id,
            "document_id": rule.document_id,
            "clause_ref": rule.clause_ref,
            "source_provenance": rule.source_provenance or {},
        }
        if source:
            provenance.update({
                "source_title": source.doc_title,
                "source_authority": source.authority,
            })
        if document:
            provenance.update({
                "document_version": document.version_label,
                "storage_path": document.storage_path,
            })
        if clause:
            provenance.update({
                "clause_heading": clause.section_heading,
                "clause_text": clause.text_span,
            })

        normalized = {
            "id": rule.id,
            "jurisdiction": rule.jurisdiction,
            "authority": rule.authority,
            "topic": rule.topic,
            "clause_ref": rule.clause_ref,
            "parameter_key": rule.parameter_key,
            "operator": rule.operator,
            "value": rule.value,
            "unit": rule.unit,
            "value_normalized": normalized_value,
            "applicability": rule.applicability or {},
            "exceptions": rule.exceptions or [],
            "review_status": rule.review_status,
            "provenance": provenance,
        }
        return normalized

    def _normalize_value(self, raw_value: str, unit: Optional[str]) -> Optional[float]:
        if raw_value is None:
            return None
        try:
            if unit:
                if self._ureg is not None:
                    quantity = (
                        self._ureg(raw_value)
                        if not isinstance(raw_value, str) or not raw_value.replace(".", "", 1).isdigit()
                        else float(raw_value) * self._ureg(unit)
                    )
                    return quantity.to_base_units().magnitude
                if isinstance(raw_value, str) and raw_value.replace(".", "", 1).isdigit():
                    magnitude = float(raw_value)
                else:
                    magnitude = float(raw_value)
                unit_lower = unit.lower()
                conversion = {"mm": 0.001, "millimeter": 0.001, "millimeters": 0.001, "m": 1.0, "meter": 1.0, "meters": 1.0}
                factor = conversion.get(unit_lower, 1.0)
                return magnitude * factor
            return float(raw_value)
        except Exception:
            return None
