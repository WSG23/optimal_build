#!/usr/bin/env node
const { spawnSync } = require('node:child_process')
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')

const repoRoot = path.resolve(__dirname, '..', '..')
const frontendDir = path.resolve(repoRoot, 'frontend')
const defaultCache = path.join(repoRoot, '.playwright-browsers')
const homeCache = path.join(os.homedir(), '.cache', 'ms-playwright')
const env = { ...process.env }
const backendDir = path.resolve(repoRoot, 'backend')
const sqlitePath = path.resolve(repoRoot, '.playwright-e2e.db')
const sqliteUrl =
  env.PLAYWRIGHT_E2E_DB_URL ??
  `sqlite+aiosqlite:///${sqlitePath.replace(/\\/g, '/')}`
env.PLAYWRIGHT_E2E_DB_URL = sqliteUrl
if (!env.SQLALCHEMY_DATABASE_URI || env.SQLALCHEMY_DATABASE_URI.trim() === '') {
  env.SQLALCHEMY_DATABASE_URI = sqliteUrl
}
if (!env.BUILDABLE_USE_POSTGIS || env.BUILDABLE_USE_POSTGIS.trim() === '') {
  env.BUILDABLE_USE_POSTGIS = '0'
}

const pythonPathParts = [backendDir, repoRoot]
if (env.PYTHONPATH && env.PYTHONPATH.trim() !== '') {
  pythonPathParts.push(env.PYTHONPATH)
}
env.PYTHONPATH = pythonPathParts.filter(Boolean).join(path.delimiter)

function hasBrowserMetadata(directory) {
  return fs.existsSync(path.join(directory, 'browsers.json'))
}

if (
  !env.PLAYWRIGHT_BROWSERS_PATH ||
  env.PLAYWRIGHT_BROWSERS_PATH.trim() === ''
) {
  if (hasBrowserMetadata(defaultCache)) {
    env.PLAYWRIGHT_BROWSERS_PATH = defaultCache
  } else if (hasBrowserMetadata(homeCache)) {
    env.PLAYWRIGHT_BROWSERS_PATH = homeCache
  } else {
    env.PLAYWRIGHT_BROWSERS_PATH = defaultCache
  }
}

const cachePath = env.PLAYWRIGHT_BROWSERS_PATH

const pnpmCommand = process.platform === 'win32' ? 'pnpm.cmd' : 'pnpm'

function parseBoolean(value, defaultValue = false) {
  if (value === undefined || value === null) {
    return defaultValue
  }
  const normalized = String(value).trim().toLowerCase()
  if (normalized === '') {
    return defaultValue
  }
  if (['1', 'true', 'yes', 'on'].includes(normalized)) {
    return true
  }
  if (['0', 'false', 'no', 'off'].includes(normalized)) {
    return false
  }
  return defaultValue
}

const shouldSkipInstall = parseBoolean(env.PLAYWRIGHT_SKIP_BROWSER_INSTALL)
let installWithDeps = parseBoolean(env.PLAYWRIGHT_INSTALL_WITH_DEPS, true)

if (!shouldSkipInstall) {
  fs.mkdirSync(cachePath, { recursive: true })

  if (installWithDeps && process.platform === 'linux') {
    const aptProbe = spawnSync('apt-get', ['--version'], {
      stdio: 'ignore',
    })
    if (aptProbe.status !== 0) {
      console.warn(
        'apt-get not available; skipping Playwright --with-deps install.',
      )
      installWithDeps = false
    }
  } else if (installWithDeps && process.platform !== 'linux') {
    installWithDeps = false
  }

  const installArgs = ['exec', 'playwright', 'install']
  if (installWithDeps) {
    installArgs.push('--with-deps')
  }
  const installResult = spawnSync(pnpmCommand, installArgs, {
    stdio: 'inherit',
    cwd: frontendDir,
    env,
  })

  if (installResult.status !== 0) {
    console.warn(
      `Playwright browser installation exited with code ${
        installResult.status ?? 'unknown'
      }.`,
    )
    console.warn('Continuing with existing browser cache.')
  }
} else {
  console.log(
    'PLAYWRIGHT_SKIP_BROWSER_INSTALL set; skipping Playwright install step.',
  )
}

if (!fs.existsSync(cachePath)) {
  console.error(`Playwright browser cache not found at ${cachePath}.`)
  console.error(
    'Populate the directory by running the install command on a machine with internet access:',
  )
  console.error(
    '  PLAYWRIGHT_BROWSERS_PATH="$(pwd)/.playwright-browsers" pnpm -C frontend exec playwright install',
  )
  console.error(
    'Then copy the contents of that directory (or ~/.cache/ms-playwright) into the target environment.',
  )
  process.exit(1)
}

const metadataFile = path.join(cachePath, 'browsers.json')
if (!fs.existsSync(metadataFile)) {
  console.error(`Playwright metadata missing at ${metadataFile}.`)
  console.error(
    'Ensure the cache directory contains the downloaded browser builds expected by Playwright.',
  )
  process.exit(1)
}

fs.rmSync(sqlitePath, { force: true })

const seedResult = spawnSync('python', ['-m', 'scripts.seed_screening'], {
  stdio: 'inherit',
  cwd: backendDir,
  env,
})

if (seedResult.status !== 0) {
  process.exit(seedResult.status ?? 1)
}

const result = spawnSync('playwright', ['test'], {
  stdio: 'inherit',
  cwd: path.resolve(__dirname, '..'),
  env,
})

if (result.error) {
  console.error(result.error)
}

process.exit(result.status ?? 1)
