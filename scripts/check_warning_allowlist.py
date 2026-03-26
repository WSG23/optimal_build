#!/usr/bin/env python3
"""Validate pytest warning allowlist metadata and coverage."""

from __future__ import annotations

import argparse
import configparser
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class AllowlistEntry:
    line_no: int
    filter_spec: str
    owner: str
    remove_by: str
    reason: str


def parse_allowlist(path: Path) -> list[AllowlistEntry]:
    entries: list[AllowlistEntry] = []
    for line_no, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 4:
            raise ValueError(f"invalid allowlist line {line_no}: expected 4 columns")
        entries.append(
            AllowlistEntry(
                line_no=line_no,
                filter_spec=parts[0],
                owner=parts[1],
                remove_by=parts[2],
                reason=parts[3],
            )
        )
    return entries


def extract_pytest_filterwarnings(path: Path) -> list[str]:
    parser = configparser.ConfigParser()
    parser.read(path, encoding="utf-8")
    raw_value = parser.get("pytest", "filterwarnings", fallback="")
    return [line.strip() for line in raw_value.splitlines() if line.strip()]


def evaluate_allowlist(
    *,
    entries: list[AllowlistEntry],
    filterwarnings: list[str],
    today: date,
) -> tuple[list[AllowlistEntry], list[tuple[int, str]], list[str], list[str]]:
    expired: list[AllowlistEntry] = []
    invalid_date_lines: list[tuple[int, str]] = []

    allowed_specs = {entry.filter_spec for entry in entries}
    missing = [warning for warning in filterwarnings if warning not in allowed_specs]
    unused = sorted(
        entry.filter_spec
        for entry in entries
        if entry.filter_spec not in set(filterwarnings)
    )

    for entry in entries:
        try:
            remove_by = date.fromisoformat(entry.remove_by)
        except ValueError:
            invalid_date_lines.append((entry.line_no, entry.remove_by))
            continue
        if remove_by < today:
            expired.append(entry)

    return expired, invalid_date_lines, missing, unused


def write_summary(
    path: Path,
    *,
    entries: list[AllowlistEntry],
    expired: list[AllowlistEntry],
    invalid_date_lines: list[tuple[int, str]],
    missing: list[str],
    unused: list[str],
) -> None:
    lines = [
        "# Warning Allowlist Summary",
        "",
        f"- Total entries: **{len(entries)}**",
        f"- Expired entries: **{len(expired)}**",
        f"- Invalid date entries: **{len(invalid_date_lines)}**",
        f"- Missing pytest filters: **{len(missing)}**",
        f"- Unused allowlist entries: **{len(unused)}**",
        "",
    ]

    if missing:
        lines.extend(["## Missing Filters", ""])
        lines.extend(f"- `{entry}`" for entry in missing)
        lines.append("")

    if unused:
        lines.extend(["## Unused Allowlist Entries", ""])
        lines.extend(f"- `{entry}`" for entry in unused)
        lines.append("")

    if expired:
        lines.extend(
            [
                "## Expired Entries",
                "",
                "| Line | Owner | remove_by | Filter |",
                "| --- | --- | --- | --- |",
            ]
        )
        for item in expired:
            safe_filter = item.filter_spec.replace("|", "\\|")
            lines.append(
                f"| {item.line_no} | {item.owner} | {item.remove_by} | {safe_filter} |"
            )
        lines.append("")

    if invalid_date_lines:
        lines.extend(
            [
                "## Invalid Date Entries",
                "",
                "| Line | remove_by |",
                "| --- | --- |",
            ]
        )
        for line_no, remove_by in invalid_date_lines:
            lines.append(f"| {line_no} | {remove_by} |")
        lines.append("")

    while lines and lines[-1] == "":
        lines.pop()

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allowlist",
        default="config/testing/pytest_warning_allowlist.txt",
        help="Warning allowlist file path",
    )
    parser.add_argument(
        "--pytest-ini",
        default="pytest.ini",
        help="Pytest configuration file path",
    )
    parser.add_argument(
        "--summary-md",
        default="reports/warning-allowlist-summary.md",
        help="Summary markdown output path",
    )
    parser.add_argument(
        "--fail-on-expired",
        action="store_true",
        help="Fail when any allowlist entry has expired.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    allowlist_path = Path(args.allowlist)
    pytest_ini_path = Path(args.pytest_ini)
    if not allowlist_path.exists():
        print(f"allowlist not found: {allowlist_path}")
        return 2
    if not pytest_ini_path.exists():
        print(f"pytest.ini not found: {pytest_ini_path}")
        return 2

    entries = parse_allowlist(allowlist_path)
    filterwarnings = extract_pytest_filterwarnings(pytest_ini_path)
    expired, invalid_dates, missing, unused = evaluate_allowlist(
        entries=entries,
        filterwarnings=filterwarnings,
        today=date.today(),
    )

    write_summary(
        Path(args.summary_md),
        entries=entries,
        expired=expired,
        invalid_date_lines=invalid_dates,
        missing=missing,
        unused=unused,
    )

    print(
        "warning-allowlist "
        f"entries={len(entries)} expired={len(expired)} invalid_dates={len(invalid_dates)} "
        f"missing={len(missing)} unused={len(unused)}"
    )

    if invalid_dates or missing or unused:
        return 1
    if args.fail_on_expired and expired:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
