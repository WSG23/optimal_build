"""Comprehensive tests for Property model and related entities."""

from __future__ import annotations

import pytest
from datetime import date, datetime
from decimal import Decimal
import uuid as uuid_module

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.property import (
    Property,
    PropertyType,
    PropertyStatus,
    TenureType,
    MarketTransaction,
    RentalListing,
    DevelopmentPipeline,
    PropertyPhoto,
    DevelopmentAnalysis,
)


pytestmark = pytest.mark.asyncio


class TestPropertyModel:
    """Test Property model CRUD operations and validation."""

    async def test_create_minimal_property(self, session: AsyncSession):
        """Test creating a property with only required fields."""
        prop = Property(
            name="Minimal Property",
            address="123 Test Street",
            property_type=PropertyType.OFFICE,
            location="POINT(103.8535 1.2830)",
        )
        session.add(prop)
        await session.commit()
        await session.refresh(prop)

        assert prop.id is not None
        assert prop.name == "Minimal Property"
        assert prop.address == "123 Test Street"
        assert prop.property_type == PropertyType.OFFICE
        assert prop.status == PropertyStatus.EXISTING  # default value
        assert prop.location is not None

    async def test_create_full_property(self, session: AsyncSession):
        """Test creating a property with all fields populated."""
        prop = Property(
            name="Marina Waterfront Complex",
            address="456 Marina Boulevard, Singapore 018989",
            postal_code="018989",
            property_type=PropertyType.MIXED_USE,
            status=PropertyStatus.COMPLETED,
            location="POINT(103.8535 1.2830)",
            district="Downtown Core",
            subzone="Marina Centre",
            planning_area="Downtown Core",
            land_area_sqm=Decimal("5000.00"),
            gross_floor_area_sqm=Decimal("125000.00"),
            net_lettable_area_sqm=Decimal("110000.00"),
            building_height_m=Decimal("180.50"),
            floors_above_ground=45,
            floors_below_ground=3,
            units_total=500,
            year_built=2010,
            year_renovated=2020,
            developer="Premium Developers Pte Ltd",
            architect="Iconic Architects",
            tenure_type=TenureType.LEASEHOLD_99,
            lease_start_date=date(2010, 1, 1),
            lease_expiry_date=date(2109, 1, 1),
            zoning_code="C6",
            plot_ratio=Decimal("6.50"),
            is_conservation=False,
            conservation_status=None,
            ura_property_id="URA-2010-001",
            data_source="URA database",
            heritage_constraints=None,
            external_references={"gmap": "123456789"},
        )
        session.add(prop)
        await session.commit()
        await session.refresh(prop)

        assert prop.id is not None
        assert prop.name == "Marina Waterfront Complex"
        assert prop.postal_code == "018989"
        assert prop.property_type == PropertyType.MIXED_USE
        assert prop.status == PropertyStatus.COMPLETED
        assert prop.district == "Downtown Core"
        assert prop.gross_floor_area_sqm == Decimal("125000.00")
        assert prop.building_height_m == Decimal("180.50")
        assert prop.floors_above_ground == 45
        assert prop.year_built == 2010
        assert prop.developer == "Premium Developers Pte Ltd"
        assert prop.tenure_type == TenureType.LEASEHOLD_99
        assert prop.ura_property_id == "URA-2010-001"
        assert prop.plot_ratio == Decimal("6.50")

    async def test_all_property_types(self, session: AsyncSession):
        """Test that all PropertyType enum values can be stored."""
        property_types = [
            PropertyType.OFFICE,
            PropertyType.RETAIL,
            PropertyType.INDUSTRIAL,
            PropertyType.RESIDENTIAL,
            PropertyType.MIXED_USE,
            PropertyType.HOTEL,
            PropertyType.WAREHOUSE,
            PropertyType.LAND,
            PropertyType.SPECIAL_PURPOSE,
        ]

        for idx, ptype in enumerate(property_types):
            prop = Property(
                name=f"Test {ptype.value}",
                address=f"{idx} Test Lane",
                property_type=ptype,
                location="POINT(103.8535 1.2830)",
            )
            session.add(prop)

        await session.commit()

        result = await session.execute(select(Property))
        properties = result.scalars().all()
        assert len(properties) == len(property_types)

        # Verify each type is present
        stored_types = {p.property_type for p in properties}
        assert stored_types == set(property_types)

    async def test_all_property_statuses(self, session: AsyncSession):
        """Test that all PropertyStatus enum values can be stored."""
        statuses = [
            PropertyStatus.EXISTING,
            PropertyStatus.PLANNED,
            PropertyStatus.APPROVED,
            PropertyStatus.UNDER_CONSTRUCTION,
            PropertyStatus.COMPLETED,
            PropertyStatus.DEMOLISHED,
        ]

        for idx, status in enumerate(statuses):
            prop = Property(
                name=f"Test Status {status.value}",
                address=f"{idx} Status Street",
                property_type=PropertyType.OFFICE,
                status=status,
                location="POINT(103.8535 1.2830)",
            )
            session.add(prop)

        await session.commit()

        result = await session.execute(select(Property))
        properties = result.scalars().all()
        assert len(properties) == len(statuses)

        # Verify each status is present
        stored_statuses = {p.status for p in properties}
        assert stored_statuses == set(statuses)

    async def test_all_tenure_types(self, session: AsyncSession):
        """Test that all TenureType enum values can be stored."""
        tenure_types = [
            TenureType.FREEHOLD,
            TenureType.LEASEHOLD_99,
            TenureType.LEASEHOLD_999,
            TenureType.LEASEHOLD_60,
            TenureType.LEASEHOLD_30,
            TenureType.LEASEHOLD_OTHER,
        ]

        for idx, tenure in enumerate(tenure_types):
            prop = Property(
                name=f"Test Tenure {tenure.value}",
                address=f"{idx} Tenure Road",
                property_type=PropertyType.RESIDENTIAL,
                tenure_type=tenure,
                location="POINT(103.8535 1.2830)",
            )
            session.add(prop)

        await session.commit()

        result = await session.execute(select(Property))
        properties = result.scalars().all()
        assert len(properties) == len(tenure_types)

        # Verify each tenure type is present
        stored_tenures = {p.tenure_type for p in properties}
        assert stored_tenures == set(tenure_types)

    async def test_ura_property_id_unique_constraint(self, session: AsyncSession):
        """Test that ura_property_id must be unique when provided."""
        prop1 = Property(
            name="Property 1",
            address="111 Street",
            property_type=PropertyType.OFFICE,
            ura_property_id="URA-UNIQUE-001",
            location="POINT(103.8535 1.2830)",
        )
        session.add(prop1)
        await session.commit()

        prop2 = Property(
            name="Property 2",
            address="222 Street",
            property_type=PropertyType.OFFICE,
            ura_property_id="URA-UNIQUE-001",  # Duplicate
            location="POINT(103.8535 1.2830)",
        )
        session.add(prop2)

        with pytest.raises(Exception) as exc_info:
            await session.commit()

        assert (
            "unique" in str(exc_info.value).lower()
            or "duplicate" in str(exc_info.value).lower()
        )

    async def test_property_numeric_fields(self, session: AsyncSession):
        """Test numeric fields with decimal precision."""
        prop = Property(
            name="Precision Test Property",
            address="999 Precision Lane",
            property_type=PropertyType.OFFICE,
            location="POINT(103.8535 1.2830)",
            land_area_sqm=Decimal("1234.56"),
            gross_floor_area_sqm=Decimal("98765.43"),
            net_lettable_area_sqm=Decimal("87654.32"),
            building_height_m=Decimal("156.78"),
            plot_ratio=Decimal("3.25"),
        )
        session.add(prop)
        await session.commit()
        await session.refresh(prop)

        assert prop.land_area_sqm == Decimal("1234.56")
        assert prop.gross_floor_area_sqm == Decimal("98765.43")
        assert prop.net_lettable_area_sqm == Decimal("87654.32")
        assert prop.building_height_m == Decimal("156.78")
        assert prop.plot_ratio == Decimal("3.25")

    async def test_property_json_fields(self, session: AsyncSession):
        """Test JSON fields for storing structured data."""
        heritage_data = {
            "conservation_class": "A",
            "protected_elements": ["facade", "interior"],
        }
        external_refs = {
            "google_maps": "https://maps.google.com/...",
            "streetview": "https://streetview.google.com/...",
        }

        prop = Property(
            name="JSON Test Property",
            address="555 JSON Street",
            property_type=PropertyType.OFFICE,
            location="POINT(103.8535 1.2830)",
            is_conservation=True,
            conservation_status="Grade A",
            heritage_constraints=heritage_data,
            external_references=external_refs,
        )
        session.add(prop)
        await session.commit()
        await session.refresh(prop)

        assert prop.heritage_constraints == heritage_data
        assert prop.external_references == external_refs
        assert prop.is_conservation is True
        assert prop.conservation_status == "Grade A"

    async def test_property_date_fields(self, session: AsyncSession):
        """Test date fields for lease and development timelines."""
        lease_start = date(2015, 1, 1)
        lease_expiry = date(2114, 1, 1)

        prop = Property(
            name="Date Test Property",
            address="777 Date Avenue",
            property_type=PropertyType.RESIDENTIAL,
            location="POINT(103.8535 1.2830)",
            tenure_type=TenureType.LEASEHOLD_99,
            lease_start_date=lease_start,
            lease_expiry_date=lease_expiry,
            year_built=2015,
            year_renovated=2020,
        )
        session.add(prop)
        await session.commit()
        await session.refresh(prop)

        assert prop.lease_start_date == lease_start
        assert prop.lease_expiry_date == lease_expiry
        assert prop.year_built == 2015
        assert prop.year_renovated == 2020

    async def test_property_integer_fields(self, session: AsyncSession):
        """Test integer fields for floors and units."""
        prop = Property(
            name="Integer Test Property",
            address="888 Integer Drive",
            property_type=PropertyType.OFFICE,
            location="POINT(103.8535 1.2830)",
            floors_above_ground=50,
            floors_below_ground=5,
            units_total=750,
            year_built=2018,
        )
        session.add(prop)
        await session.commit()
        await session.refresh(prop)

        assert prop.floors_above_ground == 50
        assert prop.floors_below_ground == 5
        assert prop.units_total == 750
        assert prop.year_built == 2018

    async def test_property_update(self, session: AsyncSession):
        """Test updating property fields."""
        prop = Property(
            name="Original Name",
            address="100 Original Lane",
            property_type=PropertyType.OFFICE,
            location="POINT(103.8535 1.2830)",
            status=PropertyStatus.PLANNED,
            floors_above_ground=20,
        )
        session.add(prop)
        await session.commit()
        await session.refresh(prop)
        original_id = prop.id

        # Update fields
        prop.name = "Updated Name"
        prop.status = PropertyStatus.UNDER_CONSTRUCTION
        prop.floors_above_ground = 30
        prop.completion_percentage = 50.0
        await session.commit()
        await session.refresh(prop)

        assert prop.id == original_id
        assert prop.name == "Updated Name"
        assert prop.status == PropertyStatus.UNDER_CONSTRUCTION
        assert prop.floors_above_ground == 30

    async def test_query_properties_by_type(self, session: AsyncSession):
        """Test querying properties by property type."""
        for _i in range(3):
            prop = Property(
                name=f"Office {_i}",
                address=f"{_i} Office Lane",
                property_type=PropertyType.OFFICE,
                location="POINT(103.8535 1.2830)",
            )
            session.add(prop)

        for _i in range(2):
            prop = Property(
                name=f"Retail {_i}",
                address=f"{_i} Retail Street",
                property_type=PropertyType.RETAIL,
                location="POINT(103.8535 1.2830)",
            )
            session.add(prop)

        await session.commit()

        # Query office properties
        stmt = select(Property).where(Property.property_type == PropertyType.OFFICE)
        result = await session.execute(stmt)
        office_props = result.scalars().all()
        assert len(office_props) == 3

        # Query retail properties
        stmt = select(Property).where(Property.property_type == PropertyType.RETAIL)
        result = await session.execute(stmt)
        retail_props = result.scalars().all()
        assert len(retail_props) == 2

    async def test_query_properties_by_status(self, session: AsyncSession):
        """Test querying properties by status."""
        for _i in range(4):
            prop = Property(
                name=f"Existing {_i}",
                address=f"{_i} Existing Road",
                property_type=PropertyType.OFFICE,
                status=PropertyStatus.EXISTING,
                location="POINT(103.8535 1.2830)",
            )
            session.add(prop)

        for _i in range(2):
            prop = Property(
                name=f"Planned {_i}",
                address=f"{_i} Planned Avenue",
                property_type=PropertyType.OFFICE,
                status=PropertyStatus.PLANNED,
                location="POINT(103.8535 1.2830)",
            )
            session.add(prop)

        await session.commit()

        stmt = select(Property).where(Property.status == PropertyStatus.EXISTING)
        result = await session.execute(stmt)
        existing = result.scalars().all()
        assert len(existing) == 4

        stmt = select(Property).where(Property.status == PropertyStatus.PLANNED)
        result = await session.execute(stmt)
        planned = result.scalars().all()
        assert len(planned) == 2

    async def test_property_optional_fields_nullable(self, session: AsyncSession):
        """Test that optional fields can be null."""
        prop = Property(
            name="Minimal Optional",
            address="123 Optional Street",
            property_type=PropertyType.LAND,
            location="POINT(103.8535 1.2830)",
            postal_code=None,
            district=None,
            subzone=None,
            planning_area=None,
            land_area_sqm=None,
            gross_floor_area_sqm=None,
            year_built=None,
            developer=None,
            architect=None,
            tenure_type=None,
            zoning_code=None,
            conservation_status=None,
            ura_property_id=None,
        )
        session.add(prop)
        await session.commit()
        await session.refresh(prop)

        assert prop.postal_code is None
        assert prop.district is None
        assert prop.developer is None
        assert prop.tenure_type is None
        assert prop.ura_property_id is None


