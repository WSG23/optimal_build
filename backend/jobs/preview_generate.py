"""Background job for generating developer preview assets."""

from __future__ import annotations

import inspect
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend._compat.datetime import UTC, utcnow
from backend.jobs import job
from app.core.database import get_session
from app.models.preview import PreviewJob, PreviewJobStatus
from app.services.preview_generator import PreviewAssets, ensure_preview_asset
from app.utils import metrics


def _resolve_session_dependency():
    try:
        from app.main import app as fastapi_app  # type: ignore
    except Exception:  # pragma: no cover - fallback when app isn't available
        fastapi_app = None

    if fastapi_app is not None:
        override = fastapi_app.dependency_overrides.get(get_session)
        if override is not None:
            return override
    return get_session


@asynccontextmanager
async def _job_session() -> AsyncIterator[AsyncSession]:
    dependency = _resolve_session_dependency()
    resource = dependency()

    if inspect.isasyncgen(resource):
        generator = resource
        try:
            session = await anext(generator)  # type: ignore[arg-type]
        except StopAsyncIteration as exc:  # pragma: no cover - defensive guard
            raise RuntimeError("Session dependency did not yield a session") from exc
        try:
            yield session
        finally:
            await generator.aclose()
        return

    if inspect.isawaitable(resource):
        session = await resource
        try:
            yield session
        finally:
            close = getattr(session, "close", None)
            if callable(close):
                await close()
        return

    if isinstance(resource, AsyncSession):
        try:
            yield resource
        finally:
            await resource.close()
        return

    raise TypeError(
        "Session dependency must return an AsyncSession, coroutine, or async generator"
    )


async def _load_job(session: AsyncSession, job_id: UUID) -> PreviewJob | None:
    result = await session.execute(select(PreviewJob).where(PreviewJob.id == job_id))
    return result.scalars().first()


def _resolve_backend_name(job: PreviewJob | None) -> str:
    if job and isinstance(job.metadata, dict):
        backend_name = job.metadata.get("job_backend")
        if isinstance(backend_name, str) and backend_name:
            return backend_name
    return "inline"


def _job_duration_ms(job: PreviewJob) -> float | None:
    if job.finished_at and job.requested_at:
        finished = job.finished_at
        requested = job.requested_at
        if finished.tzinfo is None:
            finished = finished.replace(tzinfo=UTC)
        else:
            finished = finished.astimezone(UTC)
        if requested.tzinfo is None:
            requested = requested.replace(tzinfo=UTC)
        else:
            requested = requested.astimezone(UTC)
        delta = finished - requested
        total_ms = delta.total_seconds() * 1000.0
        return total_ms if total_ms >= 0 else 0.0
    return None


async def _update_queue_depth(session: AsyncSession, backend_name: str) -> None:
    result = await session.execute(
        select(func.count())
        .select_from(PreviewJob)
        .where(PreviewJob.status == PreviewJobStatus.QUEUED)
    )
    queued_total = result.scalar() or 0
    metrics.PREVIEW_QUEUE_DEPTH.labels(backend=backend_name).set(float(queued_total))


async def _record_completion(
    session: AsyncSession,
    job: PreviewJob,
    outcome: str,
    backend_name: str,
) -> None:
    metrics.PREVIEW_JOBS_COMPLETED_TOTAL.labels(outcome=outcome).inc()
    duration_ms = _job_duration_ms(job)
    if duration_ms is not None:
        metrics.PREVIEW_JOB_DURATION_MS.labels(outcome=outcome).observe(duration_ms)
    await _update_queue_depth(session, backend_name)


@job(name="preview.generate", queue="preview")
async def generate_preview_job(job_id: str) -> dict[str, Any]:
    """Generate preview assets for the specified job."""

    job_uuid = UUID(str(job_id))
    async with _job_session() as session:
        job = await _load_job(session, job_uuid)
        backend_name = _resolve_backend_name(job)
        if job is None:
            await _update_queue_depth(session, backend_name)
            return {"status": "missing", "job_id": job_id}

        payload_layers = job.metadata.get("massing_layers") if job.metadata else None
        if not isinstance(payload_layers, list) or not payload_layers:
            job.status = PreviewJobStatus.FAILED
            job.finished_at = utcnow()
            job.message = "Preview job missing massing layer metadata"
            await session.commit()
            await _record_completion(session, job, "failed", backend_name)
            return {"status": "failed", "job_id": job_id}

        job.status = PreviewJobStatus.PROCESSING
        job.started_at = utcnow()
        job.message = None
        await session.flush()

        try:
            assets: PreviewAssets = ensure_preview_asset(
                job.property_id, job.id, payload_layers
            )
            job.preview_url = assets.preview_url
            job.metadata_url = assets.metadata_url
            job.thumbnail_url = assets.thumbnail_url
            job.asset_version = assets.asset_version
            job.status = PreviewJobStatus.READY
            job.finished_at = utcnow()
            asset_manifest = job.metadata.setdefault("asset_manifest", {})
            if isinstance(asset_manifest, dict):
                asset_manifest.update(
                    {
                        "gltf": assets.preview_url,
                        "metadata": assets.metadata_url,
                        "thumbnail": assets.thumbnail_url,
                        "version": assets.asset_version,
                    }
                )
            await session.commit()
            await _record_completion(session, job, "ready", backend_name)
            return {
                "status": "ready",
                "job_id": job_id,
                "preview_url": assets.preview_url,
                "metadata_url": assets.metadata_url,
                "thumbnail_url": assets.thumbnail_url,
            }
        except Exception as exc:  # pragma: no cover - defensive guard
            job.status = PreviewJobStatus.FAILED
            job.finished_at = utcnow()
            job.message = str(exc)
            await session.commit()
            await _record_completion(session, job, "failed", backend_name)
            raise


__all__ = ["generate_preview_job"]
