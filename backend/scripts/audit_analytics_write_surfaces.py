"""Inventory database write surfaces and analytics capture instrumentation.

This is a lightweight guardrail for analytics completeness reviews. It scans
application and job code for mutating database operations, capture helper calls,
and fire-and-forget task scheduling, then prints a concise JSON summary.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = (
    REPO_ROOT / "backend" / "app",
    REPO_ROOT / "backend" / "jobs",
)
WRITE_METHODS = {
    "add",
    "add_all",
    "bulk_save_objects",
    "delete",
    "merge",
}
SQL_MUTATORS = {
    "delete",
    "insert",
    "pg_insert",
    "sqlite_insert",
    "update",
}
CAPTURE_HELPERS = {
    "capture_external_call",
    "capture_failure",
    "capture_lifecycle_event",
    "capture_raw_artifact",
    "capture_rejection",
    "capture_status_transition",
    "capture_success",
}
BACKGROUND_TASKS = {"create_task", "add_task", "enqueue", "delay"}


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


def _receiver_looks_like_session(name: str) -> bool:
    parts = name.split(".")[:-1]
    return any(part in {"db", "sess", "session", "sync_session"} for part in parts)


def _record(path: Path, node: ast.AST, name: str) -> dict[str, Any]:
    return {
        "file": str(path.relative_to(REPO_ROOT)),
        "line": getattr(node, "lineno", None),
        "call": name,
    }


def _is_sql_mutator_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    name = _call_name(node.func)
    if not name:
        return False
    leaf = name.rsplit(".", 1)[-1]
    if leaf not in SQL_MUTATORS:
        return False
    if isinstance(node.func, ast.Name):
        return True
    return ".__table__." in name


def _execute_runs_mutator(node: ast.Call, mutator_vars: set[str]) -> bool:
    if not node.args:
        return False
    first_arg = node.args[0]
    if _is_sql_mutator_call(first_arg):
        return True
    if isinstance(first_arg, ast.Name):
        return first_arg.id in mutator_vars
    return False


def _scan_file(path: Path) -> dict[str, list[dict[str, Any]]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    writes: list[dict[str, Any]] = []
    captures: list[dict[str, Any]] = []
    background_tasks: list[dict[str, Any]] = []
    mutator_vars: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and _is_sql_mutator_call(node.value):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    mutator_vars.add(target.id)
        elif isinstance(node, ast.AnnAssign) and _is_sql_mutator_call(node.value):
            if isinstance(node.target, ast.Name):
                mutator_vars.add(node.target.id)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node.func)
        if not name:
            continue
        leaf = name.rsplit(".", 1)[-1]
        is_session_write = leaf in WRITE_METHODS and _receiver_looks_like_session(name)
        is_sql_write = leaf in SQL_MUTATORS and _is_sql_mutator_call(node)
        is_execute_write = leaf == "execute" and _execute_runs_mutator(
            node, mutator_vars
        )
        if is_session_write or is_sql_write or is_execute_write:
            writes.append(_record(path, node, name))
        if leaf in CAPTURE_HELPERS:
            captures.append(_record(path, node, name))
        if leaf in BACKGROUND_TASKS:
            background_tasks.append(_record(path, node, name))

    return {
        "writes": writes,
        "captures": captures,
        "background_tasks": background_tasks,
    }


def build_inventory() -> dict[str, Any]:
    files: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for root in SCAN_ROOTS:
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            result = _scan_file(path)
            if any(result.values()):
                files[str(path.relative_to(REPO_ROOT))] = result

    write_files = {
        path: result
        for path, result in files.items()
        if result["writes"] or result["background_tasks"]
    }
    captured_files = {path for path, result in files.items() if result["captures"]}
    write_files_without_capture = sorted(
        path
        for path, result in write_files.items()
        if path not in captured_files and not path.startswith("backend/app/models/")
    )

    return {
        "summary": {
            "files_with_writes_or_background_tasks": len(write_files),
            "files_with_capture_helpers": len(captured_files),
            "write_files_without_capture_helpers": len(write_files_without_capture),
            "write_calls": sum(len(result["writes"]) for result in files.values()),
            "capture_calls": sum(len(result["captures"]) for result in files.values()),
            "background_task_calls": sum(
                len(result["background_tasks"]) for result in files.values()
            ),
        },
        "write_files_without_capture_helpers": write_files_without_capture,
        "files": files,
    }


def main() -> int:
    print(json.dumps(build_inventory(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