class TestMarketTransactionModel:
    """Test MarketTransaction model for property sales records."""

    async def test_create_market_transaction(self, session: AsyncSession):
        """Test creating a market transaction."""
        # Create property first
        prop = Property(
            name="Transaction Test Property",
            address="200 Transaction Street",
            property_type=PropertyType.OFFICE,
            location="POINT(103.8535 1.2830)",
        )
        session.add(prop)
        await session.commit()
        await session.refresh(prop)

        # Create transaction
        txn = MarketTransaction(
            property_id=prop.id,
            transaction_date=date(2023, 6, 15),
            transaction_type="sale",
            sale_price=Decimal("50000000.00"),
            psf_price=Decimal("2500.00"),
            psm_price=Decimal("26910.00"),
            buyer_type="company",
            seller_type="individual",
            buyer_profile={"name": "ABC Corp", "country": "Singapore"},
            data_source="URA",
            confidence_score=Decimal("0.95"),
        )
        session.add(txn)
        await session.commit()
        await session.refresh(txn)

        assert txn.id is not None
        assert txn.property_id == prop.id
        assert txn.sale_price == Decimal("50000000.00")
        assert txn.transaction_type == "sale"
        assert txn.buyer_type == "company"

    async def test_market_transaction_relationships(self, session: AsyncSession):
        """Test that transactions are linked to properties."""
        prop = Property(
            name="Relationship Property",
            address="300 Relationship Lane",
            property_type=PropertyType.OFFICE,
            location="POINT(103.8535 1.2830)",
        )
        session.add(prop)
        await session.commit()
        await session.refresh(prop)

        txn1 = MarketTransaction(
            property_id=prop.id,
            transaction_date=date(2020, 1, 1),
            sale_price=Decimal("40000000.00"),
            data_source="URA",
        )
        txn2 = MarketTransaction(
            property_id=prop.id,
            transaction_date=date(2023, 1, 1),
            sale_price=Decimal("50000000.00"),
            data_source="URA",
        )
        session.add(txn1)
        session.add(txn2)
        await session.commit()

        # Query to verify relationship
        stmt = select(MarketTransaction).where(MarketTransaction.property_id == prop.id)
        result = await session.execute(stmt)
        transactions = result.scalars().all()
        assert len(transactions) == 2
        assert all(t.property_id == prop.id for t in transactions)


