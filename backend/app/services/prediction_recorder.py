"""Helper for emitting rows into the ``predictions`` table.

AI services call :func:`record_prediction` after computing their output. The
row goes through the same ``AsyncSession`` the service already holds, so it
commits with whatever business transaction triggered the inference. If the
caller hasn't committed yet, the prediction row participates in their commit;
if they roll back, the prediction row rolls back too.

Keep the helper deliberately thin — domain serialization and confidence
extraction belong in the service, not here.
"""

from __future__ import annotations

import hashlib
import json
import logging
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.predictions import Prediction
from app.services.analytics_capture import capture_failure, should_raise_capture_errors

logger = logging.getLogger(__name__)


def _hash_input(payload: Any) -> str | None:
    if payload is None:
        return None
    try:
        encoded = json.dumps(payload, sort_keys=True, default=str)
    except (TypeError, ValueError):
        return None
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


async def record_prediction(
    db: AsyncSession,
    *,
    model_name: str,
    model_version: str,
    input_entity_type: str,
    input_entity_id: str,
    output: dict[str, Any],
    confidence: Decimal | float | None = None,
    label: str | None = None,
    input_payload: dict[str, Any] | None = None,
    cost_estimate: Decimal | float | None = None,
    latency_ms: int | None = None,
    tokens_used: int | None = None,
    model_provider: str | None = None,
    organization_id: str | None = None,
    created_by: str | None = None,
    flush: bool = True,
) -> int | None:
    """Persist one prediction row. Returns the new ``id`` or ``None`` on failure.

    Failure modes are logged but never raised — model-call paths must not be
    blocked by telemetry side effects.
    """

    try:
        pred = Prediction(
            model_name=model_name,
            model_version=model_version,
            model_provider=model_provider,
            input_entity_type=input_entity_type,
            input_entity_id=input_entity_id,
            input_payload=input_payload,
            input_hash=_hash_input(input_payload),
            output=output,
            label=label,
            confidence=(Decimal(str(confidence)) if confidence is not None else None),
            cost_estimate=(
                Decimal(str(cost_estimate)) if cost_estimate is not None else None
            ),
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            organization_id=organization_id,
            created_by=created_by,
        )
        db.add(pred)
        if flush:
            await db.flush()
        return pred.id
    except Exception as exc:  # pragma: no cover - defensive
        await capture_failure(
            source="prediction_recorder",
            error=exc,
            request_payload={
                "model_name": model_name,
                "model_version": model_version,
                "input_entity_type": input_entity_type,
                "input_entity_id": input_entity_id,
                "input_payload": input_payload,
            },
            raw_payload={"output": output},
            metadata={
                "model_provider": model_provider,
                "organization_id": organization_id,
                "created_by": created_by,
            },
            operation="record_prediction",
            raise_on_error=False,
        )
        if should_raise_capture_errors():
            raise
        logger.warning("record_prediction failed (%s): %s", model_name, exc)
        return None


__all__ = ["record_prediction"]
