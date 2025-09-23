# Continuous Integration

## Dependency mirror maintenance

CI installs both Python and frontend dependencies from mirrors committed to the
repository so that workflows do not reach public package registries. When any
Python or Node dependency changes, refresh the mirrors before pushing:

```bash
pip download --dest third_party/python -r backend/requirements-dev.txt
pnpm fetch
cp -r node_modules/.pnpm-store third_party/pnpm-store
```

Commit the updated `third_party/python` wheels and the contents of
`third_party/pnpm-store` together with the dependency lockfile updates. This
keeps the GitHub Actions workflows functioning in offline mode and ensures that
local developers can reproduce the CI environment.
