from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

import pytest

from app.utils import logging as logging_utils


class SampleEnum(Enum):
    VALUE = "example"


class StubLogger:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    def info(
        self, event: str, **kwargs: object
    ) -> None:  # pragma: no cover - invoked by log_event
        self.calls.append((event, kwargs))


@pytest.mark.parametrize(
    "value, expected",
    [
        (
            UUID("12345678-1234-5678-1234-567812345678"),
            "12345678-1234-5678-1234-567812345678",
        ),
        (Decimal("12.50"), "12.50"),
        (
            datetime(2024, 5, 1, 12, 30, tzinfo=timezone.utc),
            "2024-05-01T12:30:00+00:00",
        ),
        (SampleEnum.VALUE, "example"),
        (
            {"nested": datetime(2024, 5, 1, 0, 0, tzinfo=timezone.utc)},
            {"nested": "2024-05-01T00:00:00+00:00"},
        ),
        (
            [UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")],
            ["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"],
        ),
    ],
)
def test_serialise_for_logging_normalises_values(value, expected) -> None:
    assert logging_utils._serialise_for_logging(value) == expected


def test_log_event_serialises_payload() -> None:
    logger = StubLogger()
    event_id = uuid4()
    payload = {
        "identifier": event_id,
        "amount": Decimal("42.75"),
        "metadata": {"occurred_at": datetime(2024, 5, 1, tzinfo=timezone.utc)},
    }

    logging_utils.log_event(logger, "agent.event", **payload)

    assert logger.calls == [
        (
            "agent.event",
            {
                "identifier": str(event_id),
                "amount": "42.75",
                "metadata": {"occurred_at": "2024-05-01T00:00:00+00:00"},
            },
        )
    ]
