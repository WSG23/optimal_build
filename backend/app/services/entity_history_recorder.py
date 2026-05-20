"""Automatic ``entity_history`` writer.

Registers per-mapper ``after_insert`` / ``after_update`` / ``after_delete``
SQLAlchemy listeners on the tracked core tables (``properties``,
``projects``, ``fin_scenarios``, ``users``). Each listener writes a single
``entity_history`` row using the same ``connection`` that fired the change,
so the audit row commits inside the originating transaction or rolls back
with it — no orphans, no dual-write risk.

Why mapper-level rather than session ``before_flush``: integer-autoincrement
primary keys (``FinScenario``) are only assigned after the INSERT statement,
and even UUID column defaults are evaluated mid-flush. Mapper ``after_*``
events fire once the row is in the database, so the ``entity_id`` is stable.

Writers don't need to know this exists — touching one of the tracked rows is
sufficient. Attribution metadata (``user``, ``reason``, ``request_id``) can
be attached by the caller via ``session.info``:

    session.info["changed_by"] = current_user.id
    session.info["reason"] = "user_correction"
    session.info["request_id"] = request_id

The mapper events propagate ``session.info`` via a per-connection contextvar
populated on ``before_flush``. If nothing is set the attribution columns are
``NULL`` for that mutation rather than blocking the write.
"""

from __future__ import annotations

import logging
import uuid as uuid_module
from contextvars import ContextVar
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Mapping

from sqlalchemy import event, func, inspect, select
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Mapper, Session

from app.models.entity_history import EntityHistory
from app.models.finance import FinScenario
from app.models.projects import Project
from app.models.property import Property
from app.models.users import User

logger = logging.getLogger(__name__)

TRACKED_MODELS: tuple[type, ...] = (Property, Project, FinScenario, User)

_REGISTERED = False
_current_attribution: ContextVar[Mapping[str, Any] | None] = ContextVar(
    "entity_history_attribution", default=None
)


def _serialize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, uuid_module.UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    return str(value)


def _snapshot(obj: Any) -> dict[str, Any]:
    table = getattr(obj, "__table__", None)
    if table is None:
        return {}
    return {
        col.name: _serialize_value(getattr(obj, col.name, None))
        for col in table.columns
    }


def _diff_update(obj: Any) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    state = inspect(obj)
    before: dict[str, Any] = {}
    after: dict[str, Any] = {}
    changed: list[str] = []
    for attr in state.attrs:
        hist = attr.history
        if not hist.has_changes():
            continue
        changed.append(attr.key)
        old = hist.deleted[0] if hist.deleted else None
        new = hist.added[0] if hist.added else getattr(obj, attr.key, None)
        before[attr.key] = _serialize_value(old)
        after[attr.key] = _serialize_value(new)
    return before, after, changed


def _next_version(connection: Connection, entity_type: str, entity_id: str) -> int:
    result = connection.execute(
        select(func.coalesce(func.max(EntityHistory.version), 0))
        .where(EntityHistory.entity_type == entity_type)
        .where(EntityHistory.entity_id == entity_id)
    ).scalar()
    return int(result or 0) + 1


def _attribution() -> Mapping[str, Any]:
    attr = _current_attribution.get()
    if attr is None:
        return {}
    return attr


def _write_history(
    connection: Connection,
    obj: Any,
    operation: str,
    *,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
    changed_fields: list[str] | None,
) -> None:
    entity_type = obj.__tablename__
    raw_id = getattr(obj, "id", None)
    if raw_id is None:
        # Should not happen for mapper after_* events; defend against weird
        # cases (e.g. composite PKs) by skipping rather than crashing.
        logger.debug("entity_history: skipping %s (no id)", entity_type)
        return
    entity_id = str(_serialize_value(raw_id))
    version = _next_version(connection, entity_type, entity_id)
    attribution = _attribution()

    connection.execute(
        EntityHistory.__table__.insert().values(
            entity_type=entity_type,
            entity_id=entity_id,
            version=version,
            operation=operation,
            before=before,
            after=after,
            changed_fields=changed_fields,
            organization_id=_serialize_value(getattr(obj, "organization_id", None)),
            changed_by=attribution.get("changed_by"),
            changed_by_label=attribution.get("changed_by_label"),
            reason=attribution.get("reason"),
            request_id=attribution.get("request_id"),
        )
    )


def _make_after_insert(model: type) -> Any:
    def _handler(_mapper: Mapper, connection: Connection, target: Any) -> None:
        _write_history(
            connection,
            target,
            "insert",
            before=None,
            after=_snapshot(target),
            changed_fields=None,
        )

    return _handler


def _make_after_update(model: type) -> Any:
    def _handler(_mapper: Mapper, connection: Connection, target: Any) -> None:
        before, after, changed = _diff_update(target)
        if not changed:
            return
        _write_history(
            connection,
            target,
            "update",
            before=before,
            after=after,
            changed_fields=changed,
        )

    return _handler


def _make_after_delete(model: type) -> Any:
    def _handler(_mapper: Mapper, connection: Connection, target: Any) -> None:
        _write_history(
            connection,
            target,
            "delete",
            before=_snapshot(target),
            after=None,
            changed_fields=None,
        )

    return _handler


def _capture_attribution_from_session(
    session: Session, _flush_context: Any, _instances: Any
) -> None:
    """Lift ``session.info`` attribution into the contextvar for the flush.

    The mapper-level ``after_*`` events don't have direct access to the
    ``Session``; this listener publishes the relevant ``session.info`` keys
    onto a contextvar so the per-row writers can read them.
    """

    info = session.info or {}
    _current_attribution.set(
        {
            "changed_by": info.get("changed_by"),
            "changed_by_label": info.get("changed_by_label"),
            "reason": info.get("reason"),
            "request_id": info.get("request_id"),
        }
    )


def register_entity_history_recorder() -> None:
    """Idempotently attach mapper + session listeners for tracked models."""

    global _REGISTERED
    if _REGISTERED:
        return

    event.listen(Session, "before_flush", _capture_attribution_from_session)

    for model in TRACKED_MODELS:
        event.listen(model, "after_insert", _make_after_insert(model))
        event.listen(model, "after_update", _make_after_update(model))
        event.listen(model, "after_delete", _make_after_delete(model))

    _REGISTERED = True
    logger.debug(
        "entity_history recorder registered for: %s",
        [m.__name__ for m in TRACKED_MODELS],
    )


# Register on import so any process that imports this module gets coverage.
register_entity_history_recorder()


__all__ = [
    "TRACKED_MODELS",
    "register_entity_history_recorder",
]
