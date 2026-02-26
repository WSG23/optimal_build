#!/usr/bin/env python3
"""Canonical runner for verification and agent memory operations."""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import math
import os
import pickle
import re
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import threading
import uuid
from collections import Counter
from collections.abc import Sequence
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

try:  # pragma: no cover - optional in constrained environments
    from sklearn.decomposition import TruncatedSVD
    from sklearn.feature_extraction.text import TfidfVectorizer
except Exception:  # pragma: no cover
    TruncatedSVD = None  # type: ignore[assignment]
    TfidfVectorizer = None  # type: ignore[assignment]

try:  # pragma: no cover - not available on some platforms
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None

try:  # pragma: no cover - optional at runtime
    from cryptography.fernet import Fernet, InvalidToken
except Exception:  # pragma: no cover
    Fernet = None
    InvalidToken = Exception


SCHEMA_VERSION = 2
DEFAULT_RUNS_FILE = Path("metrics/agent_runs.jsonl")
DEFAULT_MEMORY_FILE = Path("metrics/agent_memory.jsonl")
DEFAULT_DB_FILE = Path("metrics/agent_memory.db")
DEFAULT_EMBEDDING_MODEL_FILE = Path("metrics/agent_embedding_model.pkl")
DEFAULT_AUDIT_FILE = Path("metrics/agent_audit.jsonl")
CORRUPT_SUFFIX = ".corrupt"

EMBEDDING_DIM = 96
SEMANTIC_DIM = 128
SEMANTIC_MIN_SIMILARITY = 0.18
BASE_HINT_THRESHOLD = 0.32
ANN_BANDS = 12
ANN_BITS_PER_BAND = 8
ANN_TOTAL_BITS = ANN_BANDS * ANN_BITS_PER_BAND
AB_CONTROL_RATE = 0.2

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
EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"\+?\d[\d\-\s()]{7,}\d")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")

_EMBED_MODEL_LOCK = threading.Lock()
_EMBED_MODEL_CACHE: dict[str, Any] = {
    "version": "",
    "vectorizer": None,
    "svd": None,
}

PLAYBOOKS: list[dict[str, Any]] = [
    {
        "name": "backend-typecheck",
        "component": "backend",
        "root_keywords": ["mypy", "type", "import", "contract"],
        "safeCommand": "make typecheck-backend",
        "confidenceGate": 0.55,
        "rollback": "Revert the last typing-only refactor and rerun make typecheck-backend",
    },
    {
        "name": "frontend-lint",
        "component": "frontend",
        "root_keywords": ["eslint", "lint", "tsx", "hook"],
        "safeCommand": "pnpm -C frontend lint",
        "confidenceGate": 0.55,
        "rollback": (
            "Revert recent frontend formatting/styling edits and rerun "
            "pnpm -C frontend lint"
        ),
    },
    {
        "name": "security-gate",
        "component": "security",
        "root_keywords": ["security", "vulnerability", "pip-audit", "bandit"],
        "safeCommand": "make lint-prod",
        "confidenceGate": 0.6,
        "rollback": "Revert dependency/security-policy changes and rerun make lint-prod",
    },
    {
        "name": "quality-rules",
        "component": "quality",
        "root_keywords": ["coding", "rule", "format", "ruff", "black"],
        "safeCommand": "make check-coding-rules",
        "confidenceGate": 0.5,
        "rollback": "Revert broad formatting updates and rerun make check-coding-rules",
    },
]


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


def _db_path() -> Path:
    return _path_from_env(
        [
            "AGENT_DB_FILE",
            "AGENT_DB_PATH",
            "OB_AGENT_DB_FILE",
            "OB_AGENT_DB_PATH",
            "ICS_AGENT_DB_FILE",
            "ICS_AGENT_DB_PATH",
        ],
        DEFAULT_DB_FILE,
    )


def _embedding_model_path() -> Path:
    return _path_from_env(
        [
            "AGENT_EMBED_MODEL_FILE",
            "AGENT_EMBED_MODEL_PATH",
            "OB_AGENT_EMBED_MODEL_FILE",
            "OB_AGENT_EMBED_MODEL_PATH",
            "ICS_AGENT_EMBED_MODEL_FILE",
            "ICS_AGENT_EMBED_MODEL_PATH",
        ],
        DEFAULT_EMBEDDING_MODEL_FILE,
    )