class TestRentalListingModel:
    """Test RentalListing model for rental information."""

    async def test_create_rental_listing(self, session: AsyncSession):
        """Test creating a rental listing."""
        prop = Property(
            name="Rental Property",
            address="400 Rental Street",
            property_type=PropertyType.OFFICE,
            location="POINT(103.8535 1.2830)",
        )
        session.add(prop)
        await session.commit()
        await session.refresh(prop)

        listing = RentalListing(
            property_id=prop.id,
            listing_date=date(2024, 1, 1),
            listing_type="whole_building",
            is_active=True,
            floor_area_sqm=Decimal("5000.00"),
            floor_level="1-10",
            unit_number=None,
            asking_rent_monthly=Decimal("100000.00"),
            asking_psf_monthly=Decimal("20.00"),
            listing_source="PropTech",
            agent_company="Premium Agents Pte Ltd",
        )
        session.add(listing)
        await session.commit()
        await session.refresh(listing)

        assert listing.id is not None
        assert listing.property_id == prop.id
        assert listing.is_active is True
        assert listing.asking_rent_monthly == Decimal("100000.00")
        assert listing.listing_type == "whole_building"

    async def test_rental_listing_active_filter(self, session: AsyncSession):
        """Test filtering rental listings by active status."""
        prop = Property(
            name="Multi Listing Property",
            address="500 Multi Street",
            property_type=PropertyType.OFFICE,
            location="POINT(103.8535 1.2830)",
        )
        session.add(prop)
        await session.commit()
        await session.refresh(prop)

        # Create active and inactive listings
        for _i in range(3):
            listing = RentalListing(
                property_id=prop.id,
                listing_date=date(2024, 1, 1),
                is_active=True,
                floor_area_sqm=Decimal("1000.00"),
                listing_source="Source",
            )
            session.add(listing)

        for _i in range(2):
            listing = RentalListing(
                property_id=prop.id,
                listing_date=date(2023, 1, 1),
                is_active=False,
                floor_area_sqm=Decimal("1000.00"),
                listing_source="Source",
            )
            session.add(listing)

        await session.commit()

        stmt = select(RentalListing).where(RentalListing.is_active.is_(True))
        result = await session.execute(stmt)
        active = result.scalars().all()
        assert len(active) == 3

        stmt = select(RentalListing).where(RentalListing.is_active.is_(False))
        result = await session.execute(stmt)
        inactive = result.scalars().all()
        assert len(inactive) == 2


