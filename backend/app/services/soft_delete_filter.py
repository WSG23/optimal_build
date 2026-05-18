"""Session-level soft-delete query filter.

Without this filter, a SELECT on ``properties`` would return logically-deleted
rows by default — callers would have to remember to add
``WHERE deleted_at IS NULL`` on every query, and forgetting it silently
exposes tombstoned data.

We attach a SQLAlchemy ``do_orm_execute`` Session event that injects a
``with_loader_criteria`` predicate for each tracked model so the filter is
applied automatically.

To bypass the filter (admin tools, restore flows, audit), set::

    session.info["include_deleted"] = True

before issuing the query. The flag is read once per execution; turning it on
mid-session, then off, behaves as expected.
"""

from __future__ import annotations

import logging

from sqlalchemy import event
from sqlalchemy.orm import Session, with_loader_criteria

from app.models.documents import Document
from app.models.finance import FinScenario
from app.models.projects import Project
from app.models.property import Property
from app.models.users import User

logger = logging.getLogger(__name__)

# Tables that have ``deleted_at`` and should be filtered by default.
SOFT_DELETE_MODELS: tuple[type, ...] = (
    Property,
    Project,
    FinScenario,
    User,
    Document,
)

_REGISTERED = False


def _on_orm_execute(orm_execute_state):
    """Apply ``deleted_at IS NULL`` to every SELECT against tracked models."""

    if not orm_execute_state.is_select:
        return
    info = (
        orm_execute_state.session.info if orm_execute_state.session is not None else {}
    )
    if info.get("include_deleted"):
        return
    # Per-statement opt-out is also useful for ad-hoc queries:
    #     stmt = select(Property).execution_options(include_deleted=True)
    if orm_execute_state.execution_options.get("include_deleted"):
        return

    for model in SOFT_DELETE_MODELS:
        orm_execute_state.statement = orm_execute_state.statement.options(
            with_loader_criteria(
                model,
                lambda cls: cls.deleted_at.is_(None),
                include_aliases=True,
            )
        )


def register_soft_delete_filter() -> None:
    """Idempotently attach the ``do_orm_execute`` listener."""

    global _REGISTERED
    if _REGISTERED:
        return
    event.listen(Session, "do_orm_execute", _on_orm_execute)
    _REGISTERED = True
    logger.debug(
        "soft-delete filter registered for: %s",
        [m.__name__ for m in SOFT_DELETE_MODELS],
    )


# Register on import so any process that imports this module gets coverage.
register_soft_delete_filter()


__all__ = [
    "SOFT_DELETE_MODELS",
    "register_soft_delete_filter",
]
