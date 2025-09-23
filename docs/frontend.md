# Frontend operations

## Refreshing the Playwright browser cache

The end-to-end harness prefers the checked-in `.playwright-browsers/` directory, but it will also fall back to `~/.cache/ms-playwright` when that cache already contains Playwright's metadata. Our CI workflow restores the cache directory using [`actions/cache`](https://github.com/actions/cache) so the tests never need to download browsers during `pnpm --dir frontend test:e2e`.

When bumping Playwright (or when rebuilding the offline cache), perform the following steps from a machine with internet access:

1. Start with a clean cache directory:
   ```bash
   rm -rf .playwright-browsers
   mkdir -p .playwright-browsers
   ```
2. Install the desired browsers into the repository cache. The `--with-deps` flag is optional and only required when the host can reach the apt repositories:
   ```bash
   PLAYWRIGHT_BROWSERS_PATH="$(pwd)/.playwright-browsers" pnpm --dir frontend exec playwright install
   ```
3. (Optional) Package the cache into a tarball that can be shipped to air-gapped environments:
   ```bash
   tar -C .playwright-browsers -czf .playwright-browsers.tar.gz .
   ```
4. Copy `.playwright-browsers/` (or the tarball) into the offline environment. If the offline environment already has the cache in `~/.cache/ms-playwright`, you can skip this step.
5. Verify the cached bundle works without touching the network:
   ```bash
   PLAYWRIGHT_SKIP_BROWSER_INSTALL=1 pnpm --dir frontend test:e2e
   ```

If the environment lacks apt access, set `PLAYWRIGHT_INSTALL_WITH_DEPS=0` before invoking the E2E helper. The wrapper script will then reuse the cached browser binaries instead of attempting to install additional system packages.
