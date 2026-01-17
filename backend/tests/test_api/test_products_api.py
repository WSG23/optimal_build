from __future__ import annotations

import pytest
import pytest_asyncio

from app.models.rkp import RefProduct


@pytest_asyncio.fixture
async def products_seed(db_session):
    first = RefProduct(
        vendor="Acme",
        category="fixtures",
        product_code="AC-100",
        name="Acme Basin",
        brand="Acme",
        model_number="B100",
        dimensions={"width_mm": 620},
        specifications={"material": "ceramic"},
        sku="SKU-1",
    )
    second = RefProduct(
        vendor="Globex",
        category="fixtures",
        product_code="GL-200",
        name="Globex Basin",
        brand="Globex",
        model_number="G200",
        dimensions={},
        specifications={"material": "steel"},
        sku="SKU-2",
    )
    db_session.add_all([first, second])
    await db_session.commit()
    return {
        "first": first,
        "second": second,
    }


@pytest.mark.asyncio
async def test_list_products_filters_by_brand(client, products_seed):
    response = await client.get("/api/v1/products", params={"brand": "Acme"})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["product_code"] == "AC-100"


@pytest.mark.asyncio
async def test_list_products_filters_by_width_range(client, products_seed):
    response = await client.get(
        "/api/v1/products",
        params={"width_mm_min": 600, "width_mm_max": 650},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["name"] == "Acme Basin"


@pytest.mark.asyncio
async def test_list_products_slash_route(client, products_seed):
    response = await client.get("/api/v1/products/", params={"category": "fixtures"})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2


@pytest.mark.asyncio
async def test_list_products_no_filters(client, products_seed):
    """Test listing all products without filters."""
    response = await client.get("/api/v1/products")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 2


@pytest.mark.asyncio
async def test_list_products_width_filters_exclude_missing_dimensions(
    client, products_seed
):
    """Test that products without width_mm are excluded when filtering by width."""
    # The second product has empty dimensions, so should be excluded
    response = await client.get(
        "/api/v1/products",
        params={
            "width_mm_min": 1
        },  # Any positive min should exclude products without width
    )
    assert response.status_code == 200
    payload = response.json()
    # Only Acme Basin should match (has width_mm: 620)
    assert len(payload) == 1
    assert payload[0]["product_code"] == "AC-100"


@pytest.mark.asyncio
async def test_list_products_width_max_filter(client, products_seed):
    """Test filtering by maximum width."""
    response = await client.get(
        "/api/v1/products",
        params={"width_mm_max": 500},  # 620 is too wide
    )
    assert response.status_code == 200
    payload = response.json()
    # No products should match
    assert len(payload) == 0


@pytest_asyncio.fixture
async def product_with_invalid_width(db_session):
    """Create a product with non-numeric width value."""
    product = RefProduct(
        vendor="Invalid",
        category="fixtures",
        product_code="INV-100",
        name="Invalid Width Product",
        brand="Invalid",
        model_number="INV100",
        dimensions={"width_mm": "not-a-number"},  # Invalid width
        specifications={},
        sku="SKU-INV",
    )
    db_session.add(product)
    await db_session.commit()
    return product


@pytest.mark.asyncio
async def test_list_products_handles_invalid_width(client, product_with_invalid_width):
    """Test that products with invalid width values are handled gracefully."""
    response = await client.get(
        "/api/v1/products",
        params={"width_mm_min": 100},
    )
    assert response.status_code == 200
    # Product with invalid width should be excluded (treated as None)
    payload = response.json()
    assert all(p["product_code"] != "INV-100" for p in payload)
