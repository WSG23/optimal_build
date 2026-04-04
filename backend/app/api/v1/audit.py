"""Audit ledger API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_viewer
from app.core.audit.ledger import (
    build_evidence_report,
    diff_logs,
    serialise_log,
    verify_chain,
)
from app.core.database import get_session
from app.services.deals.utils import audit_key_from_value
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/audit", tags=["audit"])


def _resolve_audit_project_id(project_ref: str) -> int:
    project_id = audit_key_from_value(project_ref)
    if project_id is None:
        raise HTTPException(status_code=404, detail="Audit project not found")
    return project_id


@router.get("/{project_id}")
async def list_project_audit(
    project_id: int,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> dict[str, object]:
    """Return audit ledger entries for a project with validation status."""

    valid, logs = await verify_chain(session, project_id)
    items = [serialise_log(log) for log in logs]
    return {
        "project_id": project_id,
        "valid": valid,
        "count": len(items),
        "items": items,
    }


@router.get("/{project_id}/evidence")
async def project_audit_evidence(
    project_id: int,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> dict[str, object]:
    """Return an evidence-pack summary for a project's audit ledger."""

    valid, logs = await verify_chain(session, project_id)
    return build_evidence_report(project_id, valid, logs)


@router.get("/by-ref/{project_ref}/evidence")
async def project_audit_evidence_by_ref(
    project_ref: str,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> dict[str, object]:
    """Return an evidence-pack summary using a UUID/string project reference."""

    project_id = _resolve_audit_project_id(project_ref)
    valid, logs = await verify_chain(session, project_id)
    return build_evidence_report(project_id, valid, logs)


@router.get("/{project_id}/diff/{version_a}/{version_b}")
async def diff_project_audit(
    project_id: int,
    version_a: int,
    version_b: int,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> dict[str, object]:
    """Return a diff between two ledger entries for the project."""

    valid, logs = await verify_chain(session, project_id)
    lookup = {log.version: log for log in logs}
    log_a = lookup.get(version_a)
    log_b = lookup.get(version_b)
    if log_a is None or log_b is None:
        raise HTTPException(status_code=404, detail="Audit entry not found")
    diff = diff_logs(log_a, log_b)
    return {
        "project_id": project_id,
        "valid": valid,
        "version_a": serialise_log(log_a),
        "version_b": serialise_log(log_b),
        "diff": diff,
    }


__all__ = ["router"]