def _audit_path() -> Path:
    return _path_from_env(
        [
            "AGENT_AUDIT_FILE",
            "AGENT_AUDIT_PATH",
            "OB_AGENT_AUDIT_FILE",
            "OB_AGENT_AUDIT_PATH",
            "ICS_AGENT_AUDIT_FILE",
            "ICS_AGENT_AUDIT_PATH",
        ],
        DEFAULT_AUDIT_FILE,
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


def _redact_pii(text: str) -> str:
    redacted = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    redacted = PHONE_RE.sub("[REDACTED_PHONE]", redacted)
    redacted = SSN_RE.sub("[REDACTED_SSN]", redacted)
    redacted = CARD_RE.sub("[REDACTED_CARD]", redacted)
    return redacted


def _fernet() -> Fernet | None:
    key = os.environ.get("AGENT_MEMORY_ENCRYPTION_KEY", "").strip()
    if not key:
        return None
    if Fernet is None:
        raise RuntimeError(
            "AGENT_MEMORY_ENCRYPTION_KEY is set but cryptography.fernet is unavailable"
        )

    try:
        if len(key) != 44:
            key = base64.urlsafe_b64encode(
                hashlib.sha256(key.encode()).digest()
            ).decode()
        return Fernet(key.encode())
    except Exception as exc:  # pragma: no cover - defensive
        raise RuntimeError("Invalid AGENT_MEMORY_ENCRYPTION_KEY") from exc


def _encrypt_field(text: str) -> str:
    codec = _fernet()
    if codec is None:
        return text
    token = codec.encrypt(text.encode()).decode()
    return f"enc::{token}"


def _decrypt_field(value: str) -> str:
    if not value.startswith("enc::"):
        return value
    codec = _fernet()
    if codec is None:
        return "[ENCRYPTED:KEY_MISSING]"
    token = value.split("enc::", 1)[1]
    try:
        return codec.decrypt(token.encode()).decode()
    except InvalidToken:
        return "[ENCRYPTED:INVALID_TOKEN]"


def _govern_text(text: str | None) -> str | None:
    if text is None:
        return None
    return _encrypt_field(_redact_pii(text))


def _tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def _vector_normalize(vector: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(float(value) * float(value) for value in vector))
    if norm == 0:
        return [0.0 for _ in vector]
    return [round(float(value) / norm, 6) for value in vector]


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

    return _vector_normalize(vector)


def _embedding_model_version(corpus_texts: Sequence[str]) -> str:
    digest = hashlib.sha256()
    for text in corpus_texts:
        digest.update(text.encode())
        digest.update(b"\n")
    return f"lsa-{digest.hexdigest()[:20]}"


def _load_embedding_model() -> tuple[str, TfidfVectorizer, TruncatedSVD] | None:
    path = _embedding_model_path()
    if not path.exists():
        return None
    try:
        payload = pickle.loads(path.read_bytes())
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    version = str(payload.get("version", ""))
    vectorizer = payload.get("vectorizer")
    svd = payload.get("svd")
    if not version or vectorizer is None or svd is None:
        return None
    return version, vectorizer, svd


def _save_embedding_model(
    version: str, vectorizer: TfidfVectorizer, svd: TruncatedSVD
) -> None:
    path = _embedding_model_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": version, "vectorizer": vectorizer, "svd": svd}
    path.write_bytes(pickle.dumps(payload))


def _fit_embedding_model(
    corpus_texts: Sequence[str],
) -> tuple[str, TfidfVectorizer | None, TruncatedSVD | None]:
    cleaned = [text.strip() for text in corpus_texts if text.strip()]
    if len(cleaned) < 2:
        return _embedding_model_version(cleaned), None, None

    version = _embedding_model_version(cleaned)
    if TfidfVectorizer is None or TruncatedSVD is None:
        return version, None, None
    with _EMBED_MODEL_LOCK:
        cache_version = str(_EMBED_MODEL_CACHE.get("version", ""))
        cache_vectorizer = _EMBED_MODEL_CACHE.get("vectorizer")
        cache_svd = _EMBED_MODEL_CACHE.get("svd")
        if (
            cache_version == version
            and cache_vectorizer is not None
            and cache_svd is not None
        ):
            return version, cache_vectorizer, cache_svd

        loaded = _load_embedding_model()
        if loaded is not None and loaded[0] == version:
            _EMBED_MODEL_CACHE["version"] = loaded[0]
            _EMBED_MODEL_CACHE["vectorizer"] = loaded[1]
            _EMBED_MODEL_CACHE["svd"] = loaded[2]
            return loaded

        try:
            vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                min_df=1,
                max_features=4096,
                lowercase=True,
            )
            matrix = vectorizer.fit_transform(cleaned)
            max_components = min(matrix.shape[0] - 1, matrix.shape[1] - 1, SEMANTIC_DIM)
            if max_components < 2:
                return version, None, None
            svd = TruncatedSVD(n_components=max_components, random_state=42)
            svd.fit(matrix)
            _save_embedding_model(version, vectorizer, svd)
            _EMBED_MODEL_CACHE["version"] = version
            _EMBED_MODEL_CACHE["vectorizer"] = vectorizer
            _EMBED_MODEL_CACHE["svd"] = svd
            return version, vectorizer, svd
        except Exception:
            return version, None, None


def _db_lookup_embedding_cache(
    text_hash: str, model_version: str
) -> list[float] | None:
    _ensure_db_schema()
    with closing(_db_connect()) as conn:
        row = conn.execute(
            """
            SELECT vector_json
            FROM embedding_cache
            WHERE text_hash = ? AND model_version = ?
            """,
            (text_hash, model_version),
        ).fetchone()
        if row is None:
            return None
        conn.execute(
            """
            UPDATE embedding_cache
            SET last_used_at = ?
            WHERE text_hash = ? AND model_version = ?
            """,
            (_utc_now(), text_hash, model_version),
        )
        try:
            vector = json.loads(str(row["vector_json"]))
            return [float(value) for value in vector]
        except Exception:
            return None


def _db_store_embedding_cache(
    text_hash: str, model_version: str, vector: list[float]
) -> None:
    _ensure_db_schema()
    with closing(_db_connect()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            """
            INSERT INTO embedding_cache(text_hash, model_version, vector_json, last_used_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(text_hash, model_version)
            DO UPDATE SET vector_json = excluded.vector_json, last_used_at = excluded.last_used_at
            """,
            (text_hash, model_version, json.dumps(vector), _utc_now()),
        )
        conn.execute("COMMIT")


def _semantic_embedding(
    text: str, corpus_texts: Sequence[str]
) -> tuple[str, list[float]]:
    version, vectorizer, svd = _fit_embedding_model(corpus_texts)
    text_hash = hashlib.sha256(text.encode()).hexdigest()
    cached = _db_lookup_embedding_cache(text_hash, version)
    if cached is not None:
        return version, cached

    if vectorizer is None or svd is None:
        vector = _hash_embedding(text, EMBEDDING_DIM)
        _db_store_embedding_cache(text_hash, version, vector)
        return version, vector

    try:
        transformed = svd.transform(vectorizer.transform([text]))[0]
        vector = _vector_normalize(transformed.tolist())
    except Exception:
        vector = _hash_embedding(text, EMBEDDING_DIM)
    _db_store_embedding_cache(text_hash, version, vector)
    return version, vector


def _hyperplanes(model_version: str, dim: int) -> list[list[float]]:
    # Deterministic pseudo-random hyperplanes from model version.
    planes: list[list[float]] = []
    seed = hashlib.sha256(model_version.encode()).digest()
    cursor = seed
    for index in range(ANN_TOTAL_BITS):
        values: list[float] = []
        while len(values) < dim:
            cursor = hashlib.sha256(cursor + index.to_bytes(2, "big")).digest()
            for byte in cursor:
                values.append((byte / 255.0) * 2.0 - 1.0)
                if len(values) >= dim:
                    break
        planes.append(_vector_normalize(values))
    return planes


