# Python Wheels Mirror

This directory is a placeholder for the pre-downloaded Python wheels that the CI
workflow installs with `--no-index`. Refresh the contents whenever
`backend/requirements-dev.txt` changes by running:

```bash
pip download --dest third_party/python -r backend/requirements-dev.txt
```

Make sure the resulting wheels are committed to the repository so CI jobs can
install dependencies without reaching external package indexes.
