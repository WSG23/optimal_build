"""Audit ledger helpers for append-only hash chains."""

from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from backend._compat.datetime import UTC

from app.core.config import settings
from app.models.audit import AuditLog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def _as_utc(timestamp: datetime | None) -> datetime | None:
    """Return a timezone-aware UTC timestamp suitable for hashing."""

    if timestamp is None:
        return None
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=UTC)
    return timestamp.astimezone(UTC)


def _coerce_float(value: Any) -> float | None:
    """Normalise numeric values to floats for hashing and storage."""

    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive guard
        raise TypeError(f"Expected numeric value, received {value!r}") from exc


def _normalise_context(context: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a JSON-serialisable dictionary for the event context."""

    if context is None:
        return {}
    return {str(key): value for key, value in dict(context).items()}


def _payload_for_hash(log: AuditLog) -> dict[str, Any]:
    """Build a canonical payload for hashing and signing."""

    recorded_at = _as_utc(log.recorded_at)
    timestamp = recorded_at.isoformat() if recorded_at else None
    payload = {
        "project_id": int(log.project_id),
        "version": int(log.version),
        "event_type": log.event_type,
        "baseline_seconds": _coerce_float(log.baseline_seconds),
        "actual_seconds": _coerce_float(log.actual_seconds),
        "context": _normalise_context(log.context),
        "recorded_at": timestamp,
        "prev_hash": log.prev_hash or "",
    }
    return payload


def compute_event_hash(payload: Mapping[str, Any]) -> str:
    """Compute a SHA-256 hash for the supplied payload."""

    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _sign_hash(hash_value: str) -> str:
    """Return an HMAC signature over ``hash_value`` using the app secret."""

    secret = settings.SECRET_KEY.encode("utf-8")
    digest = hmac.new(secret, hash_value.encode("utf-8"), hashlib.sha256)
    return digest.hexdigest()


async def _latest_entry(session: AsyncSession, project_id: int) -> AuditLog | None:
    """Fetch the most recent audit entry for ``project_id``."""

    stmt = (
        select(AuditLog)
        .where(AuditLog.project_id == project_id)
        .order_by(AuditLog.version.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def append_event(
    session: AsyncSession,
    *,
    project_id: int,
    event_type: str,
    baseline_seconds: float | None = None,
    actual_seconds: float | None = None,
    context: Mapping[str, Any] | None = None,
    recorded_at: datetime | None = None,
) -> AuditLog:
    """Append an event to the project audit ledger and return the stored row."""

    previous = await _latest_entry(session, project_id)
    version = 1 if previous is None else previous.version + 1
    prev_hash = previous.hash if previous is not None else None
    timestamp = _as_utc(recorded_at) or datetime.now(UTC)

    normalised_context = _normalise_context(context)
    log = AuditLog(
        project_id=project_id,
        event_type=event_type,
        baseline_seconds=_coerce_float(baseline_seconds),
        actual_seconds=_coerce_float(actual_seconds),
        context=normalised_context,
        recorded_at=timestamp,
        version=version,
        prev_hash=prev_hash,
    )
    payload = _payload_for_hash(log)
    log.hash = compute_event_hash(payload)
    log.signature = _sign_hash(log.hash)

    session.add(log)
    await session.flush()
    return log


def serialise_log(log: AuditLog) -> dict[str, Any]:
    """Convert an :class:`AuditLog` row into an API friendly dictionary."""

    recorded_at = log.recorded_at.isoformat() if log.recorded_at else None
    return {
        "id": log.id,
        "project_id": log.project_id,
        "event_type": log.event_type,
        "version": log.version,
        "baseline_seconds": _coerce_float(log.baseline_seconds),
        "actual_seconds": _coerce_float(log.actual_seconds),
        "context": _normalise_context(log.context),
        "recorded_at": recorded_at,
        "hash": log.hash,
        "prev_hash": log.prev_hash,
        "signature": log.signature,
    }


def build_evidence_report(
    project_id: int, valid: bool, logs: list[AuditLog]
) -> dict[str, Any]:
    """Assemble an evidence-oriented summary for a project's audit ledger."""

    event_counts: dict[str, int] = {}
    exports: list[dict[str, Any]] = []
    imports: list[dict[str, Any]] = []
    recipients: set[str] = set()
    scenario_events: list[dict[str, Any]] = []
    finance_events: list[dict[str, Any]] = []
    submission_events: list[dict[str, Any]] = []

    for log in logs:
        event_counts[log.event_type] = event_counts.get(log.event_type, 0) + 1
        context = _normalise_context(log.context)
        recorded_at = log.recorded_at.isoformat() if log.recorded_at else None

        for key in ("recipient", "recipient_email", "shared_with"):
            value = context.get(key)
            if isinstance(value, str) and value.strip():
                recipients.add(value.strip())
        for key in ("recipients", "recipient_emails"):
            value = context.get(key)
            if isinstance(value, list):
                recipients.update(
                    item.strip()
                    for item in value
                    if isinstance(item, str) and item.strip()
                )

        if log.event_type == "export_generated":
            exports.append(
                {
                    "version": log.version,
                    "recorded_at": recorded_at,
                    "format": context.get("format"),
                    "export_type": context.get("export_type"),
                    "scenario_id": context.get("scenario_id"),
                    "scenario_name": context.get("scenario_name"),
                    "accepted_suggestions": context.get("accepted_suggestions"),
                    "include_pending": context.get("include_pending"),
                    "include_rejected": context.get("include_rejected"),
                }
            )
        if log.event_type == "workbook_imported":
            imports.append(
                {
                    "version": log.version,
                    "recorded_at": recorded_at,
                    "format": context.get("format"),
                    "workbook_format": context.get("workbook_format"),
                    "scenario_id": context.get("scenario_id"),
                    "scenario_name": context.get("scenario_name"),
                    "asset_count": context.get("asset_count"),
                }
            )

        scenario_name = context.get("scenario_name") or context.get("scenario")
        scenario_id = context.get("scenario_id")
        if scenario_name or scenario_id is not None:
            scenario_events.append(
                {
                    "version": log.version,
                    "event_type": log.event_type,
                    "scenario_name": scenario_name,
                    "scenario_id": scenario_id,
                    "origin": context.get("origin"),
                    "recorded_at": recorded_at,
                }
            )

        if log.event_type == "finance_scenario_created":
            finance_events.append(
                {
                    "version": log.version,
                    "recorded_at": recorded_at,
                    "scenario_id": context.get("scenario_id"),
                    "scenario_name": context.get("scenario_name"),
                    "origin": context.get("origin"),
                    "currency": context.get("currency"),
                    "is_primary": context.get("is_primary"),
                    "has_asset_mix": context.get("has_asset_mix"),
                    "has_capital_stack": context.get("has_capital_stack"),
                    "has_sensitivity_bands": context.get("has_sensitivity_bands"),
                }
            )

        if any(
            key in context
            for key in (
                "agency",
                "submission_no",
                "submission_number",
                "submission_type",
                "package_status",
                "submission_mode",
            )
        ):
            submission_events.append(
                {
                    "version": log.version,
                    "event_type": log.event_type,
                    "recorded_at": recorded_at,
                    "agency": context.get("agency"),
                    "agency_name": context.get("agency_name"),
                    "submission_no": context.get("submission_no")
                    or context.get("submission_number"),
                    "submission_type": context.get("submission_type"),
                    "status": context.get("status"),
                    "submission_mode": context.get("submission_mode"),
                    "package_status": context.get("package_status"),
                }
            )

    first_log = logs[0] if logs else None
    last_log = logs[-1] if logs else None
    event_type_summary = [
        {"event_type": event_type, "count": count}
        for event_type, count in sorted(event_counts.items())
    ]
    return {
        "project_id": project_id,
        "valid": valid,
        "report_generated_at": datetime.now(UTC).isoformat(),
        "timeframe": {
            "first_recorded_at": (
                first_log.recorded_at.isoformat() if first_log and first_log.recorded_at else None
            ),
            "last_recorded_at": (
                last_log.recorded_at.isoformat() if last_log and last_log.recorded_at else None
            ),
        },
        "chain": {
            "entry_count": len(logs),
            "signed_entries": sum(1 for log in logs if log.signature),
            "latest_hash": last_log.hash if last_log else None,
        },
        "event_types": event_type_summary,
        "exports": exports,
        "imports": imports,
        "recipients": sorted(recipients),
        "scenario_events": scenario_events,
        "finance_events": finance_events,
        "submission_events": submission_events,
    }


def _diff_value(value_a: Any, value_b: Any) -> dict[str, Any] | None:
    """Return a diff structure describing the change between two scalars."""

    if value_a == value_b:
        return None
    return {"from": value_a, "to": value_b}


def _diff_context(
    context_a: Mapping[str, Any], context_b: Mapping[str, Any]
) -> dict[str, dict[str, Any]]:
    """Compute added/removed/changed keys between two context payloads."""

    added: dict[str, Any] = {}
    removed: dict[str, Any] = {}
    changed: dict[str, dict[str, Any]] = {}

    for key, value in context_b.items():
        if key not in context_a:
            added[key] = value
        elif context_a[key] != value:
            changed[key] = {"from": context_a[key], "to": value}
    for key, value in context_a.items():
        if key not in context_b:
            removed[key] = value

    return {"added": added, "removed": removed, "changed": changed}


def diff_logs(log_a: AuditLog, log_b: AuditLog) -> dict[str, Any]:
    """Return a structured diff between two audit log entries."""

    context_a = _normalise_context(log_a.context)
    context_b = _normalise_context(log_b.context)
    diff = {
        "event_type": _diff_value(log_a.event_type, log_b.event_type),
        "baseline_seconds": _diff_value(
            _coerce_float(log_a.baseline_seconds), _coerce_float(log_b.baseline_seconds)
        ),
        "actual_seconds": _diff_value(
            _coerce_float(log_a.actual_seconds), _coerce_float(log_b.actual_seconds)
        ),
        "context": _diff_context(context_a, context_b),
    }
    return diff


async def verify_chain(
    session: AsyncSession, project_id: int
) -> tuple[bool, list[AuditLog]]:
    """Validate the audit chain for ``project_id`` and return ordered entries."""

    stmt = (
        select(AuditLog)
        .where(AuditLog.project_id == project_id)
        .order_by(AuditLog.version)
    )
    result = await session.execute(stmt)
    logs = list(result.scalars().all())

    previous_hash = None
    for log in logs:
        expected_payload = _payload_for_hash(log)
        expected_hash = compute_event_hash(expected_payload)
        expected_signature = _sign_hash(expected_hash)
        if log.prev_hash != previous_hash:
            return False, logs
        if log.hash != expected_hash:
            return False, logs
        if log.signature != expected_signature:
            return False, logs
        previous_hash = log.hash

    return True, logs
