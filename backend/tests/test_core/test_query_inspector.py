"""Tests for Query Performance Observatory.

Tests cover:
- QueryStats tracking and calculation
- QueryReport generation
- N+1 detection logic
- Query normalization
- QueryProfiler singleton behavior
- Decorator functionality
"""

from app.core.query_inspector import (
    QueryInspector,
    QueryProfiler,
    QueryReport,
    QueryStats,
)


class TestQueryStats:
    """Tests for QueryStats dataclass."""

    def test_initial_values(self) -> None:
        """Test initial QueryStats values."""
        stats = QueryStats(
            query_hash="SELECT * FROM users WHERE id = ?",
            query_template="SELECT * FROM users WHERE id = ?",
        )

        assert stats.execution_count == 0
        assert stats.total_time_ms == 0.0
        assert stats.min_time_ms == float("inf")
        assert stats.max_time_ms == 0.0

    def test_record_single_execution(self) -> None:
        """Test recording a single query execution."""
        stats = QueryStats(
            query_hash="test_query",
            query_template="SELECT * FROM test",
        )

        stats.record_execution(50.0)

        assert stats.execution_count == 1
        assert stats.total_time_ms == 50.0
        assert stats.min_time_ms == 50.0
        assert stats.max_time_ms == 50.0
        assert stats.avg_time_ms == 50.0

    def test_record_multiple_executions(self) -> None:
        """Test recording multiple query executions."""
        stats = QueryStats(
            query_hash="test_query",
            query_template="SELECT * FROM test",
        )

        stats.record_execution(10.0)
        stats.record_execution(20.0)
        stats.record_execution(30.0)

        assert stats.execution_count == 3
        assert stats.total_time_ms == 60.0
        assert stats.min_time_ms == 10.0
        assert stats.max_time_ms == 30.0
        assert stats.avg_time_ms == 20.0

    def test_avg_time_zero_executions(self) -> None:
        """Test average time with zero executions."""
        stats = QueryStats(
            query_hash="test_query",
            query_template="SELECT * FROM test",
        )

        assert stats.avg_time_ms == 0.0

    def test_timestamps_updated(self) -> None:
        """Test that timestamps are updated on execution."""
        stats = QueryStats(
            query_hash="test_query",
            query_template="SELECT * FROM test",
        )

        first_seen = stats.first_seen
        stats.record_execution(10.0)

        assert stats.first_seen == first_seen  # Unchanged
        assert stats.last_seen >= first_seen  # Updated


class TestQueryInspector:
    """Tests for QueryInspector context manager."""

    def test_normalize_query_removes_literals(self) -> None:
        """Test query normalization removes literal values."""
        inspector = QueryInspector()

        # String literals
        normalized = inspector._normalize_query(
            "SELECT * FROM users WHERE name = 'John'"
        )
        assert "'?'" in normalized
        assert "'John'" not in normalized

        # Numeric literals
        normalized = inspector._normalize_query("SELECT * FROM orders WHERE id = 123")
        assert "?" in normalized
        assert "123" not in normalized

    def test_normalize_query_handles_multiple_values(self) -> None:
        """Test normalization with multiple values."""
        inspector = QueryInspector()

        query = "SELECT * FROM products WHERE price > 100 AND name = 'Widget'"
        normalized = inspector._normalize_query(query)

        assert "100" not in normalized
        assert "'Widget'" not in normalized
        assert "?" in normalized

    def test_get_report_empty(self) -> None:
        """Test report with no queries."""
        inspector = QueryInspector()
        report = inspector.get_report()

        assert report.total_queries == 0
        assert report.unique_queries == 0
        assert report.potential_n_plus_one is False
        assert len(report.n_plus_one_candidates) == 0

    def test_n_plus_one_detection_threshold(self) -> None:
        """Test N+1 detection with custom threshold."""
        inspector = QueryInspector(n_plus_one_threshold=3)

        # Record 3 similar queries (should trigger N+1 warning)
        inspector._record_query("SELECT * FROM orders WHERE user_id = 1", 10.0)
        inspector._record_query("SELECT * FROM orders WHERE user_id = 2", 10.0)
        inspector._record_query("SELECT * FROM orders WHERE user_id = 3", 10.0)

        report = inspector.get_report()

        assert report.potential_n_plus_one is True
        assert len(report.n_plus_one_candidates) >= 1

    def test_n_plus_one_below_threshold(self) -> None:
        """Test N+1 detection below threshold."""
        inspector = QueryInspector(n_plus_one_threshold=5)

        # Record only 3 similar queries (below threshold of 5)
        inspector._record_query("SELECT * FROM orders WHERE user_id = 1", 10.0)
        inspector._record_query("SELECT * FROM orders WHERE user_id = 2", 10.0)
        inspector._record_query("SELECT * FROM orders WHERE user_id = 3", 10.0)

        report = inspector.get_report()

        assert report.potential_n_plus_one is False

    def test_slowest_queries_ordering(self) -> None:
        """Test that slowest queries are correctly ordered."""
        inspector = QueryInspector()

        inspector._record_query("SELECT * FROM fast", 10.0)
        inspector._record_query("SELECT * FROM slow", 100.0)
        inspector._record_query("SELECT * FROM medium", 50.0)

        report = inspector.get_report()

        assert len(report.slowest_queries) == 3
        assert report.slowest_queries[0].avg_time_ms == 100.0
        assert report.slowest_queries[1].avg_time_ms == 50.0
        assert report.slowest_queries[2].avg_time_ms == 10.0

    def test_total_time_calculation(self) -> None:
        """Test total time is sum of all query times."""
        inspector = QueryInspector()

        inspector._record_query("SELECT 1", 10.0)
        inspector._record_query("SELECT 2", 20.0)
        inspector._record_query("SELECT 3", 30.0)

        report = inspector.get_report()

        assert report.total_time_ms == 60.0


