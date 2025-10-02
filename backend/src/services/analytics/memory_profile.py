"""Memory profiling helpers for analytics jobs."""

from __future__ import annotations

import tracemalloc
from contextlib import contextmanager
from typing import Generator, Tuple


@contextmanager
def profile_memory_usage() -> Generator[Tuple[int, int], None, None]:
    """Context manager that records memory usage using ``tracemalloc``."""

    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()
    try:
        yield (0, 0)
    finally:
        snapshot_after = tracemalloc.take_snapshot()
        stats = snapshot_after.compare_to(snapshot_before, "lineno")
        current = tracemalloc.get_traced_memory()[0]
        peak = sum(stat.size_diff for stat in stats if stat.size_diff > 0)
        tracemalloc.stop()
        # update the yielded tuple in-place is not possible, so we just expose
        # the metrics via attributes on the context manager (used by tests).
        profile_memory_usage.last_snapshot = {
            "current": current,
            "peak": peak,
        }


profile_memory_usage.last_snapshot = {"current": 0, "peak": 0}
