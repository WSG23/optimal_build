#!/usr/bin/env python3
"""Enforce the backend ``# type: `` ``ignore[...]`` budget."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    # type-ignore-meta: owner=platform expires=2026-06-30 reason=Python 3.11 fallback import
    import tomli as tomllib  # type: ignore[import-not-found]

REPO_ROOT = Path(__file__).resolve().parents[1]
GUARDRAIL_CONFIG = REPO_ROOT / "config" / "type_safety" / "guardrails.toml"


def load_baseline_count(config_path: Path = GUARDRAIL_CONFIG) -> int:
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    return int(data["type_ignore"]["backend_baseline"])


def count_backend_type_ignores(repo_root: Path = REPO_ROOT) -> int:
    count = 0
    for path in (repo_root / "backend").rglob("*.py"):
        count += path.read_text(encoding="utf-8", errors="ignore").count(
            "# type: ignore["
        )
    return count


def evaluate_budget(
    *,
    current_count: int,
    baseline_count: int,
    allow_increase: bool,
) -> tuple[bool, str]:
    if current_count <= baseline_count:
        return (
            True,
            f"Backend type: ignore budget ok ({current_count} <= {baseline_count})",
        )
    if allow_increase:
        return (
            True,
            (
                "Backend type: ignore count increased from "
                f"{baseline_count} to {current_count} with explicit override"
            ),
        )
    return (
        False,
        f"Backend type: ignore count increased from {baseline_count} to {current_count}",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-increase",
        action="store_true",
        help="Allow a budget increase for an explicitly approved run.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    baseline = load_baseline_count()
    current = count_backend_type_ignores()
    ok, message = evaluate_budget(
        current_count=current,
        baseline_count=baseline,
        allow_increase=args.allow_increase,
    )
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
