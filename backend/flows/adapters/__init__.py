"""Adapters for flow inputs."""

from .products_csv_validator import ProductRow, ValidationReport, validate_csv

__all__ = ["ProductRow", "ValidationReport", "validate_csv"]
