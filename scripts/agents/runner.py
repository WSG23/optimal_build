#!/usr/bin/env python3
"""Canonical runner for verification and agent memory operations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_RUNS_FILE = Path("metrics/agent_runs.jsonl")
DEFAULT_MEMORY_FILE = Path("metrics/agent_memory.jsonl")


@dataclass(frozen=True)
class VerifyPhase:
    name: str
    command: str
    failing_component: str
    likely_root_cause: str
    recommended_rerun_command: str


VERIFY_PHASES_BY_MODE: dict[str, list[VerifyPhase]] = {
    "quick": [
        VerifyPhase(
            name="backend-lint",
            command="make lint",
            failing_component="backend",
            likely_root_cause="Python linting or formatting violation",
            recommended_rerun_command="make lint",
        ),
    ],
    "full": [
        VerifyPhase(
            name="full-verify",
            command="make verify",
            failing_component="quality",
            likely_root_cause="One or more quality gates failed in full verification",
            recommended_rerun_command="make verify",
        ),
    ],
    "pre-pr": [
        VerifyPhase(
            name="format-check",
            command="make format-check",
            failing_component="quality",
            likely_root_cause="Formatting drift or formatter mismatch",
            recommended_rerun_command="make format-check",
        ),
        VerifyPhase(
            name="lint",
            command="make lint",
            failing_component="quality",
            likely_root_cause="Lint violation in backend/frontend source",
            recommended_rerun_command="make lint",
        ),
        VerifyPhase(
            name="coding-rules",
            command="make check-coding-rules",
            failing_component="quality",
            likely_root_cause="Repository coding rules violation",
            recommended_rerun_command="make check-coding-rules",
        ),
    ],
    "integration": [
        VerifyPhase(
            name="backend-typecheck",
            command="make typecheck-backend",
            failing_component="backend",
            likely_root_cause="Backend typing or import contract regression",
            recommended_rerun_command="make typecheck-backend",
        ),
        VerifyPhase(
            name="frontend-quality",
            command="make lint-ui-standards",
            failing_component="frontend",
            likely_root_cause="Frontend UI standards or lint drift",
            recommended_rerun_command="make lint-ui-standards",
        ),
        VerifyPhase(
            name="security-gate",
            command="make lint-prod",
            failing_component="security",
            likely_root_cause="Security lint gate failed",
            recommended_rerun_command="make lint-prod",
        ),
        VerifyPhase(
            name="deps-gate",
            command="make check-tool-versions",
            failing_component="deps",
            likely_root_cause="Dependency or tool version mismatch",
            recommended_rerun_command="make check-tool-versions",
        ),
        VerifyPhase(
            name="quality-rules",
            command="make check-coding-rules",
            failing_component="quality",
            likely_root_cause="Coding rules regression",
            recommended_rerun_command="make check-coding-rules",
        ),
    ],
    "audit": [
        VerifyPhase(
            name="audit-rules",
            command="make check-coding-rules",
            failing_component="quality",
            likely_root_cause="Coding rules audit failed",
            recommended_rerun_command="make check-coding-rules",
        ),
        VerifyPhase(
            name="audit-delivery-plan",
            command="make validate-delivery-plan",
            failing_component="quality",
            likely_root_cause="Delivery plan structure validation failed",
            recommended_rerun_command="make validate-delivery-plan",
        ),
        VerifyPhase(
            name="audit-security",
            command="make lint-prod",
            failing_component="security",
            likely_root_cause="Security audit gate failed",
            recommended_rerun_command="make lint-prod",
        ),
    ],
    "pre-deploy": [
        VerifyPhase(
            name="pre-deploy",
            command="make pre-deploy",
            failing_component="quality",
            likely_root_cause="Deployment readiness checks failed",
            recommended_rerun_command="make pre-deploy",
        )
    ],
}


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _path_from_env(candidates: Sequence[str], default: Path) -> Path:
    for candidate in candidates:
        raw = os.environ.get(candidate)
        if raw:
            return Path(raw)
    return default


def _runs_path() -> Path:
    return _path_from_env(
        [
            "AGENT_RUNS_FILE",
            "AGENT_RUNS_PATH",
            "OB_AGENT_RUNS_FILE",
            "OB_AGENT_RUNS_PATH",
            "ICS_AGENT_RUNS_FILE",
            "ICS_AGENT_RUNS_PATH",
        ],
        DEFAULT_RUNS_FILE,
    )


def _memory_path() -> Path:
    return _path_from_env(
        [
            "AGENT_MEMORY_FILE",
            "AGENT_MEMORY_PATH",
            "OB_AGENT_MEMORY_FILE",
            "OB_AGENT_MEMORY_PATH",
            "ICS_AGENT_MEMORY_FILE",
            "ICS_AGENT_MEMORY_PATH",
        ],
        DEFAULT_MEMORY_FILE,
    )


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True))
            handle.write("\n")


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True))
        handle.write("\n")


def _dedupe_hash(category: str, title: str, details: str, fingerprint: str) -> str:
    payload = "|".join(
        [category.lower(), title.lower(), details.lower(), fingerprint.lower()]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _default_fingerprint(title: str, details: str, category: str) -> str:
    digest = hashlib.sha256(f"{category}|{title}|{details}".encode()).hexdigest()
    return digest[:20]


def _add_memory_entry(
    *,
    title: str,
    details: str,
    category: str,
    source: str,
    evidence: str | None = None,
    fingerprint: str | None = None,
    resolved: bool = False,
    metadata: dict[str, Any] | None = None,
) -> tuple[bool, dict[str, Any]]:
    path = _memory_path()
    records = _load_jsonl(path)

    fp = fingerprint or _default_fingerprint(title, details, category)
    dedupe = _dedupe_hash(category, title, details, fp)

    for record in reversed(records):
        if record.get("category") == category and record.get("fingerprint") == fp:
            return (False, record)
        if record.get("dedupe_hash") == dedupe:
            return (False, record)

    payload: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "timestamp": _utc_now(),
        "title": title,
        "details": details,
        "category": category,
        "source": source,
        "fingerprint": fp,
        "dedupe_hash": dedupe,
        "resolved": resolved,
    }
    if evidence:
        payload["evidence"] = evidence
    if metadata:
        payload["metadata"] = metadata

    _append_jsonl(path, payload)
    return (True, payload)


def _record_run(
    *,
    command: str,
    status: str,
    details: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "timestamp": _utc_now(),
        "command": command,
        "status": status,
        "details": details,
    }
    if context:
        payload["context"] = context
    _append_jsonl(_runs_path(), payload)


def _git(cwd: Path, args: Sequence[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def _repo_root(cwd: Path) -> Path:
    root = _git(cwd, ["rev-parse", "--show-toplevel"])
    return Path(root) if root else cwd


def _git_context(cwd: Path) -> dict[str, Any]:
    root = _repo_root(cwd)

    base_sha = os.environ.get("AGENT_BASE_SHA") or _git(
        root, ["merge-base", "HEAD", "@{upstream}"]
    )
    head_sha = os.environ.get("AGENT_HEAD_SHA") or _git(root, ["rev-parse", "HEAD"])

    changed_files_env = os.environ.get("AGENT_CHANGED_FILES", "").strip()
    if changed_files_env:
        changed_files = [item for item in changed_files_env.split(",") if item]
    elif base_sha and head_sha:
        raw = _git(root, ["diff", "--name-only", f"{base_sha}..{head_sha}"])
        changed_files = [line for line in raw.splitlines() if line.strip()]
    else:
        raw = _git(root, ["diff", "--name-only"])
        changed_files = [line for line in raw.splitlines() if line.strip()]

    diff_hash = os.environ.get("AGENT_DIFF_HASH", "")
    if not diff_hash:
        if base_sha and head_sha:
            diff_blob = _git(root, ["diff", f"{base_sha}..{head_sha}"])
        else:
            diff_blob = _git(root, ["diff"])
        if diff_blob:
            diff_hash = hashlib.sha256(diff_blob.encode("utf-8")).hexdigest()[:24]

    return {
        "changed_files": changed_files,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "diff_hash": diff_hash,
    }


def _failure_signature(mode: str, phase: VerifyPhase) -> str:
    payload = (
        f"verify|{mode}|{phase.name}|{phase.failing_component}|"
        f"{phase.likely_root_cause.lower()}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def _unresolved_failures(records: list[dict[str, Any]]) -> set[str]:
    state: dict[str, str] = {}
    for record in records:
        fingerprint = record.get("fingerprint")
        if not isinstance(fingerprint, str):
            continue
        category = record.get("category")
        if category == "verify_failure":
            state[fingerprint] = "failed"
        elif category == "verify_resolution":
            state[fingerprint] = "resolved"
    return {fingerprint for fingerprint, value in state.items() if value == "failed"}


def _mark_failure_records_resolved(fingerprint: str) -> None:
    path = _memory_path()
    records = _load_jsonl(path)
    changed = False
    for record in records:
        if record.get("category") != "verify_failure":
            continue
        if record.get("fingerprint") != fingerprint:
            continue
        if bool(record.get("resolved", False)):
            continue
        record["resolved"] = True
        changed = True
    if changed:
        _write_jsonl(path, records)


def _find_memory_hints(
    records: list[dict[str, Any]],
    *,
    fingerprint: str,
    failing_component: str,
    limit: int = 3,
) -> list[dict[str, Any]]:
    scored: list[tuple[int, dict[str, Any]]] = []
    token = failing_component.lower()
    for record in records:
        title = str(record.get("title", ""))
        details = str(record.get("details", ""))
        haystack = f"{title} {details}".lower()
        score = 0
        if record.get("fingerprint") == fingerprint:
            score += 5
        if token and token in haystack:
            score += 2
        if record.get("category") == "verify_failure":
            score += 1
        if score > 0:
            scored.append((score, record))
    scored.sort(key=lambda item: (item[0], item[1].get("timestamp", "")), reverse=True)
    return [record for _, record in scored[:limit]]


def _execute_command(command: str, *, dry_run: bool) -> tuple[int, str, str]:
    if dry_run:
        return (0, f"[dry-run] {command}", "")
    proc = subprocess.run(
        command,
        shell=True,
        text=True,
        capture_output=True,
        check=False,
    )
    return (proc.returncode, proc.stdout, proc.stderr)


def _command_memory_add(args: argparse.Namespace) -> int:
    context = _git_context(Path.cwd())
    added, record = _add_memory_entry(
        title=args.title,
        details=args.details,
        category=args.category,
        source=args.source,
        evidence=args.evidence,
        fingerprint=args.fingerprint,
        metadata={"context": context},
    )
    print(
        json.dumps(
            {"status": "added" if added else "deduped", "entry": record}, sort_keys=True
        )
    )
    _record_run(
        command="memory-add",
        status="success",
        details={"added": added, "category": record.get("category")},
        context=context,
    )
    return 0


def _command_memory_list(args: argparse.Namespace) -> int:
    records = _load_jsonl(_memory_path())
    if args.category:
        records = [
            record for record in records if record.get("category") == args.category
        ]
    if args.limit is not None:
        records = records[-args.limit :]

    for record in records:
        print(json.dumps(record, sort_keys=True))

    _record_run(
        command="memory-list",
        status="success",
        details={"count": len(records), "limit": args.limit, "category": args.category},
    )
    return 0


def _command_memory_report(args: argparse.Namespace) -> int:
    records = _load_jsonl(_memory_path())
    by_category: dict[str, int] = {}
    by_fingerprint: dict[str, int] = {}

    for record in records:
        category = str(record.get("category", "unknown"))
        fingerprint = str(record.get("fingerprint", ""))
        by_category[category] = by_category.get(category, 0) + 1
        if fingerprint:
            by_fingerprint[fingerprint] = by_fingerprint.get(fingerprint, 0) + 1

    top_categories = sorted(
        by_category.items(), key=lambda item: item[1], reverse=True
    )[: args.top]
    top_fingerprints = sorted(
        by_fingerprint.items(), key=lambda item: item[1], reverse=True
    )[: args.top]

    payload = {
        "totalEntries": len(records),
        "topCategories": [
            {"category": key, "count": value} for key, value in top_categories
        ],
        "topFingerprints": [
            {"fingerprint": key, "count": value} for key, value in top_fingerprints
        ],
    }
    print(json.dumps(payload, sort_keys=True))
    _record_run(
        command="memory-report", status="success", details={"top": args.top, **payload}
    )
    return 0


def _command_memory_compact(args: argparse.Namespace) -> int:
    keep_last = max(args.keep_last, 0)
    before = _load_jsonl(_memory_path())
    after = before[-keep_last:] if keep_last else []
    removed = max(len(before) - len(after), 0)

    payload = {"before": len(before), "after": len(after), "removed": removed}
    if args.dry_run:
        print(json.dumps({"status": "dry-run", **payload}, sort_keys=True))
    else:
        _write_jsonl(_memory_path(), after)
        print(json.dumps({"status": "compacted", **payload}, sort_keys=True))

    _record_run(
        command="memory-compact",
        status="success",
        details={"dry_run": bool(args.dry_run), **payload},
    )
    return 0


def _command_verify(args: argparse.Namespace) -> int:
    phases = VERIFY_PHASES_BY_MODE.get(args.mode)
    if not phases:
        print(f"No verify phases configured for mode '{args.mode}'.", file=sys.stderr)
        return 1

    context = _git_context(Path.cwd())
    existing_memory = _load_jsonl(_memory_path())
    unresolved = _unresolved_failures(existing_memory)

    triage_records: list[dict[str, str]] = []
    phase_results: list[dict[str, Any]] = []
    status = "success"

    for phase in phases:
        signature = _failure_signature(args.mode, phase)
        code, stdout, stderr = _execute_command(phase.command, dry_run=args.dry_run)

        phase_result: dict[str, Any] = {
            "phase": phase.name,
            "command": phase.command,
            "component": phase.failing_component,
            "exit_code": code,
        }
        if stdout.strip():
            phase_result["stdout"] = stdout.strip()[:3000]
        if stderr.strip():
            phase_result["stderr"] = stderr.strip()[:3000]
        phase_results.append(phase_result)

        if stdout.strip():
            print(stdout.strip())
        if stderr.strip():
            print(stderr.strip(), file=sys.stderr)

        if code != 0:
            status = "failed"
            triage = {
                "phase": phase.name,
                "failingComponent": phase.failing_component,
                "likelyRootCause": phase.likely_root_cause,
                "recommendedRerunCommand": phase.recommended_rerun_command,
            }
            triage_records.append(triage)
            print(f"TRIAGE_JSON: {json.dumps(triage, sort_keys=True)}")

            hints = _find_memory_hints(
                existing_memory,
                fingerprint=signature,
                failing_component=phase.failing_component,
            )
            if hints:
                print("Memory Hints")
                for hint in hints:
                    print(f"- {hint.get('title', '(untitled)')}")

            _add_memory_entry(
                title=f"Verify failure: {phase.name}",
                details=f"{phase.likely_root_cause}. Command: {phase.command}",
                category="verify_failure",
                source="runner.verify",
                evidence=stderr.strip() or stdout.strip() or None,
                fingerprint=signature,
                resolved=False,
                metadata={"triage": triage, "context": context},
            )

            if args.fail_fast:
                break
        else:
            if signature in unresolved:
                _mark_failure_records_resolved(signature)
                _add_memory_entry(
                    title=f"Verify resolution: {phase.name}",
                    details=f"Previously failing signature for '{phase.name}' now passes.",
                    category="verify_resolution",
                    source="runner.verify",
                    evidence=phase.command,
                    fingerprint=signature,
                    resolved=True,
                    metadata={"context": context},
                )

    _record_run(
        command="verify",
        status=status,
        details={
            "mode": args.mode,
            "fail_fast": bool(args.fail_fast),
            "dry_run": bool(args.dry_run),
            "phase_results": phase_results,
            "triage": triage_records,
        },
        context=context,
    )

    return 0 if status == "success" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agent verify and memory runner")
    sub = parser.add_subparsers(dest="command", required=True)

    verify = sub.add_parser("verify", help="Run configured verify phases")
    verify.add_argument(
        "--mode", required=True, choices=sorted(VERIFY_PHASES_BY_MODE.keys())
    )
    verify.add_argument("--fail-fast", action="store_true")
    verify.add_argument("--dry-run", action="store_true")
    verify.set_defaults(handler=_command_verify)

    memory_add = sub.add_parser("memory-add", help="Add a memory entry")
    memory_add.add_argument("--title", required=True)
    memory_add.add_argument("--details", required=True)
    memory_add.add_argument("--category", default="general")
    memory_add.add_argument("--source", default="manual")
    memory_add.add_argument("--evidence")
    memory_add.add_argument("--fingerprint")
    memory_add.set_defaults(handler=_command_memory_add)

    memory_list = sub.add_parser("memory-list", help="List memory entries")
    memory_list.add_argument("--limit", type=int, default=25)
    memory_list.add_argument("--category")
    memory_list.set_defaults(handler=_command_memory_list)

    memory_report = sub.add_parser("memory-report", help="Report memory categories")
    memory_report.add_argument("--top", type=int, default=10)
    memory_report.set_defaults(handler=_command_memory_report)

    memory_compact = sub.add_parser("memory-compact", help="Keep only recent entries")
    memory_compact.add_argument("--keep-last", type=int, default=200)
    memory_compact.add_argument("--dry-run", action="store_true")
    memory_compact.set_defaults(handler=_command_memory_compact)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
