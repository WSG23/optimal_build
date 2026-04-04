from __future__ import annotations

from pathlib import Path

from scripts import check_type_ignore_budget


def test_load_baseline_counts_reads_split_budgets(tmp_path: Path) -> None:
    config_path = tmp_path / "guardrails.toml"
    config_path.write_text(
        "[type_ignore]\n"
        "production_baseline = 0\n"
        "backend_tests_baseline = 4\n"
        "tests_baseline = 2\n",
        encoding="utf-8",
    )

    baselines = check_type_ignore_budget.load_baseline_counts(config_path)

    assert baselines == check_type_ignore_budget.BudgetCounts(
        production=0,
        backend_tests=4,
        tests=2,
    )


def test_count_budgeted_suppressions_splits_production_and_tests(
    tmp_path: Path,
) -> None:
    files = {
        "backend/app/service.py": (
            "value = 1  # type: ignore[attr-defined]\n"
            "# mypy: disable-error-code=attr-defined\n"
        ),
        "backend/tests/test_service.py": (
            "# type: ignore[attr-defined]\n" "# mypy: ignore-errors\n"
        ),
        "tests/test_script.py": "# type: ignore[attr-defined]\n",
    }
    for relative_path, content in files.items():
        target = tmp_path / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    counts = check_type_ignore_budget.count_budgeted_suppressions(tmp_path)

    assert counts == check_type_ignore_budget.BudgetCounts(
        production=2,
        backend_tests=2,
        tests=1,
    )


def test_count_budgeted_suppressions_ignores_string_literals(tmp_path: Path) -> None:
    target = tmp_path / "tests" / "test_budget.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        'TEXT = "# type: ignore[attr-defined]\\n# mypy: ignore-errors"\n',
        encoding="utf-8",
    )

    counts = check_type_ignore_budget.count_budgeted_suppressions(tmp_path)

    assert counts == check_type_ignore_budget.BudgetCounts(
        production=0,
        backend_tests=0,
        tests=0,
    )


def test_evaluate_budgets_fails_only_the_scope_that_regressed() -> None:
    ok, messages = check_type_ignore_budget.evaluate_budgets(
        current_counts=check_type_ignore_budget.BudgetCounts(
            production=12,
            backend_tests=5,
            tests=1,
        ),
        baseline_counts=check_type_ignore_budget.BudgetCounts(
            production=0,
            backend_tests=4,
            tests=1,
        ),
        allow_increase=False,
    )

    assert ok is False
    assert messages == [
        (
            "Production suppression baseline is fixed at 0; "
            "new production suppressions are blocked by the staged type guardrails "
            "(current tree count: 12)"
        ),
        "backend/tests suppression count increased from 4 to 5",
        "tests suppression budget ok (1 <= 1)",
    ]


def test_load_baseline_counts_rejects_nonzero_production_baseline(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "guardrails.toml"
    config_path.write_text(
        "[type_ignore]\n"
        "production_baseline = 1\n"
        "backend_tests_baseline = 4\n"
        "tests_baseline = 2\n",
        encoding="utf-8",
    )

    try:
        check_type_ignore_budget.load_baseline_counts(config_path)
    except ValueError as exc:
        assert str(exc) == "type_ignore.production_baseline must remain 0"
    else:  # pragma: no cover - explicit failure branch
        raise AssertionError("Expected nonzero production baseline to be rejected")
