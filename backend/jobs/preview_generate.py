"""Background job for generating developer preview assets."""

from __future__ import annotations

import inspect
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend._compat.datetime import utcnow
from backend.jobs import job
from app.core.database import get_session
from app.models.preview import PreviewJob, PreviewJobStatus
from app.services.preview_generator import ensure_preview_asset


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


@job(name="preview.generate", queue="preview")
async def generate_preview_job(job_id: str) -> dict[str, Any]:
    """Generate preview assets for the specified job."""

    job_uuid = UUID(str(job_id))
    async with _job_session() as session:
        job = await _load_job(session, job_uuid)
        if job is None:
            return {"status": "missing", "job_id": job_id}

        payload_layers = job.metadata.get("massing_layers") if job.metadata else None
        if not isinstance(payload_layers, list) or not payload_layers:
            job.status = PreviewJobStatus.FAILED
            job.finished_at = utcnow()
            job.message = "Preview job missing massing layer metadata"
            await session.commit()
            return {"status": "failed", "job_id": job_id}

        job.status = PreviewJobStatus.PROCESSING
        job.started_at = utcnow()
        job.message = None
        await session.flush()

        try:
            preview_url = ensure_preview_asset(job.property_id, payload_layers)
            job.preview_url = preview_url
            job.status = PreviewJobStatus.READY
            job.finished_at = utcnow()
            await session.commit()
            return {
                "status": "ready",
                "job_id": job_id,
                "preview_url": preview_url,
            }
        except Exception as exc:  # pragma: no cover - defensive guard
            job.status = PreviewJobStatus.FAILED
            job.finished_at = utcnow()
            job.message = str(exc)
            await session.commit()
            raise


__all__ = ["generate_preview_job"]
