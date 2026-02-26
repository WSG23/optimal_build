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


def test_semantic_hint_ranking_prefers_relevant_entries(
    runner_env: dict[str, Path],
) -> None:
    runner._add_memory_entry(
        title="Backend typecheck import issue",
        details="Mypy import contract regression in backend services package",
        category="verify_failure",
        source="runner.verify",
        fingerprint="fp-backend-similar",
        metadata={"triage": {"failingComponent": "backend"}},
    )
    runner._add_memory_entry(
        title="Frontend button spacing",
        details="CSS spacing mismatch on frontend dashboard",
        category="verify_failure",
        source="runner.verify",
        fingerprint="fp-frontend-unrelated",
        metadata={"triage": {"failingComponent": "frontend"}},
    )

    records = runner._load_jsonl(runner_env["memory"], kind="memory")
    assert isinstance(records, list)

    hints = runner._find_memory_hints(
        records,
        fingerprint="no-match",
        failing_component="backend",
        query_text="backend mypy import contract regression",
        runs_records=[],
        limit=3,
    )
    assert hints
    assert str(hints[0]["title"]) == "Backend typecheck import issue"
    assert all(
        "Frontend button spacing" != str(item.get("title", "")) for item in hints
    )


def test_memory_lifecycle_compact_prunes_expired_and_low_usefulness(
    runner_env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    runner._add_memory_entry(
        title="Expired issue",
        details="Old stale hint",
        category="verify_failure",
        source="runner.verify",
        fingerprint="fp-expired",
    )
    runner._add_memory_entry(
        title="Low usefulness issue",
        details="Never helped",
        category="verify_failure",
        source="runner.verify",
        fingerprint="fp-low-usefulness",
    )
    runner._add_memory_entry(
        title="Healthy issue",
        details="Frequently useful",
        category="verify_failure",
        source="runner.verify",
        fingerprint="fp-healthy",
    )

    records = _read_jsonl(runner_env["memory"])
    for record in records:
        if record["fingerprint"] == "fp-expired":
            record["expiresAt"] = "2020-01-01T00:00:00Z"
        if record["fingerprint"] == "fp-low-usefulness":
            record["hintShownCount"] = 8
            record["hintUsefulCount"] = 0
            record["usefulnessScore"] = 0.0
            record["occurrenceCount"] = 1
        if record["fingerprint"] == "fp-healthy":
            record["hintShownCount"] = 10
            record["hintUsefulCount"] = 8
            record["usefulnessScore"] = 0.8
            record["occurrenceCount"] = 2
    runner._atomic_write_jsonl(
        runner_env["memory"],
        [
            runner._normalize_memory_record(item, now=runner.datetime.now(runner.UTC))
            for item in records
        ],
    )

    assert (
        runner.main(
            [
                "memory-compact",
                "--keep-last",
                "10",
                "--min-confidence",
                "0.2",
                "--min-usefulness",
                "0.3",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["removedByReason"]["expired"] >= 1
    assert payload["removedByReason"]["low_usefulness"] >= 1

    compacted = _read_jsonl(runner_env["memory"])
    assert len(compacted) == 1
    assert compacted[0]["fingerprint"] == "fp-healthy"


def test_conflict_resolution_marks_prior_resolution_superseded(
    runner_env: dict[str, Path],
) -> None:
    fingerprint = "fp-conflict"
    runner._add_memory_entry(
        title="Failure first",
        details="backend failed",
        category="verify_failure",
        source="runner.verify",
        fingerprint=fingerprint,
    )
    runner._add_memory_entry(
        title="Resolution",
        details="backend passed",
        category="verify_resolution",
        source="runner.verify",
        fingerprint=fingerprint,
        resolved=True,
    )
    runner._add_memory_entry(
        title="Failure regressed",
        details="backend failed again",
        category="verify_failure",
        source="runner.verify",
        fingerprint=fingerprint,
    )

    records = _read_jsonl(runner_env["memory"])
    resolution = next(
        entry
        for entry in records
        if entry["fingerprint"] == fingerprint
        and entry["category"] == "verify_resolution"
    )
    assert resolution["status"] == "superseded"


def test_memory_report_contains_clusters_trends_and_feedback(
    runner_env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    triage = {
        "failingComponent": "backend",
        "likelyRootCause": "Mypy import contract regression",
        "recommendedRerunCommand": "make typecheck-backend",
    }
    runner._add_memory_entry(
        title="Failure A",
        details="backend fail",
        category="verify_failure",
        source="runner.verify",
        fingerprint="fp-a",
        metadata={"triage": triage},
    )
    runner._add_memory_entry(
        title="Failure B",
        details="backend fail again",
        category="verify_failure",
        source="runner.verify",
        fingerprint="fp-b",
        metadata={"triage": triage},
    )
    runner._add_memory_entry(
        title="Resolution A",
        details="fixed",
        category="verify_resolution",
        source="runner.verify",
        fingerprint="fp-a",
        resolved=True,
        metadata={"hintAssisted": True, "timeToResolutionSeconds": 120.0},
    )
    runner._record_run(
        command="verify",
        status="failed",
        details={"hintStats": {"shown": 3, "useful": 1}, "phase_results": []},
        context={"changed_files": []},
    )

    assert runner.main(["memory-report", "--top", "5"]) == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["clusters"]
    assert payload["trends"]["topRootCauses"]
    assert payload["remediationSuggestions"]
    assert "hintPrecision" in payload["hintEffectiveness"]


def test_corrupt_jsonl_lines_are_tolerated_and_counted(
    runner_env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    runner_env["memory"].write_text(
        "this is not json\n"
        + json.dumps(
            {
                "id": "ok-line",
                "timestamp": "2026-01-01T00:00:00Z",
                "title": "Valid",
                "details": "Valid line",
                "category": "verify_failure",
                "source": "runner.verify",
                "fingerprint": "fp-ok",
                "resolved": False,
            }
        )
        + "\n"
    )
    assert runner.main(["memory-report", "--top", "3"]) == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["corruptLines"] >= 1


def test_outcome_feedback_marks_hint_useful_after_resolution(
    runner_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    phase = runner.VerifyPhase(
        name="backend-typecheck",
        command="make typecheck-backend",
        failing_component="backend",
        likely_root_cause="Mypy import contract regression",
        recommended_rerun_command="make typecheck-backend",
    )
    monkeypatch.setitem(runner.VERIFY_PHASES_BY_MODE, "quick", [phase])

    signature = runner._failure_signature("quick", phase)
    runner._add_memory_entry(
        title="Previous helpful hint",
        details="Mypy import contract regression in backend service",
        category="verify_failure",
        source="runner.verify",
        fingerprint=signature,
        metadata={"triage": {"failingComponent": "backend"}},
    )

    outcomes = iter([1, 0])

    def _fake_exec(command: str, *, dry_run: bool) -> tuple[int, str, str]:
        _ = command, dry_run
        code = next(outcomes)
        if code:
            return (1, "", "typecheck failed")
        return (0, "typecheck ok", "")

    monkeypatch.setattr(runner, "_execute_command", _fake_exec)

    assert runner.main(["verify", "--mode", "quick", "--fail-fast"]) == 1
    assert runner.main(["verify", "--mode", "quick", "--fail-fast"]) == 0

    records = _read_jsonl(runner_env["memory"])
    hint_entry = next(
        entry
        for entry in records
        if entry["fingerprint"] == signature and entry["category"] == "verify_failure"
    )
    assert int(hint_entry["hintShownCount"]) >= 1
    assert int(hint_entry["hintUsefulCount"]) >= 1

    resolution_entry = next(
        entry
        for entry in records
        if entry["fingerprint"] == signature
        and entry["category"] == "verify_resolution"
    )
    metadata = resolution_entry.get("metadata", {})
    assert metadata.get("hintAssisted") is True


def test_governance_redacts_pii_and_writes_audit(
    runner_env: dict[str, Path],
) -> None:
    runner._add_memory_entry(
        title="PII leak incident",
        details="Contact john.doe@example.com or +1 (415) 555-1212 and SSN 123-45-6789",
        category="verify_failure",
        source="runner.verify",
        fingerprint="pii-fp",
        evidence="Sensitive identifier",
    )

    raw_line = runner_env["memory"].read_text(encoding="utf-8").splitlines()[0]
    assert "john.doe@example.com" not in raw_line
    assert "123-45-6789" not in raw_line
    assert "[REDACTED_EMAIL]" in raw_line
    assert "[REDACTED_PHONE]" in raw_line

    assert runner_env["audit"].exists()
    audit_entries = _read_jsonl(runner_env["audit"])
    assert audit_entries
    assert str(audit_entries[-1].get("action")) in {"create", "update"}


def test_hint_scores_include_explainability_breakdown(
    runner_env: dict[str, Path],
) -> None:
    runner._add_memory_entry(
        title="Backend import failure",
        details="Mypy import contract mismatch in backend handlers",
        category="verify_failure",
        source="runner.verify",
        fingerprint="fp-breakdown",
        metadata={"triage": {"failingComponent": "backend"}},
    )
    records = runner._load_jsonl(runner_env["memory"], kind="memory")
    assert isinstance(records, list)

    hints = runner._find_memory_hints(
        records,
        fingerprint="fp-breakdown",
        failing_component="backend",
        query_text="mypy import contract mismatch",
        runs_records=[],
        limit=1,
    )
    assert hints
    breakdown = hints[0].get("scoreBreakdown")
    assert isinstance(breakdown, dict)
    assert "semantic" in breakdown
    assert "recency" in breakdown
    assert "confidence" in breakdown
    assert "usefulness" in breakdown
    assert "impact" in breakdown


def test_memory_dashboard_once_writes_html(
    runner_env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    runner._add_memory_entry(
        title="Lint drift",
        details="Formatter mismatch in CI",
        category="verify_failure",
        source="runner.verify",
        fingerprint="fp-dashboard",
    )
    output_path = runner_env["memory"].parent / "dashboard.html"
    assert (
        runner.main(
            [
                "memory-dashboard",
                "--top",
                "5",
                "--once",
                "--output",
                str(output_path),
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["status"] == "rendered"
    assert output_path.exists()
    html_doc = output_path.read_text(encoding="utf-8")
    assert "Agent Memory Dashboard" in html_doc
    assert "/api/report" in html_doc


def test_ranking_weights_update_from_feedback(runner_env: dict[str, Path]) -> None:
    _ = runner_env
    baseline = runner._load_ranking_weights()
    runner._update_ranking_from_feedback(
        [
            {
                "semanticSimilarity": 0.8,
                "recencyWeight": 0.6,
                "confidence": 0.7,
                "usefulness": 0.5,
                "impactWeight": 0.4,
            }
        ],
        reward=1.0,
    )
    updated = runner._load_ranking_weights()
    assert updated != baseline
    assert abs(sum(updated) - 1.0) < 1e-6


def test_causal_evaluation_reports_holdout_uplift(runner_env: dict[str, Path]) -> None:
    _ = runner_env
    runner._record_experiment(
        signature="sig-treatment",
        assignment="treatment",
        hint_ids=["a"],
        hint_features=[{"semanticSimilarity": 0.9}],
    )
    runner._record_experiment(
        signature="sig-control",
        assignment="control",
        hint_ids=["b"],
        hint_features=[{"semanticSimilarity": 0.2}],
    )
    runner._resolve_experiment("sig-treatment", ttr_seconds=40.0)
    runner._resolve_experiment("sig-control", ttr_seconds=110.0)

    causal = runner._causal_evaluation(5)
    assert causal["sampleSize"] >= 2
    assert "uplift" in causal
    assert "resolutionRateDelta" in causal["uplift"]
