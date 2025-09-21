"""PWP pro-forma cost adjustment services."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Optional, cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.costs import get_latest_cost_index
from app.utils import metrics
from app.utils.logging import get_logger, log_event

logger = get_logger(__name__)


async def adjust_pro_forma_cost(
    session: AsyncSession,
    *,
    base_cost: Decimal,
    series_name: str,
    jurisdiction: str = "SG",
    provider: Optional[str] = None,
) -> Decimal:
    """Apply the latest cost index scalar to a base cost."""

    index = await get_latest_cost_index(
        session,
        series_name=series_name,
        jurisdiction=jurisdiction,
        provider=provider,
    )
    if index is None:
        log_event(logger, "pro_forma_cost_no_index", series=series_name, jurisdiction=jurisdiction)
        return base_cost

    scalar = Decimal(cast(Any, index).value)
    metrics.COST_ADJUSTMENT_GAUGE.labels(series=series_name).set(float(scalar))
    adjusted = (base_cost * scalar).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    log_event(
        logger,
        "pro_forma_cost_adjusted",
        series=series_name,
        jurisdiction=jurisdiction,
        base_cost=str(base_cost),
        scalar=str(scalar),
        adjusted=str(adjusted),
    )
    return adjusted
