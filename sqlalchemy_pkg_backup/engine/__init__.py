"""Engine related placeholders for the SQLAlchemy stub."""

from __future__ import annotations

__all__ = ["Connection"]


class Connection:
    """Placeholder for :class:`sqlalchemy.engine.Connection`."""

    def run_sync(self, fn, *args, **kwargs):  # noqa: D401 - simple passthrough
        raise RuntimeError("SQLAlchemy is required to use Connection.run_sync")
