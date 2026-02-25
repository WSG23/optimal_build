from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_pre_push_routes_through_canonical_agent_runner() -> None:
    hook = (ROOT / ".git-hooks" / "pre-push").read_text()
    assert "scripts/agents/runner.py verify --mode pre-pr" in hook
    assert "AGENT_BASE_SHA" in hook
    assert "AGENT_HEAD_SHA" in hook
    assert "AGENT_CHANGED_FILES" in hook
    assert "AGENT_DIFF_HASH" in hook


def test_ci_routes_through_canonical_agent_runner_and_uploads_artifacts() -> None:
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
    assert "scripts/agents/runner.py verify --mode integration" in ci
    assert "metrics/agent_runs.jsonl" in ci
    assert "metrics/agent_memory.jsonl" in ci
