#!/usr/bin/env python3
"""Single-writer coordination primitive for concurrent AI agents.

Background: this repo is regularly worked on by more than one AI agent
(Claude Code, Codex, IDE-side linters). Concurrent writes to the same
branch silently overwrite each other — the only signal is files
"mysteriously" reverting between turns. This script provides a
lightweight, local lock so each agent can declare ownership before
editing and detect conflicts before stomping someone else's work.

Lock file: ``.agent-active`` at the repo root (gitignored). Format is
plain key/value lines so a human or another agent can read it without
parsing JSON:

    agent: claude
    pid: 12345
    branch: codex/some-branch
    started_at: 2026-05-17T08:30:00+10:00
    intent: Stage and commit cleanup buckets

Subcommands:

    start <agent>     Acquire the lock for ``<agent>`` (claude, codex, ...).
                      Fails if another live agent owns it. Use
                      ``--intent "short description"`` to record what
                      you're about to do.
    check             Exit 0 if no lock or the current process owns it,
                      exit 1 with details if another agent owns it.
                      Reads ``AGENT_SESSION_NAME`` env var if set so
                      hooks can pose "is the committer the lock owner?".
    stop              Release the lock. No-op if file is missing.
    clear --force     Drop a stale lock unconditionally. Use when the
                      prior agent died without calling ``stop``.

Stale locks: a lock is considered stale if its PID is no longer
running or ``started_at`` is more than ``STALE_AFTER_SECONDS`` ago.
Stale locks are auto-cleared by ``start`` and ignored by ``check``.

Exit codes follow shell convention so this can wire into hooks:
0 = ok / lock acquired / no conflict; 1 = conflict; 2 = bad invocation.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCK_FILE = REPO_ROOT / ".agent-active"
# Stale window in minutes. Short enough to recover from a crashed/abandoned
# session, long enough to cover normal idle time between turns. PID-based
# liveness intentionally isn't used: each script invocation runs in a new
# process, so the writer PID is always dead by the time a peer checks.
STALE_AFTER_SECONDS = 60 * 60  # 60 minutes
KNOWN_AGENTS = ("claude", "codex", "cursor", "copilot", "human", "other")


def _now_iso() -> str:
    return datetime.now(UTC).astimezone().isoformat(timespec="seconds")


def _read_lock() -> dict[str, str] | None:
    if not LOCK_FILE.exists():
        return None
    data: dict[str, str] = {}
    for raw in LOCK_FILE.read_text().splitlines():
        if ":" not in raw:
            continue
        key, _, value = raw.partition(":")
        data[key.strip()] = value.strip()
    return data or None


def _lock_is_stale(lock: dict[str, str]) -> bool:
    started = lock.get("started_at")
    if not started:
        return True
    try:
        started_dt = datetime.fromisoformat(started)
    except ValueError:
        return True
    age = datetime.now(started_dt.tzinfo or UTC) - started_dt
    return age > timedelta(seconds=STALE_AFTER_SECONDS)


def _current_branch() -> str:
    head_file = REPO_ROOT / ".git" / "HEAD"
    if not head_file.exists():
        return ""
    head = head_file.read_text().strip()
    if head.startswith("ref: refs/heads/"):
        return head[len("ref: refs/heads/") :]
    return head[:12]  # detached HEAD — short sha


def _write_lock(agent: str, intent: str) -> None:
    body = (
        f"agent: {agent}\n"
        f"pid: {os.getpid()}\n"
        f"branch: {_current_branch()}\n"
        f"started_at: {_now_iso()}\n"
        f"intent: {intent}\n"
    )
    LOCK_FILE.write_text(body)


def cmd_start(args: argparse.Namespace) -> int:
    existing = _read_lock()
    if existing and not _lock_is_stale(existing):
        if existing.get("agent") == args.agent:
            # Same agent re-acquiring — refresh started_at and continue.
            _write_lock(args.agent, args.intent)
            print(f"✅ Lock refreshed for {args.agent}.")
            return 0
        print(
            f"❌ .agent-active is held by {existing.get('agent', '?')} "
            f"(branch {existing.get('branch', '?')}, started "
            f"{existing.get('started_at', '?')}).",
            file=sys.stderr,
        )
        intent = existing.get("intent")
        if intent and intent != "(unspecified)":
            print(f"   Their intent: {intent}", file=sys.stderr)
        print(
            "   Coordinate with that session before editing, or run "
            "`scripts/agent_session.py clear --force` if you're sure it's dead.",
            file=sys.stderr,
        )
        return 1
    if existing and _lock_is_stale(existing):
        print(
            f"ℹ️  Clearing stale lock from {existing.get('agent', '?')} "
            f"(started {existing.get('started_at', '?')}).",
            file=sys.stderr,
        )
    _write_lock(args.agent, args.intent)
    print(f"✅ Lock acquired for {args.agent}.")
    return 0


def cmd_check(_args: argparse.Namespace) -> int:
    existing = _read_lock()
    if not existing:
        return 0
    if _lock_is_stale(existing):
        return 0
    caller = os.environ.get("AGENT_SESSION_NAME", "").strip().lower()
    owner = existing.get("agent", "").lower()
    if caller and caller == owner:
        return 0
    print(
        f"❌ Another agent owns .agent-active: {existing.get('agent', '?')} "
        f"(pid {existing.get('pid', '?')}, branch "
        f"{existing.get('branch', '?')}, started "
        f"{existing.get('started_at', '?')}).",
        file=sys.stderr,
    )
    intent = existing.get("intent")
    if intent:
        print(f"   Their intent: {intent}", file=sys.stderr)
    return 1


def cmd_stop(_args: argparse.Namespace) -> int:
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()
        print("✅ Lock released.")
    return 0


def cmd_clear(args: argparse.Namespace) -> int:
    existing = _read_lock()
    if not existing:
        print("ℹ️  No lock to clear.")
        return 0
    if not args.force and not _lock_is_stale(existing):
        print(
            "❌ Refusing to clear a live lock without --force. "
            f"Held by {existing.get('agent', '?')} (pid "
            f"{existing.get('pid', '?')}).",
            file=sys.stderr,
        )
        return 1
    LOCK_FILE.unlink()
    print("✅ Lock cleared.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_start = sub.add_parser("start", help="Acquire the lock for an agent.")
    p_start.add_argument("agent", choices=KNOWN_AGENTS)
    p_start.add_argument(
        "--intent",
        default="(unspecified)",
        help="One-line description of what you're about to do.",
    )
    p_start.set_defaults(func=cmd_start)

    p_check = sub.add_parser("check", help="Verify the lock isn't held elsewhere.")
    p_check.set_defaults(func=cmd_check)

    p_stop = sub.add_parser("stop", help="Release the lock.")
    p_stop.set_defaults(func=cmd_stop)

    p_clear = sub.add_parser("clear", help="Force-clear a stale lock.")
    p_clear.add_argument("--force", action="store_true")
    p_clear.set_defaults(func=cmd_clear)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
