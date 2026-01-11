#!/usr/bin/env python3
"""
Seed script for regulatory compliance paths.

Seeds the database with:
1. Singapore regulatory agencies (URA, BCA, SCDF, etc.)
2. Compliance paths for each asset type (office, retail, heritage, etc.)

Usage:
    cd backend && python scripts/seed_compliance_paths.py
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Add parent directories to path for imports
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.regulatory import RegulatoryAgency, AssetCompliancePath


# Singapore Regulatory Agencies
AGENCIES = [
    {
        "code": "URA",
        "name": "Urban Redevelopment Authority",
        "description": "Singapore's national land use planning authority",
    },
    {
        "code": "BCA",
        "name": "Building and Construction Authority",
        "description": "Regulates building and construction industry in Singapore",
    },
    {
        "code": "SCDF",
        "name": "Singapore Civil Defence Force",
        "description": "Fire safety and emergency response authority",
    },
    {
        "code": "NEA",
        "name": "National Environment Agency",
        "description": "Environmental protection and public health authority",
    },
    {
        "code": "LTA",
        "name": "Land Transport Authority",
        "description": "Land transport infrastructure and traffic management",
    },
    {
        "code": "PUB",
        "name": "Public Utilities Board",
        "description": "Singapore's national water agency",
    },
    {
        "code": "STB",
        "name": "Singapore Tourism Board",
        "description": "Heritage conservation and tourism development",
    },
    {
        "code": "JTC",
        "name": "JTC Corporation",
        "description": "Industrial infrastructure and development agency",
    },
    {
        "code": "NPARKS",
        "name": "National Parks Board",
        "description": "Parks, nature reserves, and greenery management",
    },
    {
        "code": "SLA",
        "name": "Singapore Land Authority",
        "description": "State land administration and survey",
    },
]


# Compliance paths by asset type
# Format: (agency_code, submission_type, sequence_order, is_mandatory, duration_days, description)
COMPLIANCE_PATHS = {
    "office": [
        ("URA", "DC", 1, True, 42, "Development Control approval for land use"),
        ("BCA", "BP", 2, True, 28, "Building Plan approval for structural design"),
        ("SCDF", "CONSULTATION", 3, True, 14, "Fire safety clearance"),
        ("BCA", "TOP", 4, True, 14, "Temporary Occupation Permit"),
        ("BCA", "CSC", 5, True, 7, "Certificate of Statutory Completion"),
    ],
    "retail": [
        ("URA", "DC", 1, True, 42, "Development Control approval"),
        ("BCA", "BP", 2, True, 28, "Building Plan approval"),
        ("SCDF", "CONSULTATION", 3, True, 14, "Fire safety requirements for retail"),
        ("NEA", "CONSULTATION", 4, True, 7, "Food/environmental health clearance"),
        ("BCA", "TOP", 5, True, 14, "Temporary Occupation Permit"),
        ("BCA", "CSC", 6, True, 7, "Certificate of Statutory Completion"),
    ],
    "residential": [
        ("URA", "DC", 1, True, 56, "Development Control for residential use"),
        ("BCA", "BP", 2, True, 35, "Building Plan approval"),
        ("SCDF", "CONSULTATION", 3, True, 14, "Fire safety certification"),
        ("PUB", "CONSULTATION", 4, False, 7, "Drainage and sewerage consultation"),
        ("BCA", "TOP", 5, True, 14, "Temporary Occupation Permit"),
        ("BCA", "CSC", 6, True, 7, "Certificate of Statutory Completion"),
    ],
    "industrial": [
        ("JTC", "INDUSTRIAL_PERMIT", 1, True, 21, "Industrial land use permit"),
        ("URA", "DC", 2, True, 42, "Development Control approval"),
        ("BCA", "BP", 3, True, 28, "Building Plan approval"),
        ("NEA", "CONSULTATION", 4, True, 45, "Environmental impact assessment"),
        ("SCDF", "CONSULTATION", 5, True, 14, "Industrial fire safety"),
        ("BCA", "TOP", 6, True, 14, "Temporary Occupation Permit"),
        ("BCA", "CSC", 7, True, 7, "Certificate of Statutory Completion"),
    ],
    "heritage": [
        ("STB", "HERITAGE_APPROVAL", 1, True, 30, "Heritage conservation approval"),
        ("URA", "DC", 2, True, 42, "Development Control for conservation"),
        ("BCA", "BP", 3, True, 28, "Building Plan with heritage considerations"),
        ("SCDF", "CONSULTATION", 4, True, 14, "Fire safety for heritage buildings"),
        ("BCA", "TOP", 5, True, 14, "Temporary Occupation Permit"),
        ("BCA", "CSC", 6, True, 7, "Certificate of Statutory Completion"),
    ],
    "mixed_use": [
        ("URA", "DC", 1, True, 56, "Development Control for mixed use"),
        ("BCA", "BP", 2, True, 35, "Building Plan approval"),
        ("SCDF", "CONSULTATION", 3, True, 14, "Fire safety assessment"),
        ("NEA", "CONSULTATION", 4, False, 7, "Environmental clearance"),
        ("BCA", "TOP", 5, True, 14, "Temporary Occupation Permit"),
        ("BCA", "CSC", 6, True, 7, "Certificate of Statutory Completion"),
    ],
    "hospitality": [
        ("STB", "CONSULTATION", 1, True, 14, "Tourism board consultation"),
        ("URA", "DC", 2, True, 42, "Development Control approval"),
        ("BCA", "BP", 3, True, 28, "Building Plan approval"),
        ("SCDF", "CONSULTATION", 4, True, 21, "Fire safety for hospitality"),
        ("NEA", "CONSULTATION", 5, True, 7, "Health and sanitation clearance"),
        ("BCA", "TOP", 6, True, 14, "Temporary Occupation Permit"),
        ("BCA", "CSC", 7, True, 7, "Certificate of Statutory Completion"),
    ],
}


async def seed_agencies(db: AsyncSession) -> dict[str, RegulatoryAgency]:
    """Seed or fetch regulatory agencies, returning a code->agency mapping."""
    agency_map = {}

    for agency_data in AGENCIES:
        # Check if agency exists
        result = await db.execute(
            select(RegulatoryAgency).where(RegulatoryAgency.code == agency_data["code"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing agency with full details
            existing.name = agency_data["name"]
            existing.description = agency_data["description"]
            agency_map[agency_data["code"]] = existing
            print(f"  Updated agency: {agency_data['code']}")
        else:
            # Create new agency
            agency = RegulatoryAgency(
                id=uuid4(),
                code=agency_data["code"],
                name=agency_data["name"],
                description=agency_data["description"],
            )
            db.add(agency)
            agency_map[agency_data["code"]] = agency
            print(f"  Created agency: {agency_data['code']}")

    await db.commit()
    return agency_map


async def seed_compliance_paths(
    db: AsyncSession, agency_map: dict[str, RegulatoryAgency], reset: bool = False
) -> int:
    """Seed compliance paths for all asset types."""
    if reset:
        # Delete existing compliance paths
        await db.execute(delete(AssetCompliancePath))
        await db.commit()
        print("  Cleared existing compliance paths")

    count = 0
    for asset_type, paths in COMPLIANCE_PATHS.items():
        # Check if paths already exist for this asset type
        result = await db.execute(
            select(AssetCompliancePath).where(
                AssetCompliancePath.asset_type == asset_type
            )
        )
        existing = result.scalars().all()

        if existing and not reset:
            print(f"  Skipping {asset_type}: {len(existing)} paths already exist")
            continue

        print(f"  Seeding {asset_type} ({len(paths)} steps)...")
        for agency_code, submission_type, seq, mandatory, days, desc in paths:
            agency = agency_map.get(agency_code)
            if not agency:
                print(f"    WARNING: Agency {agency_code} not found, skipping")
                continue

            path = AssetCompliancePath(
                id=uuid4(),
                asset_type=asset_type,
                agency_id=agency.id,
                submission_type=submission_type,
                sequence_order=seq,
                is_mandatory=mandatory,
                typical_duration_days=days,
                description=desc,
            )
            db.add(path)
            count += 1

    await db.commit()
    return count


async def main(reset: bool = False):
    """Main entry point for seeding compliance paths."""
    print("\n=== Seeding Regulatory Compliance Paths ===\n")

    async with AsyncSessionLocal() as db:
        print("1. Seeding regulatory agencies...")
        agency_map = await seed_agencies(db)
        print(f"   {len(agency_map)} agencies ready\n")

        print("2. Seeding compliance paths...")
        count = await seed_compliance_paths(db, agency_map, reset=reset)
        print(f"   {count} compliance paths created\n")

    print("=== Seeding complete ===\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed compliance path data")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing compliance paths before seeding",
    )
    args = parser.parse_args()

    asyncio.run(main(reset=args.reset))
