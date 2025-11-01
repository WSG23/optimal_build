#!/usr/bin/env python3
"""Minimal concurrent load test for the health endpoint."""

from __future__ import annotations

import argparse
import asyncio
import statistics
import time

import httpx


async def _worker(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    url: str,
    latencies: list[float],
    errors: list[str],
) -> None:
    async with semaphore:
        start = time.perf_counter()
        try:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
        except Exception as exc:  # pragma: no cover - network issues surfaced to caller
            errors.append(str(exc))
        else:
            latencies.append((time.perf_counter() - start) * 1000)


async def _run_load_test(args: argparse.Namespace) -> None:
    latencies: list[float] = []
    errors: list[str] = []
    semaphore = asyncio.Semaphore(args.concurrency)

    async with httpx.AsyncClient() as client:
        tasks = [
            asyncio.create_task(
                _worker(client, semaphore, args.url, latencies, errors)
            )
            for _ in range(args.requests)
        ]
        await asyncio.gather(*tasks)

    total = len(latencies)
    print(f"Completed {total} successful requests out of {args.requests}")
    if errors:
        print(f"Encountered {len(errors)} errors (see below):")
        for item in errors[:5]:
            print(f"  - {item}")

    if not latencies:
        return

    print(f"Average latency: {statistics.fmean(latencies):.2f} ms")
    print(f"Median latency: {statistics.median(latencies):.2f} ms")
    print(f"p95 latency: {statistics.quantiles(latencies, n=100)[94]:.2f} ms")
    print(f"Max latency: {max(latencies):.2f} ms")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load test a health endpoint")
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:9400/api/v1/health",
        help="Endpoint to benchmark",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=1000,
        help="Number of requests to issue",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Number of concurrent requests",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(_run_load_test(args))


if __name__ == "__main__":
    main()
