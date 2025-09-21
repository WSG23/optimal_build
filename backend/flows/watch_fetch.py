"""Prefect flow to watch sources and fetch documents into storage."""

from __future__ import annotations

import importlib.util
from dataclasses import asdict
from typing import Any, Dict, List, Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio.session import async_sessionmaker

from app.models.rkp import RefDocument, RefIngestionRun
from app.services.storage import StorageArtifact, StorageConfig, StorageService
from app.utils.logging import get_logger

_PrefectSpec = importlib.util.find_spec("prefect")
HAS_PREFECT = _PrefectSpec is not None

if HAS_PREFECT:  # pragma: no cover
    from prefect import flow, get_run_logger, task
else:  # pragma: no cover
    def flow(*_args: Any, **_kwargs: Any):
        def decorator(func):
            return func

        return decorator

    def get_run_logger():
        return get_logger("watch-fetch")


async def _record_run_impl(
    session_factory: async_sessionmaker[AsyncSession],
    source_id: int,
    artifact: StorageArtifact,
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    async with session_factory() as session:
        document = RefDocument(
            source_id=source_id,
            version_label=metadata.get("version") or artifact.checksum[:8],
            storage_path=artifact.key,
            file_hash=artifact.checksum,
            http_etag=metadata.get("etag"),
            http_last_modified=metadata.get("last_modified"),
            suspected_update=False,
        )
        session.add(document)
        await session.flush()

        run = RefIngestionRun(
            source_id=source_id,
            document_id=document.id,
            run_key=f"{source_id}-{artifact.checksum}",
            status="succeeded",
            metrics={"bytes": artifact.size},
            storage_artifact=asdict(artifact),
            provenance={"url": metadata.get("url")},
        )
        session.add(run)
        await session.commit()

        return {"run_id": run.id, "document_id": document.id}


if HAS_PREFECT:  # pragma: no cover
    _record_run = task(_record_run_impl)
else:

    async def _record_run(
        session_factory: async_sessionmaker[AsyncSession],
        source_id: int,
        artifact: StorageArtifact,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        return await _record_run_impl(session_factory, source_id, artifact, metadata)


async def _run_task(task_or_fn, *args: Any, **kwargs: Any) -> Any:
    if HAS_PREFECT:
        future = task_or_fn.submit(*args, **kwargs)
        return await future.result()
    return await task_or_fn(*args, **kwargs)


@flow(name="watch-fetch")
async def watch_fetch(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    storage_config: Dict[str, Any],
    sources: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Download a set of sources and record ingestion runs."""

    logger = get_run_logger()
    storage = StorageService(StorageConfig(**storage_config))
    results: List[Dict[str, Any]] = []

    for source in sources:
        source_id = source["id"]
        url = source["url"]
        object_key = source.get("object_key") or f"sources/{source_id}.bin"
        artifact = await storage.download_to_object_store(
            url,
            object_key,
            metadata={"source_id": str(source_id)},
            headers=source.get("headers"),
        )
        logger.info("fetched_source", source_id=source_id, key=artifact.key)
        run_result = await _run_task(
            _record_run,
            session_factory,
            source_id,
            artifact,
            {"url": url, "version": source.get("version"), "etag": source.get("etag")},
        )
        results.append({"source_id": source_id, **run_result, "artifact": asdict(artifact)})

    return results
