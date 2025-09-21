"""Prefect flow package."""

from .ingestion import material_standard_ingestion_flow  # noqa: F401

__all__ = ["material_standard_ingestion_flow"]
