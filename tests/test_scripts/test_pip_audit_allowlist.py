from __future__ import annotations

from datetime import date

from scripts import run_pip_audit_with_allowlist


def test_validate_allowlist_flags_expired_entries() -> None:
    entries = [
        run_pip_audit_with_allowlist.AllowlistEntry(
            vulnerability_id="GHSA-test",
            owner="platform",
            remove_by="2026-03-01",
            reason="test",
        )
    ]

    violations = run_pip_audit_with_allowlist.validate_allowlist(
        entries,
        today=date(2026, 3, 27),
    )
    assert violations == ["expired allowlist entry for GHSA-test: 2026-03-01"]


def test_build_pip_audit_command_includes_allowlisted_vulnerabilities() -> None:
    entries = [
        run_pip_audit_with_allowlist.AllowlistEntry(
            vulnerability_id="GHSA-one",
            owner="platform",
            remove_by="2026-06-30",
            reason="test",
        ),
        run_pip_audit_with_allowlist.AllowlistEntry(
            vulnerability_id="GHSA-two",
            owner="platform",
            remove_by="2026-06-30",
            reason="test",
        ),
    ]

    command = run_pip_audit_with_allowlist.build_pip_audit_command(
        requirements=__import__("pathlib").Path("backend/requirements.txt"),
        entries=entries,
        extra_args=["--desc"],
    )

    assert command[-1] == "--desc"
    assert command.count("--ignore-vuln") == 2
