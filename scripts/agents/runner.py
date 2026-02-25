#!/usr/bin/env python3
"""Canonical runner for verification and agent memory operations."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import uuid
from collections import Counter
from collections.abc import Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

try:  # pragma: no cover - not available on some platforms
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None


SCHEMA_VERSION = 2
DEFAULT_RUNS_FILE = Path("metrics/agent_runs.jsonl")
DEFAULT_MEMORY_FILE = Path("metrics/agent_memory.jsonl")
CORRUPT_SUFFIX = ".corrupt"

EMBEDDING_DIM = 96
SEMANTIC_MIN_SIMILARITY = 0.18
BASE_HINT_THRESHOLD = 0.32

HALF_LIFE_DAYS = 30.0
DEFAULT_TTL_DAYS = {
    "verify_failure": 45,
    "verify_resolution": 180,
    "general": 120,
}
DEFAULT_IMPACT = {
    "verify_failure": 1.0,
    "verify_resolution": 0.8,
    "backend": 0.8,
    "frontend": 0.8,
    "security": 1.3,
    "deps": 1.1,
    "quality": 1.0,
}

TOKEN_RE = re.compile(r"[a-z0-9]+")


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


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def _to_iso(dt: datetime) -> str:
    return dt.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def _coerce_float(
    value: Any, default: float, *, min_value: float, max_value: float
) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(min(number, max_value), min_value)


def _coerce_int(value: Any, default: int, *, min_value: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(number, min_value)


def _default_ttl_days(category: str) -> int:
    return DEFAULT_TTL_DAYS.get(category, DEFAULT_TTL_DAYS["general"])


def _default_impact(category: str) -> float:
    return DEFAULT_IMPACT.get(category, 0.8)


def _initial_confidence(source: str, evidence: str | None) -> float:
    baseline = 0.6
    lowered = source.lower()
    if lowered.startswith("runner.verify"):
        baseline = 0.7
    elif lowered == "manual":
        baseline = 0.8
    if evidence:
        baseline += 0.05
    return _coerce_float(baseline, 0.7, min_value=0.05, max_value=0.99)


def _tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def _hash_embedding(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    tokens = _tokenize(text)
    if not tokens:
        return [0.0] * dim

    vector = [0.0] * dim
    for index, token in enumerate(tokens):
        ngrams = [token]
        if index > 0:
            ngrams.append(f"{tokens[index - 1]}_{token}")
        if index + 1 < len(tokens):
            ngrams.append(f"{token}_{tokens[index + 1]}")

        for gram in ngrams:
            digest = hashlib.sha256(gram.encode()).digest()
            bucket = int.from_bytes(digest[:4], "big") % dim
            sign = 1.0 if digest[4] % 2 else -1.0
            magnitude = 1.0 + min(len(gram), 12) / 24.0
            vector[bucket] += sign * magnitude

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return [0.0] * dim
    return [round(value / norm, 6) for value in vector]


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    left_slice = left[:size]
    right_slice = right[:size]
    dot = sum(
        float(a) * float(b) for a, b in zip(left_slice, right_slice, strict=False)
    )
    left_norm = math.sqrt(sum(float(a) * float(a) for a in left_slice))
    right_norm = math.sqrt(sum(float(b) * float(b) for b in right_slice))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def _memory_embedding(record: dict[str, Any]) -> list[float]:
    embedding = record.get("embedding")
    if isinstance(embedding, list) and embedding:
        try:
            return [float(value) for value in embedding]
        except (TypeError, ValueError):
            pass
    text = f"{record.get('title', '')}\n{record.get('details', '')}"
    return _hash_embedding(text)


def _normalize_memory_record(record: dict[str, Any], now: datetime) -> dict[str, Any]:
    normalized = dict(record)
    normalized.setdefault("id", str(uuid.uuid4()))
    timestamp = _parse_timestamp(str(normalized.get("timestamp", ""))) or now
    normalized["timestamp"] = _to_iso(timestamp)

    category = str(normalized.get("category", "general"))
    normalized["category"] = category
    normalized.setdefault("title", "(untitled)")
    normalized.setdefault("details", "")
    normalized.setdefault("source", "unknown")

    resolved = bool(normalized.get("resolved", False))
    normalized["resolved"] = resolved

    status = str(normalized.get("status", "")).strip().lower()
    if not status:
        status = "resolved" if resolved else "active"
    normalized["status"] = status

    normalized["schemaVersion"] = _coerce_int(
        normalized.get("schemaVersion", SCHEMA_VERSION),
        SCHEMA_VERSION,
        min_value=1,
    )
    normalized["confidence"] = _coerce_float(
        normalized.get(
            "confidence",
            _initial_confidence(normalized["source"], normalized.get("evidence")),
        ),
        0.7,
        min_value=0.01,
        max_value=0.99,
    )
    normalized["impactScore"] = _coerce_float(
        normalized.get("impactScore", _default_impact(category)),
        _default_impact(category),
        min_value=0.1,
        max_value=3.0,
    )
    normalized["occurrenceCount"] = _coerce_int(
        normalized.get("occurrenceCount", 1),
        1,
        min_value=1,
    )
    normalized["hintShownCount"] = _coerce_int(
        normalized.get("hintShownCount", 0),
        0,
        min_value=0,
    )
    normalized["hintUsefulCount"] = _coerce_int(
        normalized.get("hintUsefulCount", 0),
        0,
        min_value=0,
    )
    normalized["usefulnessScore"] = _coerce_float(
        normalized.get("usefulnessScore", 0.5),
        0.5,
        min_value=0.0,
        max_value=1.0,
    )

    fingerprint = str(normalized.get("fingerprint", "")).strip()
    if not fingerprint:
        fingerprint = _default_fingerprint(
            str(normalized.get("title", "")),
            str(normalized.get("details", "")),
            category,
        )
    normalized["fingerprint"] = fingerprint
    normalized["dedupe_hash"] = str(
        normalized.get(
            "dedupe_hash",
            _dedupe_hash(
                category,
                str(normalized.get("title", "")),
                str(normalized.get("details", "")),
                fingerprint,
            ),
        )
    )

    expires_at_raw = str(normalized.get("expiresAt", "")).strip()
    expires_at = _parse_timestamp(expires_at_raw)
    if expires_at is None:
        ttl_days = _coerce_int(
            normalized.get("ttlDays", _default_ttl_days(category)),
            _default_ttl_days(category),
            min_value=1,
        )
        expires_at = timestamp + timedelta(days=ttl_days)
    normalized["expiresAt"] = _to_iso(expires_at)

    normalized.setdefault("metadata", {})
    if not isinstance(normalized["metadata"], dict):
        normalized["metadata"] = {"legacyMetadata": normalized["metadata"]}

    normalized["embedding"] = _memory_embedding(normalized)
    return normalized


def _normalize_run_record(record: dict[str, Any], now: datetime) -> dict[str, Any]:
    normalized = dict(record)
    normalized.setdefault("id", str(uuid.uuid4()))
    timestamp = _parse_timestamp(str(normalized.get("timestamp", ""))) or now
    normalized["timestamp"] = _to_iso(timestamp)
    normalized["schemaVersion"] = _coerce_int(
        normalized.get("schemaVersion", SCHEMA_VERSION),
        SCHEMA_VERSION,
        min_value=1,
    )
    if "details" not in normalized or not isinstance(normalized.get("details"), dict):
        normalized["details"] = {}
    return normalized


def _corrupt_path(path: Path) -> Path:
    return path.with_name(path.name + CORRUPT_SUFFIX)


def _append_corrupt_line(path: Path, line_number: int, line: str) -> None:
    target = _corrupt_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": _utc_now(),
        "source": str(path),
        "line": line_number,
        "content": line,
    }
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True))
        handle.write("\n")


@contextmanager
def _file_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        if fcntl is not None:  # pragma: no branch - platform dependent
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:  # pragma: no branch
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _load_jsonl(
    path: Path,
    *,
    kind: str,
    with_stats: bool = False,
) -> list[dict[str, Any]] | tuple[list[dict[str, Any]], dict[str, int]]:
    if not path.exists():
        result: list[dict[str, Any]] = []
        if with_stats:
            return result, {"corruptLines": 0}
        return result

    records: list[dict[str, Any]] = []
    corrupt = 0
    now = datetime.now(UTC)
    for line_number, raw in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            corrupt += 1
            _append_corrupt_line(path, line_number, raw)
            continue
        if not isinstance(payload, dict):
            corrupt += 1
            _append_corrupt_line(path, line_number, raw)
            continue

        if kind == "memory":
            records.append(_normalize_memory_record(payload, now))
        elif kind == "runs":
            records.append(_normalize_run_record(payload, now))
        else:
            records.append(payload)

    if with_stats:
        return records, {"corruptLines": corrupt}
    return records


def _atomic_write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        delete=False,
        dir=str(path.parent),
        encoding="utf-8",
        prefix=f"{path.name}.",
        suffix=".tmp",
    ) as tmp:
        for record in records:
            tmp.write(json.dumps(record, sort_keys=True))
            tmp.write("\n")
    Path(tmp.name).replace(path)


def _append_jsonl(path: Path, record: dict[str, Any], *, kind: str) -> None:
    lock = path.with_name(path.name + ".lock")
    with _file_lock(lock):
        record_payload = record
        if kind == "memory":
            record_payload = _normalize_memory_record(record_payload, datetime.now(UTC))
        elif kind == "runs":
            record_payload = _normalize_run_record(record_payload, datetime.now(UTC))
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record_payload, sort_keys=True))
            handle.write("\n")


def _dedupe_hash(category: str, title: str, details: str, fingerprint: str) -> str:
    payload = "|".join(
        [category.lower(), title.lower(), details.lower(), fingerprint.lower()]
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def _default_fingerprint(title: str, details: str, category: str) -> str:
    digest = hashlib.sha256(f"{category}|{title}|{details}".encode()).hexdigest()
    return digest[:20]


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
        "schemaVersion": SCHEMA_VERSION,
        "command": command,
        "status": status,
        "details": details,
    }
    if context:
        payload["context"] = context
    _append_jsonl(_runs_path(), payload, kind="runs")


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
            diff_hash = hashlib.sha256(diff_blob.encode()).hexdigest()[:24]

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
    return hashlib.sha256(payload.encode()).hexdigest()[:20]


def _decayed_confidence(record: dict[str, Any], now: datetime) -> float:
    baseline = _coerce_float(
        record.get("confidence", 0.6), 0.6, min_value=0.01, max_value=0.99
    )
    timestamp = _parse_timestamp(str(record.get("timestamp", ""))) or now
    half_life = _coerce_float(
        os.environ.get("AGENT_MEMORY_HALF_LIFE_DAYS", HALF_LIFE_DAYS),
        HALF_LIFE_DAYS,
        min_value=1.0,
        max_value=365.0,
    )
    age_days = max((now - timestamp).total_seconds() / 86400.0, 0.0)
    return baseline * (0.5 ** (age_days / half_life))


def _is_expired(record: dict[str, Any], now: datetime) -> bool:
    expires = _parse_timestamp(str(record.get("expiresAt", "")))
    return bool(expires and expires <= now)


def _hint_usefulness(record: dict[str, Any]) -> float:
    shown = _coerce_int(record.get("hintShownCount", 0), 0, min_value=0)
    useful = _coerce_int(record.get("hintUsefulCount", 0), 0, min_value=0)
    if shown == 0:
        return _coerce_float(
            record.get("usefulnessScore", 0.5), 0.5, min_value=0.0, max_value=1.0
        )
    return _coerce_float(useful / shown, 0.0, min_value=0.0, max_value=1.0)


def _dynamic_hint_threshold(runs_records: list[dict[str, Any]]) -> float:
    base = _coerce_float(
        os.environ.get("AGENT_HINT_THRESHOLD", BASE_HINT_THRESHOLD),
        BASE_HINT_THRESHOLD,
        min_value=0.05,
        max_value=0.95,
    )

    impressions = 0
    useful = 0
    for record in runs_records:
        details = record.get("details")
        if not isinstance(details, dict):
            continue
        hint_stats = details.get("hintStats")
        if not isinstance(hint_stats, dict):
            continue
        impressions += _coerce_int(hint_stats.get("shown", 0), 0, min_value=0)
        useful += _coerce_int(hint_stats.get("useful", 0), 0, min_value=0)

    if impressions < 8:
        return base

    precision = useful / impressions if impressions else 0.0
    if precision < 0.2:
        return min(0.9, base + 0.05)
    if precision > 0.55:
        return max(0.1, base - 0.05)
    return base


def _find_memory_hints(
    records: list[dict[str, Any]],
    *,
    fingerprint: str,
    failing_component: str,
    query_text: str,
    runs_records: list[dict[str, Any]] | None = None,
    limit: int = 3,
) -> list[dict[str, Any]]:
    if not records:
        return []

    now = datetime.now(UTC)
    runs = runs_records or []
    threshold = _dynamic_hint_threshold(runs)
    query_embedding = _hash_embedding(f"{failing_component} {query_text}")

    scored: list[tuple[float, dict[str, Any]]] = []
    component_token = failing_component.lower().strip()

    for record in records:
        if _is_expired(record, now):
            continue

        title = str(record.get("title", ""))
        details = str(record.get("details", ""))
        haystack = f"{title} {details}".lower()

        exact_fingerprint = record.get("fingerprint") == fingerprint
        component_match = bool(component_token and component_token in haystack)

        similarity = _cosine_similarity(query_embedding, _memory_embedding(record))
        if exact_fingerprint:
            similarity = max(similarity, 0.97)

        if (
            not exact_fingerprint
            and not component_match
            and similarity < SEMANTIC_MIN_SIMILARITY
        ):
            continue

        timestamp = _parse_timestamp(str(record.get("timestamp", ""))) or now
        age_days = max((now - timestamp).total_seconds() / 86400.0, 0.0)
        recency_weight = math.exp(-age_days / 21.0)

        confidence = _decayed_confidence(record, now)
        impact = _coerce_float(
            record.get("impactScore", 1.0), 1.0, min_value=0.1, max_value=3.0
        )
        impact_weight = min(impact / 3.0, 1.0)
        usefulness = _hint_usefulness(record)

        score = (
            similarity * 0.52
            + recency_weight * 0.15
            + confidence * 0.14
            + usefulness * 0.1
            + impact_weight * 0.09
            + (0.08 if component_match else 0.0)
        )

        status = str(record.get("status", "active"))
        if status in {"superseded", "stale"}:
            score -= 0.2

        if not exact_fingerprint and score < threshold:
            continue

        annotated = dict(record)
        annotated["hintScore"] = round(score, 6)
        annotated["semanticSimilarity"] = round(similarity, 6)
        scored.append((score, annotated))

    scored.sort(key=lambda item: item[0], reverse=True)
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


def _upsert_memory_record(
    records: list[dict[str, Any]],
    *,
    title: str,
    details: str,
    category: str,
    source: str,
    evidence: str | None,
    fingerprint: str,
    resolved: bool,
    metadata: dict[str, Any],
) -> tuple[bool, dict[str, Any]]:
    now = datetime.now(UTC)
    dedupe = _dedupe_hash(category, title, details, fingerprint)

    for index in range(len(records) - 1, -1, -1):
        candidate = records[index]
        same_category = candidate.get("category") == category
        same_fingerprint = candidate.get("fingerprint") == fingerprint
        same_dedupe = candidate.get("dedupe_hash") == dedupe
        if not (same_dedupe or (same_category and same_fingerprint)):
            continue

        candidate["occurrenceCount"] = (
            _coerce_int(
                candidate.get("occurrenceCount", 1),
                1,
                min_value=1,
            )
            + 1
        )
        candidate["lastSeenAt"] = _to_iso(now)
        candidate["details"] = details
        candidate["metadata"] = metadata
        if evidence:
            candidate["evidence"] = evidence
        candidate["confidence"] = _coerce_float(
            candidate.get("confidence", 0.7) + 0.02,
            0.7,
            min_value=0.01,
            max_value=0.99,
        )
        candidate["resolved"] = bool(resolved)
        candidate["status"] = "resolved" if resolved else "active"
        candidate["embedding"] = _hash_embedding(f"{title}\n{details}")
        records[index] = _normalize_memory_record(candidate, now)
        return (False, records[index])

    payload: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "schemaVersion": SCHEMA_VERSION,
        "timestamp": _to_iso(now),
        "title": title,
        "details": details,
        "category": category,
        "source": source,
        "fingerprint": fingerprint,
        "dedupe_hash": dedupe,
        "resolved": bool(resolved),
        "status": "resolved" if resolved else "active",
        "confidence": _initial_confidence(source, evidence),
        "impactScore": _default_impact(category),
        "occurrenceCount": 1,
        "hintShownCount": 0,
        "hintUsefulCount": 0,
        "usefulnessScore": 0.5,
        "expiresAt": _to_iso(now + timedelta(days=_default_ttl_days(category))),
        "metadata": metadata,
        "embedding": _hash_embedding(f"{title}\n{details}"),
    }
    if evidence:
        payload["evidence"] = evidence

    normalized = _normalize_memory_record(payload, now)
    records.append(normalized)
    return (True, normalized)


def _apply_conflict_resolution(
    records: list[dict[str, Any]], *, fingerprint: str, category: str
) -> None:
    now_iso = _utc_now()
    if category == "verify_resolution":
        for record in records:
            if record.get("fingerprint") != fingerprint:
                continue
            if record.get("category") != "verify_failure":
                continue
            if bool(record.get("resolved", False)):
                continue
            record["resolved"] = True
            record["status"] = "resolved"
            record["resolvedAt"] = now_iso
    elif category == "verify_failure":
        for record in records:
            if record.get("fingerprint") != fingerprint:
                continue
            if record.get("category") != "verify_resolution":
                continue
            if record.get("status") == "superseded":
                continue
            record["status"] = "superseded"
            record["supersededAt"] = now_iso


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
    lock = path.with_name(path.name + ".lock")
    with _file_lock(lock):
        records = _load_jsonl(path, kind="memory")
        fp = fingerprint or _default_fingerprint(title, details, category)
        added, record = _upsert_memory_record(
            records,
            title=title,
            details=details,
            category=category,
            source=source,
            evidence=evidence,
            fingerprint=fp,
            resolved=resolved,
            metadata=metadata or {},
        )
        _apply_conflict_resolution(records, fingerprint=fp, category=category)
        _atomic_write_jsonl(path, records)
        return (added, record)


def _increment_hint_counters(
    hint_ids: Sequence[str],
    *,
    shown_delta: int = 0,
    useful_delta: int = 0,
) -> None:
    if not hint_ids:
        return

    path = _memory_path()
    lock = path.with_name(path.name + ".lock")
    id_set = set(hint_ids)
    with _file_lock(lock):
        records = _load_jsonl(path, kind="memory")
        changed = False
        for record in records:
            if str(record.get("id")) not in id_set:
                continue
            shown = _coerce_int(record.get("hintShownCount", 0), 0, min_value=0)
            useful = _coerce_int(record.get("hintUsefulCount", 0), 0, min_value=0)
            shown += shown_delta
            useful += useful_delta
            useful = min(useful, shown)
            record["hintShownCount"] = shown
            record["hintUsefulCount"] = useful
            if shown:
                record["usefulnessScore"] = round(useful / shown, 6)
            changed = True
        if changed:
            _atomic_write_jsonl(path, records)


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


def _phase_failure_history(
    runs_records: list[dict[str, Any]], signature: str
) -> tuple[list[str], datetime | None]:
    hint_ids: list[str] = []
    latest_failure_ts: datetime | None = None
    for run in runs_records:
        if run.get("command") != "verify":
            continue
        details = run.get("details")
        if not isinstance(details, dict):
            continue
        phase_results = details.get("phase_results")
        if not isinstance(phase_results, list):
            continue
        for phase_result in phase_results:
            if not isinstance(phase_result, dict):
                continue
            if str(phase_result.get("signature", "")) != signature:
                continue
            if _coerce_int(phase_result.get("exit_code", 0), 0, min_value=0) == 0:
                continue
            hint_ids.extend(
                str(value) for value in phase_result.get("hint_ids", []) if value
            )
            ts = _parse_timestamp(str(run.get("timestamp", "")))
            if ts and (latest_failure_ts is None or ts > latest_failure_ts):
                latest_failure_ts = ts
    return hint_ids, latest_failure_ts


def _build_cluster_key(record: dict[str, Any]) -> str:
    metadata = record.get("metadata")
    triage = metadata.get("triage") if isinstance(metadata, dict) else None
    root = ""
    component = str(record.get("category", "unknown"))
    if isinstance(triage, dict):
        root = str(triage.get("likelyRootCause", ""))
        component = str(triage.get("failingComponent", component))
    if not root:
        root = str(record.get("details", ""))
    tokens = _tokenize(root)[:8]
    canonical = " ".join(tokens)
    digest = hashlib.sha256(f"{component}|{canonical}".encode()).hexdigest()[:12]
    return f"{component}:{digest}"


def _clusters_from_memory(
    records: list[dict[str, Any]], top: int
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if record.get("category") != "verify_failure":
            continue
        key = _build_cluster_key(record)
        grouped.setdefault(key, []).append(record)

    clusters: list[dict[str, Any]] = []
    for key, group in grouped.items():
        remediation = Counter()
        root_causes = Counter()
        component = "quality"
        for item in group:
            metadata = item.get("metadata")
            triage = metadata.get("triage") if isinstance(metadata, dict) else None
            if isinstance(triage, dict):
                component = str(triage.get("failingComponent", component))
                remediation[str(triage.get("recommendedRerunCommand", ""))] += 1
                root_causes[str(triage.get("likelyRootCause", "unknown"))] += 1
            else:
                root_causes[str(item.get("details", "unknown"))] += 1

        top_root, _ = root_causes.most_common(1)[0] if root_causes else ("unknown", 0)
        top_fix, _ = (
            remediation.most_common(1)[0]
            if remediation
            else ("inspect failing command", 0)
        )
        clusters.append(
            {
                "clusterId": key,
                "failingComponent": component,
                "occurrences": len(group),
                "likelyRootCause": top_root,
                "recommendedRemediation": top_fix,
            }
        )

    clusters.sort(key=lambda item: item["occurrences"], reverse=True)
    return clusters[:top]


def _trend_analysis(records: list[dict[str, Any]], top: int) -> dict[str, Any]:
    root_cause_counter: Counter[str] = Counter()
    fingerprint_flow: dict[str, set[str]] = {}

    for record in records:
        metadata = record.get("metadata")
        triage = metadata.get("triage") if isinstance(metadata, dict) else None
        if isinstance(triage, dict):
            root_cause_counter[str(triage.get("likelyRootCause", "unknown"))] += 1
        elif record.get("category") == "verify_failure":
            root_cause_counter[str(record.get("details", "unknown"))] += 1

        fp = str(record.get("fingerprint", ""))
        if not fp:
            continue
        fingerprint_flow.setdefault(fp, set()).add(str(record.get("category", "")))

    flapping = [
        fingerprint
        for fingerprint, categories in fingerprint_flow.items()
        if "verify_failure" in categories and "verify_resolution" in categories
    ]

    return {
        "topRootCauses": [
            {"rootCause": cause, "count": count}
            for cause, count in root_cause_counter.most_common(top)
        ],
        "flappingFingerprints": flapping[:top],
    }


def _hint_effectiveness(
    records: list[dict[str, Any]], runs_records: list[dict[str, Any]]
) -> dict[str, Any]:
    shown = 0
    useful = 0
    for record in records:
        shown += _coerce_int(record.get("hintShownCount", 0), 0, min_value=0)
        useful += _coerce_int(record.get("hintUsefulCount", 0), 0, min_value=0)

    precision = useful / shown if shown else 0.0

    resolution_seconds: list[float] = []
    assisted_resolutions = 0
    for record in records:
        if record.get("category") != "verify_resolution":
            continue
        metadata = record.get("metadata")
        if not isinstance(metadata, dict):
            continue
        if bool(metadata.get("hintAssisted", False)):
            assisted_resolutions += 1
        seconds = metadata.get("timeToResolutionSeconds")
        if isinstance(seconds, int | float) and seconds >= 0:
            resolution_seconds.append(float(seconds))

    runs_hint_stats = {
        "shown": 0,
        "useful": 0,
    }
    for run in runs_records:
        details = run.get("details")
        if not isinstance(details, dict):
            continue
        hint_stats = details.get("hintStats")
        if not isinstance(hint_stats, dict):
            continue
        runs_hint_stats["shown"] += _coerce_int(
            hint_stats.get("shown", 0), 0, min_value=0
        )
        runs_hint_stats["useful"] += _coerce_int(
            hint_stats.get("useful", 0), 0, min_value=0
        )

    mean_resolution_seconds = (
        sum(resolution_seconds) / len(resolution_seconds)
        if resolution_seconds
        else None
    )

    return {
        "hintImpressions": shown,
        "hintUsefulOutcomes": useful,
        "hintPrecision": round(precision, 6),
        "assistedResolutions": assisted_resolutions,
        "meanTimeToResolutionSeconds": mean_resolution_seconds,
        "runHintStats": runs_hint_stats,
    }


def _build_remediation_suggestions(
    clusters: list[dict[str, Any]], top: int
) -> list[str]:
    suggestions: list[str] = []
    for cluster in clusters[:top]:
        component = cluster.get("failingComponent", "quality")
        remediation = cluster.get("recommendedRemediation", "inspect failing command")
        root = cluster.get("likelyRootCause", "unknown")
        suggestions.append(
            f"{component}: {root} -> rerun '{remediation}' and add targeted regression coverage"
        )
    return suggestions


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
    records, stats = _load_jsonl(_memory_path(), kind="memory", with_stats=True)
    assert isinstance(records, list)
    assert isinstance(stats, dict)

    if args.category:
        records = [
            record for record in records if record.get("category") == args.category
        ]

    if args.query:
        runs_records = _load_jsonl(_runs_path(), kind="runs")
        assert isinstance(runs_records, list)
        records = _find_memory_hints(
            records,
            fingerprint="",
            failing_component=args.component or "quality",
            query_text=args.query,
            runs_records=runs_records,
            limit=args.limit,
        )
    elif args.limit is not None:
        records = records[-args.limit :]

    for record in records:
        print(json.dumps(record, sort_keys=True))

    _record_run(
        command="memory-list",
        status="success",
        details={
            "count": len(records),
            "limit": args.limit,
            "category": args.category,
            "query": args.query,
            "corruptLines": stats.get("corruptLines", 0),
        },
    )
    return 0


def _command_memory_report(args: argparse.Namespace) -> int:
    memory_records, memory_stats = _load_jsonl(
        _memory_path(),
        kind="memory",
        with_stats=True,
    )
    runs_records, runs_stats = _load_jsonl(
        _runs_path(),
        kind="runs",
        with_stats=True,
    )
    assert isinstance(memory_records, list)
    assert isinstance(memory_stats, dict)
    assert isinstance(runs_records, list)
    assert isinstance(runs_stats, dict)

    by_category: dict[str, int] = {}
    by_fingerprint: dict[str, int] = {}
    status_counter: Counter[str] = Counter()

    now = datetime.now(UTC)
    expired = 0
    for record in memory_records:
        category = str(record.get("category", "unknown"))
        fingerprint = str(record.get("fingerprint", ""))
        by_category[category] = by_category.get(category, 0) + 1
        if fingerprint:
            by_fingerprint[fingerprint] = by_fingerprint.get(fingerprint, 0) + 1
        status_counter[str(record.get("status", "active"))] += 1
        if _is_expired(record, now):
            expired += 1

    top_categories = sorted(
        by_category.items(),
        key=lambda item: item[1],
        reverse=True,
    )[: args.top]
    top_fingerprints = sorted(
        by_fingerprint.items(),
        key=lambda item: item[1],
        reverse=True,
    )[: args.top]

    clusters = _clusters_from_memory(memory_records, args.top)
    trends = _trend_analysis(memory_records, args.top)
    hint_effectiveness = _hint_effectiveness(memory_records, runs_records)
    suggestions = _build_remediation_suggestions(clusters, args.top)

    payload = {
        "schemaVersion": SCHEMA_VERSION,
        "totalEntries": len(memory_records),
        "corruptLines": memory_stats.get("corruptLines", 0)
        + runs_stats.get("corruptLines", 0),
        "topCategories": [
            {"category": key, "count": value} for key, value in top_categories
        ],
        "topFingerprints": [
            {"fingerprint": key, "count": value} for key, value in top_fingerprints
        ],
        "clusters": clusters,
        "trends": trends,
        "remediationSuggestions": suggestions,
        "hintEffectiveness": hint_effectiveness,
        "dashboard": {
            "statusCounts": dict(status_counter),
            "expiredEntries": expired,
            "activeEntries": status_counter.get("active", 0),
            "resolvedEntries": status_counter.get("resolved", 0),
            "supersededEntries": status_counter.get("superseded", 0),
        },
    }
    print(json.dumps(payload, sort_keys=True))
    _record_run(
        command="memory-report",
        status="success",
        details={"top": args.top, **payload},
    )
    return 0


def _command_memory_compact(args: argparse.Namespace) -> int:
    keep_last = max(args.keep_last, 0)
    min_confidence = _coerce_float(
        args.min_confidence,
        0.1,
        min_value=0.0,
        max_value=1.0,
    )
    min_usefulness = _coerce_float(
        args.min_usefulness,
        0.0,
        min_value=0.0,
        max_value=1.0,
    )

    records = _load_jsonl(_memory_path(), kind="memory")
    assert isinstance(records, list)
    now = datetime.now(UTC)

    kept: list[dict[str, Any]] = []
    removed_reasons: Counter[str] = Counter()

    for record in records:
        if _is_expired(record, now):
            removed_reasons["expired"] += 1
            continue
        if _decayed_confidence(record, now) < min_confidence:
            removed_reasons["low_confidence"] += 1
            continue
        if (
            _hint_usefulness(record) < min_usefulness
            and _coerce_int(
                record.get("occurrenceCount", 1),
                1,
                min_value=1,
            )
            <= 1
        ):
            removed_reasons["low_usefulness"] += 1
            continue
        kept.append(record)

    if keep_last:
        kept = kept[-keep_last:]

    payload = {
        "before": len(records),
        "after": len(kept),
        "removed": max(len(records) - len(kept), 0),
        "removedByReason": dict(removed_reasons),
        "minConfidence": min_confidence,
        "minUsefulness": min_usefulness,
    }

    if args.dry_run:
        print(json.dumps({"status": "dry-run", **payload}, sort_keys=True))
    else:
        lock = _memory_path().with_name(_memory_path().name + ".lock")
        with _file_lock(lock):
            _atomic_write_jsonl(_memory_path(), kept)
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
    memory_records = _load_jsonl(_memory_path(), kind="memory")
    runs_records = _load_jsonl(_runs_path(), kind="runs")
    assert isinstance(memory_records, list)
    assert isinstance(runs_records, list)
    unresolved = _unresolved_failures(memory_records)

    triage_records: list[dict[str, str]] = []
    phase_results: list[dict[str, Any]] = []
    status = "success"

    shown_hint_total = 0
    useful_hint_total = 0

    for phase in phases:
        signature = _failure_signature(args.mode, phase)
        query = f"{phase.likely_root_cause} {phase.command}"
        code, stdout, stderr = _execute_command(phase.command, dry_run=args.dry_run)

        phase_result: dict[str, Any] = {
            "phase": phase.name,
            "signature": signature,
            "command": phase.command,
            "component": phase.failing_component,
            "exit_code": code,
        }
        if stdout.strip():
            phase_result["stdout"] = stdout.strip()[:3000]
        if stderr.strip():
            phase_result["stderr"] = stderr.strip()[:3000]

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
                memory_records,
                fingerprint=signature,
                failing_component=phase.failing_component,
                query_text=f"{query} {stderr[:300]}",
                runs_records=runs_records,
                limit=3,
            )
            hint_ids = [str(hint.get("id")) for hint in hints if hint.get("id")]
            shown_hint_total += len(hint_ids)
            if hint_ids:
                _increment_hint_counters(hint_ids, shown_delta=1, useful_delta=0)

            if hints:
                print("Memory Hints")
                for hint in hints:
                    print(f"- {hint.get('title', '(untitled)')}")

            added, _ = _add_memory_entry(
                title=f"Verify failure: {phase.name}",
                details=f"{phase.likely_root_cause}. Command: {phase.command}",
                category="verify_failure",
                source="runner.verify",
                evidence=stderr.strip() or stdout.strip() or None,
                fingerprint=signature,
                resolved=False,
                metadata={
                    "triage": triage,
                    "context": context,
                    "hintIds": hint_ids,
                },
            )
            if not added:
                memory_records = _load_jsonl(_memory_path(), kind="memory")
                assert isinstance(memory_records, list)

            phase_result["hint_ids"] = hint_ids
            phase_result["hint_count"] = len(hint_ids)
            if args.fail_fast:
                phase_results.append(phase_result)
                break
        else:
            if signature in unresolved:
                prior_hint_ids, latest_failure_ts = _phase_failure_history(
                    runs_records, signature
                )
                unique_hint_ids = sorted(set(prior_hint_ids))
                hint_assisted = bool(unique_hint_ids)
                if unique_hint_ids:
                    _increment_hint_counters(
                        unique_hint_ids, shown_delta=0, useful_delta=1
                    )
                    useful_hint_total += len(unique_hint_ids)

                now = datetime.now(UTC)
                ttr_seconds = None
                if latest_failure_ts is not None:
                    ttr_seconds = max((now - latest_failure_ts).total_seconds(), 0.0)

                _add_memory_entry(
                    title=f"Verify resolution: {phase.name}",
                    details=f"Previously failing signature for '{phase.name}' now passes.",
                    category="verify_resolution",
                    source="runner.verify",
                    evidence=phase.command,
                    fingerprint=signature,
                    resolved=True,
                    metadata={
                        "context": context,
                        "hintAssisted": hint_assisted,
                        "hintIds": unique_hint_ids,
                        "timeToResolutionSeconds": ttr_seconds,
                    },
                )

        phase_results.append(phase_result)

    _record_run(
        command="verify",
        status=status,
        details={
            "schemaVersion": SCHEMA_VERSION,
            "mode": args.mode,
            "fail_fast": bool(args.fail_fast),
            "dry_run": bool(args.dry_run),
            "phase_results": phase_results,
            "triage": triage_records,
            "hintStats": {
                "shown": shown_hint_total,
                "useful": useful_hint_total,
            },
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
    memory_list.add_argument("--query")
    memory_list.add_argument("--component")
    memory_list.set_defaults(handler=_command_memory_list)

    memory_report = sub.add_parser("memory-report", help="Report memory categories")
    memory_report.add_argument("--top", type=int, default=10)
    memory_report.set_defaults(handler=_command_memory_report)

    memory_compact = sub.add_parser("memory-compact", help="Keep only recent entries")
    memory_compact.add_argument("--keep-last", type=int, default=200)
    memory_compact.add_argument("--dry-run", action="store_true")
    memory_compact.add_argument("--min-confidence", type=float, default=0.1)
    memory_compact.add_argument("--min-usefulness", type=float, default=0.0)
    memory_compact.set_defaults(handler=_command_memory_compact)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
