# Multi-Agent Coordination

This repo is regularly worked on by more than one AI agent (Claude Code, Codex, plus IDE-side linters and the human). This page is the canonical reference for how those agents stay out of each other's way. Both [CLAUDE.md](../../CLAUDE.md) and [docs/ai-agents/codex.md](codex.md) defer here for the details.

## The problem we're solving

Concurrent writes to the same branch silently overwrite each other. The only signal is files "mysteriously" reverting between turns. We've seen this fail four distinct ways:

1. **Direct overwrite.** Both agents edit the same file; whichever writes last wins.
2. **Cross-revert.** Agent A removes a `# type: ignore`; agent B's linter re-adds it; A removes it again. The file ping-pongs.
3. **Stale-status reads.** Long `git status` output gets truncated in one agent's view; it misses files the other is editing and operates on an incomplete picture.
4. **Race at commit time.** Two agents stage different files and run `git commit` near-simultaneously on the same branch.

## The rule

**Single-writer per branch.** Only one agent edits files on a given branch at a time. The other agent can read, review, run tests, or open separate worktrees for non-overlapping work — but does not write to disk.

The `.agent-active` lock file at the repo root makes ownership explicit so every agent (and human) can see who's currently writing.

## Lifecycle

```bash
# Before opening any write tool (Edit, Write, Bash with rm/sed/mv, etc.):
python3 scripts/agent_session.py start <agent> --intent "<short description>"

# At any point, to verify you still own the lock:
AGENT_SESSION_NAME=<agent> python3 scripts/agent_session.py check

# When you're done writing:
python3 scripts/agent_session.py stop
```

`<agent>` is one of: `claude`, `codex`, `cursor`, `copilot`, `human`, `other`.

The lock file contains:

```
agent: claude
pid: 40141
branch: codex/some-branch
started_at: 2026-05-17T08:30:00+10:00
intent: Stage and commit cleanup buckets
```

Locks auto-expire after 60 minutes of inactivity. The same agent re-invoking `start` refreshes the timestamp.

## What to do when the lock is held by someone else

`start` exits 1 with a clear error showing who holds the lock, since when, and their declared intent.

When this happens:

1. **Stop.** Do not edit any file. Even a "small" change risks overwriting in-progress work.
2. **Surface to the user.** Quote the lock contents. Ask whether to wait, hand off, or clear the lock.
3. **Only clear after explicit user confirmation.** Use `python3 scripts/agent_session.py clear --force`. Then `start` your own session.

Do not silently `clear --force` to take a lock you didn't earn. The whole point is to make handoffs visible.

## Parallel work when it's genuinely needed

Use git worktrees so each agent has its own filesystem and its own branch:

```bash
git worktree add ../optimal_build-codex codex/my-branch
git worktree add ../optimal_build-claude claude/my-branch
```

Each worktree has its own `.agent-active` and the agents can write in parallel without colliding. Merge via PR. This is the right pattern for genuinely independent streams of work (e.g. backend feature on one branch, unrelated docs/refactor on another).

Don't use worktrees as a workaround for "I want to skip the lock" on the *same* branch. That just hides the conflict.

## Detection guardrails

The lock is **honor-based** — agents check it and yield. Two supporting checks make violations visible:

- **`scripts/agent_session.py check`** can be wired into any hook or CI step. It exits non-zero if `.agent-active` is held by someone other than `AGENT_SESSION_NAME`. Pre-commit hooks may opt in by adding a local hook that runs it (kept opt-in so the user driving manually isn't blocked).
- **`git status` discipline.** When `git status` output truncates, run `git status --porcelain | wc -l` to see how many files are actually modified, and `git status --porcelain` to read the full list. Never assume the truncated view is complete. This is the single most common way one agent misses work the other has done.

## Workflow patterns

Two patterns are blessed; everything else needs the user's explicit OK.

### Pattern A — Codex implements, Claude verifies and commits

This is what the existing [docs/ai-agents/codex.md §7](codex.md) already describes. Refined with the lock:

1. Codex runs `agent_session.py start codex --intent "<feature>"` on its branch.
2. Codex makes edits, runs tests, leaves the working tree dirty.
3. Codex runs `agent_session.py stop`. Reports test results + file list to the user.
4. Claude runs `agent_session.py start claude --intent "review and commit <feature>"`.
5. Claude reviews the diff, runs verification, and commits. Then `stop`.

Single-writer invariant is preserved across the handoff.

### Pattern B — Two agents, two worktrees, two branches

For genuinely independent streams of work:

1. Each agent creates a separate worktree on a distinct branch.
2. Each acquires its own `.agent-active` (each worktree has its own).
3. They commit independently. Merges go through PR review like normal.

## When this doc applies vs. doesn't

- **Applies** to AI agents with write capabilities operating on this repo.
- **Doesn't apply** when only one agent is writing (the common case — `start` is cheap, just do it anyway so the lock shows the current owner).
- **Doesn't apply** to read-only review sessions. Use `AGENT_SESSION_NAME=<your-agent> check` to verify you can read safely without writing.

## Why honor-based instead of OS-level locking

A true OS-level lock (`flock`, `fcntl`) would require every write tool (`Edit`, `Write`, the human's editor) to go through a shared wrapper. We don't control the tools that other agents use, and we can't lock the entire filesystem without breaking normal development. The honor-based lock is the contract; the script is the enforcement aid. Skipping it costs the user time in the form of lost work — that's the natural backpressure.
