#!/usr/bin/env python3
"""Create demo property using the working test fixture approach."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


async def create_demo_property():
    """Create a demo property using raw SQL that matches the fixture pattern."""

    engine = create_async_engine(
        "postgresql+asyncpg://postgres:password@localhost:5432/building_compliance",
        echo=False,
    )

    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # First check if properties table exists
        result = await session.execute(
            text("SELECT 1 FROM properties LIMIT 1")
        )

        # Generate a new UUID
        result = await session.execute(text("SELECT gen_random_uuid()"))
        property_id = result.scalar()

        # Insert using the same pattern as the test fixture
        await session.execute(
            text("""
                INSERT INTO properties (
                    id, name, address, postal_code, property_type, status,
                    location, district, subzone, planning_area,
                    land_area_sqm, gross_floor_area_sqm, net_lettable_area_sqm,
                    building_height_m, floors_above_ground, floors_below_ground,
                    units_total, year_built, developer, architect,
                    tenure_type, plot_ratio, is_conservation, data_source
                ) VALUES (
                    :id,
                    'Marina Bay Executive Tower',
                    '1 Marina Boulevard, Singapore',
                    '018989',
                    'office',
                    'existing',
                    ST_GeomFromText('POINT(103.8535 1.2830)', 4326),
                    'Downtown Core',
                    'Marina Centre',
                    'Downtown Core',
                    8000.0,
                    45000.0,
                    40000.0,
                    180.0,
                    40,
                    3,
                    200,
                    2018,
                    'Demo Developers Pte Ltd',
                    'Demo Architects LLP',
                    'leasehold_99',
                    5.625,
                    false,
                    'manual_demo'
                )
            """),
            {"id": property_id}
        )
        await session.commit()

        print(f"✅ Created demo property:")
        print(f"   ID: {property_id}")
        print(f"   Name: Marina Bay Executive Tower")
        print(f"   Type: Office")
        print(f"   GFA: 45,000 sqm")
        print(f"\n🌐 Test URL:")
        print(f"   http://localhost:4400/#/agents/advisory?propertyId={property_id}")
        print(f"\n🧪 Test API:")
        print(f"   curl -H 'X-Role: admin' http://localhost:9400/api/v1/agents/commercial-property/properties/{property_id}/advisory")

        return str(property_id)


if __name__ == "__main__":
    property_id = asyncio.run(create_demo_property())
