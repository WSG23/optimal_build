# Contributing to Optimal Build

Thanks for your interest in contributing! This guide covers the basics to get
your environment ready, follow our coding standards, and run the full suite of
checks before opening a pull request.

## 📚 REQUIRED READING (Before You Start)

**All contributors (human and AI agents) MUST read these documents FIRST:**

1. **[FEATURES.md](FEATURES.md)** - Complete product vision and requirements
   - Defines all roles: Agents, Developers, Architects, Engineers
   - Specifies every feature requirement
   - **THIS IS THE SOURCE OF TRUTH**

2. **[docs/feature_delivery_plan_v2.md](docs/feature_delivery_plan_v2.md)** - Comprehensive delivery roadmap
   - Maps 100% of FEATURES.md into 6 phases
   - Shows dependencies and priorities
   - Includes acceptance criteria and estimates
   - **ALWAYS CHECK THIS BEFORE STARTING NEW WORK**

3. **[docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md](docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md)** - Current priorities
   - Updated regularly with what to build next
   - Shows completed vs. in-progress vs. not-started features
   - **CHECK THIS TO KNOW WHAT TO WORK ON**

4. **[CODING_RULES.md](CODING_RULES.md)** - Technical standards
   - Migrations, async patterns, compliance checks
   - Singapore-specific requirements
   - **FOLLOW THESE RULES IN ALL CODE**

### ⚠️ Why This Matters:

- Building features NOT in FEATURES.md wastes time
- Skipping the delivery plan creates integration conflicts
- Ignoring priorities causes rework
- Not following coding rules breaks the build

### ✅ Onboarding Checklist:

Before writing any code, confirm you've:
- [ ] Read FEATURES.md completely
- [ ] Reviewed feature_delivery_plan_v2.md for current phase
- [ ] Checked NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md for priorities
- [ ] Read CODING_RULES.md for technical standards
- [ ] Understand which phase you're working in
- [ ] Know the acceptance criteria for your task

**If you're an AI agent:** Include "I have read all required documents" in your first message.

### AI Agent Code Generation Workflow

All AI agents (Claude, Codex, etc.) MUST follow this workflow:

**BEFORE writing code:**
1. Run `make ai-preflight` to verify the current codebase state
2. Check that all coding rules checks pass
3. Review CODING_RULES.md sections relevant to your task

**DURING code generation:**
1. Follow all 7 rules in CODING_RULES.md
2. Never edit existing migration files (Rule 1)
3. Use async/await for all database/API operations (Rule 2)
4. Follow import ordering conventions (Rule 6)
5. Avoid unused variables and use proper exception chaining (Rule 7)

**AFTER writing code (MANDATORY):**
1. **Run `make format`** - Fixes formatting, import ordering
2. **Run `make verify`** - Runs format-check, lint, coding rules, tests
3. Fix any violations before presenting code to the user
4. Never present code that fails `make verify`

**If verification fails:**
- Fix the issues immediately
- Re-run `make format` and `make verify`
- Only present code after all checks pass

---

## Initial setup

1. Create and activate a virtual environment.
2. Upgrade pip and install pre-commit.
3. Install the repository's pre-commit hooks.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip pre-commit
pre-commit install
```

If you prefer a single command that installs both Python and JavaScript
dependencies, run `make venv` from the repository root. This target also sets
up the `frontend` workspace and installs the configured pre-commit hooks if the
`pre-commit` binary is available.

## Coding standards

For project-specific rules (migrations, async patterns, compliance checks), see [CODING_RULES.md](CODING_RULES.md).

### Python

- Format Python code with **Black** (`black --line-length 88`) and keep imports
  organized through **Ruff**'s isort integration. Both tools run automatically
  via pre-commit across the backend, application packages, scripts, and tests.
- Address lint findings reported by **Ruff** and the targeted **Flake8** checks
  that protect the test suites.
- Keep type hints current—**mypy** runs against `backend/` using the
  configuration in `backend/pyproject.toml`.

#### Linting Strategy

This project uses a multi-layered linting approach:

**Primary Linter: Ruff** (`ruff.toml`)
- Line length: 100 characters
- Checks: E (pycodestyle errors), F (Pyflakes), W (pycodestyle warnings), B (bugbear), UP (pyupgrade), I (isort), C4 (comprehensions)
- Runs on all production code: `backend/`, `app/`, `core/`, etc.
- Fastest Python linter, replaces flake8 + isort + pyupgrade

**Secondary Linter: Flake8** (`.flake8` - DEPRECATED)
- Line length: 100 characters (aligned with Ruff)
- Runs ONLY on test files: `backend/tests/`, `tests/`
- Kept for backward compatibility; may be removed in future

**Type Checker: mypy** (`mypy.ini`)
- Strict type checking on `backend/` code
- Helps catch bugs before runtime

**Common Lint Errors:**
- `B904`: Always use `raise ... from e` when re-raising exceptions to preserve stack traces
- `B007`: Rename unused loop variables to `_variablename`
- `F401`: Remove unused imports
- `E501`: Keep lines under 100 characters

**Running Linters Locally:**
```bash
# Run all quality checks
make verify

