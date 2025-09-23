"""Vendored fallback providing a tiny subset of :mod:`structlog`."""

from __future__ import annotations

import logging
from typing import Any, Callable, Iterable

from . import processors, stdlib
from ._internal import (
    BoundLogger,
    get_logger_factory,
    get_wrapper_class,
    set_logger_factory,
    set_processors,
    set_wrapper_class,
)

__all__ = [
    "configure",
    "get_logger",
    "make_filtering_bound_logger",
    "processors",
    "stdlib",
]

_IS_VENDORED_STRUCTLOG = True


def configure(
    *,
    processors: Iterable[Callable[[logging.Logger, str, Any], Any]] | None = None,
    wrapper_class: Callable[[BoundLogger], BoundLogger] | None = None,
    logger_factory: Callable[..., logging.Logger] | None = None,
    **_: Any,
) -> None:
    """Capture the configuration expected by :func:`app.utils.logging.configure_logging`."""

    set_processors(processors or [])
    set_wrapper_class(wrapper_class)
    set_logger_factory(logger_factory)


def get_logger(name: str | None = None) -> BoundLogger:
    """Return a structured logger compatible with the application's expectations."""

    factory = get_logger_factory()
    base_logger: logging.Logger | None = None
    if callable(factory):
        try:
            base_logger = factory(name)
        except TypeError:
            base_logger = factory()
    if base_logger is None:
        base_logger = logging.getLogger(name)
    bound = BoundLogger(name or base_logger.name, logger=base_logger)
    wrapper = get_wrapper_class()
    if callable(wrapper):
        bound = wrapper(bound)
    return bound


def make_filtering_bound_logger(_: int) -> Callable[[BoundLogger], BoundLogger]:
    """Return a wrapper that leaves the provided logger unchanged."""

    def _wrapper(logger: BoundLogger) -> BoundLogger:
        return logger

    return _wrapper
