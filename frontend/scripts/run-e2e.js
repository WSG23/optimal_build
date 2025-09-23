#!/usr/bin/env node
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const repoRoot = path.resolve(__dirname, '..', '..');
const defaultCache = path.join(repoRoot, '.playwright-browsers');
const env = { ...process.env };

if (!env.PLAYWRIGHT_BROWSERS_PATH || env.PLAYWRIGHT_BROWSERS_PATH.trim() === '') {
  env.PLAYWRIGHT_BROWSERS_PATH = defaultCache;
}

const cachePath = env.PLAYWRIGHT_BROWSERS_PATH;

if (!fs.existsSync(cachePath)) {
  console.error(`Playwright browser cache not found at ${cachePath}.`);
  console.error('Populate the directory by running the install command on a machine with internet access:');
  console.error('  pnpm -C frontend exec playwright install --with-deps');
  console.error('Then copy the contents of ~/.cache/ms-playwright into .playwright-browsers/.');
  process.exit(1);
}

const metadataFile = path.join(cachePath, 'browsers.json');
if (!fs.existsSync(metadataFile)) {
  console.error(`Playwright metadata missing at ${metadataFile}.`);
  console.error('Ensure the cache directory contains the downloaded browser builds expected by Playwright.');
  process.exit(1);
}

const result = spawnSync('playwright', ['test'], {
  stdio: 'inherit',
  cwd: path.resolve(__dirname, '..'),
  env,
});

if (result.error) {
  console.error(result.error);
}

process.exit(result.status ?? 1);

