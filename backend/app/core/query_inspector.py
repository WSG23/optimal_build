"""Query Performance Observatory for detecting and analyzing query patterns.

This module provides:
- N+1 query detection during development/testing
- Query timing and statistics collection
- Performance reporting utilities

Usage:
    from app.core.query_inspector import QueryInspector, track_queries

    # As context manager for specific operations
    async with QueryInspector() as inspector:
        result = await fetch_users_with_orders()
        report = inspector.get_report()
        if report.potential_n_plus_one:
            logger.warning("Potential N+1 detected: %s", report.summary)

    # As decorator for endpoint functions
    @track_queries(warn_threshold=5)
    async def list_users():
        return await db.execute(select(User))
"""

from __future__ import annotations

import functools
import logging
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from collections.abc import AsyncIterator
from typing import Any, Callable, TypeVar

from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger("app.query_inspector")

# Thread-local storage for query tracking
_query_context = threading.local()

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class QueryStats:
    """Statistics for a single query pattern."""

    query_hash: str
    query_template: str
    execution_count: int = 0
    total_time_ms: float = 0.0
    min_time_ms: float = float("inf")
    max_time_ms: float = 0.0
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)

    @property
    def avg_time_ms(self) -> float:
        """Average execution time in milliseconds."""
        if self.execution_count == 0:
            return 0.0
        return self.total_time_ms / self.execution_count

    def record_execution(self, duration_ms: float) -> None:
        """Record a query execution."""
        self.execution_count += 1
        self.total_time_ms += duration_ms
        self.min_time_ms = min(self.min_time_ms, duration_ms)
        self.max_time_ms = max(self.max_time_ms, duration_ms)
        self.last_seen = time.time()


@dataclass
class QueryReport:
    """Report of query activity during an inspection period."""

    total_queries: int
    unique_queries: int
    total_time_ms: float
    query_stats: list[QueryStats]
    potential_n_plus_one: bool
    n_plus_one_candidates: list[str]
    slowest_queries: list[QueryStats]

    @property
    def summary(self) -> str:
        """Human-readable summary of the query activity."""
        lines = [
            f"Total queries: {self.total_queries}",
            f"Unique patterns: {self.unique_queries}",
            f"Total time: {self.total_time_ms:.2f}ms",
        ]

        if self.potential_n_plus_one:
            lines.append(
                f"⚠️  Potential N+1: {len(self.n_plus_one_candidates)} patterns"
            )
            for candidate in self.n_plus_one_candidates[:3]:
                lines.append(f"   - {candidate[:80]}...")

        if self.slowest_queries:
            lines.append("Slowest queries:")
            for qs in self.slowest_queries[:3]:
                lines.append(
                    f"   - {qs.avg_time_ms:.2f}ms avg: {qs.query_template[:60]}..."
                )

        return "\n".join(lines)


