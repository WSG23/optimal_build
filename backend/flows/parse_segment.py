"""Prefect flow that parses a fetched document into clauses and rules."""

from __future__ import annotations

import importlib.util
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio.session import async_sessionmaker

from app.models.rkp import RefClause, RefDocument, RefRule, RefSource
from app.services.storage import StorageConfig, StorageService
from app.utils.logging import get_logger

_PREFECT_SPEC = importlib.util.find_spec("prefect")
HAS_PREFECT = _PREFECT_SPEC is not None

if HAS_PREFECT:  # pragma: no cover
    from prefect import flow, get_run_logger, task
else:  # pragma: no cover
    def flow(*_args: Any, **_kwargs: Any):
        def decorator(func):
            return func

        return decorator

    def get_run_logger():
        return get_logger("parse-segment")

_FITZ_AVAILABLE = importlib.util.find_spec("fitz") is not None
_PDFMINER_AVAILABLE = importlib.util.find_spec("pdfminer") is not None

if _FITZ_AVAILABLE:  # pragma: no cover - heavy dependency import
    import fitz  # type: ignore

if _PDFMINER_AVAILABLE:  # pragma: no cover
    from pdfminer.high_level import extract_text as pdfminer_extract_text  # type: ignore

RULE_PATTERN = re.compile(r"(?P<param>[\w.]+)\s*(?P<operator>>=|<=|=)\s*(?P<value>[0-9.]+)\s*(?P<unit>[a-zA-Z%]+)?")


@dataclass
class ClauseCandidate:
    clause_ref: str
    text: str
    page_from: int
    page_to: int


async def _load_document_impl(
    session_factory: async_sessionmaker[AsyncSession], document_id: int
) -> Dict[str, Any]:
    async with session_factory() as session:
        document = await session.get(RefDocument, document_id)
        if document is None:
            raise ValueError(f"Document {document_id} not found")
        source = await session.get(RefSource, document.source_id)
        return {
            "document": {
                "id": document.id,
                "source_id": document.source_id,
                "storage_path": document.storage_path,
            },
            "source": {
                "jurisdiction": source.jurisdiction if source else "SG",
                "authority": source.authority if source else "Unknown",
                "topic": source.topic if source else "general",
            },
        }


if HAS_PREFECT:  # pragma: no cover
    _load_document = task(_load_document_impl)
else:

    async def _load_document(
        session_factory: async_sessionmaker[AsyncSession], document_id: int
    ) -> Dict[str, Any]:
        return await _load_document_impl(session_factory, document_id)


def _extract_text_impl(data: bytes) -> str:
    if not data:
        return ""
    if _FITZ_AVAILABLE:
        with fitz.open(stream=data, filetype="pdf") as pdf:  # type: ignore[attr-defined]
            return "\n".join(page.get_text() for page in pdf)
    if _PDFMINER_AVAILABLE:
        return pdfminer_extract_text(data)
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="ignore")


if HAS_PREFECT:  # pragma: no cover
    _extract_text = task(_extract_text_impl)
else:

    def _extract_text(data: bytes) -> str:
        return _extract_text_impl(data)


def _split_into_clauses_impl(text: str) -> List[ClauseCandidate]:
    clauses: List[ClauseCandidate] = []
    for idx, chunk in enumerate(part.strip() for part in text.split("\n\n")):
        if not chunk:
            continue
        clause_ref = f"C{idx + 1}"
        clauses.append(ClauseCandidate(clause_ref=clause_ref, text=chunk, page_from=idx + 1, page_to=idx + 1))
    return clauses


if HAS_PREFECT:  # pragma: no cover
    _split_into_clauses = task(_split_into_clauses_impl)
else:

    def _split_into_clauses(text: str) -> List[ClauseCandidate]:
        return _split_into_clauses_impl(text)


def _derive_rules_impl(clauses: Sequence[ClauseCandidate]) -> List[Dict[str, Any]]:
    rules: List[Dict[str, Any]] = []
    for clause in clauses:
        match = RULE_PATTERN.search(clause.text)
        if not match:
            continue
        payload = match.groupdict()
        rules.append(
            {
                "clause_ref": clause.clause_ref,
                "parameter_key": payload["param"],
                "operator": payload["operator"],
                "value": payload["value"],
                "unit": payload.get("unit"),
            }
        )
    return rules


if HAS_PREFECT:  # pragma: no cover
    _derive_rules = task(_derive_rules_impl)
else:

    def _derive_rules(clauses: Sequence[ClauseCandidate]) -> List[Dict[str, Any]]:
        return _derive_rules_impl(clauses)


async def _persist_impl(
    session_factory: async_sessionmaker[AsyncSession],
    document_payload: Dict[str, Any],
    source_payload: Dict[str, Any],
    clauses: Sequence[ClauseCandidate],
    rules: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    async with session_factory() as session:
        await session.execute(delete(RefClause).where(RefClause.document_id == document_payload["id"]))
        await session.execute(delete(RefRule).where(RefRule.document_id == document_payload["id"]))

        for clause in clauses:
            session.add(
                RefClause(
                    document_id=document_payload["id"],
                    clause_ref=clause.clause_ref,
                    section_heading=None,
                    text_span=clause.text,
                    page_from=clause.page_from,
                    page_to=clause.page_to,
                    extraction_quality="inferred",
                )
            )

        for rule in rules:
            session.add(
                RefRule(
                    source_id=document_payload["source_id"],
                    document_id=document_payload["id"],
                    jurisdiction=source_payload["jurisdiction"],
                    authority=source_payload["authority"],
                    topic=source_payload["topic"],
                    clause_ref=rule["clause_ref"],
                    parameter_key=rule["parameter_key"],
                    operator=rule["operator"],
                    value=rule["value"],
                    unit=rule["unit"],
                    applicability={},
                    exceptions=[],
                    source_provenance={"clause_ref": rule["clause_ref"]},
                )
            )

        await session.commit()
        return {"clauses": len(clauses), "rules": len(rules)}


if HAS_PREFECT:  # pragma: no cover
    _persist = task(_persist_impl)
else:

    async def _persist(
        session_factory: async_sessionmaker[AsyncSession],
        document_payload: Dict[str, Any],
        source_payload: Dict[str, Any],
        clauses: Sequence[ClauseCandidate],
        rules: Sequence[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return await _persist_impl(session_factory, document_payload, source_payload, clauses, rules)


async def _execute_task(task_or_fn, *args: Any, **kwargs: Any) -> Any:
    if HAS_PREFECT:
        future = task_or_fn.submit(*args, **kwargs)
        return await future.result()
    result = task_or_fn(*args, **kwargs)
    if hasattr(result, "__await__"):
        return await result  # type: ignore[arg-type]
    return result


@flow(name="parse-segment")
async def parse_segment(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    storage_config: Dict[str, Any],
    document_id: int,
) -> Dict[str, Any]:
    """Parse a document stored in object storage into rules."""

    logger = get_run_logger()
    storage = StorageService(StorageConfig(**storage_config))

    context = await _execute_task(_load_document, session_factory, document_id)
    document_payload = context["document"]
    source_payload = context["source"]

    data = storage.read_bytes(document_payload["storage_path"])
    text = await _execute_task(_extract_text, data)
    clauses = await _execute_task(_split_into_clauses, text)
    rules = await _execute_task(_derive_rules, clauses)

    persistence = await _execute_task(
        _persist,
        session_factory,
        document_payload,
        source_payload,
        clauses,
        rules,
    )

    logger.info("parsed_document", document_id=document_id, **persistence)

    return persistence
