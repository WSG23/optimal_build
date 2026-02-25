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
python scripts/agents/runner.py memory-list [--limit 25] [--category verify_failure]
python scripts/agents/runner.py memory-report [--top 10]
python scripts/agents/runner.py memory-compact [--keep-last 200] [--dry-run]
```

## JSONL Stores

- `metrics/agent_runs.jsonl`: canonical run metrics and verify triage records.
- `metrics/agent_memory.jsonl`: learned memory entries, dedupe fingerprints, and resolutions.

Environment overrides:

- `AGENT_RUNS_FILE` (or `AGENT_RUNS_PATH`)
- `AGENT_MEMORY_FILE` (or `AGENT_MEMORY_PATH`)

Each verify run persists context fields:

- `changed_files`
- `base_sha`
- `head_sha`
- `diff_hash`

## Learning Loop Behavior

- On verify failure, the runner writes a `verify_failure` memory entry automatically.
- On later success of the same failure signature, the runner writes `verify_resolution`.
- On failure, the runner prints `Memory Hints` from similar historical entries.

## Triage Contract

Verify failures emit machine-readable triage lines:

```text
TRIAGE_JSON: {"phase":"...","failingComponent":"...","likelyRootCause":"...","recommendedRerunCommand":"..."}
```

`failingComponent` maps to repository domains (`backend`, `frontend`, `security`, `deps`, `quality`) with deterministic rerun guidance.
