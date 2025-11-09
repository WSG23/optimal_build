"""Tests for vendor product adapter utilities."""

from __future__ import annotations

from app.services.products import VendorProduct, VendorProductAdapter


def test_vendor_product_as_orm_kwargs():
    """Test VendorProduct.as_orm_kwargs()."""
    product = VendorProduct(
        vendor="TestVendor",
        category="fixtures",
        product_code="PROD-123",
        name="Test Product",
        brand="TestBrand",
        model_number="MODEL-456",
        sku="SKU-789",
        dimensions={"width_mm": 100.0, "height_mm": 200.0},
        specifications={"material": "steel"},
        bim_uri="https://example.com/bim",
        spec_uri="https://example.com/spec",
    )

    kwargs = product.as_orm_kwargs()
    assert kwargs["vendor"] == "TestVendor"
    assert kwargs["category"] == "fixtures"
    assert kwargs["product_code"] == "PROD-123"
    assert kwargs["name"] == "Test Product"
    assert kwargs["brand"] == "TestBrand"
    assert kwargs["model_number"] == "MODEL-456"
    assert kwargs["sku"] == "SKU-789"
    assert kwargs["dimensions"] == {"width_mm": 100.0, "height_mm": 200.0}
    assert kwargs["specifications"] == {"material": "steel"}
    assert kwargs["bim_uri"] == "https://example.com/bim"
    assert kwargs["spec_uri"] == "https://example.com/spec"


def test_vendor_product_as_orm_kwargs_with_none_values():
    """Test VendorProduct.as_orm_kwargs() converts None dimensions/specs to empty dicts."""
    product = VendorProduct(
        vendor="TestVendor",
        category="general",
        product_code="PROD-001",
        name="Minimal Product",
        dimensions=None,
        specifications=None,
    )

    kwargs = product.as_orm_kwargs()
    assert kwargs["dimensions"] == {}
    assert kwargs["specifications"] == {}


def test_vendor_product_adapter_transform():
    """Test VendorProductAdapter.transform() basic flow."""
    adapter = VendorProductAdapter(vendor="TestVendor", default_category="general")

    payload = {
        "products": [
            {
                "product_code": "PROD-001",
                "name": "Product 1",
                "category": "fixtures",
            },
            {
                "code": "PROD-002",
                "name": "Product 2",
            },
        ]
    }

    products = adapter.transform(payload)
    assert len(products) == 2
    assert products[0].product_code == "PROD-001"
    assert products[0].category == "fixtures"
    assert products[1].product_code == "PROD-002"
    assert products[1].category == "general"  # default category


def test_vendor_product_adapter_skips_invalid_products():
    """Test VendorProductAdapter.transform() skips products without code or name."""
    adapter = VendorProductAdapter(vendor="TestVendor")

    payload = {
        "products": [
            {"product_code": "PROD-001", "name": "Valid Product"},
            {"product_code": "PROD-002"},  # Missing name
            {"name": "No Code Product"},  # Missing code
            {"name": ""},  # Empty name
        ]
    }

    products = adapter.transform(payload)
    assert len(products) == 1
    assert products[0].product_code == "PROD-001"


def test_vendor_product_adapter_extract_code_fallback():
    """Test _extract_code tries multiple keys (code, id)."""
    adapter = VendorProductAdapter(vendor="TestVendor")

    # Test with "code" key
    raw = {"code": "CODE-123", "name": "Product"}
    product = adapter._build_product(raw)
    assert product.product_code == "CODE-123"

    # Test with "id" key
    raw = {"id": "ID-456", "name": "Product"}
    product = adapter._build_product(raw)
    assert product.product_code == "ID-456"


def test_vendor_product_adapter_parse_dimensions_invalid():
    """Test _parse_dimensions returns None for non-dict input."""
    adapter = VendorProductAdapter(vendor="TestVendor")

    assert adapter._parse_dimensions(None) is None
    assert adapter._parse_dimensions("not a dict") is None
    assert adapter._parse_dimensions([]) is None


def test_vendor_product_adapter_parse_dimensions_with_conversion_errors():
    """Test _parse_dimensions handles non-numeric values gracefully."""
    adapter = VendorProductAdapter(vendor="TestVendor")

    # Valid values mixed with invalid
    data = {
        "width_mm": 100.0,
        "height": "not-a-number",  # Invalid, should be skipped
        "depth_mm": 200.0,
    }
    result = adapter._parse_dimensions(data)
    assert result == {"width_mm": 100.0, "depth_mm": 200.0}
    assert "height_mm" not in result


def test_vendor_product_adapter_parse_dimensions_empty_result():
    """Test _parse_dimensions returns None if no valid dimensions."""
    adapter = VendorProductAdapter(vendor="TestVendor")

    data = {"width": "invalid", "height": "invalid"}
    result = adapter._parse_dimensions(data)
    assert result is None


def test_vendor_product_adapter_model_number_fallback():
    """Test model_number extraction from 'model' or 'model_number' keys."""
    adapter = VendorProductAdapter(vendor="TestVendor")

    # Test with "model" key
    raw = {"product_code": "P1", "name": "Product", "model": "MODEL-A"}
    product = adapter._build_product(raw)
    assert product.model_number == "MODEL-A"

    # Test with "model_number" key
    raw = {"product_code": "P1", "name": "Product", "model_number": "MODEL-B"}
    product = adapter._build_product(raw)
    assert product.model_number == "MODEL-B"


def test_vendor_product_adapter_bim_and_spec_uri_fallback():
    """Test bim_uri and spec_uri extraction with fallback keys."""
    adapter = VendorProductAdapter(vendor="TestVendor")

    # Test with short key names
    raw = {
        "product_code": "P1",
        "name": "Product",
        "bim": "https://example.com/bim.ifc",
        "spec": "https://example.com/spec.pdf",
    }
    product = adapter._build_product(raw)
    assert product.bim_uri == "https://example.com/bim.ifc"
    assert product.spec_uri == "https://example.com/spec.pdf"


def test_vendor_product_adapter_safe_str_empty_strips_to_none():
    """Test _safe_str returns None for empty/whitespace strings."""
    adapter = VendorProductAdapter(vendor="TestVendor")

    assert adapter._safe_str("   ") is None
    assert adapter._safe_str("") is None
    assert adapter._safe_str(None) is None
    assert adapter._safe_str("valid") == "valid"
