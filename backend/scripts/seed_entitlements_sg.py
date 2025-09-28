"""Seed Singapore entitlement reference data."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Iterable
from dataclasses import dataclass

import app.utils.logging  # noqa: F401  pylint: disable=unused-import
import structlog
from app.core.database import AsyncSessionLocal, engine
from app.models import (  # noqa: F401  pylint: disable=unused-import
    entitlements as ent_models,
)
from app.models.base import BaseModel
from app.models.entitlements import EntApprovalCategory, EntRoadmapStatus
from app.services.entitlements import EntitlementsService
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

AUTHORITIES: Iterable[dict[str, str | None]] = (
    {
        "slug": "ura",
        "name": "Urban Redevelopment Authority",
        "jurisdiction": "SG",
        "website": "https://www.ura.gov.sg",
        "contact_email": "enquiry@ura.gov.sg",
    },
    {
        "slug": "bca",
        "name": "Building and Construction Authority",
        "jurisdiction": "SG",
        "website": "https://www1.bca.gov.sg",
        "contact_email": "bca_contact@bca.gov.sg",
    },
    {
        "slug": "lta",
        "name": "Land Transport Authority",
        "jurisdiction": "SG",
        "website": "https://www.lta.gov.sg",
        "contact_email": "feedback@lta.gov.sg",
    },
    {
        "slug": "nea",
        "name": "National Environment Agency",
        "jurisdiction": "SG",
        "website": "https://www.nea.gov.sg",
        "contact_email": "contact_nea@nea.gov.sg",
    },
)


APPROVAL_TYPES: Iterable[dict[str, object]] = (
    {
        "authority_slug": "ura",
        "code": "outline_planning_permission",
        "name": "Outline Planning Permission",
        "category": EntApprovalCategory.PLANNING,
        "description": "High-level planning consent establishing allowable development parameters.",
        "processing_time_days": 35,
    },
    {
        "authority_slug": "ura",
        "code": "written_permission",
        "name": "Written Permission",
        "category": EntApprovalCategory.PLANNING,
        "description": "Detailed planning permission for construction and change of use.",
        "processing_time_days": 42,
    },
    {
        "authority_slug": "bca",
        "code": "building_plan_approval",
        "name": "Building Plan Approval",
        "category": EntApprovalCategory.BUILDING,
        "description": "Approval for structural, architectural, and M&E plans prior to construction.",
        "processing_time_days": 28,
    },
    {
        "authority_slug": "lta",
        "code": "traffic_impact_assessment",
        "name": "Traffic Impact Assessment Clearance",
        "category": EntApprovalCategory.TRANSPORT,
        "description": "Assessment of transport impacts and mitigation requirements.",
        "processing_time_days": 30,
    },
    {
        "authority_slug": "nea",
        "code": "environmental_impact_assessment",
        "name": "Environmental Impact Assessment",
        "category": EntApprovalCategory.ENVIRONMENTAL,
        "description": "Review of environmental impacts and mitigation strategies for sensitive sites.",
        "processing_time_days": 45,
    },
)


ROADMAP_SEQUENCE: Iterable[dict[str, str]] = (
    {"authority_slug": "ura", "approval_code": "outline_planning_permission"},
    {"authority_slug": "ura", "approval_code": "written_permission"},
    {"authority_slug": "nea", "approval_code": "environmental_impact_assessment"},
    {"authority_slug": "lta", "approval_code": "traffic_impact_assessment"},
    {"authority_slug": "bca", "approval_code": "building_plan_approval"},
)


@dataclass
class EntitlementsSeedSummary:
    """Counts of seeded entitlement reference rows."""

    authorities: int
    approval_types: int
    roadmap_items: int

    def as_dict(self) -> dict[str, int]:
        return {
            "authorities": self.authorities,
            "approval_types": self.approval_types,
            "roadmap_items": self.roadmap_items,
        }


async def seed_entitlements(
    session: AsyncSession,
    *,
    project_id: int,
    reset_existing: bool = False,
) -> EntitlementsSeedSummary:
    """Seed Singapore entitlement authorities and default roadmap."""

    service = EntitlementsService(session)

    authority_records = {}
    for payload in AUTHORITIES:
        authority = await service.upsert_authority(**payload)
        authority_records[payload["slug"]] = authority

    approval_records = {}
    for payload in APPROVAL_TYPES:
        authority = authority_records[payload["authority_slug"]]
        approval = await service.upsert_approval_type(
            authority=authority,
            code=payload["code"],
            name=payload["name"],
            category=payload["category"],
            description=payload.get("description"),
            processing_time_days=payload.get("processing_time_days"),
        )
        approval_records[(payload["authority_slug"], payload["code"])] = approval

    if reset_existing:
        existing = await service.all_roadmap_items(project_id)
        for item in existing:
            await service.delete_roadmap_item(item_id=item.id, project_id=project_id)

    for index, item in enumerate(ROADMAP_SEQUENCE, start=1):
        approval = approval_records[(item["authority_slug"], item["approval_code"])]
        await service.create_roadmap_item(
            project_id=project_id,
            approval_type_id=approval.id,
            sequence_order=index,
            status=EntRoadmapStatus.PLANNED,
            status_changed_at=None,
            target_submission_date=None,
            target_decision_date=None,
            actual_submission_date=None,
            actual_decision_date=None,
            notes=None,
            metadata={"jurisdiction": "SG"},
        )

    return EntitlementsSeedSummary(
        authorities=len(authority_records),
        approval_types=len(approval_records),
        roadmap_items=len(tuple(ROADMAP_SEQUENCE)),
    )


async def _run_async(project_id: int, reset_existing: bool) -> EntitlementsSeedSummary:
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    async with AsyncSessionLocal() as session:
        summary = await seed_entitlements(
            session, project_id=project_id, reset_existing=reset_existing
        )
        await session.commit()
        return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed Singapore entitlement reference data and roadmap sequences."
    )
    parser.add_argument(
        "--project-id",
        type=int,
        default=501,
        help="Project identifier to attach the default roadmap to (default: 501)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Remove existing roadmap items before seeding defaults.",
    )
    return parser


def main(argv: list[str] | None = None) -> EntitlementsSeedSummary:
    parser = build_parser()
    args = parser.parse_args(argv)
    summary = asyncio.run(
        _run_async(project_id=args.project_id, reset_existing=args.reset)
    )
    logger.info("seed_entitlements.summary", **summary.as_dict())
    return summary


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
