"""Prefect schedule helpers for compliance and analytics flows."""

from __future__ import annotations

from datetime import timedelta
from typing import Iterable

try:  # pragma: no cover - optional dependency
    from prefect.deployments import Deployment
    from prefect.events.schemas import DeploymentTrigger
    from prefect.server.schemas.schedules import CronSchedule
except ModuleNotFoundError:  # pragma: no cover
    Deployment = None  # type: ignore[assignment]
    CronSchedule = None  # type: ignore[assignment]
    DeploymentTrigger = None  # type: ignore[assignment]

from backend.flows.analytics_flow import refresh_market_intelligence
from backend.flows.compliance_flow import refresh_singapore_compliance

COMPLIANCE_TAG = "compliance"
MARKET_TAG = "market-intelligence"


async def ensure_deployments(work_queue: str = "default") -> None:
    """Create Prefect deployments if Prefect is available."""

    if Deployment is None or CronSchedule is None:  # pragma: no cover
        return

    analytics = await Deployment.build_from_flow(
        flow=refresh_market_intelligence,
        name="market-intelligence-daily",
        work_queue_name=work_queue,
        schedule=CronSchedule(cron="0 3 * * *", timezone="UTC"),
        parameters={"period_months": 12},
        tags=[MARKET_TAG],
    )
    compliance = await Deployment.build_from_flow(
        flow=refresh_singapore_compliance,
        name="singapore-compliance-hourly",
        work_queue_name=work_queue,
        schedule=CronSchedule(cron="0 * * * *", timezone="UTC"),
        tags=[COMPLIANCE_TAG],
    )

    await analytics.apply()
    await compliance.apply()


__all__ = ["ensure_deployments", "COMPLIANCE_TAG", "MARKET_TAG"]
