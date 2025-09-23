# Frontend operations

## Refreshing the Playwright browser cache

Our CI pipeline keeps a checked-in `.playwright-browsers/` directory so Playwright never needs to download browsers during the `test:e2e` run. When bumping Playwright, regenerate the cache and accompanying tarball so the workflow keeps using the prebuilt binaries:

1. Remove the existing cache and create a clean workspace:
   ```bash
   rm -rf .playwright-browsers
   mkdir -p .playwright-browsers
   ```
2. Install the browsers into the local cache:
   ```bash
   PLAYWRIGHT_BROWSERS_PATH=$(pwd)/.playwright-browsers pnpm -C frontend exec playwright install --with-deps
   ```
3. Package the cache into a tarball that can be uploaded to the artifact store or committed alongside the directory:
   ```bash
   tar -C .playwright-browsers -czf .playwright-browsers.tar.gz .
   ```
4. Commit the refreshed `.playwright-browsers/` directory and updated tarball, then push the changes.

This ensures the synced browsers match the version expected by the GitHub Actions workflow and keeps the offline cache reproducible.
