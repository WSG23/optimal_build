"""Vendor product adapter utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class VendorProduct:
    """Normalised representation of a vendor product."""

    vendor: str
    category: str
    product_code: str
    name: str
    brand: str | None = None
    model_number: str | None = None
    sku: str | None = None
    dimensions: dict[str, float] | None = None
    specifications: dict[str, Any] | None = None
    bim_uri: str | None = None
    spec_uri: str | None = None

    def as_orm_kwargs(self) -> dict[str, Any]:
        """Return keyword arguments compatible with ``RefProduct``."""

        return {
            "vendor": self.vendor,
            "category": self.category,
            "product_code": self.product_code,
            "name": self.name,
            "brand": self.brand,
            "model_number": self.model_number,
            "sku": self.sku,
            "dimensions": self.dimensions or {},
            "specifications": self.specifications or {},
            "bim_uri": self.bim_uri,
            "spec_uri": self.spec_uri,
        }


class VendorProductAdapter:
    """Adapter that converts vendor feeds into :class:`VendorProduct` objects."""

    def __init__(self, vendor: str, *, default_category: str = "general") -> None:
        self.vendor = vendor
        self.default_category = default_category

    def transform(self, payload: dict[str, Any]) -> list[VendorProduct]:
        """Transform the vendor payload into ``VendorProduct`` instances."""

        products: list[VendorProduct] = []
        for raw in payload.get("products", []):
            product = self._build_product(raw)
            if product:
                products.append(product)
        return products

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_product(self, raw: dict[str, Any]) -> VendorProduct | None:
        code = self._extract_code(raw)
        name = str(raw.get("name") or "").strip()
        if not code or not name:
            return None

        dimensions = self._parse_dimensions(raw.get("dimensions"))
        specifications = self._ensure_dict(raw.get("specifications"))

        return VendorProduct(
            vendor=self.vendor,
            category=str(raw.get("category") or self.default_category),
            product_code=code,
            name=name,
            brand=self._safe_str(raw.get("brand")),
            model_number=self._safe_str(raw.get("model") or raw.get("model_number")),
            sku=self._safe_str(raw.get("sku")),
            dimensions=dimensions,
            specifications=specifications,
            bim_uri=self._safe_str(raw.get("bim_uri") or raw.get("bim")),
            spec_uri=self._safe_str(raw.get("spec_uri") or raw.get("spec")),
        )

    def _extract_code(self, raw: dict[str, Any]) -> str | None:
        for key in ("product_code", "code", "id"):
            value = raw.get(key)
            if value:
                return str(value)
        return None

    def _parse_dimensions(self, data: dict[str, Any] | None) -> dict[str, float] | None:
        if not isinstance(data, dict):
            return None
        result: dict[str, float] = {}
        for key in ("width", "width_mm", "depth", "depth_mm", "height", "height_mm"):
            value = data.get(key)
            if value is None:
                continue
            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                continue
            result_key = key if key.endswith("_mm") else f"{key}_mm"
            result[result_key] = numeric_value
        if not result:
            return None
        normalised = {
            "width_mm": result.get("width_mm"),
            "depth_mm": result.get("depth_mm"),
            "height_mm": result.get("height_mm"),
        }
        # Remove ``None`` entries
        return {k: v for k, v in normalised.items() if v is not None}

    def _ensure_dict(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        return {}

    def _safe_str(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None


__all__ = ["VendorProduct", "VendorProductAdapter"]
