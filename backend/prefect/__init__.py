"""Compatibility layer for Prefect stubs used in backend tests."""

from backend._vendor.prefect_shim import flow, task

__all__ = ["flow", "task"]
