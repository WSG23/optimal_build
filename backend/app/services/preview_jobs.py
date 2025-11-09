"""Preview job service helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Mapping, Sequence
from uuid import UUID

from backend._compat.datetime import utcnow
from backend.jobs import job_queue
from backend.jobs.preview_generate import generate_preview_job  # noqa: F401

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

_registry = getattr(job_queue._backend, "_registry", {})
if "preview.generate" not in _registry:
    job_queue.register(generate_preview_job, "preview.generate", queue="preview")

from app.models.preview import PreviewJob, PreviewJobStatus
from app.utils import metrics


def _serialise_layers(
    layers: Sequence[Mapping[str, object]]
) -> list[dict[str, object]]:
    serialised: list[dict[str, object]] = []
    for entry in layers:
        if hasattr(entry, "model_dump"):
            serialised.append(entry.model_dump())  # type: ignore[attr-defined]
        else:
            serialised.append(dict(entry))
    return serialised


class PreviewJobService:
    """Persist and generate property preview jobs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _record_queue_depth(self, backend_name: str) -> None:
        """Update preview queue depth gauge for the supplied backend."""

        result = await self._session.execute(
            select(func.count())
            .select_from(PreviewJob)
            .where(PreviewJob.status == PreviewJobStatus.QUEUED)
        )
        queued_total = result.scalar() or 0
        metrics.PREVIEW_QUEUE_DEPTH.labels(backend=backend_name).set(
            float(queued_total)
        )

    async def list_jobs(self, property_id: UUID) -> list[PreviewJob]:
        result = await self._session.execute(
            select(PreviewJob)
            .where(PreviewJob.property_id == property_id)
            .order_by(PreviewJob.requested_at.desc())
        )
        return result.scalars().all()

    async def get_job(self, job_id: UUID) -> PreviewJob | None:
        return await self._session.get(PreviewJob, job_id)

    async def queue_preview(
        self,
        *,
        property_id: UUID,
        scenario: str,
        massing_layers: Sequence[Mapping[str, object]],
        camera_orbit: Mapping[str, float] | None = None,
    ) -> PreviewJob:
        """Create a preview job and enqueue it for asynchronous rendering."""

        serialised_layers = _serialise_layers(massing_layers)
        checksum_source = json.dumps(serialised_layers, sort_keys=True).encode("utf-8")
        checksum = hashlib.sha256(checksum_source).hexdigest()

        job = PreviewJob(
            property_id=property_id,
            scenario=scenario,
            status=PreviewJobStatus.QUEUED,
            requested_at=utcnow(),
            started_at=None,
            asset_version=None,
            payload_checksum=checksum,
            metadata={
                "massing_layers": serialised_layers,
                "camera_orbit": camera_orbit or {},
            },
        )
        self._session.add(job)
        await self._session.flush()

        registry = getattr(job_queue._backend, "_registry", {})
        if "preview.generate" not in registry:
            job_queue.register(
                generate_preview_job, "preview.generate", queue="preview"
            )

        backend_name = getattr(job_queue._backend, "name", "inline")
        job.metadata["job_backend"] = backend_name
        await self._session.flush()
        metrics.PREVIEW_JOBS_CREATED_TOTAL.labels(
            scenario=scenario,
            backend=backend_name,
        ).inc()
        await self._record_queue_depth(backend_name)

        if backend_name == "inline":
            await generate_preview_job(str(job.id))
        else:
            try:
                await job_queue.enqueue(
                    "preview.generate",
                    queue="preview",
                    args=(str(job.id),),
                    kwargs={},
                )
            except KeyError:
                job_queue.register(
                    generate_preview_job, "preview.generate", queue="preview"
                )
                await job_queue.enqueue(
                    "preview.generate",
                    queue="preview",
                    args=(str(job.id),),
                    kwargs={},
                )
        await self._session.refresh(job)
        if backend_name != "inline" and job.status == PreviewJobStatus.QUEUED:
            job.status = PreviewJobStatus.PROCESSING
            job.preview_url = None
            job.metadata_url = None
            job.thumbnail_url = None
            await self._session.flush()
            await self._record_queue_depth(backend_name)

        return job

    async def refresh_job(self, job: PreviewJob) -> PreviewJob:
        """Re-enqueue a preview job using stored metadata."""

        payload_layers = job.metadata.get("massing_layers") if job.metadata else None
        if not isinstance(payload_layers, list) or not payload_layers:
            raise ValueError("Preview job missing massing layer metadata")

        serialised_layers = _serialise_layers(payload_layers)
        checksum_source = json.dumps(serialised_layers, sort_keys=True).encode("utf-8")
        job.payload_checksum = hashlib.sha256(checksum_source).hexdigest()

        job.status = PreviewJobStatus.QUEUED
        job.requested_at = utcnow()
        job.started_at = None
        job.finished_at = None
        job.preview_url = None
        job.metadata_url = None
        job.asset_version = None
        job.thumbnail_url = None
        job.message = None
        job.metadata.pop("asset_manifest", None)

        registry = getattr(job_queue._backend, "_registry", {})
        if "preview.generate" not in registry:
            job_queue.register(
                generate_preview_job, "preview.generate", queue="preview"
            )

        backend_name = getattr(job_queue._backend, "name", "inline")
        job.metadata["job_backend"] = backend_name
        await self._session.flush()
        metrics.PREVIEW_JOBS_CREATED_TOTAL.labels(
            scenario=job.scenario,
            backend=backend_name,
        ).inc()
        await self._record_queue_depth(backend_name)

        if backend_name == "inline":
            await generate_preview_job(str(job.id))
        else:
            try:
                await job_queue.enqueue(
                    "preview.generate",
                    queue="preview",
                    args=(str(job.id),),
                    kwargs={},
                )
            except KeyError:
                job_queue.register(
                    generate_preview_job, "preview.generate", queue="preview"
                )
                await job_queue.enqueue(
                    "preview.generate",
                    queue="preview",
                    args=(str(job.id),),
                    kwargs={},
                )
        await self._session.refresh(job)
        return job


__all__ = ["PreviewJobService", "PreviewJobStatus"]
