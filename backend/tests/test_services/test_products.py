"""Comprehensive tests for products service.

Tests cover:
- VendorProduct dataclass
- VendorProductAdapter class
- Product transformation logic
- Dimension parsing
- Code extraction
"""

from __future__ import annotations

import pytest

from app.services.products import VendorProduct, VendorProductAdapter

# Mark all tests in this module as not requiring database
pytestmark = pytest.mark.no_db


class TestVendorProduct:
    """Tests for VendorProduct dataclass."""

    def test_required_fields(self) -> None:
        """Test required fields."""
        product = VendorProduct(
            vendor="Kohler",
            category="toilet",
            product_code="K-123456",
            name="San Raphael",
        )
        assert product.vendor == "Kohler"
        assert product.category == "toilet"
        assert product.product_code == "K-123456"
        assert product.name == "San Raphael"

    def test_optional_fields_default_none(self) -> None:
        """Test optional fields default to None."""
        product = VendorProduct(
            vendor="Kohler",
            category="toilet",
            product_code="K-123456",
            name="San Raphael",
        )
        assert product.brand is None
        assert product.model_number is None
        assert product.sku is None
        assert product.dimensions is None
        assert product.specifications is None
        assert product.bim_uri is None
        assert product.spec_uri is None

    def test_all_fields(self) -> None:
        """Test all fields can be set."""
        product = VendorProduct(
            vendor="Kohler",
            category="toilet",
            product_code="K-123456",
            name="San Raphael Comfort Height",
            brand="Kohler",
            model_number="77780",
            sku="K-77780-0",
            dimensions={"width_mm": 390, "depth_mm": 700, "height_mm": 780},
            specifications={"flush_volume_l": 4.8, "material": "vitreous_china"},
            bim_uri="https://revit.kohler.com/K-77780",
            spec_uri="https://specs.kohler.com/K-77780",
        )
        assert product.brand == "Kohler"
        assert product.dimensions["width_mm"] == 390
        assert product.specifications["flush_volume_l"] == 4.8


class TestVendorProductAsOrmKwargs:
    """Tests for VendorProduct.as_orm_kwargs method."""

    def test_returns_dict(self) -> None:
        """Test as_orm_kwargs returns a dictionary."""
        product = VendorProduct(
            vendor="Kohler",
            category="toilet",
            product_code="K-123456",
            name="San Raphael",
        )
        kwargs = product.as_orm_kwargs()
        assert isinstance(kwargs, dict)

    def test_contains_required_fields(self) -> None:
        """Test kwargs contains all required fields."""
        product = VendorProduct(
            vendor="Kohler",
            category="toilet",
            product_code="K-123456",
            name="San Raphael",
        )
        kwargs = product.as_orm_kwargs()
        assert kwargs["vendor"] == "Kohler"
        assert kwargs["category"] == "toilet"
        assert kwargs["product_code"] == "K-123456"
        assert kwargs["name"] == "San Raphael"

    def test_dimensions_defaults_to_empty_dict(self) -> None:
        """Test dimensions defaults to empty dict if None."""
        product = VendorProduct(
            vendor="Kohler",
            category="toilet",
            product_code="K-123456",
            name="San Raphael",
        )
        kwargs = product.as_orm_kwargs()
        assert kwargs["dimensions"] == {}

    def test_specifications_defaults_to_empty_dict(self) -> None:
        """Test specifications defaults to empty dict if None."""
        product = VendorProduct(
            vendor="Kohler",
            category="toilet",
            product_code="K-123456",
            name="San Raphael",
        )
        kwargs = product.as_orm_kwargs()
        assert kwargs["specifications"] == {}


class TestVendorProductAdapter:
    """Tests for VendorProductAdapter class."""

    def test_init_with_vendor(self) -> None:
        """Test initialization with vendor name."""
        adapter = VendorProductAdapter("Kohler")
        assert adapter.vendor == "Kohler"

    def test_init_with_default_category(self) -> None:
        """Test initialization with default category."""
        adapter = VendorProductAdapter("Kohler", default_category="bathroom")
        assert adapter.default_category == "bathroom"

    def test_default_category_is_general(self) -> None:
        """Test default category defaults to 'general'."""
        adapter = VendorProductAdapter("Kohler")
        assert adapter.default_category == "general"


class TestVendorProductAdapterTransform:
    """Tests for VendorProductAdapter.transform method."""

    def test_empty_payload(self) -> None:
        """Test transform with empty payload."""
        adapter = VendorProductAdapter("Kohler")
        products = adapter.transform({})
        assert products == []

    def test_empty_products_list(self) -> None:
        """Test transform with empty products list."""
        adapter = VendorProductAdapter("Kohler")
        products = adapter.transform({"products": []})
        assert products == []

    def test_single_product(self) -> None:
        """Test transform with single product."""
        adapter = VendorProductAdapter("Kohler")
        payload = {
            "products": [
                {
                    "product_code": "K-123456",
                    "name": "San Raphael",
                    "category": "toilet",
                }
            ]
        }
        products = adapter.transform(payload)
        assert len(products) == 1
        assert products[0].product_code == "K-123456"
        assert products[0].vendor == "Kohler"

    def test_multiple_products(self) -> None:
        """Test transform with multiple products."""
        adapter = VendorProductAdapter("Kohler")
        payload = {
            "products": [
                {"product_code": "K-1", "name": "Product 1"},
                {"product_code": "K-2", "name": "Product 2"},
                {"product_code": "K-3", "name": "Product 3"},
            ]
        }
        products = adapter.transform(payload)
        assert len(products) == 3

    def test_skips_invalid_products(self) -> None:
        """Test transform skips products without code or name."""
        adapter = VendorProductAdapter("Kohler")
        payload = {
            "products": [
                {"product_code": "K-1", "name": "Valid"},
                {"product_code": "K-2", "name": ""},  # Empty name
                {"name": "No Code"},  # No code
                {},  # Empty
            ]
        }
        products = adapter.transform(payload)
        assert len(products) == 1
        assert products[0].name == "Valid"

    def test_uses_default_category(self) -> None:
        """Test uses default category when not specified."""
        adapter = VendorProductAdapter("Kohler", default_category="fixture")
        payload = {"products": [{"product_code": "K-1", "name": "Product 1"}]}
        products = adapter.transform(payload)
        assert products[0].category == "fixture"


