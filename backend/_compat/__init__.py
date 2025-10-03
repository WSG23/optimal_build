"""Backward compatibility shims for optional runtime features."""

from .datetime import UTC  # noqa: F401
from .dataclasses import compat_dataclass  # noqa: F401

__all__ = ["UTC", "compat_dataclass"]
