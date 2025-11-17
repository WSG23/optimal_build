# Optimal Build

## AI Agent Onboarding *(Mandatory)*
- Start with `START_HERE.md` for the exact reading order.
- Read both `docs/all_steps_to_product_completion.md` and `docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md` **before** planning, writing a to‑do list, or touching code, then grab your next task from the [📌 Unified Execution Backlog](docs/all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work).
- Keep `docs/all_steps_to_product_completion.md#-known-testing-issues` handy while implementing and validating changes.

## Developer Setup

After cloning the repository, install git hooks to enforce code quality:

```bash
./scripts/install-git-hooks.sh
```

This installs pre-push hooks that run formatting checks, linting, and coding rules verification before allowing you to push. This prevents code quality violations from reaching the remote repository.

**To bypass hooks (not recommended):**
```bash
SKIP_PRE_PUSH_CHECKS=1 git push
```

## Working Notes
- Backend is Python/FastAPI; frontend is React/TypeScript.
- Prefer local pytest/NPM commands for verification; always tell the user which tests to run.
- Update delivery docs alongside code changes.
