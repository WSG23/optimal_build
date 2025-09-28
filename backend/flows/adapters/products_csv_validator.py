"""Utilities for validating vendor product CSV files."""

from __future__ import annotations

import csv
import datetime as dt
from collections.abc import Iterator, Mapping
from pathlib import Path

from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    ValidationError,
    confloat,
    conint,
    field_validator,
)


class ProductRow(BaseModel):
    """Representation of a product row within the vendor CSV."""

    brand: str
    model: str
    sku: str
    category: str
    width_mm: conint(ge=0)
    depth_mm: conint(ge=0)
    height_mm: conint(ge=0)
    weight_kg: confloat(ge=0) | None = None
    power_w: confloat(ge=0) | None = None
    bim_uri: HttpUrl | None = None
    spec_uri: HttpUrl | None = None

    model_config = {"extra": "ignore"}

    @field_validator("brand", "model", "sku", "category", mode="before")
    @classmethod
    def _validate_required_text(cls, value: object) -> str:
        """Ensure required text fields contain non-empty strings."""

        if value is None:
            raise ValueError("field required")
        if isinstance(value, str):
            value = value.strip()
        text = str(value)
        if not text:
            raise ValueError("field required")
        return text

    @field_validator("width_mm", "depth_mm", "height_mm", mode="before")
    @classmethod
    def _ensure_numeric(cls, value: object) -> object:
        """Reject empty numeric fields so Pydantic can coerce the value."""

        if value in {"", None}:
            raise ValueError("value is required")
        return value


class ValidationReport(BaseModel):
    """Summary of a CSV validation run."""

    generated_at: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.UTC))
    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: list[str] = Field(default_factory=list)


def read_csv(path: Path) -> Iterator[Mapping[str, str | None]]:
    """Yield rows from a CSV file as dictionaries.

    Blank rows are skipped to avoid generating spurious validation errors.
    """

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if not row:
                continue
            if all(
                (value is None or str(value).strip() == "") for value in row.values()
            ):
                continue
            yield {
                key: value.strip() if isinstance(value, str) else value
                for key, value in row.items()
            }


def _format_validation_error(line_number: int, error: ValidationError) -> str:
    """Convert a :class:`ValidationError` into a human-readable message."""

    details = []
    for err in error.errors():
        location = "".join(str(part) for part in err.get("loc", ()))
        message = err.get("msg", "invalid value")
        if location:
            details.append(f"{location}: {message}")
        else:
            details.append(message)
    joined = "; ".join(details)
    return (
        f"line {line_number}: {joined}"
        if joined
        else f"line {line_number}: invalid row"
    )


def validate_csv(path: Path) -> tuple[ValidationReport, list[ProductRow]]:
    """Validate the CSV file at ``path``.

    The function returns both a :class:`ValidationReport` containing aggregate
    statistics and a list of the successfully validated :class:`ProductRow`
    instances.
    """

    report = ValidationReport()
    valid: list[ProductRow] = []
    for line_number, row in enumerate(read_csv(path), start=2):
        report.total += 1
        try:
            model = ProductRow.model_validate(row)
        except ValidationError as exc:  # pragma: no cover - exercised in tests
            report.failed += 1
            report.errors.append(_format_validation_error(line_number, exc))
        else:
            report.passed += 1
            valid.append(model)
    return report, valid


__all__ = [
    "ProductRow",
    "ValidationReport",
    "read_csv",
    "validate_csv",
]