class TestDimensionParsing:
    """Tests for dimension parsing logic."""

    def test_parse_dimensions_with_mm(self) -> None:
        """Test parsing dimensions with _mm suffix."""
        adapter = VendorProductAdapter("Kohler")
        payload = {
            "products": [
                {
                    "product_code": "K-1",
                    "name": "Product",
                    "dimensions": {
                        "width_mm": 390,
                        "depth_mm": 700,
                        "height_mm": 780,
                    },
                }
            ]
        }
        products = adapter.transform(payload)
        assert products[0].dimensions["width_mm"] == 390
        assert products[0].dimensions["depth_mm"] == 700
        assert products[0].dimensions["height_mm"] == 780

    def test_parse_dimensions_without_mm(self) -> None:
        """Test parsing dimensions without _mm suffix."""
        adapter = VendorProductAdapter("Kohler")
        payload = {
            "products": [
                {
                    "product_code": "K-1",
                    "name": "Product",
                    "dimensions": {
                        "width": 390,
                        "depth": 700,
                        "height": 780,
                    },
                }
            ]
        }
        products = adapter.transform(payload)
        dimensions = products[0].dimensions
        assert dimensions is not None
        assert "width_mm" in dimensions

    def test_parse_invalid_dimensions(self) -> None:
        """Test parsing handles invalid dimension values."""
        adapter = VendorProductAdapter("Kohler")
        payload = {
            "products": [
                {
                    "product_code": "K-1",
                    "name": "Product",
                    "dimensions": {
                        "width_mm": "invalid",
                        "depth_mm": 700,
                    },
                }
            ]
        }
        products = adapter.transform(payload)
        dimensions = products[0].dimensions
        assert dimensions is not None
        # Invalid value should be skipped
        assert "width_mm" not in dimensions or dimensions.get("width_mm") is None


class TestCodeExtraction:
    """Tests for product code extraction logic."""

    def test_extract_product_code(self) -> None:
        """Test extraction from product_code field."""
        adapter = VendorProductAdapter("Kohler")
        payload = {"products": [{"product_code": "K-123", "name": "Product"}]}
        products = adapter.transform(payload)
        assert products[0].product_code == "K-123"

    def test_extract_code_field(self) -> None:
        """Test extraction from code field."""
        adapter = VendorProductAdapter("Kohler")
        payload = {"products": [{"code": "K-123", "name": "Product"}]}
        products = adapter.transform(payload)
        assert products[0].product_code == "K-123"

    def test_extract_id_field(self) -> None:
        """Test extraction from id field."""
        adapter = VendorProductAdapter("Kohler")
        payload = {"products": [{"id": "K-123", "name": "Product"}]}
        products = adapter.transform(payload)
        assert products[0].product_code == "K-123"


class TestProductScenarios:
    """Tests for product use case scenarios."""

    def test_bathroom_fixture_product(self) -> None:
        """Test bathroom fixture product."""
        product = VendorProduct(
            vendor="Kohler",
            category="toilet",
            product_code="K-77780-0",
            name="San Raphael Comfort Height",
            brand="Kohler",
            model_number="77780",
            dimensions={"width_mm": 390, "depth_mm": 700, "height_mm": 780},
            specifications={
                "flush_volume_l": 4.8,
                "material": "vitreous_china",
                "color": "white",
            },
        )
        assert product.specifications["flush_volume_l"] == 4.8

    def test_kitchen_appliance_product(self) -> None:
        """Test kitchen appliance product."""
        product = VendorProduct(
            vendor="Miele",
            category="dishwasher",
            product_code="G-7160-SCVI",
            name="G 7160 SCVi AutoDos",
            brand="Miele",
            model_number="G7160",
            dimensions={"width_mm": 598, "depth_mm": 570, "height_mm": 805},
            specifications={
                "capacity_place_settings": 14,
                "energy_class": "A+++",
                "noise_db": 42,
            },
        )
        assert product.specifications["capacity_place_settings"] == 14

    def test_lighting_product(self) -> None:
        """Test lighting product."""
        product = VendorProduct(
            vendor="Philips",
            category="lighting",
            product_code="PH-DN145B",
            name="GreenSpace LED Downlight",
            brand="Philips",
            model_number="DN145B",
            specifications={
                "wattage": 12,
                "lumens": 1200,
                "color_temp_k": 4000,
                "cri": 80,
            },
            bim_uri="https://revit.philips.com/DN145B",
        )
        assert product.specifications["lumens"] == 1200