class TestQueryReport:
    """Tests for QueryReport dataclass."""

    def test_summary_format(self) -> None:
        """Test report summary formatting."""
        stats = QueryStats(
            query_hash="test",
            query_template="SELECT * FROM test WHERE id = ?",
        )
        stats.record_execution(50.0)

        report = QueryReport(
            total_queries=10,
            unique_queries=5,
            total_time_ms=500.0,
            query_stats=[stats],
            potential_n_plus_one=False,
            n_plus_one_candidates=[],
            slowest_queries=[stats],
        )

        summary = report.summary

        assert "Total queries: 10" in summary
        assert "Unique patterns: 5" in summary
        assert "500.00ms" in summary

    def test_summary_with_n_plus_one(self) -> None:
        """Test report summary includes N+1 warning."""
        report = QueryReport(
            total_queries=20,
            unique_queries=2,
            total_time_ms=100.0,
            query_stats=[],
            potential_n_plus_one=True,
            n_plus_one_candidates=["SELECT * FROM orders WHERE user_id = ?"],
            slowest_queries=[],
        )

        summary = report.summary

        assert "⚠️" in summary
        assert "N+1" in summary


class TestQueryProfiler:
    """Tests for QueryProfiler singleton."""

    def test_singleton_pattern(self) -> None:
        """Test that QueryProfiler is a singleton."""
        profiler1 = QueryProfiler()
        profiler2 = QueryProfiler()

        assert profiler1 is profiler2

    def test_record_query(self) -> None:
        """Test recording queries to profiler."""
        profiler = QueryProfiler()
        profiler.reset()

        profiler.record("SELECT * FROM users", 10.0)
        profiler.record("SELECT * FROM users", 20.0)

        summary = profiler.get_summary()

        assert summary["total_queries"] == 2
        assert summary["unique_patterns"] == 1

    def test_increment_request_count(self) -> None:
        """Test request count tracking."""
        profiler = QueryProfiler()
        profiler.reset()

        profiler.increment_request_count()
        profiler.increment_request_count()
        profiler.increment_request_count()

        summary = profiler.get_summary()

        assert summary["request_count"] == 3

    def test_get_top_queries_by_time(self) -> None:
        """Test getting top queries by total time."""
        profiler = QueryProfiler()
        profiler.reset()

        profiler.record("SELECT * FROM slow", 100.0)
        profiler.record("SELECT * FROM fast", 10.0)
        profiler.record("SELECT * FROM medium", 50.0)

        top = profiler.get_top_queries(n=3)

        assert len(top) == 3
        assert top[0].total_time_ms == 100.0

    def test_get_frequent_queries(self) -> None:
        """Test getting most frequent queries."""
        profiler = QueryProfiler()
        profiler.reset()

        profiler.record("SELECT * FROM common", 10.0)
        profiler.record("SELECT * FROM common", 10.0)
        profiler.record("SELECT * FROM common", 10.0)
        profiler.record("SELECT * FROM rare", 10.0)

        frequent = profiler.get_frequent_queries(n=2)

        assert len(frequent) == 2
        assert frequent[0].execution_count == 3

    def test_reset_clears_data(self) -> None:
        """Test that reset clears all data."""
        profiler = QueryProfiler()

        profiler.record("SELECT 1", 10.0)
        profiler.increment_request_count()

        profiler.reset()

        summary = profiler.get_summary()

        assert summary["total_queries"] == 0
        assert summary["request_count"] == 0

    def test_avg_queries_per_request(self) -> None:
        """Test average queries per request calculation."""
        profiler = QueryProfiler()
        profiler.reset()

        # 10 queries across 2 requests = 5 avg
        for _ in range(10):
            profiler.record("SELECT 1", 10.0)
        profiler.increment_request_count()
        profiler.increment_request_count()

        summary = profiler.get_summary()

        assert summary["avg_queries_per_request"] == 5.0

    def test_summary_structure(self) -> None:
        """Test summary dictionary structure."""
        profiler = QueryProfiler()
        profiler.reset()

        profiler.record("SELECT * FROM test", 10.0)
        profiler.increment_request_count()

        summary = profiler.get_summary()

        assert "request_count" in summary
        assert "total_queries" in summary
        assert "unique_patterns" in summary
        assert "total_time_ms" in summary
        assert "avg_queries_per_request" in summary
        assert "top_by_time" in summary
        assert "top_by_count" in summary


