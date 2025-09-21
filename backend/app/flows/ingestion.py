"""Prefect ingestion flows."""

from __future__ import annotations

from typing import Any, Callable, Dict, Sequence

from prefect import flow
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.services import alerts, ingestion as ingestion_service, standards
from app.utils.logging import get_logger, log_event

logger = get_logger(__name__)


@flow(name="material-standard-ingestion")
async def material_standard_ingestion_flow(
    records: Sequence[Dict[str, Any]],
    session_factory: Callable[[], AsyncSession] = AsyncSessionLocal,
) -> Dict[str, int]:
    """Ingest material standards and capture run metrics."""

    async with session_factory() as session:
        run = await ingestion_service.start_ingestion_run(session, flow_name="material-standard-ingestion")
        records_ingested = 0
        suspected_updates = 0

        try:
            for raw_payload in records:
                payload = dict(raw_payload)
                suspected = bool(payload.pop("suspected_update", False))
                await standards.upsert_material_standard(session, payload)
                records_ingested += 1
                if suspected:
                    suspected_updates += 1

            await ingestion_service.complete_ingestion_run(
                session,
                run,
                status="success",
                records_ingested=records_ingested,
                suspected_updates=suspected_updates,
                extra_metrics={"records_ingested": records_ingested},
            )

            if suspected_updates:
                await alerts.create_alert(
                    session,
                    alert_type="material_standard_update",
                    level="warning",
                    message=f"{suspected_updates} material standards flagged for review",
                    ingestion_run=run,
                    context={"suspected_updates": suspected_updates},
                )
            await session.commit()
        except Exception as exc:  # pragma: no cover - defensive logging
            await ingestion_service.complete_ingestion_run(
                session,
                run,
                status="failed",
                records_ingested=records_ingested,
                suspected_updates=suspected_updates,
                extra_metrics={"error": str(exc)},
            )
            await session.commit()
            log_event(logger, "material_standard_ingestion_failed", error=str(exc))
            raise

    log_event(
        logger,
        "material_standard_ingestion_completed",
        records_ingested=records_ingested,
        suspected_updates=suspected_updates,
    )
    return {"records_ingested": records_ingested, "suspected_updates": suspected_updates}
