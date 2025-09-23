"""Seed Singapore entitlement defaults."""

from __future__ import annotations

import argparse
import argparse
import asyncio
from dataclasses import dataclass
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.schemas.entitlements import EntitlementStatus, RoadmapItemCreate
from app.services.entitlements import EntitlementsService


AUTHORITY_SEED: List[Dict[str, object]] = [
    {
        "code": "URA",
        "name": "Urban Redevelopment Authority",
        "jurisdiction": "SG",
        "approval_types": [
            {
                "code": "URA-PREAPP",
                "name": "Pre-application consultation",
                "default_lead_time_days": 21,
            },
            {
                "code": "URA-DP",
                "name": "Development permission",
                "default_lead_time_days": 90,
            },
        ],
    },
    {
        "code": "LTA",
        "name": "Land Transport Authority",
        "jurisdiction": "SG",
        "approval_types": [
            {
                "code": "LTA-TIA",
                "name": "Traffic impact assessment",
                "default_lead_time_days": 60,
            }
        ],
    },
    {
        "code": "NEA",
        "name": "National Environment Agency",
        "jurisdiction": "SG",
        "approval_types": [
            {
                "code": "NEA-EH",
                "name": "Environmental health clearance",
                "default_lead_time_days": 45,
            }
        ],
    },
]

ROADMAP_TEMPLATE: List[Dict[str, object]] = [
    {
        "approval_code": "URA-PREAPP",
        "status": EntitlementStatus.PLANNED,
        "notes": "Schedule pre-application consultations with URA planners.",
    },
    {
        "approval_code": "URA-DP",
        "status": EntitlementStatus.PLANNED,
        "notes": "Prepare development control submission with supporting studies.",
    },
    {
        "approval_code": "LTA-TIA",
        "status": EntitlementStatus.PLANNED,
        "notes": "Commission traffic consultant to draft preliminary TIA scope.",
    },
    {
        "approval_code": "NEA-EH",
        "status": EntitlementStatus.PLANNED,
        "notes": "Coordinate environmental health assessment with NEA reviewers.",
    },
]


@dataclass
class SeedSummary:
    """Counts summarising seeded entitlements."""

    authorities: int = 0
    approval_types: int = 0
    roadmap_items: int = 0

    def as_dict(self) -> Dict[str, int]:
        return {
            "authorities": self.authorities,
            "approval_types": self.approval_types,
            "roadmap_items": self.roadmap_items,
        }


async def seed_singapore_entitlements(
    session: AsyncSession,
    *,
    project_id: int,
    seed_roadmap: bool = True,
) -> SeedSummary:
    """Idempotently seed Singaporean authorities and default roadmap items."""

    service = EntitlementsService(session)
    summary = SeedSummary()
    approval_lookup: Dict[str, int] = {}

    for entry in AUTHORITY_SEED:
        authority = await service.upsert_authority(
            code=str(entry["code"]),
            name=str(entry["name"]),
            jurisdiction=str(entry.get("jurisdiction", "SG")),
        )
        summary.authorities += 1
        for approval_seed in entry.get("approval_types", []):
            approval = await service.upsert_approval_type(
                authority=authority,
                code=str(approval_seed["code"]),
                name=str(approval_seed["name"]),
                default_lead_time_days=approval_seed.get("default_lead_time_days"),
            )
            approval_lookup[approval.code] = approval.id
            summary.approval_types += 1

    await session.flush()

    if seed_roadmap:
        existing = await service.list_roadmap(project_id=project_id, limit=1, offset=0)
        if existing.total == 0:
            for template in ROADMAP_TEMPLATE:
                code = str(template["approval_code"])
                approval_id = approval_lookup.get(code)
                if approval_id is None:
                    continue
                payload = RoadmapItemCreate(
                    approval_type_id=approval_id,
                    status=template.get("status", EntitlementStatus.PLANNED),
                    notes=str(template.get("notes", "")) or None,
                )
                await service.create_roadmap_item(project_id=project_id, payload=payload)
                summary.roadmap_items += 1
            await session.flush()

    return summary


async def _seed_cli(project_id: int, *, skip_roadmap: bool, dry_run: bool) -> SeedSummary:
    async with AsyncSessionLocal() as session:
        summary = await seed_singapore_entitlements(
            session, project_id=project_id, seed_roadmap=not skip_roadmap
        )
        if dry_run:
            await session.rollback()
        else:
            await session.commit()
        return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Singapore entitlement defaults")
    parser.add_argument("project_id", type=int, help="Target project identifier")
    parser.add_argument(
        "--skip-roadmap",
        action="store_true",
        help="Only seed authorities and approval types without roadmap items.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without committing changes to the database.",
    )
    args = parser.parse_args()

    summary = asyncio.run(
        _seed_cli(args.project_id, skip_roadmap=args.skip_roadmap, dry_run=args.dry_run)
    )
    print("Seeded entitlements:", summary.as_dict())


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
