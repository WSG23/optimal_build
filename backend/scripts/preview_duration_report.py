"""Summarise preview job durations for monitoring/benchmarking."""

from __future__ import annotations

import argparse
import asyncio
import csv
from dataclasses import dataclass
from statistics import mean, median
from typing import Iterable, Sequence
from uuid import UUID

from backend._compat.datetime import UTC

from app.core.database import AsyncSessionLocal
from app.models.preview import PreviewJob, PreviewJobStatus
from sqlalchemy import select


@dataclass(slots=True)
class PreviewDurationRow:
    job_id: UUID
    property_id: UUID
    scenario: str
    backend: str
    requested_at: str | None
    finished_at: str | None
    duration_ms: float | None


def _duration_ms(job: PreviewJob) -> float | None:
    if job.requested_at and job.finished_at:
        requested = (
            job.requested_at.replace(tzinfo=UTC)
            if job.requested_at.tzinfo is None
            else job.requested_at.astimezone(UTC)
        )
        finished = (
            job.finished_at.replace(tzinfo=UTC)
            if job.finished_at.tzinfo is None
            else job.finished_at.astimezone(UTC)
        )
        delta = finished - requested
        milliseconds = delta.total_seconds() * 1000.0
        return milliseconds if milliseconds >= 0 else 0.0
    return None


async def _fetch_rows(
    limit: int,
    property_id: UUID | None,
) -> list[PreviewDurationRow]:
    async with AsyncSessionLocal() as session:
        stmt = (
            select(PreviewJob)
            .where(PreviewJob.status == PreviewJobStatus.READY)
            .order_by(PreviewJob.requested_at.desc())
            .limit(limit)
        )
        if property_id:
            stmt = stmt.where(PreviewJob.property_id == property_id)
        result = await session.execute(stmt)
        jobs: Sequence[PreviewJob] = result.scalars().all()

    rows: list[PreviewDurationRow] = []
    for job in jobs:
        metadata = job.metadata if isinstance(job.metadata, dict) else {}
        backend_name = metadata.get("job_backend")
        backend = backend_name if isinstance(backend_name, str) else "inline"
        rows.append(
            PreviewDurationRow(
                job_id=job.id,
                property_id=job.property_id,
                scenario=job.scenario,
                backend=backend,
                requested_at=job.requested_at.isoformat() if job.requested_at else None,
                finished_at=job.finished_at.isoformat() if job.finished_at else None,
                duration_ms=_duration_ms(job),
            )
        )
    return rows


def _percentile(values: Sequence[float], percentile: float) -> float | None:
    if not values:
        return None
    if percentile <= 0:
        return min(values)
    if percentile >= 1:
        return max(values)
    sorted_values = sorted(values)
    index = int(round((len(sorted_values) - 1) * percentile))
    return sorted_values[index]


def _write_csv(path: str, rows: Iterable[PreviewDurationRow]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "job_id",
                "property_id",
                "scenario",
                "backend",
                "requested_at",
                "finished_at",
                "duration_ms",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.job_id,
                    row.property_id,
                    row.scenario,
                    row.backend,
                    row.requested_at or "",
                    row.finished_at or "",
                    f"{row.duration_ms:.2f}" if row.duration_ms is not None else "",
                ]
            )


def _print_summary(rows: Sequence[PreviewDurationRow]) -> None:
    durations = [row.duration_ms for row in rows if row.duration_ms is not None]
    print(f"Preview jobs analysed: {len(rows)}")
    if not durations:
        print("No completed jobs with duration metadata.")
        return
    avg = mean(durations)
    med = median(durations)
    p90 = _percentile(durations, 0.9)
    p99 = _percentile(durations, 0.99)
    print(f"Average duration: {avg:.2f} ms")
    print(f"Median duration: {med:.2f} ms")
    if p90 is not None:
        print(f"P90 duration: {p90:.2f} ms")
    if p99 is not None:
        print(f"P99 duration: {p99:.2f} ms")
    print(f"Slowest job: {max(durations):.2f} ms")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarise preview generation job durations."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Number of recent READY jobs to analyse (default: 50).",
    )
    parser.add_argument(
        "--property-id",
        type=UUID,
        default=None,
        help="Optional property UUID filter.",
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default=None,
        help="Write detailed job rows to this CSV file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = asyncio.run(_fetch_rows(args.limit, args.property_id))
    _print_summary(rows)
    if args.output_csv:
        _write_csv(args.output_csv, rows)
        print(f"Detailed rows written to {args.output_csv}")


if __name__ == "__main__":
    main()
