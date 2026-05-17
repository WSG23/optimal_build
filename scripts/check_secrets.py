#!/usr/bin/env python3
"""Secrets detection — block credentials from being committed.

Scans staged files for high-confidence credential patterns: AWS keys,
private keys, JWTs, GitHub tokens, Stripe keys, generic API key patterns
adjacent to known assignment keywords, and obvious password literals.

Designed to have very low false-positive rate. Test/example values
(test_, fake_, example_, your-) are allowed. Findings can be whitelisted
in .secrets-allowlist.txt if needed for documentation or fixtures.

Exit codes:
  0 — no secrets detected
  1 — at least one likely secret in staged files
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ALLOWLIST_FILE = REPO_ROOT / ".secrets-allowlist.txt"

# Each pattern: (name, compiled regex, description). Regexes use
# named group 'secret' for the matched credential.
PATTERNS = [
    (
        "aws-access-key",
        re.compile(r"\b(?P<secret>AKIA[0-9A-Z]{16})\b"),
        "AWS Access Key ID",
    ),
    (
        "aws-secret-key",
        re.compile(
            r"(?i)aws[_-]?secret[_-]?(?:access[_-]?)?key\s*[:=]\s*"
            r"['\"](?P<secret>[A-Za-z0-9/+=]{40})['\"]"
        ),
        "AWS Secret Access Key",
    ),
    (
        "github-token",
        re.compile(r"\b(?P<secret>gh[opsu]_[A-Za-z0-9]{36,255})\b"),
        "GitHub personal access token",
    ),
    (
        "github-oauth",
        re.compile(r"\b(?P<secret>github_pat_[A-Za-z0-9_]{82})\b"),
        "GitHub fine-grained token",
    ),
    (
        "stripe-live-key",
        re.compile(r"\b(?P<secret>sk_live_[A-Za-z0-9]{24,})\b"),
        "Stripe live secret key",
    ),
    (
        "stripe-restricted",
        re.compile(r"\b(?P<secret>rk_live_[A-Za-z0-9]{24,})\b"),
        "Stripe restricted key",
    ),
    (
        "openai-key",
        re.compile(r"\b(?P<secret>sk-(?:proj-)?[A-Za-z0-9_-]{32,})\b"),
        "OpenAI API key",
    ),
    (
        "anthropic-key",
        re.compile(r"\b(?P<secret>sk-ant-[A-Za-z0-9_-]{32,})\b"),
        "Anthropic API key",
    ),
    (
        "google-api-key",
        re.compile(r"\b(?P<secret>AIza[0-9A-Za-z_-]{35})\b"),
        "Google API key",
    ),
    (
        "slack-token",
        re.compile(r"\b(?P<secret>xox[abprs]-[A-Za-z0-9-]{10,})\b"),
        "Slack token",
    ),
    (
        "private-key-block",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
        "Private key block",
    ),
    (
        "jwt",
        re.compile(
            r"\b(?P<secret>eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}"
            r"\.[A-Za-z0-9_-]{10,})\b"
        ),
        "JSON Web Token (JWT)",
    ),
    (
        "password-literal",
        re.compile(
            r"(?i)(?:password|passwd|pwd)\s*[:=]\s*"
            r"['\"](?P<secret>(?!test|fake|example|change|your-|placeholder|\$\{|\<|x{3,}|\.{3,}|_+)[^'\"]{8,})['\"]"
        ),
        "Hardcoded password literal",
    ),
    (
        "generic-api-key",
        re.compile(
            r"(?i)(?:api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*"
            r"['\"](?P<secret>(?!test|fake|example|change|your-|placeholder|\$\{|\<|x{3,}|\.{3,}|_+)[A-Za-z0-9_\-]{20,})['\"]"
        ),
        "Generic API key / secret assignment",
    ),
]

# Skip generated/vendored content, lockfiles, and certain test fixtures
SKIP_PATH_PARTS = (
    "/node_modules/",
    "/dist/",
    "/build/",
    "/.git/",
    "/__pycache__/",
    "/coverage/",
    "/.venv/",
    "/venv/",
    # Test directories may contain fixture passwords / mock tokens
    "/unit_tests/",
    "/backend/tests/",
    "/frontend/tests/",
    "/tests/fixtures/",
    "/tests/e2e/",
    "/__tests__/",
)
SKIP_FILES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    ".secrets-allowlist.txt",
    # The scanner itself contains pattern strings that look like secrets
    "check_secrets.py",
}
SKIP_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".webp",
    ".pdf",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".min.js",
    ".min.css",
}


def load_allowlist() -> set[str]:
    """Allowlisted excerpts (full secret string, one per line)."""
    if not ALLOWLIST_FILE.exists():
        return set()
    items: set[str] = set()
    for raw in ALLOWLIST_FILE.read_text().splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            items.add(line)
    return items


def get_staged_files() -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=AM"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    files = []
    for name in result.stdout.splitlines():
        path = REPO_ROOT / name
        if path.is_file():
            files.append(path)
    return files


def should_skip(path: Path) -> bool:
    s = str(path)
    if any(part in s for part in SKIP_PATH_PARTS):
        return True
    if path.name in SKIP_FILES:
        return True
    if path.suffix in SKIP_EXTS:
        return True
    # Skip files larger than 1 MB — likely binary or assets
    try:
        if path.stat().st_size > 1_048_576:
            return True
    except OSError:
        return True
    return False


def scan_file(path: Path, allowlist: set[str]) -> list[tuple[int, str, str]]:
    """Return (line_no, pattern_name, description) tuples for findings."""
    findings: list[tuple[int, str, str]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings

    for line_no, line in enumerate(text.splitlines(), 1):
        # Skip lines that look like detection rules themselves
        if "noqa: secrets" in line or "pragma: allowlist" in line:
            continue
        for name, regex, desc in PATTERNS:
            for m in regex.finditer(line):
                secret = m.groupdict().get("secret") or m.group(0)
                if secret in allowlist:
                    continue
                findings.append((line_no, name, f"{desc}: {secret[:8]}…"))
    return findings


def main() -> int:
    full_scan = "--full" in sys.argv
    if full_scan:
        # Walk entire repo (CI mode)
        files = []
        for path in REPO_ROOT.rglob("*"):
            if path.is_file():
                files.append(path)
    else:
        files = get_staged_files()

    allowlist = load_allowlist()
    total_findings = 0
    print_header_done = False
    for path in files:
        if should_skip(path):
            continue
        findings = scan_file(path, allowlist)
        if not findings:
            continue
        if not print_header_done:
            print("\n" + "=" * 70)
            print("SECRETS DETECTED IN STAGED FILES")
            print("=" * 70)
            print("Remove secrets before committing. Use environment variables")
            print("or a secrets manager (Vault, AWS Secrets Manager).")
            print("To allowlist a known-safe value (test fixture, docs):")
            print(f"  add it to {ALLOWLIST_FILE.relative_to(REPO_ROOT)}")
            print()
            print_header_done = True
        rel = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
        for line_no, name, desc in findings:
            print(f"  {rel}:{line_no}: [{name}] {desc}")
            total_findings += 1

    if total_findings == 0:
        print(f"✓ No secrets detected ({len(files)} files scanned)")
        return 0

    print(f"\nTotal: {total_findings} potential secret(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
