import re
import sys
from pathlib import Path

try:  # Optional dependency; script should still run without YAML
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    yaml = None  # type: ignore


def _normalise(path: Path) -> str:
    return str(path).replace("\\", "/").lstrip("./")


def load_exceptions() -> set[str]:
    repo_root = Path(__file__).resolve().parent.parent
    cfg = repo_root / ".coding-rules-exceptions.yml"
    if not cfg.exists():
        return set()

    if yaml is not None:
        data = yaml.safe_load(cfg.read_text()) or {}
        exceptions = data.get("exceptions", {}) or {}
        rule_entries = exceptions.get("rule_1_migrations", []) or []
        return {_normalise(Path(entry)) for entry in rule_entries}

    # Fallback parser for simple YAML structures when PyYAML is unavailable.
    entries: set[str] = set()
    current_rule: str | None = None
    in_exceptions = False

    for raw_line in cfg.read_text().splitlines():
        no_comment = raw_line.split("#", 1)[0].rstrip()
        if not no_comment.strip():
            continue
        stripped = no_comment.strip()

        if not no_comment.startswith(" "):
            in_exceptions = stripped == "exceptions:"
            current_rule = None
            continue

        if not in_exceptions:
            continue

        if not stripped.startswith("- ") and stripped.endswith(":"):
            current_rule = stripped.rstrip(":")
            continue

        if current_rule == "rule_1_migrations" and stripped.startswith("- "):
            path = stripped[2:].strip()
            if path:
                entries.add(_normalise(Path(path)))
    return entries


repo_root = Path(__file__).resolve().parent.parent
root = repo_root / "backend" / "migrations" / "versions"
paths = sorted(root.glob("*.py"))
exceptions = load_exceptions()

enum_call_rx = re.compile(
    r"\b(?:sa\.Enum|postgresql\.ENUM)\s*\((?P<args>.*?)\)", re.DOTALL
)
enum_name_rx = re.compile(r"name\s*=\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]")
create_false_rx = re.compile(r"create_type\s*=\s*False")
upgrade_def_rx = re.compile(r"(?m)^\s*def\s+upgrade\s*\(\s*\)\s*:\s*$")
guard_block_rx = re.compile(
    r"SELECT\s+1\s+FROM\s+pg_type\s+WHERE\s+typname\s*=\s*['\"][A-Za-z_][A-Za-z0-9_]*['\"]",
    re.IGNORECASE,
)

drop_idx_rx = re.compile(r"\bop\.drop_index\s*\(")
drop_tbl_rx = re.compile(r"\bop\.drop_table\s*\(")
drop_col_rx = re.compile(r"\bop\.drop_column\s*\(")
drop_cst_rx = re.compile(r"\bop\.drop_constraint\s*\(")

lines = []
failed = 0

for p in paths:
    rel_path = _normalise(p.relative_to(repo_root))
    if rel_path in exceptions:
        continue
    s = p.read_text()
    issues = []

    calls = list(enum_call_rx.finditer(s))
    if calls:
        if any(not enum_name_rx.search(m.group("args")) for m in calls):
            issues.append("ENUM missing name=")
        if any(not create_false_rx.search(m.group("args")) for m in calls):
            issues.append("ENUM missing create_type=False")
        if upgrade_def_rx.search(s) and not guard_block_rx.search(s):
            issues.append("upgrade() missing guarded CREATE TYPE check")

    if drop_idx_rx.search(s):
        issues.append("uses op.drop_index (not guarded)")
    if drop_tbl_rx.search(s):
        issues.append("uses op.drop_table (not guarded)")
    if drop_col_rx.search(s):
        issues.append("uses op.drop_column (not guarded)")
    if drop_cst_rx.search(s):
        issues.append("uses op.drop_constraint (not guarded)")

    if issues:
        lines.append(f"[FAIL] {p.name}")
        for it in issues:
            lines.append(f"  - {it}")
        failed += 1
    else:
        lines.append(f"[OK]   {p.name}")

print("\n".join(lines))
sys.exit(1 if failed else 0)
