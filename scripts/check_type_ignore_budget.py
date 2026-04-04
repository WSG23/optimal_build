#!/usr/bin/env python3
"""Enforce frozen suppression budgets across production and test Python code."""

from __future__ import annotations

import argparse
import io
import tokenize
from pathlib import Path
from typing import NamedTuple

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    # type-ignore-meta: owner=platform expires=2026-06-30 reason=Python 3.11 fallback import
    import tomli as tomllib  # type: ignore[import-not-found]

REPO_ROOT = Path(__file__).resolve().parents[1]
GUARDRAIL_CONFIG = REPO_ROOT / "config" / "type_safety" / "guardrails.toml"
SUPPRESSION_PATTERNS = (
    "# type: ignore[",
    "# mypy: disable-error-code",
    "# mypy: ignore-errors",
)


class BudgetCounts(NamedTuple):
    production: int
    backend_tests: int
    tests: int


def load_baseline_counts(config_path: Path = GUARDRAIL_CONFIG) -> BudgetCounts:
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    section = data["type_ignore"]
    baselines = BudgetCounts(
        production=int(section["production_baseline"]),
        backend_tests=int(section["backend_tests_baseline"]),
        tests=int(section["tests_baseline"]),
    )
    if baselines.production != 0:
        raise ValueError("type_ignore.production_baseline must remain 0")
    return baselines


def _count_suppressions_in_text(text: str) -> int:
    count = 0
    try:
        tokens = tokenize.generate_tokens(io.StringIO(text).readline)
        for token in tokens:
            if token.type != tokenize.COMMENT:
                continue
            count += sum(
                token.string.count(pattern) for pattern in SUPPRESSION_PATTERNS
            )
    except tokenize.TokenError:
        for line in text.splitlines():
            count += sum(line.count(pattern) for pattern in SUPPRESSION_PATTERNS)
    return count


def _count_suppressions_in_tree(path: Path) -> int:
    count = 0
    if not path.exists():
        return 0

    for candidate in path.rglob("*.py"):
        text = candidate.read_text(encoding="utf-8", errors="ignore")
        count += _count_suppressions_in_text(text)
    return count


def count_budgeted_suppressions(repo_root: Path = REPO_ROOT) -> BudgetCounts:
    backend_root = repo_root / "backend"
    backend_tests_root = backend_root / "tests"

    production = 0
    if backend_root.exists():
        for candidate in backend_root.rglob("*.py"):
            if backend_tests_root in candidate.parents:
                continue
            text = candidate.read_text(encoding="utf-8", errors="ignore")
            production += _count_suppressions_in_text(text)

    return BudgetCounts(
        production=production,
        backend_tests=_count_suppressions_in_tree(backend_tests_root),
        tests=_count_suppressions_in_tree(repo_root / "tests"),
    )


def evaluate_scope_budget(
    *,
    label: str,
    current_count: int,
    baseline_count: int,
    allow_increase: bool,
) -> tuple[bool, str]:
    if current_count <= baseline_count:
        return (
            True,
            f"{label} suppression budget ok ({current_count} <= {baseline_count})",
        )
    if allow_increase:
        return (
            True,
            (
                f"{label} suppression count increased from "
                f"{baseline_count} to {current_count} with explicit override"
            ),
        )
    return (
        False,
        f"{label} suppression count increased from {baseline_count} to {current_count}",
    )


def evaluate_budgets(
    *,
    current_counts: BudgetCounts,
    baseline_counts: BudgetCounts,
    allow_increase: bool,
) -> tuple[bool, list[str]]:
    messages = [
        (
            "Production suppression baseline is fixed at 0; "
            "new production suppressions are blocked by the staged type guardrails "
            f"(current tree count: {current_counts.production})"
        )
    ]
    scopes = (
        ("backend/tests", current_counts.backend_tests, baseline_counts.backend_tests),
        ("tests", current_counts.tests, baseline_counts.tests),
    )
    all_ok = True
    for label, current, baseline in scopes:
        ok, message = evaluate_scope_budget(
            label=label,
            current_count=current,
            baseline_count=baseline,
            allow_increase=allow_increase,
        )
        all_ok = all_ok and ok
        messages.append(message)
    return all_ok, messages


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
    try:
        baselines = load_baseline_counts()
        current_counts = count_budgeted_suppressions()
        ok, messages = evaluate_budgets(
            current_counts=current_counts,
            baseline_counts=baselines,
            allow_increase=args.allow_increase,
        )
    except ValueError as exc:
        print(str(exc))
        return 1
    for message in messages:
        print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
