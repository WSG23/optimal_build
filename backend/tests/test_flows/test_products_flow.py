"""Tests for the vendor product sync flow."""

import pytest

pytest.importorskip("sqlalchemy")

from app.models.rkp import RefProduct
from flows.products import sync_vendor_products
from sqlalchemy import select


@pytest.mark.asyncio
async def test_sync_vendor_products(async_session_factory) -> None:
    payload = {
        "vendor": "Acme Fixtures",
        "products": [
            {
                "code": "AC-100",
                "name": "Accessible Basin",
                "category": "basin",
                "dimensions": {"width": 600, "depth": 500, "height": 850},
                "brand": "Acme",
                "model": "ComfortLine",
                "sku": "SKU-123",
                "bim_uri": "https://cdn.example.com/bim/ac-100.rvt",
                "spec_uri": "https://cdn.example.com/specs/ac-100.pdf",
            }
        ],
    }

    await sync_vendor_products(async_session_factory, payload)

    async with async_session_factory() as session:
        result = await session.execute(select(RefProduct))
        product = result.scalars().one()
        assert product.vendor == "Acme Fixtures"
        assert product.brand == "Acme"
        assert product.dimensions["width_mm"] == 600
        assert product.bim_uri.endswith(".rvt")
