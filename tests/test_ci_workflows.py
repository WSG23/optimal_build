from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"


def _load_workflow(path: Path) -> dict:
    workflow = yaml.safe_load(path.read_text()) or {}
    # PyYAML follows YAML 1.1 and treats the GitHub Actions `on` key as a
    # boolean. Normalize it so the assertions read like the workflow files.
    if True in workflow and "on" not in workflow:
        workflow["on"] = workflow.pop(True)
    return workflow


def _workflow_files() -> list[Path]:
    return sorted(
        path for path in WORKFLOW_DIR.iterdir() if path.suffix in {".yml", ".yaml"}
    )


def test_workflows_cancel_stale_runs() -> None:
    for path in _workflow_files():
        workflow = _load_workflow(path)
        concurrency = workflow.get("concurrency")

        assert isinstance(concurrency, dict), f"{path.name} must define concurrency"
        assert (
            concurrency.get("group") == "${{ github.workflow }}-${{ github.ref }}"
        ), f"{path.name} must group concurrency by workflow and ref"
        assert (
            concurrency.get("cancel-in-progress") is True
        ), f"{path.name} must cancel stale in-progress runs"


def test_all_workflow_jobs_have_timeouts() -> None:
    for path in _workflow_files():
        workflow = _load_workflow(path)
        for job_name, job in workflow.get("jobs", {}).items():
            timeout = job.get("timeout-minutes")
            assert isinstance(timeout, int), f"{path.name}:{job_name} needs a timeout"
            assert 1 <= timeout <= 60, f"{path.name}:{job_name} timeout is too high"


def test_artifact_uploads_have_short_retention() -> None:
    for path in _workflow_files():
        workflow = _load_workflow(path)
        for job_name, job in workflow.get("jobs", {}).items():
            for step in job.get("steps", []):
                if step.get("uses") != "actions/upload-artifact@v4":
                    continue

                with_config = step.get("with", {})
                retention_days = with_config.get("retention-days")
                assert isinstance(
                    retention_days, int
                ), f"{path.name}:{job_name}:{step.get('name')} must set retention-days"
                assert (
                    retention_days <= 7
                ), f"{path.name}:{job_name}:{step.get('name')} keeps artifacts too long"


def test_lint_workflow_keeps_unit_tests_on_pull_requests() -> None:
    workflow = _load_workflow(WORKFLOW_DIR / "lint.yml")
    lint_job = workflow["jobs"]["lint-tests"]

    pytest_commands = [
        step.get("run", "").strip()
        for step in lint_job["steps"]
        if "pytest" in step.get("run", "")
    ]

    assert "pytest -q" in pytest_commands


def test_main_ci_static_gates_are_not_serialized() -> None:
    workflow = _load_workflow(WORKFLOW_DIR / "ci.yml")
    jobs = workflow["jobs"]

    assert jobs["typecheck"]["needs"] == "changes"
    assert jobs["build"]["needs"] == "changes"
    assert "lint" not in jobs["tests"]["needs"]
    assert "typecheck" not in jobs["tests"]["needs"]


def test_frontend_e2e_does_not_start_duplicate_backend() -> None:
    workflow = _load_workflow(WORKFLOW_DIR / "ci.yml")
    test_steps = workflow["jobs"]["tests"]["steps"]
    step_names = {step.get("name") for step in test_steps}

    assert "Launch backend API for E2E tests" not in step_names
    assert "Wait for backend readiness (E2E)" not in step_names


def test_playwright_generated_artifacts_are_ignored() -> None:
    gitignore = (REPO_ROOT / ".gitignore").read_text().splitlines()

    for pattern in (
        "frontend/playwright-report/",
        "frontend/test-results/",
        ".playwright-browsers/*",
        "!.playwright-browsers/",
        "!.playwright-browsers/README.md",
        "!.playwright-browsers/browsers.json",
    ):
        assert pattern in gitignore
