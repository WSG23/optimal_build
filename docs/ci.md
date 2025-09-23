# Continuous Integration

## Dependency installation

CI and local development environments install Python dependencies directly from
the pinned requirement files instead of pre-downloaded wheels. Run the standard
installation command whenever the backend requirements change:

```bash
pip install -r backend/requirements-dev.txt
```

Frontend dependencies continue to use the cached pnpm store that lives under
`third_party/pnpm-store`. Refresh the cache when Node dependencies change:

```bash
pnpm fetch
cp -r node_modules/.pnpm-store third_party/pnpm-store
```

Commit the updated pnpm store together with the dependency lockfile updates so
GitHub Actions workflows can continue to run without reaching public registries.
