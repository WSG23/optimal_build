# Contributing to Optimal Build

Thanks for your interest in contributing! This guide covers the basics to get
your environment ready, keep your changes clean, and run the full suite of
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

## Before pushing changes

Always run the local quality gates before you push a branch. The verify
target executes formatting checks, linting, and the test suite in one go.

```bash
make verify
```

If you prefer, you can run the individual commands as needed:

```bash
make format
make lint
make test
```

## One-time full run

Run all pre-commit hooks across the repository at least once to ensure there
are no latent issues before you start iterating.

```bash
pre-commit run --all-files
```
