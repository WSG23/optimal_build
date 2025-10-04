"""Helpers for registering default Prefect deployments."""

from __future__ import annotations

import logging

try:  # pragma: no cover - optional dependency
    from prefect.deployments import Deployment
    from prefect.server.schemas.schedules import CronSchedule
except ModuleNotFoundError:  # pragma: no cover - allow module import without Prefect
    Deployment = None  # type: ignore[assignment]
    CronSchedule = None  # type: ignore[assignment]

from backend.flows.analytics_flow import refresh_market_intelligence
from backend.flows.compliance_flow import refresh_singapore_compliance

logger = logging.getLogger(__name__)


async def create_default_deployments(work_queue: str = "default") -> None:
    """Register default deployments when Prefect is available."""

    if (
        Deployment is None or CronSchedule is None
    ):  # pragma: no cover - graceful fallback
        logger.warning("Prefect is not installed; skipping deployment creation")
        return

    analytics_deployment = await Deployment.build_from_flow(
        flow=refresh_market_intelligence,
        name="market-intelligence-daily",
        schedule=CronSchedule(cron="0 3 * * *", timezone="UTC"),
        work_queue_name=work_queue,
        parameters={"period_months": 12},
        tags=["market-intelligence"],
    )
    compliance_deployment = await Deployment.build_from_flow(
        flow=refresh_singapore_compliance,
        name="singapore-compliance-hourly",
        schedule=CronSchedule(cron="0 * * * *", timezone="UTC"),
        work_queue_name=work_queue,
        tags=["compliance"],
    )

    await analytics_deployment.apply()
    await compliance_deployment.apply()
    logger.info(
        "Registered default Prefect deployments: %s, %s",
        analytics_deployment.name,
        compliance_deployment.name,
    )


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    import asyncio

    asyncio.run(create_default_deployments())