class TestDevelopmentPipelineModel:
    """Test DevelopmentPipeline model for upcoming projects."""

    async def test_create_development_pipeline(self, session: AsyncSession):
        """Test creating a development pipeline entry."""
        pipeline = DevelopmentPipeline(
            project_name="Signature Towers",
            developer="Grand Developers",
            project_type=PropertyType.OFFICE,
            location="POINT(103.8535 1.2830)",
            address="600 Pipeline Avenue",
            district="Downtown Core",
            total_gfa_sqm=Decimal("150000.00"),
            total_units=500,
            building_count=2,
            announcement_date=date(2023, 1, 1),
            approval_date=date(2023, 6, 1),
            construction_start=date(2024, 1, 1),
            expected_completion=date(2026, 12, 31),
            development_status=PropertyStatus.UNDER_CONSTRUCTION,
            completion_percentage=Decimal("35.50"),
            units_launched=500,
            units_sold=350,
            average_psf_transacted=Decimal("3500.00"),
            data_source="URA",
        )
        session.add(pipeline)
        await session.commit()
        await session.refresh(pipeline)

        assert pipeline.id is not None
        assert pipeline.project_name == "Signature Towers"
        assert pipeline.total_units == 500
        assert pipeline.development_status == PropertyStatus.UNDER_CONSTRUCTION
        assert pipeline.completion_percentage == Decimal("35.50")

    async def test_pipeline_with_json_fields(self, session: AsyncSession):
        """Test development pipeline with JSON fields."""
        pipeline = DevelopmentPipeline(
            project_name="Mixed Use Complex",
            project_type=PropertyType.MIXED_USE,
            location="POINT(103.8535 1.2830)",
            development_status=PropertyStatus.PLANNED,
            estimated_supply_impact={
                "office_units": 100,
                "retail_units": 50,
                "residential_units": 200,
            },
            competing_projects=[
                str(uuid_module.uuid4()),
                str(uuid_module.uuid4()),
            ],
        )
        session.add(pipeline)
        await session.commit()
        await session.refresh(pipeline)

        assert pipeline.estimated_supply_impact is not None
        assert pipeline.estimated_supply_impact["office_units"] == 100
        assert len(pipeline.competing_projects) == 2


