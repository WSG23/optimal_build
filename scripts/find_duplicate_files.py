#!/usr/bin/env python3
"""Utility to detect duplicate files within the repository.

The script walks the repository tree, ignoring common virtual environment
and dependency folders, and groups files that share the same content hash.
It is designed to help engineers quickly identify accidental duplicates
checked into the code base.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from collections.abc import Iterable, Sequence
from pathlib import Path

# Directories that are expensive to scan or intentionally vendor dependencies.
DEFAULT_IGNORED_DIRECTORIES: tuple[str, ...] = (
    ".git",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
    "venv",
    ".venv",
    ".venv.backup",
    "venv.backup",
    "env",
    ".direnv",
    ".ruff_cache",
    ".tox",
    "third_party",
    "vendor",
    "site-packages",
    "tmp",
    "logs",
)

DEFAULT_IGNORED_SUFFIXES: tuple[str, ...] = (
    ".pyc",
    ".pyo",
    ".zip",
    ".tar",
    ".gz",
    ".bak",
)


def iter_files(base: Path, ignored_directories: Sequence[str]) -> Iterable[Path]:
    """Yield files under *base* skipping directories in *ignored_directories*."""

    ignored = set(ignored_directories)
    base = base.resolve()

    for root, dirs, files in os.walk(base):
        root_path = Path(root)

        if set(root_path.parts) & ignored:
            dirs[:] = []
            continue

        dirs[:] = [directory for directory in dirs if directory not in ignored]

        for name in files:
            path = root_path / name

            if set(path.parts) & ignored:
                continue

            yield path


def hash_file(path: Path) -> str:
    """Return an md5 hash for the file at *path*."""

    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_duplicates(
    base: Path,
    *,
    ignored_directories: Sequence[str],
    ignored_suffixes: Sequence[str],
    min_size: int,
    max_groups: int | None,
) -> dict[str, list[Path]]:
    """Return a mapping of content hashes to duplicate file paths."""

    duplicates: dict[str, list[Path]] = {}
    duplicate_group_count = 0

    for path in iter_files(base, ignored_directories):
        if not path.is_file():
            continue

        if path.suffix in ignored_suffixes:
            continue

        try:
            size = path.stat().st_size
        except OSError:
            continue

        if size < min_size:
            continue

        try:
            digest = hash_file(path)
        except OSError:
            continue

        paths = duplicates.setdefault(digest, [])
        paths.append(path)

        if len(paths) == 2:
            duplicate_group_count += 1
            if max_groups is not None and duplicate_group_count >= max_groups:
                break

    return {key: paths for key, paths in duplicates.items() if len(paths) > 1}


def format_group(paths: Sequence[Path]) -> str:
    return "\n".join(f"  - {path}" for path in sorted(paths))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Path to scan for duplicate files (defaults to repository root).",
    )
    parser.add_argument(
        "--min-size",
        type=int,
        default=1,
        help="Ignore files smaller than this many bytes (default: 1).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine readable JSON instead of a text report.",
    )
    parser.add_argument(
        "--ignore-dir",
        action="append",
        default=[],
        help="Additional directory name to ignore while scanning.",
    )
    parser.add_argument(
        "--ignore-suffix",
        action="append",
        default=[],
        help="Additional file suffix to ignore while scanning.",
    )
    parser.add_argument(
        "--max-groups",
        type=int,
        default=0,
        help="Stop scanning after finding this many duplicate hash groups (0 means no limit).",
    )
    parser.add_argument(
        "--fail-on-duplicates",
        action="store_true",
        help="Exit with status code 1 if duplicate groups are detected.",
    )

    args = parser.parse_args()

    ignored_directories = tuple(set(DEFAULT_IGNORED_DIRECTORIES) | set(args.ignore_dir))
    ignored_suffixes = tuple(set(DEFAULT_IGNORED_SUFFIXES) | set(args.ignore_suffix))
    max_groups = None if args.max_groups <= 0 else args.max_groups

    duplicate_groups = find_duplicates(
        args.root,
        ignored_directories=ignored_directories,
        ignored_suffixes=ignored_suffixes,
        min_size=args.min_size,
        max_groups=max_groups,
    )

    if args.json:
        import json

        json_groups = {
            digest: [str(path) for path in paths]
            for digest, paths in sorted(duplicate_groups.items())
        }
        print(json.dumps(json_groups, indent=2))
        if args.fail_on_duplicates and duplicate_groups:
            raise SystemExit(1)
        return

    if not duplicate_groups:
        print("No duplicate files detected.")
        return

    print(f"Found {len(duplicate_groups)} duplicate content groups:\n")
    for digest, paths in sorted(duplicate_groups.items()):
        print(f"Hash {digest}:")
        print(format_group(paths))
        print()

    if args.fail_on_duplicates:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
