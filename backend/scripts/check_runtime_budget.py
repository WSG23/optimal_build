#!/usr/bin/env python3
"""Enforce backend pytest runtime budgets from JUnit XML output."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
import json
from pathlib import Path
import tomllib
import xml.etree.ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "testing" / "runtime_budget.toml"
DEFAULT_JUNIT_XML = REPO_ROOT / "artifacts" / "backend-junit.xml"


@dataclass(frozen=True)
class RuntimeBudgetAllowance:
    """Per-test override for especially slow but intentional cases."""

    nodeid: str
    max_seconds: float
    owner: str
    remove_by: str
    reason: str


@dataclass(frozen=True)
class RuntimeBudgetConfig:
    """Serializable runtime budget configuration."""

    max_total_seconds: float
    default_test_case_seconds: float
    max_slowest_tests: int
    allowances: tuple[RuntimeBudgetAllowance, ...] = ()


@dataclass(frozen=True)
class TestCaseTiming:
    """Single testcase timing extracted from JUnit XML."""

    nodeid: str
    seconds: float
    classname: str
    name: str


@dataclass(frozen=True)
class RuntimeBudgetReport:
    """Evaluation result for the current JUnit payload."""

    total_seconds: float
    case_count: int
    failures: tuple[str, ...]
    expired_allowances: tuple[str, ...]
    slowest_cases: tuple[TestCaseTiming, ...]


def load_runtime_budget_config(path: Path) -> RuntimeBudgetConfig:
    """Load runtime budget configuration from TOML."""

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    pytest_config = data.get("pytest")
    if not isinstance(pytest_config, dict):
        raise ValueError("runtime budget config must contain a [pytest] table")

    allowances = tuple(
        RuntimeBudgetAllowance(
            nodeid=str(entry["nodeid"]),
            max_seconds=float(entry["max_seconds"]),
            owner=str(entry["owner"]),
            remove_by=str(entry["remove_by"]),
            reason=str(entry["reason"]),
        )
        for entry in pytest_config.get("allowances", [])
    )

    return RuntimeBudgetConfig(
        max_total_seconds=float(pytest_config["max_total_seconds"]),
        default_test_case_seconds=float(pytest_config["default_test_case_seconds"]),
        max_slowest_tests=int(pytest_config.get("max_slowest_tests", 10)),
        allowances=allowances,
    )


def _nodeid_from_testcase(element: ET.Element) -> str:
    """Return a stable pytest-style nodeid for the given testcase element."""

    file_attr = (element.get("file") or "").strip()
    name = (element.get("name") or "").strip() or "unknown"
    if file_attr:
        return f"{file_attr}::{name}"

    classname = (element.get("classname") or "").strip()
    if classname:
        inferred_file = f"{classname.replace('.', '/')}.py"
        return f"{inferred_file}::{name}"
    return name


def parse_junit_testcases(path: Path) -> list[TestCaseTiming]:
    """Parse testcase timings from JUnit XML."""

    root = ET.fromstring(path.read_text(encoding="utf-8"))
    cases: list[TestCaseTiming] = []
    for testcase in root.iter("testcase"):
        seconds = float(testcase.get("time", "0") or 0.0)
        cases.append(
            TestCaseTiming(
                nodeid=_nodeid_from_testcase(testcase),
                seconds=seconds,
                classname=(testcase.get("classname") or "").strip(),
                name=(testcase.get("name") or "").strip() or "unknown",
            )
        )
    return cases


def evaluate_runtime_budget(
    cases: list[TestCaseTiming],
    config: RuntimeBudgetConfig,
    *,
    today: date | None = None,
) -> RuntimeBudgetReport:
    """Evaluate runtime budgets for the supplied testcase timings."""

    if not cases:
        raise ValueError("JUnit report did not contain any testcase timings")

    today = today or date.today()
    failures: list[str] = []
    expired_allowances: list[str] = []
    allowances = {entry.nodeid: entry for entry in config.allowances}
    total_seconds = round(sum(case.seconds for case in cases), 3)

    if total_seconds > config.max_total_seconds:
        failures.append(
            "Pytest runtime budget exceeded: "
            f"{total_seconds:.3f}s > {config.max_total_seconds:.3f}s"
        )

    for allowance in config.allowances:
        remove_by = date.fromisoformat(allowance.remove_by)
        if remove_by < today:
            expired_allowances.append(
                f"{allowance.nodeid} allowance expired on {allowance.remove_by}"
            )

    if expired_allowances:
        failures.extend(expired_allowances)

    slowest_cases = tuple(
        sorted(cases, key=lambda case: case.seconds, reverse=True)[
            : config.max_slowest_tests
        ]
    )

    for case in cases:
        allowance = allowances.get(case.nodeid)
        allowed_seconds = (
            allowance.max_seconds
            if allowance is not None
            else config.default_test_case_seconds
        )
        if case.seconds > allowed_seconds:
            failures.append(
                f"{case.nodeid} exceeded runtime budget: "
                f"{case.seconds:.3f}s > {allowed_seconds:.3f}s"
            )

    return RuntimeBudgetReport(
        total_seconds=total_seconds,
        case_count=len(cases),
        failures=tuple(failures),
        expired_allowances=tuple(expired_allowances),
        slowest_cases=slowest_cases,
    )


def render_markdown_summary(
    report: RuntimeBudgetReport,
    config: RuntimeBudgetConfig,
) -> str:
    """Render a concise markdown summary for CI artifacts."""

    lines = [
        "# Runtime Budget Summary",
        "",
        f"- Total runtime: `{report.total_seconds:.3f}s`",
        f"- Test cases: `{report.case_count}`",
        f"- Total budget: `{config.max_total_seconds:.3f}s`",
        f"- Default per-test budget: `{config.default_test_case_seconds:.3f}s`",
        "",
        "| Test | Time (s) | Budget (s) |",
        "| --- | ---: | ---: |",
    ]
    allowances = {entry.nodeid: entry for entry in config.allowances}
    for case in report.slowest_cases:
        allowance = allowances.get(case.nodeid)
        budget = (
            allowance.max_seconds
            if allowance is not None
            else config.default_test_case_seconds
        )
        lines.append(f"| `{case.nodeid}` | {case.seconds:.3f} | {budget:.3f} |")

    if report.failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in report.failures)

    return "\n".join(lines) + "\n"


def _serialise_report(
    report: RuntimeBudgetReport,
    config: RuntimeBudgetConfig,
) -> dict[str, object]:
    """Return a JSON-serialisable payload."""

    return {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "config": {
            "max_total_seconds": config.max_total_seconds,
            "default_test_case_seconds": config.default_test_case_seconds,
            "max_slowest_tests": config.max_slowest_tests,
            "allowances": [asdict(entry) for entry in config.allowances],
        },
        "report": {
            "total_seconds": report.total_seconds,
            "case_count": report.case_count,
            "failures": list(report.failures),
            "expired_allowances": list(report.expired_allowances),
            "slowest_cases": [asdict(case) for case in report.slowest_cases],
        },
    }


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to the runtime budget TOML config",
    )
    parser.add_argument(
        "--junit-xml",
        type=Path,
        default=DEFAULT_JUNIT_XML,
        help="Path to the JUnit XML artifact to evaluate",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        help="Optional markdown summary output path",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optional JSON summary output path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_runtime_budget_config(args.config)
    cases = parse_junit_testcases(args.junit_xml)
    report = evaluate_runtime_budget(cases, config)

    payload = _serialise_report(report, config)
    print(json.dumps(payload, indent=2, sort_keys=True))

    if args.markdown_output is not None:
        _write_text(args.markdown_output, render_markdown_summary(report, config))
    if args.json_output is not None:
        _write_text(args.json_output, json.dumps(payload, indent=2, sort_keys=True))

    if report.failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
