"""Minimal structlog stubs for offline testing."""

from __future__ import annotations

from typing import Any, Callable


class _ProcessorsModule:
    def add_log_level(self, logger: Any, name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        return event_dict

    def StackInfoRenderer(self) -> "_ProcessorCallable":  # noqa: D401 - stub
        return _ProcessorCallable()

    def format_exc_info(self, logger: Any, name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        return event_dict

    def JSONRenderer(self) -> "_ProcessorCallable":  # noqa: D401 - stub
        return _ProcessorCallable()

    class TimeStamper:
        def __init__(self, fmt: str, utc: bool = False) -> None:
            self.fmt = fmt
            self.utc = utc

        def __call__(self, logger: Any, name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
            return event_dict


class _ProcessorCallable:
    def __call__(self, logger: Any, name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        return event_dict


processors = _ProcessorsModule()


class BoundLogger:
    def __init__(self, name: str | None = None) -> None:
        self.name = name
        self._context: dict[str, Any] = {}

    def bind(self, **kwargs: Any) -> "BoundLogger":
        self._context.update(kwargs)
        return self

    def info(self, event: str, **kwargs: Any) -> None:  # pragma: no cover - stub
        return None


class LoggerFactory:
    def __call__(self, *args: Any, **kwargs: Any) -> "BoundLogger":
        return BoundLogger()


class stdlib:
    BoundLogger = BoundLogger
    LoggerFactory = LoggerFactory


def configure(**kwargs: Any) -> None:  # pragma: no cover - stub
    return None


def make_filtering_bound_logger(
    level: int,
) -> Callable[[BoundLogger], BoundLogger]:  # pragma: no cover - stub
    def _wrapper(logger: BoundLogger) -> BoundLogger:
        return logger

    return _wrapper


def get_logger(name: str | None = None) -> BoundLogger:
    return BoundLogger(name)


__all__ = [
    "BoundLogger",
    "LoggerFactory",
    "configure",
    "get_logger",
    "make_filtering_bound_logger",
    "processors",
    "stdlib",
]
