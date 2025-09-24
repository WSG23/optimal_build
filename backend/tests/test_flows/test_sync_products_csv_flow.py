"""Tests for the CSV-based product sync flow."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

import pytest_asyncio
from backend.flows import sync_products as sync_products_flow
from sqlalchemy import Column, DateTime, Integer, String, select


class Base(DeclarativeBase):
    pass


class Product(Base):
    """Simplified reference product model for testing."""

    __tablename__ = "ref_products"

    id = Column(Integer, primary_key=True)
    vendor = Column(String(100), nullable=False, index=True)
    sku = Column(String(100), nullable=False, index=True)
    data_source = Column(String(20), nullable=True)
    deprecated_at = Column(DateTime, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)


@pytest_asyncio.fixture
async def product_session_factory() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()


def _write_sample_csv(path: Path) -> None:
    path.write_text(
        """brand,model,sku,category,width_mm,depth_mm,height_mm,weight_kg,power_w,bim_uri,spec_uri
IkeaBrand,ModernSeat,SKU-1,chair,600,500,400,12.5,20.1,https://example.com/bim1,https://example.com/spec1
IkeaBrand,NewSeat,SKU-4,chair,650,520,410,11.2,18.5,https://example.com/bim4,https://example.com/spec4
""",
        encoding="utf-8",
    )


@pytest.mark.asyncio
async def test_sync_products_marks_missing_skus(
    tmp_path: Path,
    product_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Products absent from a vendor feed should be deprecated without touching others."""

    monkeypatch.setattr(sync_products_flow, "RefProduct", Product, raising=False)

    async with product_session_factory() as session:
        session.add_all(
            [
                Product(vendor="ikea", sku="SKU-1", data_source="csv"),
                Product(vendor="ikea", sku="SKU-2", data_source="csv"),
                Product(vendor="ikea", sku="SKU-5", data_source="manual"),
                Product(vendor="acme", sku="SKU-3", data_source="csv"),
            ]
        )
        await session.commit()

    csv_path = tmp_path / "products.csv"
    _write_sample_csv(csv_path)

    result = await sync_products_flow.sync_products_csv_once(
        str(csv_path), vendor="ikea", session_factory=product_session_factory
    )

    assert result == {
        "ok": True,
        "inserted": 2,
        "deprecated": 1,
        "report": result["report"],
    }
    assert result["report"]["failed"] == 0

    async with product_session_factory() as session:
        rows = (
            (await session.execute(select(Product).order_by(Product.sku)))
            .scalars()
            .all()
        )

    by_sku = {row.sku: row for row in rows}

    assert by_sku["SKU-1"].deprecated_at is None
    assert by_sku["SKU-1"].data_source == "csv"
    assert by_sku["SKU-2"].deprecated_at is not None
    assert isinstance(by_sku["SKU-2"].deprecated_at, dt.datetime)
    assert by_sku["SKU-3"].deprecated_at is None  # different vendor untouched
    assert by_sku["SKU-5"].deprecated_at is None  # non-csv source untouched
    assert by_sku["SKU-4"].vendor == "ikea"
    assert by_sku["SKU-4"].data_source == "csv"
