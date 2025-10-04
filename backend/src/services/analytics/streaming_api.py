"""Simple streaming analytics API used by the tests."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Iterable, Iterator, List


@dataclass
class Event:
    """Lightweight analytics event."""

    key: str
    value: float


class StreamingAnalyticsAPI:
    """In-memory streaming API for analytics events."""

    def __init__(self) -> None:
        self._events: Deque[Event] = deque()

    def publish(self, key: str, value: float) -> None:
        self._events.append(Event(key=key, value=value))

    def batch_publish(self, events: Iterable[Event]) -> None:
        for event in events:
            self.publish(event.key, event.value)

    def stream(self) -> Iterator[Event]:
        while self._events:
            yield self._events.popleft()

    def snapshot(self) -> List[Event]:
        return list(self._events)
