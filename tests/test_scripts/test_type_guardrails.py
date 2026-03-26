from __future__ import annotations

from pathlib import Path

from scripts import check_type_guardrails

TYPE_IGNORE_ATTR_DEFINED = "type: " "ignore[attr-defined]"


def test_find_mypy_ini_guardrail_violations_flags_unexpected_section() -> None:
    config_text = """
[mypy]
python_version = 3.11

[mypy-allowed]
ignore_errors = True

[mypy-unexpected]
ignore_errors = True
"""
    violations = check_type_guardrails.find_mypy_ini_guardrail_violations(
        config_text,
        allowed_ignore_sections={"mypy-allowed"},
    )
    assert violations == ["Unexpected mypy.ini ignore_errors section: mypy-unexpected"]


def test_parse_added_line_numbers_maps_python_additions() -> None:
    diff_text = """
diff --git a/example.py b/example.py
index 123..456 100644
--- a/example.py
+++ b/example.py
@@ -1,0 +1,2 @@
+value = 1
+result = value  # {TYPE_IGNORE_ATTR_DEFINED}
""".strip()
    assert check_type_guardrails.parse_added_line_numbers(diff_text) == {
        "example.py": {1, 2}
    }


def test_find_unjustified_type_ignore_violations_requires_metadata(
    tmp_path: Path,
) -> None:
    target = tmp_path / "backend" / "example.py"
    target.parent.mkdir(parents=True)
    target.write_text(
        f"value = 1\nresult = value  # {TYPE_IGNORE_ATTR_DEFINED}\n",
        encoding="utf-8",
    )

    violations = check_type_guardrails.find_unjustified_type_ignore_violations(
        tmp_path,
        {"backend/example.py": {2}},
        required_metadata_keys=("owner", "expires", "reason"),
    )
    assert violations == [
        "backend/example.py:2 adds `type: ignore[...]` without owner/expires/reason metadata"
    ]


def test_find_unjustified_type_ignore_violations_accepts_previous_line_metadata(
    tmp_path: Path,
) -> None:
    target = tmp_path / "backend" / "example.py"
    target.parent.mkdir(parents=True)
    target.write_text(
        "# type-ignore-meta: owner=platform expires=2026-06-30 reason=test\n"
        f"result = value  # {TYPE_IGNORE_ATTR_DEFINED}\n",
        encoding="utf-8",
    )

    violations = check_type_guardrails.find_unjustified_type_ignore_violations(
        tmp_path,
        {"backend/example.py": {2}},
        required_metadata_keys=("owner", "expires", "reason"),
    )
    assert violations == []
