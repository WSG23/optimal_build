"""SQLite-based benchmark harness for Phase 2D audit."""

from __future__ import annotations

import argparse
import math
import sqlite3
import statistics
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class BenchmarkCase:
    """Represents a single SQL benchmark."""

    name: str
    statement: str
    parameters: tuple
    fetch: str = "all"  # 'all' or 'one'
    iterations: int = 5
    warmup: int = 1


REPO_ROOT = Path(__file__).resolve().parent.parent
DEVSTACK_DIR = REPO_ROOT / ".devstack"
DEVSTACK_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DEVSTACK_DIR / "audit_bench.db"


def _percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    position = percentile * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[int(position)]
    lower_val = ordered[lower]
    upper_val = ordered[upper]
    weight = position - lower
    return lower_val + weight * (upper_val - lower_val)


def _reset_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA journal_mode = WAL;
        PRAGMA synchronous = NORMAL;

        DROP TABLE IF EXISTS ref_cost_catalogs;
        DROP TABLE IF EXISTS ref_cost_indices;

        CREATE TABLE ref_cost_catalogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jurisdiction TEXT NOT NULL DEFAULT 'SG',
            catalog_name TEXT NOT NULL,
            category TEXT,
            item_code TEXT NOT NULL,
            description TEXT,
            unit TEXT,
            unit_cost REAL,
            currency TEXT DEFAULT 'SGD',
            effective_date TEXT,
            item_metadata TEXT,
            source TEXT
        );

        CREATE INDEX idx_cost_catalogs_name_code
            ON ref_cost_catalogs (catalog_name, item_code);
        CREATE INDEX idx_cost_catalogs_category
            ON ref_cost_catalogs (category);

        CREATE TABLE ref_cost_indices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jurisdiction TEXT NOT NULL DEFAULT 'SG',
            series_name TEXT NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT,
            period TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT NOT NULL,
            source TEXT,
            provider TEXT NOT NULL DEFAULT 'internal',
            methodology TEXT
        );

        CREATE INDEX idx_cost_indices_series_period
            ON ref_cost_indices (series_name, period);
        CREATE INDEX idx_cost_indices_jurisdiction_category
            ON ref_cost_indices (jurisdiction, category);
        CREATE INDEX idx_cost_indices_provider
            ON ref_cost_indices (provider);
        """
    )
    conn.commit()


def _seed_catalog(conn: sqlite3.Connection, rows: int) -> None:
    data = [
        (
            "SG",
            "Benchmark Catalog",
            f"category_{idx % 8}",
            f"ITEM{idx:06d}",
            "Synthetic catalog row for benchmarking.",
            "m2",
            150.0 + (idx % 50),
            "SGD",
            None,
            None,
            "synthetic",
        )
        for idx in range(rows)
    ]
    conn.executemany(
        """
        INSERT INTO ref_cost_catalogs (
            jurisdiction,
            catalog_name,
            category,
            item_code,
            description,
            unit,
            unit_cost,
            currency,
            effective_date,
            item_metadata,
            source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        data,
    )
    conn.commit()


