#!/usr/bin/env node
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const repoRoot = path.resolve(__dirname, '..', '..');
const frontendRoot = path.resolve(__dirname, '..');
const defaultCache = path.join(repoRoot, '.playwright-browsers');
const env = { ...process.env };

if (!env.PLAYWRIGHT_BROWSERS_PATH || env.PLAYWRIGHT_BROWSERS_PATH.trim() === '') {
  env.PLAYWRIGHT_BROWSERS_PATH = defaultCache;
}

ensurePlaywrightBrowsers();

const cachePath = env.PLAYWRIGHT_BROWSERS_PATH;

if (!fs.existsSync(cachePath)) {
  console.error(`Playwright browser cache not found at ${cachePath}.`);
  console.error('Ensure the install command completed successfully:');
  console.error('  pnpm -C frontend exec playwright install --with-deps');
  process.exit(1);
}

const metadataFile = path.join(cachePath, 'browsers.json');
if (!fs.existsSync(metadataFile)) {
  console.error(`Playwright metadata missing at ${metadataFile}.`);
  console.error('Ensure the install command completed successfully:');
  console.error('  pnpm -C frontend exec playwright install --with-deps');
  process.exit(1);
}

const result = runPnpm(['exec', 'playwright', 'test']);

if (result.error) {
  console.error(result.error);
}

process.exit(result.status ?? 1);

function ensurePlaywrightBrowsers() {
  console.log('Ensuring Playwright browser binaries are installed...');
  const installArgs = ['exec', 'playwright', 'install', '--with-deps'];
  const installResult = runPnpm(installArgs);

  if (installResult.error) {
    console.error(installResult.error);
  }

  if ((installResult.status ?? 1) !== 0) {
    console.error('Failed to install Playwright browser binaries.');
    process.exit(installResult.status ?? 1);
  }
}

function runPnpm(args) {
  const options = {
    stdio: 'inherit',
    cwd: frontendRoot,
    env,
  };

  if (process.env.npm_execpath && process.execPath) {
    return spawnSync(process.execPath, [process.env.npm_execpath, ...args], options);
  }

  const pnpmCommand = process.platform === 'win32' ? 'pnpm.cmd' : 'pnpm';
  return spawnSync(pnpmCommand, args, options);
}

