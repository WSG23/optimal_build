from __future__ import annotations

from datetime import date
from pathlib import Path

from scripts import check_warning_allowlist


def test_extract_pytest_filterwarnings_reads_multiline_ini(tmp_path: Path) -> None:
    pytest_ini = tmp_path / "pytest.ini"
    pytest_ini.write_text(
        (
            "[pytest]\n"
            "filterwarnings =\n"
            "    ignore:first:DeprecationWarning\n"
            "    ignore:second:UserWarning\n"
        ),
        encoding="utf-8",
    )

    assert check_warning_allowlist.extract_pytest_filterwarnings(pytest_ini) == [
        "ignore:first:DeprecationWarning",
        "ignore:second:UserWarning",
    ]


def test_evaluate_allowlist_reports_missing_and_unused_entries() -> None:
    entries = [
        check_warning_allowlist.AllowlistEntry(
            line_no=1,
            filter_spec="ignore:first:DeprecationWarning",
            owner="backend",
            remove_by="2026-06-30",
            reason="test",
        ),
        check_warning_allowlist.AllowlistEntry(
            line_no=2,
            filter_spec="ignore:unused:DeprecationWarning",
            owner="backend",
            remove_by="2026-06-30",
            reason="test",
        ),
    ]

    expired, invalid_dates, missing, unused = (
        check_warning_allowlist.evaluate_allowlist(
            entries=entries,
            filterwarnings=[
                "ignore:first:DeprecationWarning",
                "ignore:missing:UserWarning",
            ],
            today=date(2026, 3, 27),
        )
    )

    assert expired == []
    assert invalid_dates == []
    assert missing == ["ignore:missing:UserWarning"]
    assert unused == ["ignore:unused:DeprecationWarning"]


def test_write_summary_ends_with_single_newline(tmp_path: Path) -> None:
    summary = tmp_path / "warning-summary.md"

    check_warning_allowlist.write_summary(
        summary,
        entries=[],
        expired=[],
        invalid_date_lines=[],
        missing=[],
        unused=[],
    )

    contents = summary.read_text(encoding="utf-8")
    assert contents.endswith("Unused allowlist entries: **0**\n")
    assert not contents.endswith("\n\n")
