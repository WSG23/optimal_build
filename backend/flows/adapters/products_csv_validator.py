"""Utilities for validating vendor product CSV exports."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

__all__ = ["ProductRow", "ValidationReport", "validate_csv"]


@dataclass(frozen=True)
class ProductRow:
    """Normalised representation of a single product row."""

    sku: str
    category: str
    brand: str | None = None
    model: str | None = None
    name: str | None = None
    product_code: str | None = None
    width_mm: int | None = None
    depth_mm: int | None = None
    height_mm: int | None = None
    weight_kg: float | None = None
    power_w: float | None = None
    bim_uri: str | None = None
    spec_uri: str | None = None


@dataclass
class ValidationReport:
    """Aggregate information about the CSV parsing process."""

    total: int = 0
    failed: int = 0
    errors: List[str] = field(default_factory=list)

    def model_dump(self) -> dict[str, object]:
        """Return a serialisable representation."""

        return {
            "total": self.total,
            "failed": self.failed,
            "errors": list(self.errors),
        }


def _normalise_text(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_int_field(raw: object | None) -> Tuple[int | None, str | None]:
    text = _normalise_text(raw)
    if text is None:
        return None, None
    try:
        # Allow floats in the CSV by converting via ``float`` first.
        return int(float(text)), None
    except (TypeError, ValueError):
        return None, text


def _parse_float_field(raw: object | None) -> Tuple[float | None, str | None]:
    text = _normalise_text(raw)
    if text is None:
        return None, None
    try:
        return float(text), None
    except (TypeError, ValueError):
        return None, text


def _row_from_mapping(mapping: dict[str, object], *, line: int) -> Tuple[ProductRow | None, List[str]]:
    errors: List[str] = []
    sku = _normalise_text(mapping.get("sku"))
    if not sku:
        errors.append(f"Row {line}: missing SKU")
        return None, errors

    category = _normalise_text(mapping.get("category")) or "general"
    brand = _normalise_text(mapping.get("brand"))
    model = _normalise_text(mapping.get("model") or mapping.get("model_number"))
    name = _normalise_text(mapping.get("name"))
    product_code = _normalise_text(mapping.get("product_code") or sku)

    width_mm, width_error = _parse_int_field(mapping.get("width_mm") or mapping.get("width"))
    if width_error is not None:
        errors.append(f"Row {line}: invalid width_mm value {width_error!r}")
    depth_mm, depth_error = _parse_int_field(mapping.get("depth_mm") or mapping.get("depth"))
    if depth_error is not None:
        errors.append(f"Row {line}: invalid depth_mm value {depth_error!r}")
    height_mm, height_error = _parse_int_field(mapping.get("height_mm") or mapping.get("height"))
    if height_error is not None:
        errors.append(f"Row {line}: invalid height_mm value {height_error!r}")

    weight_kg, weight_error = _parse_float_field(mapping.get("weight_kg") or mapping.get("weight"))
    if weight_error is not None:
        errors.append(f"Row {line}: invalid weight_kg value {weight_error!r}")
    power_w, power_error = _parse_float_field(mapping.get("power_w") or mapping.get("power"))
    if power_error is not None:
        errors.append(f"Row {line}: invalid power_w value {power_error!r}")

    bim_uri = _normalise_text(mapping.get("bim_uri") or mapping.get("bim"))
    spec_uri = _normalise_text(mapping.get("spec_uri") or mapping.get("spec"))

    if errors:
        return None, errors

    row = ProductRow(
        sku=sku,
        category=category,
        brand=brand,
        model=model,
        name=name,
        product_code=product_code,
        width_mm=width_mm,
        depth_mm=depth_mm,
        height_mm=height_mm,
        weight_kg=weight_kg,
        power_w=power_w,
        bim_uri=bim_uri,
        spec_uri=spec_uri,
    )
    return row, []


def validate_csv(path: Path) -> Tuple[ValidationReport, List[ProductRow]]:
    """Validate a vendor CSV file and return normalised rows."""

    errors: List[str] = []
    rows: List[ProductRow] = []
    total = 0

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            report = ValidationReport(total=0, failed=1, errors=["missing header"])
            return report, []
        for line, mapping in enumerate(reader, start=2):  # account for header row
            total += 1
            row, row_errors = _row_from_mapping(dict(mapping), line=line)
            if row_errors:
                errors.extend(row_errors)
                continue
            if row is not None:
                rows.append(row)

    report = ValidationReport(total=total, failed=len(errors), errors=errors)
    return report, rows
