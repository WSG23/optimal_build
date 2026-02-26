# Agent Memory and Learning Loop

This repository uses a canonical agent runner for Codex, Claude, and Gemini workflows:

```bash
python scripts/agents/runner.py
```

## Commands

```bash
# Verification
python scripts/agents/runner.py verify --mode {quick,full,pre-pr,integration,audit,pre-deploy}
python scripts/agents/runner.py verify --mode pre-pr --fail-fast
python scripts/agents/runner.py verify --mode integration --dry-run

# Memory operations
python scripts/agents/runner.py memory-add --title "..." --details "..." [--category ...] [--source ...] [--evidence ...] [--fingerprint ...]
python scripts/agents/runner.py memory-list [--limit 25] [--category verify_failure] [--query "..."] [--component backend]
python scripts/agents/runner.py memory-report [--top 10]
python scripts/agents/runner.py memory-dashboard [--top 10] [--host 127.0.0.1] [--port 8765]
python scripts/agents/runner.py memory-compact [--keep-last 200] [--dry-run] [--min-confidence 0.1] [--min-usefulness 0.0]
```

## JSONL Stores

- `metrics/agent_runs.jsonl`: canonical run metrics and verify triage records.
- `metrics/agent_memory.jsonl`: learned memory entries, dedupe fingerprints, and resolutions.

Environment overrides:

- `AGENT_RUNS_FILE` (or `AGENT_RUNS_PATH`)
- `AGENT_MEMORY_FILE` (or `AGENT_MEMORY_PATH`)
- `AGENT_DB_FILE` (or `AGENT_DB_PATH`) for durable SQLite state (`metrics/agent_memory.db`)
- `AGENT_AUDIT_FILE` (or `AGENT_AUDIT_PATH`) for audit append-only history
- `AGENT_MEMORY_ENCRYPTION_KEY` to encrypt redacted title/details/evidence at rest

Each verify run persists context fields:

- `changed_files`
- `base_sha`
- `head_sha`
- `diff_hash`

## Learning Loop Behavior

- On verify failure, the runner writes a `verify_failure` memory entry automatically.
- On later success of the same failure signature, the runner writes `verify_resolution`.
- On failure, the runner prints `Memory Hints` from similar historical entries.
- Hint retrieval uses semantic similarity + recency + confidence + impact + historical usefulness.
- Hint false-positive control applies semantic and score thresholds (with adaptive tuning from prior outcomes).
- Hint impressions and useful outcomes are tracked and fed back into future hint ranking.

## Lifecycle + Reliability

- Memory records include schema versioning (`schemaVersion`) and per-entry confidence, impact, usefulness, and TTL.
- Expired/low-value entries can be pruned by `memory-compact` with confidence/usefulness gates.
- Conflict resolution is automatic for failure/resolution regressions (for example, a resolution can be marked superseded).
- PII is redacted before persistence; optional encryption-at-rest can be enabled via `AGENT_MEMORY_ENCRYPTION_KEY`.
- Durable indexed storage uses SQLite transactions + WAL for concurrent writers, with JSONL retained for portability.
- JSONL readers tolerate corruption, quarantine bad lines to `*.corrupt`, and continue processing valid entries.
- File lock + atomic write are used for safer concurrent updates.

## Cross-run Intelligence

`memory-report` includes:

- recurring failure clusters with remediation suggestions,
- root-cause trend summaries and flapping fingerprints,
- hint effectiveness metrics (precision, assisted resolutions, mean time-to-resolution),
- dashboard health counts (active/resolved/superseded/expired/corrupt).
- causal holdout metrics (`treatment` vs `control`) and ranking weight state.

`memory-dashboard` serves a live HTML monitor with SLOs and drift alerts sourced from `/api/report`.

## Triage Contract

Verify failures emit machine-readable triage lines:

```text
TRIAGE_JSON: {"phase":"...","failingComponent":"...","likelyRootCause":"...","recommendedRerunCommand":"..."}
```

`failingComponent` maps to repository domains (`backend`, `frontend`, `security`, `deps`, `quality`) with deterministic rerun guidance.
