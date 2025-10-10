#!/usr/bin/env python3
"""Create a test property for advisory demo."""

import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text


async def create_demo_property():
    """Create a demo property in the database."""

    # Connect to PostgreSQL
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:password@localhost:5432/building_compliance",
        echo=False,
    )

    async with engine.begin() as conn:
        # Create a demo office tower using raw SQL to avoid enum casting issues
        property_id = uuid.uuid4()

        await conn.execute(
            text("""
                INSERT INTO properties (
                    id, name, address, postal_code, property_type, status,
                    location, district, subzone, planning_area,
                    land_area_sqm, gross_floor_area_sqm, net_lettable_area_sqm,
                    building_height_m, floors_above_ground, floors_below_ground,
                    units_total, year_built, developer, architect,
                    tenure_type, plot_ratio, is_conservation, data_source
                ) VALUES (
                    :id, :name, :address, :postal_code,
                    :property_type::property_type, :status::property_status,
                    ST_GeomFromText(:location, 4326), :district, :subzone, :planning_area,
                    :land_area_sqm, :gross_floor_area_sqm, :net_lettable_area_sqm,
                    :building_height_m, :floors_above_ground, :floors_below_ground,
                    :units_total, :year_built, :developer, :architect,
                    :tenure_type::tenure_type, :plot_ratio, :is_conservation, :data_source
                )
            """),
            {
                "id": property_id,
                "name": "Marina Bay Executive Tower",
                "address": "1 Marina Boulevard, Singapore",
                "postal_code": "018989",
                "property_type": "office",
                "status": "existing",
                "location": "POINT(103.8535 1.2830)",
                "district": "Downtown Core",
                "subzone": "Marina Centre",
                "planning_area": "Downtown Core",
                "land_area_sqm": 8000.0,
                "gross_floor_area_sqm": 45000.0,
                "net_lettable_area_sqm": 40000.0,
                "building_height_m": 180.0,
                "floors_above_ground": 40,
                "floors_below_ground": 3,
                "units_total": 200,
                "year_built": 2018,
                "developer": "Demo Developers Pte Ltd",
                "architect": "Demo Architects LLP",
                "tenure_type": "leasehold_99",
                "plot_ratio": 5.625,
                "is_conservation": False,
                "data_source": "manual_demo",
            }
        )

        print(f"✅ Created demo property:")
        print(f"   ID: {property_id}")
        print(f"   Name: Marina Bay Executive Tower")
        print(f"   Type: Office")
        print(f"   GFA: 45,000 sqm")
        print(f"\n🌐 Test URL:")
        print(f"   http://localhost:4400/#/agents/advisory?propertyId={property_id}")

        return str(property_id)


if __name__ == "__main__":
    property_id = asyncio.run(create_demo_property())