class QueryInspector:
    """Context manager for inspecting query patterns.

    Tracks all queries executed within the context and provides
    analysis for potential N+1 issues and performance problems.
    """

    # Class-level flag to track if listeners are installed
    _listeners_installed: bool = False
    _lock: threading.Lock = threading.Lock()

    def __init__(
        self,
        n_plus_one_threshold: int = 3,
        slow_query_threshold_ms: float = 100.0,
    ) -> None:
        """Initialize the inspector.

        Args:
            n_plus_one_threshold: Number of similar queries to trigger N+1 warning
            slow_query_threshold_ms: Queries slower than this are flagged
        """
        self.n_plus_one_threshold = n_plus_one_threshold
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self._queries: list[tuple[str, float]] = []
        self._query_counts: dict[str, QueryStats] = {}
        self._start_time: float = 0.0
        self._active = False

    @classmethod
    def _ensure_listeners(cls, engine: Engine) -> None:
        """Install SQLAlchemy event listeners if not already installed."""
        with cls._lock:
            if cls._listeners_installed:
                return

            @event.listens_for(engine, "before_cursor_execute")  # type: ignore[untyped-decorator]
            def _before_execute(
                conn: Any,
                cursor: Any,
                statement: str,
                parameters: Any,
                context: Any,
                executemany: bool,
            ) -> None:
                context._inspector_start_time = time.perf_counter()

            @event.listens_for(engine, "after_cursor_execute")  # type: ignore[untyped-decorator]
            def _after_execute(
                conn: Any,
                cursor: Any,
                statement: str,
                parameters: Any,
                context: Any,
                executemany: bool,
            ) -> None:
                start = getattr(context, "_inspector_start_time", None)
                if start is None:
                    return

                duration_ms = (time.perf_counter() - start) * 1000

                # Record in thread-local context if active
                inspector = getattr(_query_context, "inspector", None)
                if inspector is not None and inspector._active:
                    inspector._record_query(statement, duration_ms)

            cls._listeners_installed = True

    def _record_query(self, statement: str, duration_ms: float) -> None:
        """Record a query execution."""
        # Normalize query for pattern matching (remove specific values)
        query_hash = self._normalize_query(statement)

        self._queries.append((statement, duration_ms))

        if query_hash not in self._query_counts:
            self._query_counts[query_hash] = QueryStats(
                query_hash=query_hash,
                query_template=statement[:200],
            )

        self._query_counts[query_hash].record_execution(duration_ms)

    def _normalize_query(self, statement: str) -> str:
        """Normalize a query for pattern matching.

        Replaces literal values with placeholders to identify similar queries.
        """
        # Simple normalization - replace quoted strings and numbers
        import re

        normalized = statement.strip()
        # Replace string literals
        normalized = re.sub(r"'[^']*'", "'?'", normalized)
        # Replace numeric literals
        normalized = re.sub(r"\b\d+\b", "?", normalized)
        # Remove excess whitespace
        normalized = " ".join(normalized.split())

        return normalized

    def get_report(self) -> QueryReport:
        """Generate a report of query activity."""
        total_time = sum(d for _, d in self._queries)

        # Identify potential N+1 patterns
        n_plus_one_candidates = [
            stats.query_template
            for stats in self._query_counts.values()
            if stats.execution_count >= self.n_plus_one_threshold
        ]

        # Find slowest queries
        slowest = sorted(
            self._query_counts.values(),
            key=lambda s: s.avg_time_ms,
            reverse=True,
        )[:5]

        return QueryReport(
            total_queries=len(self._queries),
            unique_queries=len(self._query_counts),
            total_time_ms=total_time,
            query_stats=list(self._query_counts.values()),
            potential_n_plus_one=len(n_plus_one_candidates) > 0,
            n_plus_one_candidates=n_plus_one_candidates,
            slowest_queries=slowest,
        )

    async def __aenter__(self) -> "QueryInspector":
        """Enter the inspection context."""
        self._start_time = time.perf_counter()
        self._active = True
        _query_context.inspector = self

        # Lazy import to avoid circular imports
        from app.core.database import engine

        self._ensure_listeners(engine.sync_engine)

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit the inspection context."""
        self._active = False
        _query_context.inspector = None

        # Log report if there were issues
        report = self.get_report()
        if report.potential_n_plus_one:
            logger.warning(
                "Potential N+1 query detected:\n%s",
                report.summary,
            )


@asynccontextmanager
async def inspect_queries(
    n_plus_one_threshold: int = 3,
    slow_query_threshold_ms: float = 100.0,
) -> AsyncIterator[QueryInspector]:
    """Context manager for query inspection.

    Usage:
        async with inspect_queries() as inspector:
            await some_database_operation()
            report = inspector.get_report()
    """
    inspector = QueryInspector(
        n_plus_one_threshold=n_plus_one_threshold,
        slow_query_threshold_ms=slow_query_threshold_ms,
    )
    async with inspector:
        yield inspector


def track_queries(
    warn_threshold: int = 5,
    log_all: bool = False,
) -> Callable[[F], F]:
    """Decorator to track queries for an async function.

    Args:
        warn_threshold: Log warning if more than this many similar queries
        log_all: Log all query activity, not just warnings

    Usage:
        @track_queries(warn_threshold=3)
        async def get_users_with_orders():
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            inspector = QueryInspector(n_plus_one_threshold=warn_threshold)
            async with inspector:
                result = await func(*args, **kwargs)

            report = inspector.get_report()

            if log_all or report.potential_n_plus_one:
                level = (
                    logging.WARNING if report.potential_n_plus_one else logging.DEBUG
                )
                logger.log(
                    level,
                    "Query report for %s:\n%s",
                    func.__name__,
                    report.summary,
                )

            return result

        return wrapper  # type: ignore[return-value]

    return decorator


class QueryProfiler:
    """Singleton profiler for aggregating query statistics across requests.

    Use for long-running analysis and reporting.
    """

    _instance: "QueryProfiler | None" = None
    _lock: threading.Lock = threading.Lock()
    _stats: dict[str, QueryStats]
    _request_count: int

    def __new__(cls) -> "QueryProfiler":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._stats = {}
                cls._instance._request_count = 0
            return cls._instance

    def record(self, query: str, duration_ms: float) -> None:
        """Record a query execution."""
        # Normalize for pattern matching
        normalized = " ".join(query.strip().split())
        normalized = normalized[:200]

        with self._lock:
            if normalized not in self._stats:
                self._stats[normalized] = QueryStats(
                    query_hash=normalized,
                    query_template=normalized,
                )
            self._stats[normalized].record_execution(duration_ms)

    def increment_request_count(self) -> None:
        """Track number of requests profiled."""
        with self._lock:
            self._request_count += 1

    def get_top_queries(self, n: int = 10) -> list[QueryStats]:
        """Get top N queries by total execution time."""
        with self._lock:
            return sorted(
                self._stats.values(),
                key=lambda s: s.total_time_ms,
                reverse=True,
            )[:n]

    def get_frequent_queries(self, n: int = 10) -> list[QueryStats]:
        """Get top N queries by execution count."""
        with self._lock:
            return sorted(
                self._stats.values(),
                key=lambda s: s.execution_count,
                reverse=True,
            )[:n]

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics."""
        with self._lock:
            total_queries = sum(s.execution_count for s in self._stats.values())
            total_time = sum(s.total_time_ms for s in self._stats.values())

            return {
                "request_count": self._request_count,
                "total_queries": total_queries,
                "unique_patterns": len(self._stats),
                "total_time_ms": total_time,
                "avg_queries_per_request": (
                    total_queries / self._request_count
                    if self._request_count > 0
                    else 0
                ),
                "top_by_time": [
                    {
                        "query": s.query_template,
                        "total_ms": s.total_time_ms,
                        "count": s.execution_count,
                        "avg_ms": s.avg_time_ms,
                    }
                    for s in self.get_top_queries(5)
                ],
                "top_by_count": [
                    {
                        "query": s.query_template,
                        "count": s.execution_count,
                        "total_ms": s.total_time_ms,
                    }
                    for s in self.get_frequent_queries(5)
                ],
            }

    def reset(self) -> None:
        """Reset all statistics."""
        with self._lock:
            self._stats.clear()
            self._request_count = 0


# Global profiler instance
query_profiler = QueryProfiler()


__all__ = [
    "QueryInspector",
    "QueryReport",
    "QueryStats",
    "inspect_queries",
    "track_queries",
    "QueryProfiler",
    "query_profiler",
]