def _ann_buckets_for_vector(
    vector: Sequence[float], model_version: str
) -> list[tuple[int, int]]:
    if not vector:
        return [(band, 0) for band in range(ANN_BANDS)]
    dim = len(vector)
    planes = _hyperplanes(model_version, dim)
    bits: list[int] = []
    for plane in planes:
        dot = sum(float(a) * float(b) for a, b in zip(vector, plane, strict=False))
        bits.append(1 if dot >= 0 else 0)

    buckets: list[tuple[int, int]] = []
    for band in range(ANN_BANDS):
        offset = band * ANN_BITS_PER_BAND
        bucket = 0
        for bit_index in range(ANN_BITS_PER_BAND):
            bucket = (bucket << 1) | bits[offset + bit_index]
        buckets.append((band, bucket))
    return buckets


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
    title = _decrypt_field(str(record.get("title", "")))
    details = _decrypt_field(str(record.get("details", "")))
    text = f"{title}\n{details}"
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
    normalized["title"] = str(normalized["title"])
    normalized["details"] = str(normalized["details"])
    if normalized.get("evidence") is not None:
        normalized["evidence"] = str(normalized.get("evidence"))

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


def _db_connect() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _ensure_db_schema() -> None:
    with closing(_db_connect()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_entries (
                id TEXT PRIMARY KEY,
                schema_version INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                fingerprint TEXT NOT NULL,
                category TEXT NOT NULL,
                dedupe_hash TEXT NOT NULL,
                title TEXT NOT NULL,
                details TEXT NOT NULL,
                source TEXT NOT NULL,
                evidence TEXT,
                status TEXT NOT NULL,
                resolved INTEGER NOT NULL,
                confidence REAL NOT NULL,
                impact_score REAL NOT NULL,
                usefulness_score REAL NOT NULL,
                hint_shown_count INTEGER NOT NULL,
                hint_useful_count INTEGER NOT NULL,
                occurrence_count INTEGER NOT NULL,
                expires_at TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                embedding_json TEXT,
                embedding_model_version TEXT,
                embedding_updated_at TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_memory_category_fp "
            "ON memory_entries(category, fingerprint)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_memory_status_expires "
            "ON memory_entries(status, expires_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_memory_category_timestamp "
            "ON memory_entries(category, timestamp)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                schema_version INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                command TEXT NOT NULL,
                status TEXT NOT NULL,
                details_json TEXT NOT NULL,
                context_json TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_runs_command_timestamp ON runs(command, timestamp)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                entry_id TEXT,
                action TEXT NOT NULL,
                actor TEXT NOT NULL,
                reason TEXT,
                before_json TEXT,
                after_json TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_memory_audit_entry_timestamp "
            "ON memory_audit(entry_id, timestamp)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS embedding_cache (
                text_hash TEXT NOT NULL,
                model_version TEXT NOT NULL,
                vector_json TEXT NOT NULL,
                last_used_at TEXT NOT NULL,
                PRIMARY KEY (text_hash, model_version)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ann_buckets (
                entry_id TEXT NOT NULL,
                model_version TEXT NOT NULL,
                band INTEGER NOT NULL,
                bucket INTEGER NOT NULL,
                PRIMARY KEY (entry_id, model_version, band)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_ann_lookup ON ann_buckets(model_version, band, bucket)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ranking_state (
                key TEXT PRIMARY KEY,
                value_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS experiments (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                signature TEXT NOT NULL,
                arm TEXT NOT NULL,
                assignment TEXT NOT NULL,
                hint_ids_json TEXT NOT NULL,
                hint_features_json TEXT NOT NULL,
                resolved INTEGER NOT NULL DEFAULT 0,
                outcome TEXT,
                resolved_at TEXT,
                time_to_resolution_seconds REAL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_experiments_signature_timestamp "
            "ON experiments(signature, timestamp)"
        )


def _append_audit_event(
    *,
    entry_id: str | None,
    action: str,
    actor: str,
    reason: str | None,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> None:
    payload = {
        "id": str(uuid.uuid4()),
        "timestamp": _utc_now(),
        "entryId": entry_id,
        "action": action,
        "actor": actor,
        "reason": reason,
        "before": before,
        "after": after,
    }
    _append_jsonl(_audit_path(), payload, kind="plain")

    _ensure_db_schema()
    with closing(_db_connect()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            """
            INSERT INTO memory_audit (
                timestamp, entry_id, action, actor, reason, before_json, after_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["timestamp"],
                entry_id,
                action,
                actor,
                reason,
                json.dumps(before, sort_keys=True) if before is not None else None,
                json.dumps(after, sort_keys=True) if after is not None else None,
            ),
        )
        conn.execute("COMMIT")


def _json_dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True)


def _db_sync_memory_records(records: list[dict[str, Any]]) -> None:
    _ensure_db_schema()
    now_iso = _utc_now()
    with closing(_db_connect()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("DELETE FROM memory_entries")
        for record in records:
            conn.execute(
                """
                INSERT INTO memory_entries (
                    id, schema_version, timestamp, fingerprint, category, dedupe_hash,
                    title, details, source, evidence, status, resolved, confidence,
                    impact_score, usefulness_score, hint_shown_count, hint_useful_count,
                    occurrence_count, expires_at, metadata_json, embedding_json,
                    embedding_model_version, embedding_updated_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(record.get("id")),
                    _coerce_int(
                        record.get("schemaVersion", SCHEMA_VERSION),
                        SCHEMA_VERSION,
                        min_value=1,
                    ),
                    str(record.get("timestamp", now_iso)),
                    str(record.get("fingerprint", "")),
                    str(record.get("category", "general")),
                    str(record.get("dedupe_hash", "")),
                    str(record.get("title", "")),
                    str(record.get("details", "")),
                    str(record.get("source", "unknown")),
                    record.get("evidence"),
                    str(record.get("status", "active")),
                    1 if bool(record.get("resolved", False)) else 0,
                    float(record.get("confidence", 0.5)),
                    float(record.get("impactScore", 1.0)),
                    float(record.get("usefulnessScore", 0.5)),
                    int(record.get("hintShownCount", 0)),
                    int(record.get("hintUsefulCount", 0)),
                    int(record.get("occurrenceCount", 1)),
                    str(record.get("expiresAt", now_iso)),
                    (
                        _json_dumps(record.get("metadata", {}))
                        if isinstance(record.get("metadata"), dict)
                        else _json_dumps({"legacyMetadata": record.get("metadata")})
                    ),
                    json.dumps(record.get("embedding", [])),
                    str(record.get("embeddingModelVersion", "")),
                    str(record.get("embeddingUpdatedAt", "")),
                    now_iso,
                ),
            )
        conn.execute("COMMIT")


def _db_sync_runs_records(records: list[dict[str, Any]]) -> None:
    _ensure_db_schema()
    with closing(_db_connect()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("DELETE FROM runs")
        for record in records:
            conn.execute(
                """
                INSERT INTO runs (
                    id, schema_version, timestamp, command, status, details_json, context_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(record.get("id")),
                    _coerce_int(
                        record.get("schemaVersion", SCHEMA_VERSION),
                        SCHEMA_VERSION,
                        min_value=1,
                    ),
                    str(record.get("timestamp", _utc_now())),
                    str(record.get("command", "")),
                    str(record.get("status", "unknown")),
                    (
                        _json_dumps(record.get("details", {}))
                        if isinstance(record.get("details"), dict)
                        else _json_dumps({"legacyDetails": record.get("details")})
                    ),
                    (
                        _json_dumps(record.get("context", {}))
                        if isinstance(record.get("context"), dict)
                        else None
                    ),
                ),
            )
        conn.execute("COMMIT")


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
        elif kind == "plain":
            record_payload = dict(record_payload)
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
    runs = _load_jsonl(_runs_path(), kind="runs")
    if isinstance(runs, list):
        _db_sync_runs_records(runs)


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


def _load_ranking_weights() -> list[float]:
    _ensure_db_schema()
    default = [0.52, 0.15, 0.14, 0.10, 0.09]
    with closing(_db_connect()) as conn:
        row = conn.execute(
            "SELECT value_json FROM ranking_state WHERE key = ?",
            ("hint_weight_vector",),
        ).fetchone()
        if row is None:
            return default
        try:
            values = json.loads(str(row["value_json"]))
            if not isinstance(values, list):
                return default
            parsed = [float(value) for value in values]
            if len(parsed) != 5:
                return default
            return parsed
        except Exception:
            return default


def _save_ranking_weights(weights: Sequence[float]) -> None:
    _ensure_db_schema()
    payload = json.dumps([round(float(value), 8) for value in weights])
    with closing(_db_connect()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            """
            INSERT INTO ranking_state(key, value_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value_json = excluded.value_json,
                updated_at = excluded.updated_at
            """,
            ("hint_weight_vector", payload, _utc_now()),
        )
        conn.execute("COMMIT")


def _assign_ab_group(signature: str, context: dict[str, Any]) -> str:
    material = f"{signature}|{context.get('head_sha','')}|{context.get('diff_hash','')}"
    bucket = int(hashlib.sha256(material.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return "control" if bucket < AB_CONTROL_RATE else "treatment"


def _record_experiment(
    *,
    signature: str,
    assignment: str,
    hint_ids: Sequence[str],
    hint_features: list[dict[str, Any]],
) -> str:
    _ensure_db_schema()
    experiment_id = str(uuid.uuid4())
    with closing(_db_connect()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            """
            INSERT INTO experiments(
                id,
                timestamp,
                signature,
                arm,
                assignment,
                hint_ids_json,
                hint_features_json,
                resolved
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                experiment_id,
                _utc_now(),
                signature,
                "hint-ranking-v1",
                assignment,
                json.dumps(list(hint_ids)),
                json.dumps(hint_features),
            ),
        )
        conn.execute("COMMIT")
    return experiment_id


def _resolve_experiment(
    signature: str, *, ttr_seconds: float | None
) -> dict[str, Any] | None:
    _ensure_db_schema()
    with closing(_db_connect()) as conn:
        row = conn.execute(
            """
            SELECT id, assignment, hint_ids_json, hint_features_json, timestamp
            FROM experiments
            WHERE signature = ? AND resolved = 0
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (signature,),
        ).fetchone()
        if row is None:
            return None
        hint_ids = json.loads(str(row["hint_ids_json"]))
        features = json.loads(str(row["hint_features_json"]))
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            """
            UPDATE experiments
            SET resolved = 1, outcome = ?, resolved_at = ?, time_to_resolution_seconds = ?
            WHERE id = ?
            """,
            ("resolved", _utc_now(), ttr_seconds, str(row["id"])),
        )
        conn.execute("COMMIT")
        return {
            "id": str(row["id"]),
            "assignment": str(row["assignment"]),
            "hintIds": hint_ids if isinstance(hint_ids, list) else [],
            "hintFeatures": features if isinstance(features, list) else [],
            "timestamp": str(row["timestamp"]),
        }


def _update_ranking_from_feedback(
    features: list[dict[str, Any]], reward: float
) -> None:
    if not features:
        return
    weights = _load_ranking_weights()
    lr = _coerce_float(
        os.environ.get("AGENT_BANDIT_LR", 0.03), 0.03, min_value=0.001, max_value=0.5
    )
    for feature in features:
        semantic = _coerce_float(
            feature.get("semanticSimilarity", 0.0), 0.0, min_value=0.0, max_value=1.0
        )
        recency = _coerce_float(
            feature.get("recencyWeight", 0.0), 0.0, min_value=0.0, max_value=1.0
        )
        confidence = _coerce_float(
            feature.get("confidence", 0.0), 0.0, min_value=0.0, max_value=1.0
        )
        usefulness = _coerce_float(
            feature.get("usefulness", 0.0), 0.0, min_value=0.0, max_value=1.0
        )
        impact = _coerce_float(
            feature.get("impactWeight", 0.0), 0.0, min_value=0.0, max_value=1.0
        )
        vector = [semantic, recency, confidence, usefulness, impact]
        prediction = sum(weights[index] * vector[index] for index in range(5))
        error = reward - prediction
        for index in range(5):
            weights[index] += lr * error * vector[index]

    total = sum(max(value, 0.001) for value in weights)
    normalized = [max(value, 0.001) / total for value in weights]
    _save_ranking_weights(normalized)


def _build_embedding_corpus(records: list[dict[str, Any]]) -> list[str]:
    corpus: list[str] = []
    for record in records:
        title = _decrypt_field(str(record.get("title", "")))
        details = _decrypt_field(str(record.get("details", "")))
        corpus.append(f"{title}\n{details}".strip())
    return [item for item in corpus if item]


def _db_refresh_ann_index(records: list[dict[str, Any]]) -> str:
    corpus = _build_embedding_corpus(records)
    corpus_version = _embedding_model_version(corpus)

    vectors_by_id: dict[str, list[float]] = {}
    model_version = corpus_version
    for record in records:
        record_id = str(record.get("id", ""))
        if not record_id:
            continue
        title = _decrypt_field(str(record.get("title", "")))
        details = _decrypt_field(str(record.get("details", "")))
        text = f"{title}\n{details}"
        model_version, vector = _semantic_embedding(text, corpus)
        record["embedding"] = vector
        record["embeddingModelVersion"] = model_version
        record["embeddingUpdatedAt"] = _utc_now()
        vectors_by_id[record_id] = vector

    _ensure_db_schema()
    with closing(_db_connect()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            "DELETE FROM ann_buckets WHERE model_version = ?", (model_version,)
        )
        for record_id, vector in vectors_by_id.items():
            for band, bucket in _ann_buckets_for_vector(vector, model_version):
                conn.execute(
                    """
                    INSERT OR REPLACE INTO ann_buckets(entry_id, model_version, band, bucket)
                    VALUES (?, ?, ?, ?)
                    """,
                    (record_id, model_version, band, bucket),
                )
        conn.execute("COMMIT")
    return model_version


def _db_ann_candidates(
    *,
    model_version: str,
    query_vector: Sequence[float],
    limit: int,
) -> list[str]:
    buckets = _ann_buckets_for_vector(query_vector, model_version)
    if not buckets:
        return []

    clauses = " OR ".join(["(band = ? AND bucket = ?)"] * len(buckets))
    params: list[Any] = []
    for band, bucket in buckets:
        params.extend([band, bucket])
    params.append(model_version)
    params.append(max(limit, 10))

    _ensure_db_schema()
    with closing(_db_connect()) as conn:
        rows = conn.execute(
            f"""
            SELECT entry_id, COUNT(*) AS votes
            FROM ann_buckets
            WHERE ({clauses}) AND model_version = ?
            GROUP BY entry_id
            ORDER BY votes DESC
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()
    return [str(row["entry_id"]) for row in rows]


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
    model_version = _db_refresh_ann_index(records)
    corpus = _build_embedding_corpus(records)
    _, query_embedding = _semantic_embedding(
        f"{failing_component} {query_text}", corpus
    )
    candidate_ids = set(
        _db_ann_candidates(
            model_version=model_version,
            query_vector=query_embedding,
            limit=max(limit * 24, 40),
        )
    )
    if not candidate_ids:
        candidate_ids = {str(record.get("id", "")) for record in records}
    weights = _load_ranking_weights()

    scored: list[tuple[float, dict[str, Any]]] = []
    component_token = failing_component.lower().strip()

    for record in records:
        if str(record.get("id", "")) not in candidate_ids:
            continue
        if _is_expired(record, now):
            continue

        title = _decrypt_field(str(record.get("title", "")))
        details = _decrypt_field(str(record.get("details", "")))
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
            similarity * weights[0]
            + recency_weight * weights[1]
            + confidence * weights[2]
            + usefulness * weights[3]
            + impact_weight * weights[4]
            + (0.08 if component_match else 0.0)
        )

        status = str(record.get("status", "active"))
        if status in {"superseded", "stale"}:
            score -= 0.2

        if not exact_fingerprint and score < threshold:
            continue

        annotated = dict(record)
        annotated["title"] = title
        annotated["details"] = details
        annotated["hintScore"] = round(score, 6)
        annotated["semanticSimilarity"] = round(similarity, 6)
        annotated["scoreBreakdown"] = {
            "semantic": round(similarity * weights[0], 6),
            "recency": round(recency_weight * weights[1], 6),
            "confidence": round(confidence * weights[2], 6),
            "usefulness": round(usefulness * weights[3], 6),
            "impact": round(impact_weight * weights[4], 6),
            "componentBonus": round(0.08 if component_match else 0.0, 6),
            "threshold": round(threshold, 6),
        }
        annotated["rankingFeatures"] = {
            "semanticSimilarity": round(similarity, 6),
            "recencyWeight": round(recency_weight, 6),
            "confidence": round(confidence, 6),
            "usefulness": round(usefulness, 6),
            "impactWeight": round(impact_weight, 6),
        }
        annotated["abCandidate"] = True
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
    governed_title = _govern_text(title) or ""
    governed_details = _govern_text(details) or ""
    governed_evidence = _govern_text(evidence)
    with _file_lock(lock):
        records = _load_jsonl(path, kind="memory")
        assert isinstance(records, list)
        before_by_id = {str(item.get("id", "")): dict(item) for item in records}
        fp = fingerprint or _default_fingerprint(title, details, category)
        added, record = _upsert_memory_record(
            records,
            title=governed_title,
            details=governed_details,
            category=category,
            source=source,
            evidence=governed_evidence,
            fingerprint=fp,
            resolved=resolved,
            metadata=metadata or {},
        )
        _apply_conflict_resolution(records, fingerprint=fp, category=category)
        _atomic_write_jsonl(path, records)
        _db_sync_memory_records(records)

        after_id = str(record.get("id", ""))
        before = before_by_id.get(after_id)
        _append_audit_event(
            entry_id=after_id,
            action="create" if added else "update",
            actor=source,
            reason=f"category={category}",
            before=before,
            after=record,
        )

        # Audit supersede/resolution state transitions caused by conflict handling.
        for updated in records:
            updated_id = str(updated.get("id", ""))
            previous = before_by_id.get(updated_id)
            if previous is None:
                continue
            if str(previous.get("status", "")) == str(updated.get("status", "")):
                continue
            _append_audit_event(
                entry_id=updated_id,
                action="status-transition",
                actor="runner.conflict-resolution",
                reason=f"{previous.get('status', '')}->{updated.get('status', '')}",
                before=previous,
                after=updated,
            )
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
        assert isinstance(records, list)
        changed = False
        for record in records:
            if str(record.get("id")) not in id_set:
                continue
            before = dict(record)
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
            _append_audit_event(
                entry_id=str(record.get("id", "")),
                action="hint-feedback",
                actor="runner.feedback",
                reason=f"shown+={shown_delta},useful+={useful_delta}",
                before=before,
                after=record,
            )
        if changed:
            _atomic_write_jsonl(path, records)
            _db_sync_memory_records(records)


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


def _match_playbook(component: str, root_cause: str) -> dict[str, Any] | None:
    lowered = root_cause.lower()
    component_lower = component.lower()
    for playbook in PLAYBOOKS:
        if str(playbook.get("component", "")).lower() != component_lower:
            continue
        keywords = [
            str(keyword).lower() for keyword in playbook.get("root_keywords", [])
        ]
        if not keywords:
            continue
        matches = sum(1 for keyword in keywords if keyword in lowered)
        if matches == 0:
            continue
        confidence = min(0.95, 0.35 + 0.15 * matches)
        return {
            "name": playbook.get("name"),
            "safeCommand": playbook.get("safeCommand"),
            "confidence": round(confidence, 6),
            "confidenceGate": playbook.get("confidenceGate", 0.5),
            "rollback": playbook.get("rollback"),
        }
    return None


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
        playbook = _match_playbook(component, top_root)
        cluster_payload: dict[str, Any] = {
            "clusterId": key,
            "failingComponent": component,
            "occurrences": len(group),
            "likelyRootCause": top_root,
            "recommendedRemediation": top_fix,
        }
        if playbook is not None:
            cluster_payload["playbook"] = playbook
        clusters.append({**cluster_payload})

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


def _causal_evaluation(top: int) -> dict[str, Any]:
    _ensure_db_schema()
    with closing(_db_connect()) as conn:
        rows = conn.execute(
            """
            SELECT assignment, resolved, time_to_resolution_seconds
            FROM experiments
            WHERE outcome IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (max(top * 200, 200),),
        ).fetchall()

    group: dict[str, dict[str, Any]] = {
        "treatment": {"count": 0, "resolved": 0, "ttr": []},
        "control": {"count": 0, "resolved": 0, "ttr": []},
    }
    for row in rows:
        assignment = str(row["assignment"])
        if assignment not in group:
            continue
        group[assignment]["count"] += 1
        if int(row["resolved"]) == 1:
            group[assignment]["resolved"] += 1
            seconds = row["time_to_resolution_seconds"]
            if isinstance(seconds, int | float) and seconds >= 0:
                group[assignment]["ttr"].append(float(seconds))

    def _rate(key: str) -> float:
        count = group[key]["count"]
        if count == 0:
            return 0.0
        return group[key]["resolved"] / count

    treat_rate = _rate("treatment")
    control_rate = _rate("control")
    treat_mttr = (
        statistics.mean(group["treatment"]["ttr"])
        if group["treatment"]["ttr"]
        else None
    )
    control_mttr = (
        statistics.mean(group["control"]["ttr"]) if group["control"]["ttr"] else None
    )
    mttr_delta = None
    if treat_mttr is not None and control_mttr is not None:
        mttr_delta = control_mttr - treat_mttr

    return {
        "sampleSize": len(rows),
        "treatment": {
            "count": group["treatment"]["count"],
            "resolutionRate": round(treat_rate, 6),
            "meanTimeToResolutionSeconds": treat_mttr,
        },
        "control": {
            "count": group["control"]["count"],
            "resolutionRate": round(control_rate, 6),
            "meanTimeToResolutionSeconds": control_mttr,
        },
        "uplift": {
            "resolutionRateDelta": round(treat_rate - control_rate, 6),
            "mttrDeltaSeconds": mttr_delta,
        },
    }


def _build_remediation_suggestions(
    clusters: list[dict[str, Any]], top: int
) -> list[str]:
    suggestions: list[str] = []
    for cluster in clusters[:top]:
        component = cluster.get("failingComponent", "quality")
        remediation = cluster.get("recommendedRemediation", "inspect failing command")
        root = cluster.get("likelyRootCause", "unknown")
        playbook = cluster.get("playbook")
        if isinstance(playbook, dict):
            suggestions.append(
                f"{component}: {root} -> safe '{playbook.get('safeCommand')}' "
                f"(gate>={playbook.get('confidenceGate')}), rollback: {playbook.get('rollback')}"
            )
            continue
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


def _build_memory_report_payload(top: int) -> dict[str, Any]:
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
    )[:top]
    top_fingerprints = sorted(
        by_fingerprint.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:top]

    clusters = _clusters_from_memory(memory_records, top)
    trends = _trend_analysis(memory_records, top)
    hint_effectiveness = _hint_effectiveness(memory_records, runs_records)
    causal = _causal_evaluation(top)
    suggestions = _build_remediation_suggestions(clusters, top)
    ranking_weights = _load_ranking_weights()

    drift_alerts: list[str] = []
    if hint_effectiveness.get("hintPrecision", 0.0) < 0.2:
        drift_alerts.append("Hint precision below SLO threshold (0.20)")
    resolution_delta = causal.get("uplift", {}).get("resolutionRateDelta")
    if isinstance(resolution_delta, float) and resolution_delta < -0.05:
        drift_alerts.append(
            "Treatment underperforms control by >5% resolution-rate delta"
        )
    mttr_delta = causal.get("uplift", {}).get("mttrDeltaSeconds")
    if isinstance(mttr_delta, float) and mttr_delta < -60:
        drift_alerts.append("Treatment MTTR exceeds control by more than 60s")

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
        "causalEvaluation": causal,
        "rankingWeights": ranking_weights,
        "dashboard": {
            "statusCounts": dict(status_counter),
            "expiredEntries": expired,
            "activeEntries": status_counter.get("active", 0),
            "resolvedEntries": status_counter.get("resolved", 0),
            "supersededEntries": status_counter.get("superseded", 0),
            "driftAlerts": drift_alerts,
            "slo": {
                "hintPrecisionTarget": 0.2,
                "resolutionRateUpliftTarget": 0.0,
                "mttrDeltaTargetSeconds": 0.0,
            },
        },
    }
    return payload


def _render_dashboard_html(payload: dict[str, Any], *, refresh_seconds: int) -> str:
    initial = json.dumps(payload, sort_keys=True)
    safe_initial = html.escape(initial)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Agent Memory Dashboard</title>
  <style>
    :root {{
      --bg: #f6f8fb;
      --panel: #ffffff;
      --text: #132238;
      --muted: #4f5f77;
      --accent: #0a5a9c;
      --warn: #a64b00;
      --good: #1a6f3b;
      --border: #d8e0ea;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      background: radial-gradient(circle at top right, #dfeefe, var(--bg) 55%);
      color: var(--text);
      padding: 20px;
    }}
    h1 {{ margin: 0 0 6px 0; font-size: 28px; }}
    .sub {{ color: var(--muted); margin-bottom: 16px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 14px;
      box-shadow: 0 8px 20px rgba(20, 42, 75, 0.06);
    }}
    .k {{ color: var(--muted); font-size: 13px; margin-bottom: 4px; }}
    .v {{ font-size: 26px; font-weight: 700; }}
    .ok {{ color: var(--good); }}
    .warn {{ color: var(--warn); }}
    .panels {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 12px;
    }}
    ul {{ margin: 8px 0 0 18px; padding: 0; }}
    li {{ margin-bottom: 4px; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th, td {{
      text-align: left;
      border-bottom: 1px solid var(--border);
      padding: 6px 0;
      vertical-align: top;
    }}
    .foot {{
      margin-top: 12px;
      color: var(--muted);
      font-size: 12px;
    }}
    code {{
      font-family: "Iosevka", "SFMono-Regular", Menlo, monospace;
      background: #f1f5f9;
      border: 1px solid var(--border);
      border-radius: 5px;
      padding: 1px 4px;
    }}
  </style>
</head>
<body>
  <h1>Agent Memory Dashboard</h1>
  <div class="sub" id="subtitle">Live SLO and drift monitor</div>
  <div class="grid" id="kpi-grid"></div>
  <div class="panels">
    <section class="card">
      <h3>Drift Alerts</h3>
      <ul id="alerts"></ul>
    </section>
    <section class="card">
      <h3>Causal A/B</h3>
      <table>
        <tbody id="causal"></tbody>
      </table>
    </section>
    <section class="card">
      <h3>Top Clusters</h3>
      <table>
        <tbody id="clusters"></tbody>
      </table>
    </section>
    <section class="card">
      <h3>Remediation Suggestions</h3>
      <ul id="suggestions"></ul>
    </section>
  </div>
  <div class="foot">
    Refresh every {refresh_seconds}s from <code>/api/report</code>.
  </div>
  <script id="seed-report" type="application/json">{safe_initial}</script>
  <script>
    const rows = (target, pairs) => {{
      target.innerHTML = pairs.map(([k, v]) => `<tr><th>${{k}}</th><td>${{v}}</td></tr>`).join("");
    }};
    const format = (n) => {{
      if (n === null || n === undefined) return "-";
      if (typeof n === "number") return Number.isInteger(n) ? `${{n}}` : n.toFixed(3);
      return `${{n}}`;
    }};
    const render = (data) => {{
      const hint = data.hintEffectiveness || {{}};
      const causal = data.causalEvaluation || {{}};
      const uplift = causal.uplift || {{}};
      const dashboard = data.dashboard || {{}};
      const alerts = dashboard.driftAlerts || [];
      const precision = Number(hint.hintPrecision || 0);
      const assisted = Number(hint.assistedResolutions || 0);
      const ttr = hint.meanTimeToResolutionSeconds;
      const delta = uplift.mttrDeltaSeconds;
      const kpi = [
        ["Hint Precision", precision],
        ["Assisted Resolutions", assisted],
        ["Mean TTR (s)", ttr],
        ["MTTR Delta (s)", delta],
      ];
      document.getElementById("kpi-grid").innerHTML = kpi.map(([k, v]) => {{
        const klass = k === "Hint Precision" && precision < 0.2 ? "warn" : "ok";
        return `<article class="card"><div class="k">${{k}}</div>` +
          `<div class="v ${{klass}}">${{format(v)}}</div></article>`;
      }}).join("");
      document.getElementById("subtitle").textContent = [
        `Entries=${{data.totalEntries || 0}}`,
        `Corrupt=${{data.corruptLines || 0}}`,
        `Updated=${{new Date().toLocaleTimeString()}}`,
      ].join(" | ");

      const alertNode = document.getElementById("alerts");
      if (!alerts.length) {{
        alertNode.innerHTML = "<li>No active drift alerts.</li>";
      }} else {{
        alertNode.innerHTML = alerts.map((msg) => `<li>${{msg}}</li>`).join("");
      }}

      rows(document.getElementById("causal"), [
        ["Sample Size", causal.sampleSize || 0],
        ["Treatment Resolution", format((causal.treatment || {{}}).resolutionRate)],
        ["Control Resolution", format((causal.control || {{}}).resolutionRate)],
        ["Resolution Uplift", format(uplift.resolutionRateDelta)],
        ["MTTR Delta (control-treatment)", format(uplift.mttrDeltaSeconds)],
      ]);

      const clusterNode = document.getElementById("clusters");
      const clusters = data.clusters || [];
      if (!clusters.length) {{
        clusterNode.innerHTML = "<tr><td colspan='2'>No clusters yet.</td></tr>";
      }} else {{
        clusterNode.innerHTML = clusters.slice(0, 8).map((c) =>
          `<tr><th>${{c.failingComponent || "unknown"}} (${{c.occurrences || 0}})</th>` +
          `<td>${{c.likelyRootCause || "-"}}</td></tr>`
        ).join("");
      }}

      const suggestionNode = document.getElementById("suggestions");
      const suggestions = data.remediationSuggestions || [];
      suggestionNode.innerHTML = suggestions.length
        ? suggestions.map((s) => `<li>${{s}}</li>`).join("")
        : "<li>No remediation suggestions yet.</li>";
    }};

    const seed = document.getElementById("seed-report");
    let cached = {{}};
    try {{ cached = JSON.parse(seed.textContent || "{{}}"); }} catch (_error) {{}}
    render(cached);

    const poll = async () => {{
      try {{
        const res = await fetch("/api/report", {{ cache: "no-store" }});
        if (!res.ok) return;
        const data = await res.json();
        render(data);
      }} catch (_error) {{
        // keep last successful render
      }}
    }};
    setInterval(poll, {max(refresh_seconds, 2) * 1000});
  </script>
</body>
</html>
"""


def _command_memory_report(args: argparse.Namespace) -> int:
    payload = _build_memory_report_payload(args.top)
    print(json.dumps(payload, sort_keys=True))
    _record_run(
        command="memory-report",
        status="success",
        details={"top": args.top, **payload},
    )
    return 0


def _command_memory_dashboard(args: argparse.Namespace) -> int:
    payload = _build_memory_report_payload(args.top)
    refresh_seconds = _coerce_int(args.refresh_seconds, 20, min_value=2)
    html_doc = _render_dashboard_html(payload, refresh_seconds=refresh_seconds)

    output_path: Path | None = Path(args.output) if args.output else None
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_doc, encoding="utf-8")

    if args.once:
        result: dict[str, Any] = {
            "status": "rendered",
            "top": args.top,
            "refreshSeconds": refresh_seconds,
            "driftAlerts": payload.get("dashboard", {}).get("driftAlerts", []),
            "hintPrecision": payload.get("hintEffectiveness", {}).get(
                "hintPrecision", 0.0
            ),
        }
        if output_path is not None:
            result["output"] = str(output_path)
        else:
            result["html"] = html_doc
        print(json.dumps(result, sort_keys=True))
        _record_run(
            command="memory-dashboard",
            status="success",
            details={"mode": "once", **result},
        )
        return 0

    class _DashboardHandler(SimpleHTTPRequestHandler):
        def log_message(self, format: str, *values: Any) -> None:
            _ = format, values
            return

        def do_GET(self) -> None:  # noqa: N802
            route = self.path.split("?", 1)[0]
            if route == "/api/report":
                payload_live = _build_memory_report_payload(args.top)
                body = json.dumps(payload_live, sort_keys=True).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if route in {"/", "/index.html"}:
                payload_live = _build_memory_report_payload(args.top)
                html_live = _render_dashboard_html(
                    payload_live,
                    refresh_seconds=refresh_seconds,
                )
                body = html_live.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"not found")

    server = ThreadingHTTPServer((args.host, args.port), _DashboardHandler)
    server_addr = f"http://{args.host}:{server.server_port}"
    print(f"Memory dashboard serving at {server_addr}")
    if output_path is not None:
        print(f"Snapshot written to {output_path}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        _record_run(
            command="memory-dashboard",
            status="success",
            details={
                "mode": "serve",
                "host": args.host,
                "port": server.server_port,
                "top": args.top,
                "refreshSeconds": refresh_seconds,
            },
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
        assignment = _assign_ab_group(signature, context)

        phase_result: dict[str, Any] = {
            "phase": phase.name,
            "signature": signature,
            "command": phase.command,
            "component": phase.failing_component,
            "exit_code": code,
            "abAssignment": assignment,
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
            hint_features = [
                {
                    **(
                        hint.get("rankingFeatures", {})
                        if isinstance(hint.get("rankingFeatures"), dict)
                        else {}
                    ),
                    "hintScore": hint.get("hintScore"),
                    "hintId": hint.get("id"),
                }
                for hint in hints
            ]
            experiment_id = _record_experiment(
                signature=signature,
                assignment=assignment,
                hint_ids=hint_ids,
                hint_features=hint_features,
            )

            should_show_hints = assignment == "treatment"
            shown_hint_total += len(hint_ids) if should_show_hints else 0
            if hint_ids and should_show_hints:
                _increment_hint_counters(hint_ids, shown_delta=1, useful_delta=0)

            if hints and should_show_hints:
                print("Memory Hints")
                for hint in hints:
                    breakdown = hint.get("scoreBreakdown", {})
                    explain = ""
                    if isinstance(breakdown, dict):
                        explain = (
                            f" [semantic={breakdown.get('semantic')}, "
                            f"recency={breakdown.get('recency')}, "
                            f"confidence={breakdown.get('confidence')}, "
                            f"usefulness={breakdown.get('usefulness')}, "
                            f"impact={breakdown.get('impact')}]"
                        )
                    print(f"- {hint.get('title', '(untitled)')}{explain}")

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
                    "hintFeatures": hint_features,
                    "abAssignment": assignment,
                    "experimentId": experiment_id,
                },
            )
            if not added:
                memory_records = _load_jsonl(_memory_path(), kind="memory")
                assert isinstance(memory_records, list)

            phase_result["hint_ids"] = hint_ids
            phase_result["hint_count"] = len(hint_ids)
            phase_result["hint_features"] = hint_features
            phase_result["experiment_id"] = experiment_id
            if args.fail_fast:
                phase_results.append(phase_result)
                break
        else:
            if signature in unresolved:
                prior_hint_ids, latest_failure_ts = _phase_failure_history(
                    runs_records, signature
                )
                unique_hint_ids = sorted(set(prior_hint_ids))
                now = datetime.now(UTC)
                ttr_seconds = None
                if latest_failure_ts is not None:
                    ttr_seconds = max((now - latest_failure_ts).total_seconds(), 0.0)
                experiment = _resolve_experiment(signature, ttr_seconds=ttr_seconds)
                hint_assisted = bool(unique_hint_ids)
                assignment_for_resolution = "unknown"
                if isinstance(experiment, dict):
                    assignment_for_resolution = str(
                        experiment.get("assignment", "unknown")
                    )
                    if assignment_for_resolution == "control":
                        hint_assisted = False
                    if assignment_for_resolution == "treatment":
                        _update_ranking_from_feedback(
                            experiment.get("hintFeatures", []),
                            reward=1.0 if hint_assisted else 0.0,
                        )

                if unique_hint_ids and assignment_for_resolution == "treatment":
                    _increment_hint_counters(
                        unique_hint_ids, shown_delta=0, useful_delta=1
                    )
                    useful_hint_total += len(unique_hint_ids)

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
                        "abAssignment": assignment_for_resolution,
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

    memory_dashboard = sub.add_parser(
        "memory-dashboard",
        help="Serve a live dashboard for agent memory SLOs",
    )
    memory_dashboard.add_argument("--top", type=int, default=10)
    memory_dashboard.add_argument("--host", default="127.0.0.1")
    memory_dashboard.add_argument("--port", type=int, default=8765)
    memory_dashboard.add_argument("--refresh-seconds", type=int, default=20)
    memory_dashboard.add_argument("--output")
    memory_dashboard.add_argument("--once", action="store_true")
    memory_dashboard.set_defaults(handler=_command_memory_dashboard)

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
