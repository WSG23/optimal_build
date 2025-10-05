# NumPy Fix Status

**Updated:** 2025-10-05
**Issue:** `.venv` Python crashed with `Floating point exception: 8` when importing NumPy.

## Resolution

- Replaced the broken NumPy/OpenBLAS build in `.venv` by running `./fix_numpy_optimal_build.sh`.
- Script upgrades packaging tooling, purges old artifacts, installs `numpy==2.0.2` and `pandas==2.2.3`, and re-runs sanity checks plus the repo's verification suite.

### Verification

```bash
$ .venv/bin/python -c "import numpy, platform; print(numpy.__version__, platform.python_version())"
2.0.2 3.11.13

$ .venv/bin/pytest -q unit_tests/
15 passed in 6.7s

$ make verify
# format-check, lint (flake8 + mypy), coding rules, and unit tests all succeed
```

## Usage Notes

- Always call tools via `.venv/bin/python`, `.venv/bin/pytest`, etc., or `source .venv/bin/activate` before running commands.
- The repair script sets `VECLIB_MAXIMUM_THREADS=1` and `OPENBLAS_NUM_THREADS=1` to avoid macOS BLAS crashes; keep those when reproducing the environment.

## Artifacts

- Script: `fix_numpy_optimal_build.sh`
- Updated dependencies inside `.venv`: `numpy==2.0.2`, `pandas==2.2.3`

Refer to the git history for the exact command transcript that performed the fix.
