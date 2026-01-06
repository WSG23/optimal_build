"""Preview job service helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Protocol, Sequence, cast


class _HasModelDump(Protocol):
    def model_dump(self) -> dict[str, object]: ...


from uuid import UUID

from backend._compat.datetime import utcnow
from backend.jobs import job_queue
from backend.jobs.preview_generate import generate_preview_job  # noqa: F401

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

_registry = getattr(job_queue._backend, "_registry", {})
if "preview.generate" not in _registry:
    job_queue.register(generate_preview_job, "preview.generate", queue="preview")

from app.core.config import settings
from app.models.preview import PreviewJob, PreviewJobStatus
from app.models.property import Property
from app.services import preview_generator
from app.utils import metrics


def _serialise_layers(
    layers: Sequence[Mapping[str, object] | _HasModelDump]
) -> list[dict[str, object]]:
    serialised: list[dict[str, object]] = []
    for entry in layers:
        if hasattr(entry, "model_dump"):
            # Runtime check confirms entry has model_dump, cast for type safety
            serialised.append(cast(_HasModelDump, entry).model_dump())
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
        geometry_detail_level: str | None = None,
        color_legend: Sequence[Mapping[str, object]] | None = None,
    ) -> PreviewJob:
        """Create a preview job and enqueue it for asynchronous rendering."""

        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"[QUEUE_PREVIEW_START] Entered queue_preview for property {property_id}, scenario {scenario}"
        )

        try:
            detail_level = preview_generator.normalise_geometry_detail_level(
                geometry_detail_level or settings.PREVIEW_GEOMETRY_DETAIL_LEVEL
            )
            serialised_layers = _serialise_layers(massing_layers)
            legend_payload = _serialise_layers(color_legend) if color_legend else []
            logger.info(
                f"[QUEUE_PREVIEW_START] Serialised {len(serialised_layers)} layers"
            )

            checksum_source = json.dumps(
                {"layers": serialised_layers, "legend": legend_payload},
                sort_keys=True,
            ).encode("utf-8")
            checksum = hashlib.sha256(checksum_source).hexdigest()
            logger.info(f"[QUEUE_PREVIEW_START] Computed checksum: {checksum[:16]}...")

            property_record = await self._session.get(Property, property_id)
            jurisdiction_code = (
                property_record.jurisdiction_code if property_record else "SG"
            )
            job_metadata = {
                "massing_layers": serialised_layers,
                "camera_orbit": camera_orbit or {},
                "geometry_detail_level": detail_level,
                "color_legend": legend_payload,
                "jurisdiction_code": jurisdiction_code,
            }
            job = PreviewJob(
                property_id=property_id,
                scenario=scenario,
                status=PreviewJobStatus.QUEUED,
                requested_at=utcnow(),
                started_at=None,
                asset_version=None,
                payload_checksum=checksum,
                metadata=job_metadata,
            )
            self._session.add(job)
            logger.info("[QUEUE_PREVIEW_START] Added job to session, about to flush")
            await self._session.flush()
            logger.info(f"[QUEUE_PREVIEW_START] Flushed job {job.id}")

            logger.info(
                "[QUEUE_PREVIEW_START] About to access job_queue._backend._registry"
            )
            registry = getattr(job_queue._backend, "_registry", {})
            logger.info(
                f"[QUEUE_PREVIEW_START] Got registry with {len(registry)} entries"
            )

            if "preview.generate" not in registry:
                logger.info("[QUEUE_PREVIEW_START] Registering preview.generate job")
                job_queue.register(
                    generate_preview_job, "preview.generate", queue="preview"
                )
                logger.info("[QUEUE_PREVIEW_START] Registered preview.generate job")

            logger.info("[QUEUE_PREVIEW_START] About to get backend_name")
            backend_name = getattr(job_queue._backend, "name", "inline")
            logger.info(
                f"[QUEUE_PREVIEW] Detected backend_name: '{backend_name}' for job {job.id}"
            )
            logger.info(
                f"[QUEUE_PREVIEW] job_queue._backend type: {type(job_queue._backend)}"
            )

            logger.info("[QUEUE_PREVIEW_START] About to update job.metadata")
            job.metadata["job_backend"] = backend_name
            logger.info("[QUEUE_PREVIEW_START] Updated metadata, about to flush")
            await self._session.flush()
            logger.info("[QUEUE_PREVIEW_START] Flushed metadata update")
        except Exception as e:
            logger.error(
                f"[QUEUE_PREVIEW_ERROR] Exception in queue_preview setup: {type(e).__name__}: {e}"
            )
            raise
        metrics.PREVIEW_JOBS_CREATED_TOTAL.labels(
            scenario=scenario,
            backend=backend_name,
        ).inc()
        await self._record_queue_depth(backend_name)

        if backend_name == "inline":
            import logging

            logger = logging.getLogger(__name__)
            logger.info(
                f"[INLINE QUEUE] About to commit session and execute preview job {job.id}"
            )
            await self._session.commit()
            logger.info(
                f"[INLINE QUEUE] Session committed, now calling generate_preview_job for {job.id}"
            )
            await generate_preview_job(str(job.id))
            logger.info(f"[INLINE QUEUE] generate_preview_job completed for {job.id}")
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

    async def refresh_job(
        self,
        job: PreviewJob,
        *,
        geometry_detail_level: str | None = None,
        color_legend: Sequence[Mapping[str, object]] | None = None,
    ) -> PreviewJob:
        """Re-enqueue a preview job using stored metadata."""

        metadata_dict: dict[str, Any] = dict(job.metadata or {})
        payload_layers = metadata_dict.get("massing_layers")
        if not isinstance(payload_layers, list) or not payload_layers:
            raise ValueError("Preview job missing massing layer metadata")

        serialised_layers = _serialise_layers(payload_layers)
        if color_legend is not None:
            legend_payload = _serialise_layers(color_legend)
        else:
            stored_legend = metadata_dict.get("color_legend")
            legend_payload = (
                _serialise_layers(stored_legend)
                if isinstance(stored_legend, list)
                else []
            )
        checksum_source = json.dumps(
            {"layers": serialised_layers, "legend": legend_payload},
            sort_keys=True,
        ).encode("utf-8")
        job.payload_checksum = hashlib.sha256(checksum_source).hexdigest()
        metadata_dict["massing_layers"] = serialised_layers
        metadata_dict["color_legend"] = legend_payload

        detail_level = preview_generator.normalise_geometry_detail_level(
            geometry_detail_level
            or (metadata_dict.get("geometry_detail_level"))
            or settings.PREVIEW_GEOMETRY_DETAIL_LEVEL
        )
        metadata_dict["geometry_detail_level"] = detail_level

        job.status = PreviewJobStatus.QUEUED
        job.requested_at = utcnow()
        job.started_at = None
        job.finished_at = None
        job.preview_url = None
        job.metadata_url = None
        job.asset_version = None
        job.thumbnail_url = None
        job.message = None
        metadata_dict.pop("asset_manifest", None)
        metadata_dict["geometry_detail_level"] = detail_level
        job.metadata = metadata_dict

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
            import logging

            logger = logging.getLogger(__name__)
            logger.info(
                f"[INLINE REFRESH] About to commit session and execute preview job {job.id}"
            )
            await self._session.commit()
            logger.info(
                f"[INLINE REFRESH] Session committed, now calling generate_preview_job for {job.id}"
            )
            await generate_preview_job(str(job.id))
            logger.info(f"[INLINE REFRESH] generate_preview_job completed for {job.id}")
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