def _seed_indices(conn: sqlite3.Connection, series: int, per_series: int) -> None:
    rows: list[tuple] = []
    for series_idx in range(series):
        for offset in range(per_series):
            quarter = (offset % 4) + 1
            year = 2020 + offset // 4
            rows.append(
                (
                    "SG",
                    f"Benchmark Series {series_idx}",
                    "material" if series_idx % 2 == 0 else "labor",
                    "automation",
                    f"{year}-Q{quarter}",
                    120.0 + series_idx + offset / 10,
                    "index",
                    "synthetic",
                    "BCA",
                    "synthetic-data",
                )
            )
    conn.executemany(
        """
        INSERT INTO ref_cost_indices (
            jurisdiction,
            series_name,
            category,
            subcategory,
            period,
            value,
            unit,
            source,
            provider,
            methodology
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()


def _prepare_cases(target_series: int) -> list[BenchmarkCase]:
    return [
        BenchmarkCase(
            name="list_catalog_all",
            statement="""
                SELECT *
                FROM ref_cost_catalogs
                WHERE catalog_name = ?
                ORDER BY item_code
            """,
            parameters=("Benchmark Catalog",),
        ),
        BenchmarkCase(
            name="list_catalog_structural",
            statement="""
                SELECT *
                FROM ref_cost_catalogs
                WHERE catalog_name = ? AND category = ?
                ORDER BY item_code
            """,
            parameters=("Benchmark Catalog", "category_2"),
        ),
        BenchmarkCase(
            name="latest_cost_index",
            statement="""
                SELECT *
                FROM ref_cost_indices
                WHERE series_name = ? AND jurisdiction = ? AND provider = ?
                ORDER BY period DESC, id DESC
                LIMIT 1
            """,
            parameters=(f"Benchmark Series {target_series}", "SG", "BCA"),
            fetch="one",
        ),
    ]


def _run_case(
    conn: sqlite3.Connection, case: BenchmarkCase
) -> dict[str, float | int | str]:
    timings: list[float] = []
    result_sizes: list[int] = []
    cursor = conn.cursor()
    total_iterations = case.warmup + case.iterations

    for iteration in range(total_iterations):
        start = time.perf_counter()
        cursor.execute(case.statement, case.parameters)

        if case.fetch == "one":
            result = cursor.fetchone()
            size = 0 if result is None else 1
        else:
            result = cursor.fetchall()
            size = len(result)
        elapsed_ms = (time.perf_counter() - start) * 1000

        if iteration >= case.warmup:
            timings.append(elapsed_ms)
            result_sizes.append(size)

    mean_ms = statistics.fmean(timings) if timings else 0.0
    p95_ms = _percentile(timings, 0.95)
    max_ms = max(timings) if timings else 0.0

    return {
        "name": case.name,
        "iterations": case.iterations,
        "mean_ms": round(mean_ms, 2),
        "p95_ms": round(p95_ms, 2),
        "max_ms": round(max_ms, 2),
        "result_size": max(result_sizes) if result_sizes else 0,
    }


def _format_markdown(results: Iterable[dict[str, float | int | str]]) -> str:
    header = (
        "| Benchmark | Iterations | Mean (ms) | P95 (ms) | Max (ms) | Result size |"
    )
    divider = (
        "|-----------|------------|-----------|----------|----------|-------------|"
    )
    rows = [
        f"| {item['name']} | {item['iterations']} | {item['mean_ms']} | "
        f"{item['p95_ms']} | {item['max_ms']} | {item['result_size']} |"
        for item in results
    ]
    return "\n".join([header, divider, *rows])


def run_benchmarks(
    catalog_rows: int, indices_per_series: int
) -> list[dict[str, float | int | str]]:
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    _reset_schema(conn)
    _seed_catalog(conn, catalog_rows)
    series_count = max(5, catalog_rows // 40)
    _seed_indices(conn, series_count, indices_per_series)

    target_series = max(2, series_count // 2)
    cases = _prepare_cases(target_series)

    results = [_run_case(conn, case) for case in cases]
    conn.close()
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run lightweight SQLite benchmarks aligned with the Pre-Phase 2D audit."
    )
    parser.add_argument(
        "--catalog-rows",
        type=int,
        default=2000,
        help="Number of synthetic catalog rows to seed (default: 2000).",
    )
    parser.add_argument(
        "--indices-per-series",
        type=int,
        default=16,
        help="Number of cost index periods per series (default: 16).",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Emit a Markdown table summarising results.",
    )
    args = parser.parse_args()

    results = run_benchmarks(args.catalog_rows, args.indices_per_series)

    print("Benchmark summary:")
    for item in results:
        print(
            f"- {item['name']}: mean={item['mean_ms']} ms, "
            f"p95={item['p95_ms']} ms, max={item['max_ms']} ms, "
            f"result_size={item['result_size']}"
        )

    if args.markdown:
        print("\nMarkdown table:\n")
        print(_format_markdown(results))


if __name__ == "__main__":
    main()