class TestQueryNormalization:
    """Tests for query normalization edge cases."""

    def test_normalize_with_uuid(self) -> None:
        """Test normalization handles UUID-like strings."""
        inspector = QueryInspector()

        query = "SELECT * FROM users WHERE id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'"
        normalized = inspector._normalize_query(query)

        assert "a1b2c3d4" not in normalized

    def test_normalize_preserves_keywords(self) -> None:
        """Test normalization preserves SQL keywords."""
        inspector = QueryInspector()

        query = "SELECT id, name FROM users WHERE active = 1 ORDER BY name LIMIT 10"
        normalized = inspector._normalize_query(query)

        assert "SELECT" in normalized
        assert "FROM" in normalized
        assert "WHERE" in normalized
        assert "ORDER BY" in normalized
        assert "LIMIT" in normalized

    def test_normalize_multiple_tables(self) -> None:
        """Test normalization with joins."""
        inspector = QueryInspector()

        query = """
            SELECT u.name, o.total
            FROM users u
            JOIN orders o ON u.id = o.user_id
            WHERE o.total > 100
        """
        normalized = inspector._normalize_query(query)

        assert "users" in normalized
        assert "orders" in normalized
        assert "JOIN" in normalized

    def test_normalize_whitespace(self) -> None:
        """Test normalization handles various whitespace."""
        inspector = QueryInspector()

        query = "SELECT   *    FROM   users    WHERE   id = 1"
        normalized = inspector._normalize_query(query)

        # Should normalize to single spaces
        assert "  " not in normalized


class TestInspectorConfiguration:
    """Tests for QueryInspector configuration options."""

    def test_default_thresholds(self) -> None:
        """Test default threshold values."""
        inspector = QueryInspector()

        assert inspector.n_plus_one_threshold == 3
        assert inspector.slow_query_threshold_ms == 100.0

    def test_custom_thresholds(self) -> None:
        """Test custom threshold values."""
        inspector = QueryInspector(
            n_plus_one_threshold=10,
            slow_query_threshold_ms=500.0,
        )

        assert inspector.n_plus_one_threshold == 10
        assert inspector.slow_query_threshold_ms == 500.0

    def test_higher_threshold_reduces_warnings(self) -> None:
        """Test that higher threshold reduces false positives."""
        # With low threshold
        low_inspector = QueryInspector(n_plus_one_threshold=2)
        low_inspector._record_query("SELECT * FROM t WHERE id = 1", 10.0)
        low_inspector._record_query("SELECT * FROM t WHERE id = 2", 10.0)

        assert low_inspector.get_report().potential_n_plus_one is True

        # With high threshold
        high_inspector = QueryInspector(n_plus_one_threshold=5)
        high_inspector._record_query("SELECT * FROM t WHERE id = 1", 10.0)
        high_inspector._record_query("SELECT * FROM t WHERE id = 2", 10.0)

        assert high_inspector.get_report().potential_n_plus_one is False
