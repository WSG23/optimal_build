from __future__ import annotations

from datetime import date
from pathlib import Path

from backend.scripts import check_runtime_budget


def test_parse_junit_testcases_uses_file_attribute(tmp_path: Path) -> None:
    junit_xml = tmp_path / "junit.xml"
    junit_xml.write_text(
        """
<testsuite tests="1" failures="0" time="1.25">
  <testcase
    classname="backend.tests.test_sample"
    file="backend/tests/test_sample.py"
    name="test_fast"
    time="1.25"
  />
</testsuite>
""".strip(),
        encoding="utf-8",
    )

    cases = check_runtime_budget.parse_junit_testcases(junit_xml)

    assert cases == [
        check_runtime_budget.TestCaseTiming(
            nodeid="backend/tests/test_sample.py::test_fast",
            seconds=1.25,
            classname="backend.tests.test_sample",
            name="test_fast",
        )
    ]


def test_evaluate_runtime_budget_flags_total_and_case_regressions() -> None:
    config = check_runtime_budget.RuntimeBudgetConfig(
        max_total_seconds=3.0,
        default_test_case_seconds=1.0,
        max_slowest_tests=5,
    )
    cases = [
        check_runtime_budget.TestCaseTiming(
            nodeid="backend/tests/test_api.py::test_slow",
            seconds=2.2,
            classname="backend.tests.test_api",
            name="test_slow",
        ),
        check_runtime_budget.TestCaseTiming(
            nodeid="backend/tests/test_api.py::test_other",
            seconds=1.1,
            classname="backend.tests.test_api",
            name="test_other",
        ),
    ]

    report = check_runtime_budget.evaluate_runtime_budget(
        cases,
        config,
        today=date(2026, 3, 27),
    )

    assert report.total_seconds == 3.3
    assert any(
        "Pytest runtime budget exceeded" in failure for failure in report.failures
    )
    assert any(
        "test_slow exceeded runtime budget" in failure for failure in report.failures
    )
    assert any(
        "test_other exceeded runtime budget" in failure for failure in report.failures
    )


def test_evaluate_runtime_budget_honours_allowance_until_expiry() -> None:
    config = check_runtime_budget.RuntimeBudgetConfig(
        max_total_seconds=10.0,
        default_test_case_seconds=1.0,
        max_slowest_tests=5,
        allowances=(
            check_runtime_budget.RuntimeBudgetAllowance(
                nodeid="backend/tests/test_api.py::test_slow",
                max_seconds=3.0,
                owner="backend",
                remove_by="2026-06-30",
                reason="Temporary slow integration path",
            ),
        ),
    )
    cases = [
        check_runtime_budget.TestCaseTiming(
            nodeid="backend/tests/test_api.py::test_slow",
            seconds=2.2,
            classname="backend.tests.test_api",
            name="test_slow",
        )
    ]

    report = check_runtime_budget.evaluate_runtime_budget(
        cases,
        config,
        today=date(2026, 3, 27),
    )

    assert report.failures == ()


def test_evaluate_runtime_budget_flags_expired_allowances() -> None:
    config = check_runtime_budget.RuntimeBudgetConfig(
        max_total_seconds=10.0,
        default_test_case_seconds=1.0,
        max_slowest_tests=5,
        allowances=(
            check_runtime_budget.RuntimeBudgetAllowance(
                nodeid="backend/tests/test_api.py::test_slow",
                max_seconds=3.0,
                owner="backend",
                remove_by="2026-03-01",
                reason="Temporary slow integration path",
            ),
        ),
    )
    cases = [
        check_runtime_budget.TestCaseTiming(
            nodeid="backend/tests/test_api.py::test_slow",
            seconds=2.2,
            classname="backend.tests.test_api",
            name="test_slow",
        )
    ]

    report = check_runtime_budget.evaluate_runtime_budget(
        cases,
        config,
        today=date(2026, 3, 27),
    )

    assert report.expired_allowances == (
        "backend/tests/test_api.py::test_slow allowance expired on 2026-03-01",
    )
