from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.agents import runner


@pytest.fixture()
def runner_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    runs_path = tmp_path / "agent_runs.jsonl"
    memory_path = tmp_path / "agent_memory.jsonl"
    db_path = tmp_path / "agent_memory.db"
    audit_path = tmp_path / "agent_audit.jsonl"
    model_path = tmp_path / "agent_embedding_model.pkl"
    monkeypatch.setenv("AGENT_RUNS_FILE", str(runs_path))
    monkeypatch.setenv("AGENT_MEMORY_FILE", str(memory_path))
    monkeypatch.setenv("AGENT_DB_FILE", str(db_path))
    monkeypatch.setenv("AGENT_AUDIT_FILE", str(audit_path))
    monkeypatch.setenv("AGENT_EMBED_MODEL_FILE", str(model_path))
    return {
        "runs": runs_path,
        "memory": memory_path,
        "db": db_path,
        "audit": audit_path,
        "model": model_path,
    }


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_memory_add_list_report_and_compact(
    runner_env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = runner.main(
        [
            "memory-add",
            "--title",
            "Lint failure",
            "--details",
            "Ruff flagged import ordering",
            "--category",
            "quality",
            "--source",
            "unit-test",
            "--evidence",
            "tests/test_scripts/test_agent_runner.py",
        ]
    )
    assert exit_code == 0

    records = _read_jsonl(runner_env["memory"])
    assert len(records) == 1
    assert records[0]["title"] == "Lint failure"
    assert records[0]["fingerprint"]

    exit_code = runner.main(["memory-list", "--limit", "5", "--category", "quality"])
    assert exit_code == 0
    listed = capsys.readouterr().out
    assert "Lint failure" in listed

    exit_code = runner.main(["memory-report", "--top", "5"])
    assert exit_code == 0
    report = capsys.readouterr().out
    assert "quality" in report

    runner.main(
        [
            "memory-add",
            "--title",
            "Type check failure",
            "--details",
            "Mypy failed for backend service",
            "--category",
            "backend",
        ]
    )
    runner.main(
        [
            "memory-add",
            "--title",
            "Frontend lint failure",
            "--details",
            "ESLint failed on frontend module",
            "--category",
            "frontend",
        ]
    )
    before_compact = _read_jsonl(runner_env["memory"])
    assert len(before_compact) == 3

    exit_code = runner.main(["memory-compact", "--keep-last", "2"])
    assert exit_code == 0
    after_compact = _read_jsonl(runner_env["memory"])
    assert len(after_compact) == 2
    titles = [entry["title"] for entry in after_compact]
    assert titles == ["Type check failure", "Frontend lint failure"]


def test_memory_dedupe_and_fingerprint_behavior(
    runner_env: dict[str, Path],
) -> None:
    args = [
        "memory-add",
        "--title",
        "Persistent lint failure",
        "--details",
        "ruff E501",
        "--category",
        "quality",
        "--fingerprint",
        "lint-ruff-e501",
    ]
    assert runner.main(args) == 0
    assert runner.main(args) == 0

    records = _read_jsonl(runner_env["memory"])
    assert len(records) == 1
    assert records[0]["fingerprint"] == "lint-ruff-e501"

    assert (
        runner.main(
            [
                "memory-add",
                "--title",
                "Different issue",
                "--details",
                "frontend typecheck",
                "--category",
                "frontend",
                "--fingerprint",
                "frontend-tsc",
            ]
        )
        == 0
    )
    records = _read_jsonl(runner_env["memory"])
    assert len(records) == 2


def test_verify_failure_then_resolution_transition(
    runner_env: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    phase = runner.VerifyPhase(
        name="backend-lint",
        command="make lint",
        failing_component="backend",
        likely_root_cause="Lint violation",
        recommended_rerun_command="make lint",
    )
    monkeypatch.setitem(runner.VERIFY_PHASES_BY_MODE, "quick", [phase])
    outcomes = iter([1, 0])

    def _fake_exec(
        command: str,
        *,
        dry_run: bool,
    ) -> tuple[int, str, str]:
        assert command == "make lint"
        _ = dry_run
        code = next(outcomes)
        if code != 0:
            return (code, "", "lint failed")
        return (0, "lint pass", "")

    monkeypatch.setattr(runner, "_execute_command", _fake_exec)

    assert runner.main(["verify", "--mode", "quick", "--fail-fast"]) == 1
    assert runner.main(["verify", "--mode", "quick", "--fail-fast"]) == 0

    records = _read_jsonl(runner_env["memory"])
    categories = [entry["category"] for entry in records]
    assert "verify_failure" in categories
    assert "verify_resolution" in categories


def test_verify_emits_triage_with_precise_rerun_command(
    runner_env: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    phase = runner.VerifyPhase(
        name="frontend-lint",
        command="pnpm -C frontend lint",
        failing_component="frontend",
        likely_root_cause="ESLint/type violation in frontend code",
        recommended_rerun_command="pnpm -C frontend lint",
    )
    monkeypatch.setitem(runner.VERIFY_PHASES_BY_MODE, "quick", [phase])

    def _fake_exec(
        command: str,
        *,
        dry_run: bool,
    ) -> tuple[int, str, str]:
        assert command == "pnpm -C frontend lint"
        _ = dry_run
        return (2, "", "eslint failure")

    monkeypatch.setattr(runner, "_execute_command", _fake_exec)

    assert runner.main(["verify", "--mode", "quick", "--fail-fast"]) == 1
    output = capsys.readouterr().out
    triage_line = next(
        line for line in output.splitlines() if line.startswith("TRIAGE_JSON:")
    )
    triage = json.loads(triage_line.split("TRIAGE_JSON:", 1)[1].strip())
    assert triage["phase"] == "frontend-lint"
    assert triage["failingComponent"] == "frontend"
    assert triage["recommendedRerunCommand"] == "pnpm -C frontend lint"
    assert "ESLint" in triage["likelyRootCause"]


def test_verify_failure_prints_memory_hints(
    runner_env: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    existing = {
        "id": "existing-entry",
        "timestamp": "2026-02-20T01:02:03Z",
        "title": "Previous frontend lint issue",
        "details": "pnpm lint failed for the same module",
        "category": "verify_failure",
        "source": "runner.verify",
        "fingerprint": "fp-frontend-lint",
        "resolved": False,
    }
    runner_env["memory"].write_text(json.dumps(existing) + "\n")

    phase = runner.VerifyPhase(
        name="frontend-lint",
        command="pnpm -C frontend lint",
        failing_component="frontend",
        likely_root_cause="ESLint/type violation in frontend code",
        recommended_rerun_command="pnpm -C frontend lint",
    )
    monkeypatch.setitem(runner.VERIFY_PHASES_BY_MODE, "quick", [phase])
    monkeypatch.setattr(
        runner,
        "_execute_command",
        lambda command, *, dry_run: (3, "", "eslint failure"),
    )

    assert runner.main(["verify", "--mode", "quick", "--fail-fast"]) == 1
    output = capsys.readouterr().out
    assert "Memory Hints" in output
    assert "Previous frontend lint issue" in output


def test_verify_control_holdout_does_not_print_memory_hints(
    runner_env: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _ = runner_env
    runner._add_memory_entry(
        title="Prior backend hint",
        details="Mypy import contract mismatch",
        category="verify_failure",
        source="runner.verify",
        fingerprint="fp-control-holdout",
        metadata={"triage": {"failingComponent": "backend"}},
    )

    phase = runner.VerifyPhase(
        name="backend-typecheck",
        command="make typecheck-backend",
        failing_component="backend",
        likely_root_cause="Mypy import contract mismatch",
        recommended_rerun_command="make typecheck-backend",
    )
    monkeypatch.setitem(runner.VERIFY_PHASES_BY_MODE, "quick", [phase])
    monkeypatch.setattr(
        runner,
        "_execute_command",
        lambda command, *, dry_run: (1, "", "typecheck failed"),
    )
    monkeypatch.setattr(
        runner, "_assign_ab_group", lambda signature, context: "control"
    )

    assert runner.main(["verify", "--mode", "quick", "--fail-fast"]) == 1
    output = capsys.readouterr().out
    assert "Memory Hints" not in output