class TestPropertyPhotoModel:
    """Test PropertyPhoto model for property images."""

    async def test_create_property_photo(self, session: AsyncSession):
        """Test creating a property photo record."""
        prop = Property(
            name="Photo Test Property",
            address="700 Photo Lane",
            property_type=PropertyType.OFFICE,
            location="POINT(103.8535 1.2830)",
        )
        session.add(prop)
        await session.commit()
        await session.refresh(prop)

        photo = PropertyPhoto(
            property_id=prop.id,
            storage_key="photos/property-001/image-001.jpg",
            filename="facade_front.jpg",
            mime_type="image/jpeg",
            file_size_bytes=2500000,
            capture_date=datetime(2024, 1, 15, 10, 30),
            photographer="John Photographer",
            auto_tags=["building", "facade", "modern"],
            manual_tags=["facade", "main entrance"],
            copyright_owner="Property Dev Corp",
            usage_rights="commercial_use",
        )
        session.add(photo)
        await session.commit()
        await session.refresh(photo)

        assert photo.id is not None
        assert photo.property_id == prop.id
        assert photo.storage_key == "photos/property-001/image-001.jpg"
        assert photo.auto_tags == ["building", "facade", "modern"]
        assert photo.file_size_bytes == 2500000

    async def test_photo_count_per_property(self, session: AsyncSession):
        """Test multiple photos per property."""
        prop = Property(
            name="Multi Photo Property",
            address="800 Photo Street",
            property_type=PropertyType.OFFICE,
            location="POINT(103.8535 1.2830)",
        )
        session.add(prop)
        await session.commit()
        await session.refresh(prop)

        # Add multiple photos
        for _i in range(5):
            photo = PropertyPhoto(
                property_id=prop.id,
                storage_key=f"photos/property-001/image-{_i:03d}.jpg",
                filename=f"image_{_i}.jpg",
                mime_type="image/jpeg",
                file_size_bytes=1000000,
            )
            session.add(photo)

        await session.commit()

        stmt = select(PropertyPhoto).where(PropertyPhoto.property_id == prop.id)
        result = await session.execute(stmt)
        photos = result.scalars().all()
        assert len(photos) == 5


