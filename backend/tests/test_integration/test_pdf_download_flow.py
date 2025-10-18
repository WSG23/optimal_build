"""Integration tests for PDF generation and download flow.

Tests the complete user journey: generate PDF → get download URL → download file → verify content.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
import io
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.property import (
    DevelopmentAnalysis,
    MarketTransaction,
    Property,
    PropertyType,
)
from httpx import AsyncClient
import pytest_asyncio


@pytest_asyncio.fixture
async def integration_test_property(session: AsyncSession) -> Property:
    """Create a complete property with all related data for integration testing."""
    # Create property
    property_obj = Property(
        id=UUID("a1234567-89ab-cdef-0123-456789abcdef"),
        name="Integration Test Tower",
        address="999 Integration Ave, Singapore",
        property_type=PropertyType.OFFICE,
        district="D01",
        land_area_sqm=6000,
        gross_floor_area_sqm=48000,
        year_built=2018,
    )
    session.add(property_obj)

    # Create development analysis
    analysis = DevelopmentAnalysis(
        property_id=property_obj.id,
        analysis_date=date.today(),
        gfa_potential_sqm=55000,
        optimal_use_mix={"office": 70, "retail": 30},
        market_value_estimate=Decimal("120000000"),
        projected_cap_rate=Decimal("4.2"),
    )
    session.add(analysis)

    # Create market transactions
    for i in range(3):
        transaction = MarketTransaction(
            property_id=property_obj.id,
            transaction_date=date(2025, i + 1, 10),
            transaction_type="sale",
            sale_price=Decimal(f"{80000000 + i * 2000000}"),
            psf_price=Decimal(f"{2800 + i * 100}"),
            market_segment="CBD",
            data_source="integration_test",
        )
        session.add(transaction)

    await session.commit()
    await session.refresh(property_obj)
    return property_obj


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_pdf_generation_download_flow(
    client: AsyncClient, integration_test_property: Property
):
    """Test complete PDF flow: generate → verify response → download → validate content."""
    property_id = str(integration_test_property.id)

    # Step 1: Generate PDF via API
    generate_response = await client.post(
        f"/api/v1/agents/commercial-property/properties/{property_id}/generate-pack/universal"
    )

    # Verify generation succeeded
    assert (
        generate_response.status_code == 200
    ), f"Generation failed: {generate_response.text}"

    data = generate_response.json()

    # Verify response structure
    assert "pack_type" in data
    assert data["pack_type"] == "universal"
    assert "property_id" in data
    assert data["property_id"] == property_id
    assert "filename" in data
    assert "download_url" in data
    assert "generated_at" in data
    assert "size_bytes" in data

    # Step 2: Verify download URL is absolute (not relative)
    download_url = data["download_url"]
    assert download_url.startswith(
        "http://"
    ), f"download_url should be absolute, got: {download_url}"
    assert (
        "localhost:9400" in download_url or "127.0.0.1:9400" in download_url
    ), f"download_url should point to backend port 9400, got: {download_url}"

    # Step 3: Verify PDF size is reasonable
    size_bytes = data["size_bytes"]
    assert size_bytes > 10000, f"PDF too small ({size_bytes} bytes), likely blank"
    assert size_bytes < 10000000, f"PDF too large ({size_bytes} bytes), possible issue"

    # Step 4: Download PDF from the provided URL
    # Extract the path from the absolute URL
    download_path = download_url.split("localhost:9400")[-1]
    download_response = await client.get(download_path)

    # Verify download succeeded
    assert (
        download_response.status_code == 200
    ), f"Download failed: {download_response.status_code}"

    # Verify content-type
    assert (
        download_response.headers["content-type"] == "application/pdf"
    ), f"Wrong content-type: {download_response.headers.get('content-type')}"

    # Verify content-length matches reported size
    content_length = int(download_response.headers.get("content-length", 0))
    assert (
        content_length == size_bytes
    ), f"Content-Length ({content_length}) doesn't match size_bytes ({size_bytes})"

    # Step 5: Verify PDF has actual content
    pytest.importorskip("pypdf")
    from pypdf import PdfReader

    pdf_buffer = io.BytesIO(download_response.content)
    reader = PdfReader(pdf_buffer)

    # Check page count
    assert (
        len(reader.pages) >= 10
    ), f"PDF should have at least 10 pages, got {len(reader.pages)}"

    # Check page 1 content
    page1_text = reader.pages[0].extract_text()
    assert (
        len(page1_text) > 100
    ), f"Page 1 has insufficient text ({len(page1_text)} chars)"
    assert "Universal Site Pack" in page1_text, "Cover page missing title"
    assert (
        integration_test_property.name in page1_text
    ), "Cover page missing property name"

    # Check page 2 content
    page2_text = reader.pages[1].extract_text()
    assert (
        len(page2_text) > 100
    ), f"Page 2 has insufficient text ({len(page2_text)} chars)"

    # Step 6: Verify PDF metadata (Safari compatibility)
    assert reader.metadata is not None, "PDF missing metadata"
    metadata_dict = dict(reader.metadata)

    # Check title and author exist (required for Safari)
    title = metadata_dict.get("/Title", "")
    author = metadata_dict.get("/Author", "")
    assert title and title != "(anonymous)", "PDF missing proper title metadata"
    assert author and author != "(anonymous)", "PDF missing proper author metadata"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pdf_download_with_invalid_property_id(client: AsyncClient):
    """Test PDF generation with non-existent property ID returns 404."""
    invalid_id = "00000000-0000-0000-0000-000000000000"

    response = await client.post(
        f"/api/v1/agents/commercial-property/properties/{invalid_id}/generate-pack/universal"
    )

    # Should fail gracefully with 404 or 400
    assert response.status_code in (
        400,
        404,
    ), f"Expected 400/404 for invalid property, got {response.status_code}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pdf_download_file_not_found(client: AsyncClient):
    """Test downloading non-existent file returns 404."""
    property_id = "a1234567-89ab-cdef-0123-456789abcdef"
    fake_filename = "nonexistent_file_12345.pdf"

    response = await client.get(
        f"/api/v1/agents/commercial-property/files/{property_id}/{fake_filename}"
    )

    assert (
        response.status_code == 404
    ), f"Expected 404 for non-existent file, got {response.status_code}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pdf_generation_idempotency(
    client: AsyncClient, integration_test_property: Property
):
    """Test generating same PDF multiple times works correctly."""
    property_id = str(integration_test_property.id)

    # Generate PDF twice
    response1 = await client.post(
        f"/api/v1/agents/commercial-property/properties/{property_id}/generate-pack/universal"
    )
    response2 = await client.post(
        f"/api/v1/agents/commercial-property/properties/{property_id}/generate-pack/universal"
    )

    assert response1.status_code == 200
    assert response2.status_code == 200

    data1 = response1.json()
    data2 = response2.json()

    # Both should succeed and have same filename
    assert data1["filename"] == data2["filename"]

    # Size should be similar (may vary slightly due to timestamps)
    size_diff = abs(data1["size_bytes"] - data2["size_bytes"])
    assert (
        size_diff < 1000
    ), f"PDF sizes differ too much: {data1['size_bytes']} vs {data2['size_bytes']}"
