"""Internal helpers for the vendored structlog fallback."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Iterable, MutableMapping

Processor = Callable[[logging.Logger, str, MutableMapping[str, Any]], Any]

_STATE: dict[str, Any] = {
    "processors": [],
    "wrapper_class": None,
    "logger_factory": None,
}


def set_processors(processors: Iterable[Processor]) -> None:
    """Configure the processor pipeline used by :class:`BoundLogger`."""

    _STATE["processors"] = list(processors)


def iter_processors() -> list[Processor]:
    """Return a snapshot of the configured processors."""

    return list(_STATE.get("processors", []))


def set_wrapper_class(wrapper: Callable[["BoundLogger"], "BoundLogger"] | None) -> None:
    """Record the wrapper class applied to loggers returned by :func:`get_logger`."""

    _STATE["wrapper_class"] = wrapper


def get_wrapper_class() -> Callable[["BoundLogger"], "BoundLogger"] | None:
    """Return the configured wrapper class, if any."""

    return _STATE.get("wrapper_class")


def set_logger_factory(factory: Callable[..., logging.Logger] | None) -> None:
    """Record the factory used to create standard loggers."""

    _STATE["logger_factory"] = factory


def get_logger_factory() -> Callable[..., logging.Logger] | None:
    """Return the configured logger factory, if any."""

    return _STATE.get("logger_factory")


class BoundLogger:
    """Minimal structured logger implementation compatible with the app helpers."""

    def __init__(
        self,
        name: str,
        context: MutableMapping[str, Any] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.name = name or "structlog"
        self._context: dict[str, Any] = dict(context or {})
        self._logger = logger or logging.getLogger(self.name)

    def bind(self, **kwargs: Any) -> "BoundLogger":
        """Return a new logger with the provided context merged in."""

        new_context = dict(self._context)
        new_context.update(kwargs)
        return BoundLogger(self.name, new_context, self._logger)

    def _apply_processors(self, method_name: str, event_dict: MutableMapping[str, Any]) -> Any:
        result: Any = event_dict
        for processor in iter_processors():
            result = processor(self._logger, method_name, result)
        return result

    def info(self, event: str, **kwargs: Any) -> None:
        """Emit a processed log record for ``event``."""

        event_dict: MutableMapping[str, Any] = {"event": event, **self._context, **kwargs}
        result = self._apply_processors("info", event_dict)
        if isinstance(result, dict):
            message = json.dumps(result)
        else:
            message = str(result)
        self._logger.info(message)


__all__ = [
    "BoundLogger",
    "get_logger_factory",
    "get_wrapper_class",
    "iter_processors",
    "set_logger_factory",
    "set_processors",
    "set_wrapper_class",
]