# Run just linting
make lint

# Run ruff on specific files
.venv/bin/ruff check backend/app/

# Auto-fix ruff issues
.venv/bin/ruff check --fix backend/app/
```

### JavaScript and TypeScript

- Use **Prettier** for formatting files under `frontend/` and `ui-admin/`.
- Resolve lint warnings flagged by **ESLint** (configured with
  `@typescript-eslint` and the React plugins) to maintain consistent frontend
  code quality.

## Testing and quality checks

- Run `make verify` after each significant change. It executes Black (88-column
  formatting), Ruff (100-column linting), Flake8, mypy, the unit test suites,
  and the repository-specific coding rule checks.
- When a slice touches the front-end workspaces, also run the package-specific
  scripts:
  `pnpm -C frontend test` for the Vite UI and `pnpm -C ui-admin test` for the
  admin UI.
- Commit only after the above checks pass so that every iteration remains
  shippable. The recommended loop is:

  1. Stage your changes and run `git commit`.
  2. Let the configured pre-commit hooks execute (`make verify` is part of the
     pipeline).
  3. If a hook fails, fix the reported issue, restage, and try the commit again.
  4. Repeat until the commit succeeds, then push or open the PR.

### Security expectations

- Never commit secrets, credentials, or production data. The **gitleaks** hook
  runs in pre-commit to detect accidental disclosures—review and resolve any
  findings before pushing.
- Review changes for secure defaults (e.g., input validation, authorization
  checks) and coordinate with the maintainers if you suspect a vulnerability.

## Contributor workflow

1. **Create a branch.** Use a descriptive branch name such as
   `feature/short-description` or `fix/issue-id`.
2. **Install dependencies** following the initial setup above (or via
   `make venv`). Ensure `pre-commit install` has been run so hooks trigger on
   each commit.
3. **Prime the hooks.** Run all configured hooks one time across the repo:

   ```bash
   pre-commit run --all-files
   ```

4. **Develop your change.** Keep commits focused and reference relevant issues.
   Update documentation, configuration, and tests alongside code changes.
5. **Run checks before pushing.** Execute the local quality gates so your PR
   passes CI:

   ```bash
   make verify
   ```

   This target runs formatting checks, linting, and the Python tests. For
   targeted runs you can invoke:

   ```bash
   make format
   make lint
   make test
   ```

   Frontend workspaces have dedicated commands:

   ```bash
   pnpm -C frontend test        # Vite/Web UI checks
   pnpm -C ui-admin test        # Admin UI checks
   ```

   Run these when your changes affect the corresponding UI packages.
6. **Prepare the pull request.** Include a summary of the change, note any
   follow-up work, and call out testing performed. Ensure CI is green before
   requesting review.

## Reviewer checklist

- **Formatting and linting:** Confirm Black, Ruff, Flake8, Prettier, and ESLint
  all run cleanly (CI should execute the corresponding pre-commit hooks).
- **Tests:** Verify `make verify` and any targeted test suites (backend Pytest,
  frontend `npm test`) succeed.
- **Types:** Ensure mypy passes for backend changes and that TypeScript builds
  without errors where applicable.
- **Documentation:** Check that README, docs, or configuration files are
  updated when behavior changes or new steps are required.
- **Security:** Review gitleaks output, look for exposed secrets, and evaluate
  the change for security impacts (authentication, authorization, sensitive
  data handling).
