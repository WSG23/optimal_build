#!/usr/bin/env python3
"""Guardrails for mypy relaxations and newly added ``type: ignore`` comments."""

from __future__ import annotations

import argparse
import configparser
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import NamedTuple

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    # type-ignore-meta: owner=platform expires=2026-06-30 reason=Python 3.11 fallback import
    import tomli as tomllib  # type: ignore[import-not-found]

REPO_ROOT = Path(__file__).resolve().parents[1]
GUARDRAIL_CONFIG = REPO_ROOT / "config" / "type_safety" / "guardrails.toml"
TYPE_IGNORE_RE = re.compile(r"#\s*type:\s*ignore\[(?P<codes>[^\]]+)\](?P<meta>.*)$")
BARE_TYPE_IGNORE_RE = re.compile(r"#\s*type:\s*ignore\b(?!\[)")
TYPE_IGNORE_META_RE = re.compile(r"#\s*type-ignore-meta:\s*(?P<meta>.*)$")
FILE_LEVEL_SUPPRESSION_PATTERNS = (
    re.compile(r"#\s*mypy:\s*ignore-errors\b"),
    re.compile(r"#\s*mypy:\s*disable-error-code\b"),
)
METADATA_PAIR_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=([^\s#]+)")


class GuardrailConfig(NamedTuple):
    pyproject_ignore_modules: set[str]
    mypy_ini_ignore_sections: set[str]
    type_ignore_required_metadata_keys: tuple[str, ...]


def _require_entry_metadata(
    entry: dict[str, object],
    *,
    required_keys: tuple[str, ...],
    context: str,
) -> None:
    missing = [key for key in required_keys if not str(entry.get(key, "")).strip()]
    if missing:
        raise ValueError(f"{context} missing required metadata: {', '.join(missing)}")


def load_guardrail_config(path: Path = GUARDRAIL_CONFIG) -> GuardrailConfig:
    data = tomllib.loads(path.read_text(encoding="utf-8"))

    pyproject_modules: set[str] = set()
    for entry in data.get("pyproject_ignore_errors", []):
        _require_entry_metadata(
            entry,
            required_keys=("module", "owner", "rationale"),
            context="pyproject_ignore_errors entry",
        )
        pyproject_modules.add(str(entry["module"]))

    mypy_sections: set[str] = set()
    for entry in data.get("mypy_ini_ignore_errors", []):
        _require_entry_metadata(
            entry,
            required_keys=("section", "owner", "rationale"),
            context="mypy_ini_ignore_errors entry",
        )
        mypy_sections.add(str(entry["section"]))

    required_metadata_keys = tuple(
        key.strip()
        for key in data.get("type_ignore", {}).get("required_metadata_keys", ())
        if str(key).strip()
    )
    if not required_metadata_keys:
        raise ValueError("type_ignore.required_metadata_keys must not be empty")

    return GuardrailConfig(
        pyproject_ignore_modules=pyproject_modules,
        mypy_ini_ignore_sections=mypy_sections,
        type_ignore_required_metadata_keys=required_metadata_keys,
    )


def find_mypy_ini_guardrail_violations(
    mypy_ini_text: str,
    *,
    allowed_ignore_sections: set[str],
) -> list[str]:
    parser = configparser.ConfigParser()
    parser.read_string(mypy_ini_text)

    violations: list[str] = []
    for section in parser.sections():
        if parser.get(section, "ignore_errors", fallback="False").lower() != "true":
            continue
        if section not in allowed_ignore_sections:
            violations.append(f"Unexpected mypy.ini ignore_errors section: {section}")
    return violations


def find_pyproject_guardrail_violations(
    pyproject_text: str,
    *,
    allowed_ignore_modules: set[str],
) -> list[str]:
    data = tomllib.loads(pyproject_text)
    overrides = data.get("tool", {}).get("mypy", {}).get("overrides", [])
    violations: list[str] = []

    for override in overrides:
        if not isinstance(override, dict):
            continue

        modules = override.get("module", [])
        if isinstance(modules, str):
            module_list = [modules]
        else:
            module_list = [module for module in modules if isinstance(module, str)]

        if override.get("ignore_errors") is True:
            unexpected = sorted(set(module_list) - allowed_ignore_modules)
            for module_name in unexpected:
                violations.append(
                    f"Unexpected backend/pyproject.toml ignore_errors module: {module_name}"
                )

    return violations


def parse_added_line_numbers(diff_text: str) -> dict[str, set[int]]:
    added_by_file: dict[str, set[int]] = {}
    current_file: str | None = None
    current_line: int | None = None

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("diff --git "):
            parts = raw_line.split()
            if len(parts) >= 4 and parts[3].startswith("b/"):
                current_file = parts[3][2:]
                current_line = None
            continue
        if raw_line.startswith("+++ b/"):
            current_file = raw_line[len("+++ b/") :]
            current_line = None
            continue
        if raw_line.startswith("@@ "):
            plus_chunk = raw_line.split("+", 1)[1]
            line_part = plus_chunk.split(" ", 1)[0]
            start_text = line_part.split(",", 1)[0]
            current_line = int(start_text)
            continue
        if current_file is None or current_line is None:
            continue
        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            added_by_file.setdefault(current_file, set()).add(current_line)
            current_line += 1
            continue
        if raw_line.startswith("-") and not raw_line.startswith("---"):
            continue
        current_line += 1

    return added_by_file


def _extract_metadata(comment: str) -> str:
    match = TYPE_IGNORE_RE.search(comment)
    if match is not None:
        return match.group("meta")

    match = TYPE_IGNORE_META_RE.search(comment)
    if match is None:
        return ""
    return match.group("meta")


def _parse_metadata_pairs(comment: str) -> dict[str, str]:
    metadata = _extract_metadata(comment)
    if not metadata:
        return {}
    return dict(METADATA_PAIR_RE.findall(metadata))


def _metadata_keys_present(
    comment: str,
    required_keys: tuple[str, ...],
    *,
    previous_line: str = "",
) -> bool:
    metadata = _parse_metadata_pairs(comment)
    if not all(metadata.get(key) for key in required_keys) and previous_line:
        metadata = _parse_metadata_pairs(previous_line)
    if not all(metadata.get(key) for key in required_keys):
        return False

    expires = metadata.get("expires")
    if expires is not None:
        try:
            date.fromisoformat(expires)
        except ValueError:
            return False
    return True


def find_unjustified_type_ignore_violations(
    repo_root: Path,
    added_by_file: dict[str, set[int]],
    *,
    required_metadata_keys: tuple[str, ...],
) -> list[str]:
    violations: list[str] = []

    for relative_path, line_numbers in sorted(added_by_file.items()):
        candidate = repo_root / relative_path
        if not candidate.exists() or candidate.suffix != ".py":
            continue

        lines = candidate.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line_number in sorted(line_numbers):
            if line_number < 1 or line_number > len(lines):
                continue

            line = lines[line_number - 1]
            previous_line = lines[line_number - 2] if line_number > 1 else ""

            if any(pattern.search(line) for pattern in FILE_LEVEL_SUPPRESSION_PATTERNS):
                violations.append(
                    f"{relative_path}:{line_number} adds a broad mypy "
                    "suppression; scope it narrowly instead"
                )
                continue

            if BARE_TYPE_IGNORE_RE.search(line):
                violations.append(
                    f"{relative_path}:{line_number} adds bare `type: ignore`; "
                    "use an error code and metadata"
                )
                continue

            if TYPE_IGNORE_RE.search(line) and not _metadata_keys_present(
                line,
                required_metadata_keys,
                previous_line=previous_line,
            ):
                violations.append(
                    f"{relative_path}:{line_number} adds "
                    "`type: ignore[...]` without owner/expires/reason "
                    "metadata"
                )

    return violations


def _git_diff_text(*, diff_base: str | None, staged: bool, repo_root: Path) -> str:
    command = ["git", "diff", "--unified=0"]
    if staged:
        command.append("--cached")
    elif diff_base:
        command.append(f"{diff_base}...HEAD")
    else:
        return ""

    completed = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "git diff failed")
    return completed.stdout


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config-only",
        action="store_true",
        help="Validate allowlist configuration without inspecting a diff.",
    )
    parser.add_argument(
        "--diff-base",
        help="Compare against the provided git base revision and inspect added Python lines.",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Inspect staged Python changes instead of a branch diff.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.staged and args.diff_base:
        print("--staged and --diff-base are mutually exclusive", file=sys.stderr)
        return 2

    config = load_guardrail_config()
    violations: list[str] = []

    violations.extend(
        find_mypy_ini_guardrail_violations(
            (REPO_ROOT / "mypy.ini").read_text(encoding="utf-8"),
            allowed_ignore_sections=config.mypy_ini_ignore_sections,
        )
    )
    violations.extend(
        find_pyproject_guardrail_violations(
            (REPO_ROOT / "backend" / "pyproject.toml").read_text(encoding="utf-8"),
            allowed_ignore_modules=config.pyproject_ignore_modules,
        )
    )

    if args.staged or args.diff_base:
        diff_text = _git_diff_text(
            diff_base=args.diff_base,
            staged=args.staged,
            repo_root=REPO_ROOT,
        )
        added_by_file = parse_added_line_numbers(diff_text)
        violations.extend(
            find_unjustified_type_ignore_violations(
                REPO_ROOT,
                added_by_file,
                required_metadata_keys=config.type_ignore_required_metadata_keys,
            )
        )

    if violations:
        for violation in violations:
            print(violation, file=sys.stderr)
        return 1

    print("Type guardrails passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
