#!/usr/bin/env node
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const repoRoot = path.resolve(__dirname, '..', '..');
const frontendDir = path.resolve(repoRoot, 'frontend');
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

const pnpmCommand = process.platform === 'win32' ? 'pnpm.cmd' : 'pnpm';

let shouldSkipInstall = false;
if (env.PLAYWRIGHT_SKIP_BROWSER_INSTALL && env.PLAYWRIGHT_SKIP_BROWSER_INSTALL.trim() !== '') {
  const normalized = env.PLAYWRIGHT_SKIP_BROWSER_INSTALL.trim().toLowerCase();
  shouldSkipInstall = ['1', 'true', 'yes'].includes(normalized);
}

if (!shouldSkipInstall) {
  fs.mkdirSync(cachePath, { recursive: true });
  const installArgs = ['exec', 'playwright', 'install', '--with-deps'];
  const installResult = spawnSync(pnpmCommand, installArgs, {
    stdio: 'inherit',
    cwd: frontendDir,
    env,
  });

  if (installResult.status !== 0) {
    console.warn(
      `Playwright browser installation exited with code ${installResult.status ?? 'unknown'}.`
    );
    console.warn('Continuing with existing browser cache.');
  }
} else {
  console.log('PLAYWRIGHT_SKIP_BROWSER_INSTALL set; skipping Playwright install step.');
}

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

