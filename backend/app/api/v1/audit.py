"""Audit ledger API endpoints."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_viewer
from app.core.audit.ledger import diff_logs, serialise_log, verify_chain
from app.core.database import get_session
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/audit", tags=["audit"])


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
