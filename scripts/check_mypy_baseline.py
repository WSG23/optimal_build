#!/usr/bin/env python3
"""Check mypy results against the stored regression baseline."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = REPO_ROOT / ".mypy_baseline"
SUMMARY_RE = re.compile(r"Found (?P<count>\d+) errors? in (?P<files>\d+) files?")
SUCCESS_RE = re.compile(r"Success: no issues found in (?P<files>\d+) source files")
ERROR_RE = re.compile(
    r"^(?P<path>[^:\s][^:]*\.py):\d+(?::\d+)?:\s*error:\s*(?P<message>.*)$"
)


class BaselineError(RuntimeError):
    """Raised when the baseline file cannot be loaded."""


def build_mypy_command() -> list[str]:
    return [sys.executable, "-m", "mypy", "--config-file", str(REPO_ROOT / "mypy.ini")]


def run_mypy() -> tuple[int, str]:
    result = subprocess.run(
        build_mypy_command(),
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout


def normalise_path(raw_path: str) -> str:
    candidate = raw_path.replace("\\", "/")
    repo_prefix = str(REPO_ROOT).replace("\\", "/")
    if candidate.startswith(repo_prefix):
        candidate = candidate[len(repo_prefix) :].lstrip("/")
    return candidate.lstrip("./")


def parse_mypy_output(output: str) -> tuple[int, dict[str, int], dict[str, list[str]]]:
    errors_by_file: dict[str, int] = defaultdict(int)
    examples: dict[str, list[str]] = defaultdict(list)
    total_errors: int | None = None

    for line in output.splitlines():
        match = ERROR_RE.match(line)
        if match:
            path = normalise_path(match.group("path"))
            errors_by_file[path] += 1
            if len(examples[path]) < 3:
                examples[path].append(match.group("message").strip())
            continue

        summary_match = SUMMARY_RE.search(line)
        if summary_match:
            total_errors = int(summary_match.group("count"))
            continue

        success_match = SUCCESS_RE.search(line)
        if success_match:
            total_errors = 0

    if total_errors is None:
        total_errors = sum(errors_by_file.values())

    return total_errors, dict(errors_by_file), dict(examples)


def load_baseline() -> dict[str, Any]:
    if not BASELINE_PATH.exists():
        raise BaselineError(
            "Baseline file .mypy_baseline is missing. Run with --update to create it."
        )

    try:
        data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover
        raise BaselineError(f"Failed to parse baseline JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise BaselineError("Baseline JSON must be an object.")
    if "total_errors" not in data or "files" not in data:
        raise BaselineError("Baseline JSON must contain total_errors and files keys.")
    if not isinstance(data["files"], dict):
        raise BaselineError(
            "Baseline 'files' entry must be a mapping of paths to counts."
        )
    return data


def save_baseline(total_errors: int, per_file: dict[str, int]) -> None:
    payload = {
        "total_errors": total_errors,
        "files": dict(sorted(per_file.items())),
        "metadata": {
            "generated_at": datetime.now(UTC).isoformat(),
            "command": build_mypy_command(),
        },
    }
    BASELINE_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def compare_with_baseline(
    current_per_file: dict[str, int],
    baseline: dict[str, Any],
) -> tuple[dict[str, int], dict[str, int]]:
    baseline_per_file = {
        path: int(count) for path, count in ((baseline.get("files") or {}).items())
    }

    regressions: dict[str, int] = {}
    improvements: dict[str, int] = {}

    for path, current_count in current_per_file.items():
        baseline_count = baseline_per_file.get(path, 0)
        if current_count > baseline_count:
            regressions[path] = current_count - baseline_count
        elif current_count < baseline_count:
            improvements[path] = baseline_count - current_count

    for path, baseline_count in baseline_per_file.items():
        if path not in current_per_file and baseline_count > 0:
            improvements[path] = baseline_count

    return regressions, improvements


def _render_regressions(
    regressions: dict[str, int], examples: dict[str, list[str]]
) -> None:
    for path, delta in sorted(
        regressions.items(), key=lambda item: (-item[1], item[0])
    ):
        print(f"{path}: +{delta} mypy errors", file=sys.stderr)
        for snippet in examples.get(path, [])[:2]:
            print(f"  ↳ {snippet}", file=sys.stderr)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update",
        action="store_true",
        help="Regenerate the baseline from the current mypy output.",
    )
    parser.add_argument(
        "--json-output",
        default="",
        help="Optional JSON output path for delta metadata.",
    )
    parser.add_argument(
        "--keep-log",
        default="",
        help="Optional path to store raw mypy output.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    exit_code, output = run_mypy()

    if args.keep_log:
        Path(args.keep_log).write_text(output, encoding="utf-8")

    total_errors, per_file, examples = parse_mypy_output(output)
    if args.update:
        save_baseline(total_errors, per_file)
        print(f"Updated mypy baseline: {total_errors} errors")
        return 0

    baseline = load_baseline()
    regressions, improvements = compare_with_baseline(per_file, baseline)

    payload = {
        "current": total_errors,
        "baseline": int(baseline["total_errors"]),
        "delta": total_errors - int(baseline["total_errors"]),
        "regressions": regressions,
        "improvements": improvements,
    }
    if args.json_output:
        output_path = Path(args.json_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    if regressions:
        _render_regressions(regressions, examples)
        return 1

    if exit_code not in (0, 1):
        print(output, file=sys.stderr)
        return exit_code

    print(
        f"Mypy baseline ok ({total_errors} current errors, baseline {baseline['total_errors']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
