"""Lightweight Prefect flow shim used in offline environments."""

from backend._vendor.prefect_shim import flow, task

__all__ = ["flow", "task"]
