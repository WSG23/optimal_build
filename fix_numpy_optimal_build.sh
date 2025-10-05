#!/usr/bin/env bash
set -euo pipefail

echo "== Optimal Build: NumPy repair & verification =="

VENV_PATH="${VENV_PATH:-.venv}"
PYTEST_PATH="${PYTEST_PATH:-unit_tests}"

# Optional: uncomment if you use a proxy
# export HTTPS_PROXY="https://user:pass@host:port"
# export HTTP_PROXY="http://user:pass@host:port"

# Mitigate rare BLAS crashes on Intel macOS
export VECLIB_MAXIMUM_THREADS="${VECLIB_MAXIMUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"

if [[ ! -x "$VENV_PATH/bin/python" ]]; then
  echo "ERROR: Can't find virtualenv at $VENV_PATH (expected $VENV_PATH/bin/python)."
  echo "If needed:  python3 -m venv $VENV_PATH"
  exit 1
fi

echo "Activating venv: $VENV_PATH"
# shellcheck disable=SC1090
source "$VENV_PATH/bin/activate"

echo "Python: $(python -V)"
echo "Which python: $(which python)"
echo

echo "Upgrading pip/setuptools/wheel..."
python -m pip install --upgrade pip setuptools wheel

echo "Purging pip cache (ok if empty)..."
pip cache purge || true

echo "Uninstalling any broken NumPy..."
pip uninstall -y numpy || true

echo "Removing stray NumPy artifacts (if any)..."
python - <<'PY'
import site, shutil, glob, os
paths = []
try:
    paths.extend(site.getsitepackages())
except Exception:
    pass
try:
    paths.append(site.getusersitepackages())
except Exception:
    pass
for p in paths:
    if not p or not os.path.isdir(p):
        continue
    for g in ("numpy*", "numpy-*.dist-info", "numpy-*.egg-info"):
        for path in glob.glob(os.path.join(p, g)):
            print(" - removing", path)
            shutil.rmtree(path, ignore_errors=True)
print("Cleanup done")
PY

echo "Installing binary wheels (numpy 2.0.2, pandas 2.2.3)..."
pip install --only-binary=:all: "numpy==2.0.2" "pandas==2.2.3"

echo "Sanity check..."
python - <<'PY'
import numpy as np, platform
a = np.arange(6).reshape(2,3)
print("NumPy OK:", np.__version__, "| Python:", platform.python_version(), "| Sum:", int(a.sum()))
PY

echo
echo "Running pytest..."
if [[ -d "$PYTEST_PATH" ]]; then
  pytest -q "$PYTEST_PATH" || true
else
  echo "No tests directory at $PYTEST_PATH — skipping pytest."
fi

echo
echo "Running 'make verify'..."
if command -v make >/dev/null 2>&1; then
  make verify || true
else
  echo "'make' not found — skipping make verify."
fi

echo "Done."
