#!/usr/bin/env node
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const repoRoot = path.resolve(__dirname, '..', '..');
const defaultCache = path.join(repoRoot, '.playwright-browsers');
const env = { ...process.env };
const backendDir = path.resolve(repoRoot, 'backend');
const sqlitePath = path.resolve(repoRoot, '.playwright-e2e.db');
const sqliteUrl =
  env.PLAYWRIGHT_E2E_DB_URL ?? `sqlite+aiosqlite:///${sqlitePath.replace(/\\/g, '/')}`;
env.PLAYWRIGHT_E2E_DB_URL = sqliteUrl;
if (!env.SQLALCHEMY_DATABASE_URI || env.SQLALCHEMY_DATABASE_URI.trim() === '') {
  env.SQLALCHEMY_DATABASE_URI = sqliteUrl;
}
if (!env.BUILDABLE_USE_POSTGIS || env.BUILDABLE_USE_POSTGIS.trim() === '') {
  env.BUILDABLE_USE_POSTGIS = '0';
}

const pythonPathParts = [backendDir, repoRoot];
if (env.PYTHONPATH && env.PYTHONPATH.trim() !== '') {
  pythonPathParts.push(env.PYTHONPATH);
}
env.PYTHONPATH = pythonPathParts.filter(Boolean).join(path.delimiter);

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

fs.rmSync(sqlitePath, { force: true });

const seedResult = spawnSync('python', ['-m', 'scripts.seed_screening'], {
  stdio: 'inherit',
  cwd: backendDir,
  env,
});

if (seedResult.status !== 0) {
  process.exit(seedResult.status ?? 1);
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