class TestDevelopmentAnalysisModel:
    """Test DevelopmentAnalysis model for analysis results."""

    async def test_create_development_analysis(self, session: AsyncSession):
        """Test creating a development analysis."""
        prop = Property(
            name="Analysis Test Property",
            address="900 Analysis Drive",
            property_type=PropertyType.OFFICE,
            location="POINT(103.8535 1.2830)",
        )
        session.add(prop)
        await session.commit()
        await session.refresh(prop)

        analysis = DevelopmentAnalysis(
            property_id=prop.id,
            analysis_type="existing_building",
            gfa_potential_sqm=Decimal("200000.00"),
            optimal_use_mix={"office": 0.60, "retail": 0.40},
            market_value_estimate=Decimal("500000000.00"),
            projected_cap_rate=Decimal("4.50"),
            site_constraints=["heritage", "conservation"],
            regulatory_constraints=["height limit 150m", "setback 10m"],
            heritage_constraints={"conservation_class": "A"},
            development_opportunities=["mixed_use", "vertical_expansion"],
            recommended_scenario="office_retail_mix",
            methodology="comparative_market_analysis",
            confidence_level=Decimal("0.85"),
            assumptions={
                "rental_growth": 0.03,
                "expense_ratio": 0.25,
            },
        )
        session.add(analysis)
        await session.commit()
        await session.refresh(analysis)

        assert analysis.id is not None
        assert analysis.property_id == prop.id
        assert analysis.analysis_type == "existing_building"
        assert analysis.gfa_potential_sqm == Decimal("200000.00")
        assert analysis.optimal_use_mix["office"] == 0.60
        assert analysis.market_value_estimate == Decimal("500000000.00")

    async def test_analysis_with_scenarios(self, session: AsyncSession):
        """Test development analysis with multiple scenarios."""
        prop = Property(
            name="Scenario Test Property",
            address="1000 Scenario Road",
            property_type=PropertyType.LAND,
            location="POINT(103.8535 1.2830)",
        )
        session.add(prop)
        await session.commit()
        await session.refresh(prop)

        scenarios = {
            "scenario_1": {"name": "Office", "gfa": 100000, "value": 400000000},
            "scenario_2": {"name": "Mixed Use", "gfa": 150000, "value": 550000000},
            "scenario_3": {"name": "Residential", "gfa": 120000, "value": 480000000},
        }

        analysis = DevelopmentAnalysis(
            property_id=prop.id,
            analysis_type="raw_land",
            development_scenarios=scenarios,
            recommended_scenario="scenario_2",
            confidence_level=Decimal("0.80"),
        )
        session.add(analysis)
        await session.commit()
        await session.refresh(analysis)

        assert len(analysis.development_scenarios) == 3
        assert analysis.development_scenarios["scenario_2"]["name"] == "Mixed Use"
        assert analysis.recommended_scenario == "scenario_2"

    async def test_multiple_analyses_per_property(self, session: AsyncSession):
        """Test multiple analyses for the same property over time."""
        prop = Property(
            name="Multi Analysis Property",
            address="1100 Analysis Lane",
            property_type=PropertyType.OFFICE,
            location="POINT(103.8535 1.2830)",
        )
        session.add(prop)
        await session.commit()
        await session.refresh(prop)

        # Create analyses at different times
        for _i in range(3):
            analysis = DevelopmentAnalysis(
                property_id=prop.id,
                analysis_type="existing_building",
                market_value_estimate=Decimal(str(400000000 + (_i * 50000000))),
                confidence_level=Decimal("0.80"),
            )
            session.add(analysis)

        await session.commit()

        stmt = select(DevelopmentAnalysis).where(
            DevelopmentAnalysis.property_id == prop.id
        )
        result = await session.execute(stmt)
        analyses = result.scalars().all()
        assert len(analyses) == 3
