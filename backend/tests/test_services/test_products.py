"""High-quality tests for vendor product adapter utilities.

This test suite provides comprehensive coverage of the VendorProduct dataclass
and VendorProductAdapter, focusing on data transformation and normalization logic.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.no_db

from app.services.products import VendorProduct, VendorProductAdapter

# =============================================================================
# VendorProduct Tests
# =============================================================================


def test_vendor_product_as_orm_kwargs_with_all_fields():
    """Test VendorProduct.as_orm_kwargs() with all fields populated."""
    product = VendorProduct(
        vendor="TestVendor",
        category="fixtures",
        product_code="FIX-001",
        name="Test Fixture",
        brand="BrandA",
        model_number="M123",
        sku="SKU-789",
        dimensions={"width_mm": 100.0, "height_mm": 200.0},
        specifications={"material": "steel", "finish": "polished"},
        bim_uri="https://example.com/bim.ifc",
        spec_uri="https://example.com/spec.pdf",
    )

    result = product.as_orm_kwargs()

    assert result["vendor"] == "TestVendor"
    assert result["category"] == "fixtures"
    assert result["product_code"] == "FIX-001"
    assert result["name"] == "Test Fixture"
    assert result["brand"] == "BrandA"
    assert result["model_number"] == "M123"
    assert result["sku"] == "SKU-789"
    assert result["dimensions"] == {"width_mm": 100.0, "height_mm": 200.0}
    assert result["specifications"] == {"material": "steel", "finish": "polished"}
    assert result["bim_uri"] == "https://example.com/bim.ifc"
    assert result["spec_uri"] == "https://example.com/spec.pdf"


def test_vendor_product_as_orm_kwargs_with_minimal_fields():
    """Test VendorProduct.as_orm_kwargs() with only required fields."""
    product = VendorProduct(
        vendor="TestVendor",
        category="general",
        product_code="GEN-001",
        name="Basic Product",
    )

    result = product.as_orm_kwargs()

    assert result["vendor"] == "TestVendor"
    assert result["category"] == "general"
    assert result["product_code"] == "GEN-001"
    assert result["name"] == "Basic Product"
    assert result["brand"] is None
    assert result["model_number"] is None
    assert result["sku"] is None
    assert result["dimensions"] == {}  # None converted to empty dict
    assert result["specifications"] == {}  # None converted to empty dict
    assert result["bim_uri"] is None
    assert result["spec_uri"] is None


def test_vendor_product_as_orm_kwargs_converts_none_dicts():
    """Test that None dimensions/specifications are converted to empty dicts."""
    product = VendorProduct(
        vendor="TestVendor",
        category="test",
        product_code="T-001",
        name="Test",
        dimensions=None,
        specifications=None,
    )

    result = product.as_orm_kwargs()

    assert result["dimensions"] == {}
    assert result["specifications"] == {}


# =============================================================================
# VendorProductAdapter Initialization Tests
# =============================================================================


def test_adapter_initialization_with_defaults():
    """Test VendorProductAdapter initializes with default category."""
    adapter = VendorProductAdapter("VendorA")

    assert adapter.vendor == "VendorA"
    assert adapter.default_category == "general"


def test_adapter_initialization_with_custom_category():
    """Test VendorProductAdapter with custom default category."""
    adapter = VendorProductAdapter("VendorB", default_category="plumbing")

    assert adapter.vendor == "VendorB"
    assert adapter.default_category == "plumbing"


# =============================================================================
# VendorProductAdapter.transform() Tests
# =============================================================================


def test_transform_empty_payload():
    """Test transforming empty payload returns empty list."""
    adapter = VendorProductAdapter("TestVendor")
    payload = {}

    result = adapter.transform(payload)

    assert result == []


def test_transform_payload_with_no_products_key():
    """Test transforming payload without 'products' key."""
    adapter = VendorProductAdapter("TestVendor")
    payload = {"other_data": "value"}

    result = adapter.transform(payload)

    assert result == []


def test_transform_payload_with_empty_products_list():
    """Test transforming payload with empty products list."""
    adapter = VendorProductAdapter("TestVendor")
    payload = {"products": []}

    result = adapter.transform(payload)

    assert result == []


def test_transform_single_valid_product():
    """Test transforming payload with one valid product."""
    adapter = VendorProductAdapter("TestVendor")
    payload = {
        "products": [
            {
                "product_code": "P-001",
                "name": "Test Product",
                "category": "fixtures",
            }
        ]
    }

    result = adapter.transform(payload)

    assert len(result) == 1
    assert result[0].product_code == "P-001"
    assert result[0].name == "Test Product"
    assert result[0].vendor == "TestVendor"


def test_transform_multiple_valid_products():
    """Test transforming payload with multiple valid products."""
    adapter = VendorProductAdapter("TestVendor")
    payload = {
        "products": [
            {"code": "P-001", "name": "Product 1"},
            {"code": "P-002", "name": "Product 2"},
            {"code": "P-003", "name": "Product 3"},
        ]
    }

    result = adapter.transform(payload)

    assert len(result) == 3
    assert [p.product_code for p in result] == ["P-001", "P-002", "P-003"]


def test_transform_filters_invalid_products():
    """Test that products missing code or name are filtered out."""
    adapter = VendorProductAdapter("TestVendor")
    payload = {
        "products": [
            {"code": "P-001", "name": "Valid Product"},
            {"code": "P-002"},  # Missing name
            {"name": "No Code Product"},  # Missing code
            {"code": "", "name": "Empty Code"},  # Empty code
            {"code": "P-003", "name": ""},  # Empty name
        ]
    }

    result = adapter.transform(payload)

    # Only the first product is valid
    assert len(result) == 1
    assert result[0].product_code == "P-001"


# =============================================================================
# VendorProductAdapter._extract_code() Tests
# =============================================================================


def test_extract_code_from_product_code_key():
    """Test extracting code from 'product_code' key."""
    adapter = VendorProductAdapter("TestVendor")
    raw = {"product_code": "CODE-123"}

    code = adapter._extract_code(raw)

    assert code == "CODE-123"


def test_extract_code_from_code_key():
    """Test extracting code from 'code' key."""
    adapter = VendorProductAdapter("TestVendor")
    raw = {"code": "ABC-456"}

    code = adapter._extract_code(raw)

    assert code == "ABC-456"


def test_extract_code_from_id_key():
    """Test extracting code from 'id' key."""
    adapter = VendorProductAdapter("TestVendor")
    raw = {"id": "789"}

    code = adapter._extract_code(raw)

    assert code == "789"


def test_extract_code_priority():
    """Test that product_code has priority over code and id."""
    adapter = VendorProductAdapter("TestVendor")
    raw = {"product_code": "P-CODE", "code": "CODE", "id": "ID"}

    code = adapter._extract_code(raw)

    assert code == "P-CODE"


def test_extract_code_returns_none_when_missing():
    """Test that None is returned when no code key exists."""
    adapter = VendorProductAdapter("TestVendor")
    raw = {"name": "Product"}

    code = adapter._extract_code(raw)

    assert code is None


def test_extract_code_converts_numeric_to_string():
    """Test that numeric codes are converted to strings."""
    adapter = VendorProductAdapter("TestVendor")
    raw = {"product_code": 12345}

    code = adapter._extract_code(raw)

    assert code == "12345"
    assert isinstance(code, str)


# =============================================================================
# VendorProductAdapter._parse_dimensions() Tests
# =============================================================================


def test_parse_dimensions_with_width_height_depth():
    """Test parsing dimensions with all three measurements."""
    adapter = VendorProductAdapter("TestVendor")
    data = {"width": 100, "height": 200, "depth": 50}

    result = adapter._parse_dimensions(data)

    assert result == {"width_mm": 100.0, "height_mm": 200.0, "depth_mm": 50.0}


def test_parse_dimensions_with_mm_suffix():
    """Test parsing dimensions already with _mm suffix."""
    adapter = VendorProductAdapter("TestVendor")
    data = {"width_mm": 150.5, "height_mm": 250.5, "depth_mm": 75.5}

    result = adapter._parse_dimensions(data)

    assert result == {"width_mm": 150.5, "height_mm": 250.5, "depth_mm": 75.5}


def test_parse_dimensions_with_partial_measurements():
    """Test parsing dimensions with only some measurements."""
    adapter = VendorProductAdapter("TestVendor")
    data = {"width": 100, "depth": 50}

    result = adapter._parse_dimensions(data)

    assert result == {"width_mm": 100.0, "depth_mm": 50.0}
    assert "height_mm" not in result


def test_parse_dimensions_with_none_input():
    """Test that None input returns None."""
    adapter = VendorProductAdapter("TestVendor")

    result = adapter._parse_dimensions(None)

    assert result is None


def test_parse_dimensions_with_non_dict_input():
    """Test that non-dict input returns None."""
    adapter = VendorProductAdapter("TestVendor")

    assert adapter._parse_dimensions("not a dict") is None
    assert adapter._parse_dimensions([1, 2, 3]) is None
    assert adapter._parse_dimensions(123) is None


def test_parse_dimensions_with_string_numbers():
    """Test that string numbers are converted to floats."""
    adapter = VendorProductAdapter("TestVendor")
    data = {"width": "100.5", "height": "200"}

    result = adapter._parse_dimensions(data)

    assert result == {"width_mm": 100.5, "height_mm": 200.0}


def test_parse_dimensions_filters_invalid_values():
    """Test that invalid numeric values are filtered out."""
    adapter = VendorProductAdapter("TestVendor")
    data = {
        "width": 100,
        "height": "invalid",
        "depth": None,
    }

    result = adapter._parse_dimensions(data)

    assert result == {"width_mm": 100.0}


def test_parse_dimensions_returns_none_if_all_invalid():
    """Test that None is returned if no valid dimensions exist."""
    adapter = VendorProductAdapter("TestVendor")
    data = {"width": "invalid", "height": None}

    result = adapter._parse_dimensions(data)

    assert result is None


def test_parse_dimensions_empty_dict():
    """Test that empty dict returns None."""
    adapter = VendorProductAdapter("TestVendor")
    data = {}

    result = adapter._parse_dimensions(data)

    assert result is None


# =============================================================================
# VendorProductAdapter._ensure_dict() Tests
# =============================================================================


def test_ensure_dict_with_valid_dict():
    """Test that valid dicts are returned as-is."""
    adapter = VendorProductAdapter("TestVendor")
    data = {"key": "value", "number": 42}

    result = adapter._ensure_dict(data)

    assert result == {"key": "value", "number": 42}


def test_ensure_dict_with_none():
    """Test that None returns empty dict."""
    adapter = VendorProductAdapter("TestVendor")

    result = adapter._ensure_dict(None)

    assert result == {}


def test_ensure_dict_with_non_dict_types():
    """Test that non-dict types return empty dict."""
    adapter = VendorProductAdapter("TestVendor")

    assert adapter._ensure_dict("string") == {}
    assert adapter._ensure_dict(123) == {}
    assert adapter._ensure_dict([1, 2, 3]) == {}
    assert adapter._ensure_dict(True) == {}


def test_ensure_dict_with_empty_dict():
    """Test that empty dict is returned as-is."""
    adapter = VendorProductAdapter("TestVendor")

    result = adapter._ensure_dict({})

    assert result == {}


# =============================================================================
# VendorProductAdapter._safe_str() Tests
# =============================================================================


def test_safe_str_with_valid_string():
    """Test that valid strings are returned trimmed."""
    adapter = VendorProductAdapter("TestVendor")

    assert adapter._safe_str("  test value  ") == "test value"
    assert adapter._safe_str("no_trim_needed") == "no_trim_needed"


def test_safe_str_with_none():
    """Test that None returns None."""
    adapter = VendorProductAdapter("TestVendor")

    assert adapter._safe_str(None) is None


def test_safe_str_with_empty_string():
    """Test that empty string returns None."""
    adapter = VendorProductAdapter("TestVendor")

    assert adapter._safe_str("") is None


def test_safe_str_with_whitespace_only():
    """Test that whitespace-only string returns None."""
    adapter = VendorProductAdapter("TestVendor")

    assert adapter._safe_str("   ") is None
    assert adapter._safe_str("\t\n") is None


def test_safe_str_converts_numbers_to_strings():
    """Test that numbers are converted to strings."""
    adapter = VendorProductAdapter("TestVendor")

    assert adapter._safe_str(123) == "123"
    assert adapter._safe_str(45.67) == "45.67"


def test_safe_str_converts_booleans():
    """Test that booleans are converted to strings."""
    adapter = VendorProductAdapter("TestVendor")

    assert adapter._safe_str(True) == "True"
    assert adapter._safe_str(False) == "False"


# =============================================================================
# Integration Tests: _build_product()
# =============================================================================


def test_build_product_with_complete_data():
    """Test building a product with all fields populated."""
    adapter = VendorProductAdapter("TestVendor", default_category="default_cat")
    raw = {
        "product_code": "P-001",
        "name": "Complete Product",
        "category": "fixtures",
        "brand": "BrandX",
        "model_number": "M-123",
        "sku": "SKU-789",
        "dimensions": {"width": 100, "height": 200, "depth": 50},
        "specifications": {"material": "steel"},
        "bim_uri": "https://example.com/bim.ifc",
        "spec_uri": "https://example.com/spec.pdf",
    }

    product = adapter._build_product(raw)

    assert product is not None
    assert product.vendor == "TestVendor"
    assert product.product_code == "P-001"
    assert product.name == "Complete Product"
    assert product.category == "fixtures"
    assert product.brand == "BrandX"
    assert product.model_number == "M-123"
    assert product.sku == "SKU-789"
    assert product.dimensions == {
        "width_mm": 100.0,
        "height_mm": 200.0,
        "depth_mm": 50.0,
    }
    assert product.specifications == {"material": "steel"}
    assert product.bim_uri == "https://example.com/bim.ifc"
    assert product.spec_uri == "https://example.com/spec.pdf"


def test_build_product_uses_default_category():
    """Test that default category is used when not provided."""
    adapter = VendorProductAdapter("TestVendor", default_category="plumbing")
    raw = {"code": "P-001", "name": "Product"}

    product = adapter._build_product(raw)

    assert product is not None
    assert product.category == "plumbing"


def test_build_product_with_model_fallback():
    """Test that 'model' key is used as fallback for model_number."""
    adapter = VendorProductAdapter("TestVendor")
    raw = {"code": "P-001", "name": "Product", "model": "M-XYZ"}

    product = adapter._build_product(raw)

    assert product is not None
    assert product.model_number == "M-XYZ"


def test_build_product_with_bim_fallback():
    """Test that 'bim' key is used as fallback for bim_uri."""
    adapter = VendorProductAdapter("TestVendor")
    raw = {"code": "P-001", "name": "Product", "bim": "https://bim.example.com"}

    product = adapter._build_product(raw)

    assert product is not None
    assert product.bim_uri == "https://bim.example.com"


def test_build_product_with_spec_fallback():
    """Test that 'spec' key is used as fallback for spec_uri."""
    adapter = VendorProductAdapter("TestVendor")
    raw = {"code": "P-001", "name": "Product", "spec": "https://spec.example.com"}

    product = adapter._build_product(raw)

    assert product is not None
    assert product.spec_uri == "https://spec.example.com"


def test_build_product_returns_none_without_code():
    """Test that None is returned when code is missing."""
    adapter = VendorProductAdapter("TestVendor")
    raw = {"name": "Product Without Code"}

    product = adapter._build_product(raw)

    assert product is None


def test_build_product_returns_none_without_name():
    """Test that None is returned when name is missing."""
    adapter = VendorProductAdapter("TestVendor")
    raw = {"code": "P-001"}

    product = adapter._build_product(raw)

    assert product is None


def test_build_product_returns_none_with_empty_name():
    """Test that None is returned when name is empty after stripping."""
    adapter = VendorProductAdapter("TestVendor")
    raw = {"code": "P-001", "name": "   "}

    product = adapter._build_product(raw)

    assert product is None


def test_build_product_strips_name():
    """Test that product name is trimmed."""
    adapter = VendorProductAdapter("TestVendor")
    raw = {"code": "P-001", "name": "  Product Name  "}

    product = adapter._build_product(raw)

    assert product is not None
    assert product.name == "Product Name"
