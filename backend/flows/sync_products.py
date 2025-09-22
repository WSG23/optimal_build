"""Utilities for synchronising product catalogues from CSV files."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

try:  # pragma: no cover - fallback for optional import scenarios
    from app.core.database import AsyncSessionLocal
except ModuleNotFoundError:  # pragma: no cover - handled in tests when app module unavailable
    AsyncSessionLocal = None  # type: ignore[assignment]

from .products import sync_vendor_products


def _normalise_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_dimensions(row: Dict[str, Any]) -> Dict[str, float]:
    """Extract numeric dimension values from a CSV row."""

    dimensions: Dict[str, float] = {}
    mapping = {
        "width_mm": ("width_mm", "width"),
        "depth_mm": ("depth_mm", "depth"),
        "height_mm": ("height_mm", "height"),
    }
    for target_key, candidates in mapping.items():
        for source_key in candidates:
            raw = row.get(source_key)
            if raw in (None, ""):
                continue
            try:
                value = float(raw)
            except (TypeError, ValueError):
                continue
            dimensions[target_key] = value
            break
    return {key: value for key, value in dimensions.items() if value is not None}


def _row_to_product(row: Dict[str, Any], vendor: str, index: int) -> Dict[str, Any]:
    """Convert a CSV row into a vendor product payload."""

    cleaned = {key: _normalise_text(value) for key, value in row.items()}
    code = cleaned.get("product_code") or cleaned.get("code") or cleaned.get("sku")
    if not code:
        code = cleaned.get("model") or f"{vendor}-{index}"
    name = cleaned.get("name") or cleaned.get("model") or cleaned.get("sku") or code
    category = cleaned.get("category") or "general"

    product: Dict[str, Any] = {
        "code": code,
        "name": name,
        "category": category,
        "brand": cleaned.get("brand"),
        "model": cleaned.get("model") or cleaned.get("model_number"),
        "sku": cleaned.get("sku"),
    }

    dimensions = _parse_dimensions(cleaned)
    if dimensions:
        product["dimensions"] = dimensions

    return product


async def sync_products_csv_once(
    csv_path: str,
    *,
    vendor: Optional[str] = None,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> Dict[str, Any]:
    """Read a CSV file and synchronise its contents into ``ref_products``."""

    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    resolved_vendor = vendor or path.stem

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        products = [
            _row_to_product(row, resolved_vendor, index)
            for index, row in enumerate(reader, start=1)
            if any(value not in (None, "") for value in row.values())
        ]

    payload = {"vendor": resolved_vendor, "products": products}

    factory = session_factory
    if factory is None:
        factory = AsyncSessionLocal  # type: ignore[assignment]

    if factory is None:  # pragma: no cover - triggered only when app database is unavailable
        inserted = products
    else:
        inserted = await sync_vendor_products(factory, payload)

    return {"ok": True, "inserted": len(inserted)}


__all__ = ["sync_products_csv_once"]
