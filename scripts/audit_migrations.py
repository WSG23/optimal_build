from pathlib import Path
import re, sys

root = Path("backend/migrations/versions")
paths = sorted(root.glob("*.py"))

enum_call_rx   = re.compile(r"\b(?:sa\.Enum|postgresql\.ENUM)\s*\((?P<args>.*?)\)", re.DOTALL)
enum_name_rx   = re.compile(r"name\s*=\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]")
create_false_rx= re.compile(r"create_type\s*=\s*False")
upgrade_def_rx = re.compile(r"(?m)^\s*def\s+upgrade\s*\(\s*\)\s*:\s*$")
guard_block_rx = re.compile(r"SELECT\s+1\s+FROM\s+pg_type\s+WHERE\s+typname\s*=\s*['\"][A-Za-z_][A-Za-z0-9_]*['\"]", re.IGNORECASE)

drop_idx_rx = re.compile(r"\bop\.drop_index\s*\(")
drop_tbl_rx = re.compile(r"\bop\.drop_table\s*\(")
drop_col_rx = re.compile(r"\bop\.drop_column\s*\(")
drop_cst_rx = re.compile(r"\bop\.drop_constraint\s*\(")

lines = []
failed = 0

for p in paths:
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
