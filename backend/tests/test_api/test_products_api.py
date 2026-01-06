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
