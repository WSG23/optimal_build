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
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

# Directories that are expensive to scan or intentionally vendor dependencies.
DEFAULT_IGNORED_DIRECTORIES = {
    ".git",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
    "venv",
    ".venv",
}

DEFAULT_IGNORED_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".zip",
    ".tar",
    ".gz",
}


def iter_files(base: Path, ignored_directories: Sequence[str]) -> Iterable[Path]:
    """Yield files under *base* skipping directories in *ignored_directories*."""

    ignored = set(ignored_directories)

    for path in base.rglob("*"):
        if path.is_dir():
            if set(path.parts) & ignored:
                # Skip recursing into ignored directories by pruning children.
                # rglob will still iterate into the directory, so continue.
                continue
            continue

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
) -> Dict[str, List[Path]]:
    """Return a mapping of content hashes to duplicate file paths."""

    duplicates: Dict[str, List[Path]] = {}

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

        duplicates.setdefault(digest, []).append(path)

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

    args = parser.parse_args()

    ignored_directories = tuple(DEFAULT_IGNORED_DIRECTORIES | set(args.ignore_dir))
    ignored_suffixes = tuple(DEFAULT_IGNORED_SUFFIXES | set(args.ignore_suffix))

    duplicate_groups = find_duplicates(
        args.root,
        ignored_directories=ignored_directories,
        ignored_suffixes=ignored_suffixes,
        min_size=args.min_size,
    )

    if args.json:
        import json

        json_groups = {
            digest: [str(path) for path in paths]
            for digest, paths in sorted(duplicate_groups.items())
        }
        print(json.dumps(json_groups, indent=2))
        return

    if not duplicate_groups:
        print("No duplicate files detected.")
        return

    print(f"Found {len(duplicate_groups)} duplicate content groups:\n")
    for digest, paths in sorted(duplicate_groups.items()):
        print(f"Hash {digest}:")
        print(format_group(paths))
        print()


if __name__ == "__main__":
    main()
