# pnpm Fetch Store

This directory should contain the pnpm fetch store used by CI for offline
installs. When frontend dependencies change, refresh the mirror with:

```bash
pnpm fetch
cp -r node_modules/.pnpm-store third_party/pnpm-store
```

Commit the updated store so the GitHub Actions workflow can run `pnpm install`
with `--offline` and `--store-dir`.
