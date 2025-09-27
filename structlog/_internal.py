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

    def new(self, **kwargs: Any) -> "BoundLogger":
        """Return a new logger using *kwargs* as the complete context."""

        return BoundLogger(self.name, dict(kwargs), self._logger)

    def unbind(self, *keys: str) -> "BoundLogger":
        """Return a new logger without the specified context keys."""

        new_context = {
            key: value for key, value in self._context.items() if key not in keys
        }
        return BoundLogger(self.name, new_context, self._logger)

    def _apply_processors(
        self, method_name: str, event_dict: MutableMapping[str, Any]
    ) -> Any:
        result: Any = event_dict
        for processor in iter_processors():
            result = processor(self._logger, method_name, result)
        return result

    def _prepare_event(
        self, method_name: str, event: str, kwargs: MutableMapping[str, Any]
    ) -> tuple[str, Any]:
        event_dict: MutableMapping[str, Any] = {
            "event": event,
            **self._context,
            **kwargs,
        }
        processed = self._apply_processors(method_name, event_dict)
        exc_info: Any | None = None
        if isinstance(processed, dict):
            payload = dict(processed)
            exc_info = payload.pop("exc_info", None)
            message = json.dumps(payload)
        else:
            message = str(processed)
        return message, exc_info

    def _log(self, method_name: str, event: str, **kwargs: Any) -> None:
        message, exc_info = self._prepare_event(method_name, event, kwargs)
        log_method = getattr(self._logger, method_name, None)
        log_kwargs: dict[str, Any] = {}
        if method_name == "exception" and exc_info is None:
            exc_info = True
        if exc_info is not None:
            log_kwargs["exc_info"] = exc_info

        if callable(log_method):
            log_method(message, **log_kwargs)
        else:
            level_name = "ERROR" if method_name == "exception" else method_name.upper()
            level = getattr(logging, level_name, logging.INFO)
            self._logger.log(level, message, **log_kwargs)

    def debug(self, event: str, **kwargs: Any) -> None:
        self._log("debug", event, **kwargs)

    def info(self, event: str, **kwargs: Any) -> None:
        self._log("info", event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._log("warning", event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._log("error", event, **kwargs)

    def exception(self, event: str, **kwargs: Any) -> None:
        self._log("exception", event, **kwargs)

    def critical(self, event: str, **kwargs: Any) -> None:
        self._log("critical", event, **kwargs)


__all__ = [
    "BoundLogger",
    "get_logger_factory",
    "get_wrapper_class",
    "iter_processors",
    "set_logger_factory",
    "set_processors",
    "set_wrapper_class",
]
