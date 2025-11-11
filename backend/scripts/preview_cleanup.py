"""Cleanup utility for preview assets and jobs."""

from __future__ import annotations

import argparse
import asyncio
import shutil
from pathlib import Path
from typing import Iterable
from uuid import UUID

import structlog

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.preview import PreviewJob, PreviewJobStatus
from app.services.preview_generator import PREVIEW_STORAGE_DIR
from backend._compat.datetime import utcnow
from sqlalchemy import select

logger = structlog.get_logger(__name__)


async def _expire_versions(
    session,
    property_id: UUID,
    versions: Iterable[str],
) -> int:
    stmt = (
        select(PreviewJob)
        .where(PreviewJob.property_id == property_id)
        .where(PreviewJob.asset_version.in_(list(versions)))
    )
    result = await session.execute(stmt)
    jobs = result.scalars().all()
    for job in jobs:
        if job.status != PreviewJobStatus.EXPIRED:
            job.status = PreviewJobStatus.EXPIRED
            if not job.finished_at:
                job.finished_at = utcnow()
            job.message = job.message or "Preview assets pruned"
    if jobs:
        await session.flush()
    return len(jobs)


async def cleanup(max_versions: int) -> None:
    base_dir = Path(PREVIEW_STORAGE_DIR)
    if not base_dir.exists():
        logger.info("Preview directory missing", path=str(base_dir))
        return

    removed_dirs = 0
    expired_jobs = 0

    async with AsyncSessionLocal() as session:
        for property_path in sorted(base_dir.iterdir()):
            if not property_path.is_dir():
                continue
            version_dirs = [
                entry for entry in property_path.iterdir() if entry.is_dir()
            ]
            if len(version_dirs) <= max_versions:
                continue

            version_dirs.sort(key=lambda p: p.name, reverse=True)
            keep = version_dirs[:max_versions]
            prune = version_dirs[max_versions:]

            logger.info(
                "Pruning preview versions",
                property_id=property_path.name,
                keep=[path.name for path in keep],
                prune=[path.name for path in prune],
            )

            for path in prune:
                shutil.rmtree(path, ignore_errors=True)
                removed_dirs += 1

            try:
                property_uuid = UUID(property_path.name)
            except ValueError:
                logger.warning(
                    "Skipping job expiry; invalid property UUID",
                    property_id=property_path.name,
                )
                continue

            expired_jobs += await _expire_versions(
                session,
                property_uuid,
                [path.name for path in prune],
            )
            await session.commit()

    print(
        f"Preview cleanup complete: removed {removed_dirs} directories, marked {expired_jobs} jobs expired (keeping {max_versions} versions)."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prune preview assets beyond the configured max versions."
    )
    parser.add_argument(
        "--max-versions",
        type=int,
        default=settings.PREVIEW_MAX_VERSIONS,
        help="How many preview versions to retain per property (default: settings.PREVIEW_MAX_VERSIONS)",
    )
    args = parser.parse_args()

    if args.max_versions <= 0:
        parser.error("--max-versions must be a positive integer")

    asyncio.run(cleanup(args.max_versions))


if __name__ == "__main__":
    main()
