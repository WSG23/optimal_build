# Optimal Build

## AI Agent Onboarding *(Mandatory)*
- Start with `START_HERE.md` for the exact reading order.
- Read both `docs/feature_delivery_plan_v2.md` and `docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md` **before** planning, writing a to‑do list, or touching code.
- Skim `UI_STATUS.md` whenever frontend work is in scope.
- Keep `TESTING_KNOWN_ISSUES.md` handy while implementing and validating changes.

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
