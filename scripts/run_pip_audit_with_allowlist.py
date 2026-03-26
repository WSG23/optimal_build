#!/usr/bin/env python3
"""Run ``pip-audit`` with an expiring allowlist."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class AllowlistEntry:
    vulnerability_id: str
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
                vulnerability_id=parts[0],
                owner=parts[1],
                remove_by=parts[2],
                reason=parts[3],
            )
        )
    return entries


def validate_allowlist(entries: list[AllowlistEntry], *, today: date) -> list[str]:
    violations: list[str] = []
    for entry in entries:
        try:
            remove_by = date.fromisoformat(entry.remove_by)
        except ValueError:
            violations.append(
                f"invalid remove_by for {entry.vulnerability_id}: {entry.remove_by}"
            )
            continue
        if remove_by < today:
            violations.append(
                f"expired allowlist entry for {entry.vulnerability_id}: {entry.remove_by}"
            )
        if not entry.owner:
            violations.append(f"missing owner for {entry.vulnerability_id}")
        if not entry.reason:
            violations.append(f"missing reason for {entry.vulnerability_id}")
    return violations


def build_pip_audit_command(
    *,
    requirements: Path,
    entries: list[AllowlistEntry],
    extra_args: list[str] | None = None,
) -> list[str]:
    command = [sys.executable, "-m", "pip_audit", "-r", str(requirements)]
    for entry in entries:
        command.extend(["--ignore-vuln", entry.vulnerability_id])
    if extra_args:
        command.extend(extra_args)
    return command


def _run(command: list[str], *, stdout_path: Path | None = None) -> int:
    if stdout_path is None:
        completed = subprocess.run(command, check=False)
        return completed.returncode

    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    with stdout_path.open("w", encoding="utf-8") as handle:
        completed = subprocess.run(command, stdout=handle, check=False)
    return completed.returncode


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--requirements",
        default="backend/requirements.txt",
        help="Requirements file to audit",
    )
    parser.add_argument(
        "--allowlist",
        default="security/pip-audit-allowlist.txt",
        help="Expiring allowlist file",
    )
    parser.add_argument(
        "--json-output",
        default="",
        help="Optional JSON output path from pip-audit",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    allowlist_path = Path(args.allowlist)
    requirements_path = Path(args.requirements)
    if not allowlist_path.exists():
        print(f"allowlist not found: {allowlist_path}", file=sys.stderr)
        return 2
    if not requirements_path.exists():
        print(f"requirements file not found: {requirements_path}", file=sys.stderr)
        return 2

    entries = parse_allowlist(allowlist_path)
    violations = validate_allowlist(entries, today=date.today())
    if violations:
        for violation in violations:
            print(violation, file=sys.stderr)
        return 1

    report_code = 0
    if args.json_output:
        report_code = _run(
            build_pip_audit_command(
                requirements=requirements_path,
                entries=entries,
                extra_args=["--format", "json"],
            ),
            stdout_path=Path(args.json_output),
        )

    desc_code = _run(
        build_pip_audit_command(
            requirements=requirements_path,
            entries=entries,
            extra_args=["--desc"],
        )
    )

    return desc_code if desc_code != 0 else report_code


if __name__ == "__main__":
    raise SystemExit(main())
