"""CLI tool for enqueueing and managing preview jobs."""

from __future__ import annotations

import argparse
import asyncio
import sys
from uuid import UUID

import structlog

from app.core.database import AsyncSessionLocal
from app.services.preview_jobs import PreviewJobService

logger = structlog.get_logger(__name__)

DEFAULT_MASSING_LAYERS = [
    {
        "asset_type": "office",
        "allocation_pct": 60.0,
        "gfa_sqm": 5000.0,
        "nia_sqm": 4500.0,
        "estimated_height_m": 45.0,
        "color": "#4A90E2",
    },
    {
        "asset_type": "retail",
        "allocation_pct": 40.0,
        "gfa_sqm": 3000.0,
        "nia_sqm": 2700.0,
        "estimated_height_m": 15.0,
        "color": "#E24A90",
    },
]


async def enqueue_preview(property_id: str) -> None:
    """Enqueue a preview job for the specified property."""
    try:
        property_uuid = UUID(property_id)
    except ValueError:
        logger.error("Invalid property ID format", property_id=property_id)
        sys.exit(1)

    async with AsyncSessionLocal() as session:
        service = PreviewJobService(session)

        logger.info(
            "Enqueueing preview job",
            property_id=property_id,
            scenario="base",
        )

        job = await service.queue_preview(
            property_id=property_uuid,
            scenario="base",
            massing_layers=DEFAULT_MASSING_LAYERS,
            camera_orbit={"theta": 45.0, "phi": 30.0, "radius": 100.0},
        )

        await session.commit()

        logger.info(
            "Preview job enqueued",
            job_id=str(job.id),
            status=job.status.value,
            preview_url=job.preview_url,
            metadata_url=job.metadata_url,
            thumbnail_url=job.thumbnail_url,
        )

        print(f"✓ Preview job enqueued: {job.id}")
        print(f"  Status: {job.status.value}")
        if job.preview_url:
            print(f"  Preview URL: {job.preview_url}")
        if job.metadata_url:
            print(f"  Metadata URL: {job.metadata_url}")
        if job.thumbnail_url:
            print(f"  Thumbnail URL: {job.thumbnail_url}")


async def list_jobs(property_id: str | None) -> None:
    """List preview jobs for the specified property."""
    async with AsyncSessionLocal() as session:
        service = PreviewJobService(session)

        if property_id:
            try:
                property_uuid = UUID(property_id)
            except ValueError:
                logger.error("Invalid property ID format", property_id=property_id)
                sys.exit(1)

            jobs = await service.list_jobs(property_uuid)
            print(f"Preview jobs for property {property_id}:")
        else:
            logger.error("property_id is required for list command")
            sys.exit(1)

        if not jobs:
            print("  No jobs found")
            return

        for job in jobs:
            print(f"  - {job.id}")
            print(f"    Status: {job.status.value}")
            print(f"    Scenario: {job.scenario}")
            print(f"    Requested: {job.requested_at}")
            if job.preview_url:
                print(f"    Preview URL: {job.preview_url}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Preview job management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # enqueue command
    enqueue_parser = subparsers.add_parser("enqueue", help="Enqueue a preview job")
    enqueue_parser.add_argument(
        "--property-id",
        required=True,
        help="Property UUID to generate preview for",
    )

    # list command
    list_parser = subparsers.add_parser("list", help="List preview jobs")
    list_parser.add_argument(
        "--property-id",
        required=True,
        help="Property UUID to list jobs for",
    )

    args = parser.parse_args()

    if args.command == "enqueue":
        asyncio.run(enqueue_preview(args.property_id))
    elif args.command == "list":
        asyncio.run(list_jobs(args.property_id))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
