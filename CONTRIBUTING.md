# Contributing to Optimal Build

Thanks for your interest in contributing! This guide covers the basics to get
your environment ready, follow our coding standards, and run the full suite of
checks before opening a pull request.

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
