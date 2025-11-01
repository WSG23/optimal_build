import { defineConfig } from '@playwright/test'
import { defineBddConfig } from 'playwright-bdd'
import path from 'node:path'

const rootDir = path.resolve(__dirname, '..')
const backendDir = path.resolve(rootDir, 'backend')
const pythonPathEntries = [backendDir, rootDir]
if (process.env.PYTHONPATH && process.env.PYTHONPATH.trim() !== '') {
  pythonPathEntries.push(process.env.PYTHONPATH)
}
const pythonPath = pythonPathEntries.filter(Boolean).join(path.delimiter)

const defaultDbPath = path.resolve(rootDir, '.playwright-e2e.db')
const defaultDbUrl = `sqlite+aiosqlite:///${defaultDbPath.replace(/\\/g, '/')}`
const configuredDbUrl =
  process.env.SQLALCHEMY_DATABASE_URI ??
  process.env.PLAYWRIGHT_E2E_DB_URL ??
  defaultDbUrl
const e2eDbUrl = process.env.PLAYWRIGHT_E2E_DB_URL ?? configuredDbUrl
const buildableUsePostgis = process.env.BUILDABLE_USE_POSTGIS ?? '0'

export default defineConfig({
  testDir: path.resolve(__dirname, 'tests/e2e'),
  timeout: 120_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: 'http://127.0.0.1:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'e2e',
      testDir: path.resolve(__dirname, 'tests/e2e'),
    },
    {
      name: 'bdd',
      testDir: path.resolve(__dirname, 'tests/bdd/.generated'),
    },
  ],
  webServer: [
    {
      command:
        'python -m backend.uvicorn app.main:app --host 127.0.0.1 --port 8000',
      cwd: backendDir,
      env: {
        PYTHONPATH: pythonPath,
        SQLALCHEMY_DATABASE_URI: configuredDbUrl,
        PLAYWRIGHT_E2E_DB_URL: e2eDbUrl,
        BUILDABLE_USE_POSTGIS: buildableUsePostgis,
      },
      port: 8000,
      reuseExistingServer: !process.env.CI,
      stdout: 'pipe',
      stderr: 'pipe',
      timeout: 120_000,
    },
    {
      command: 'pnpm dev -- --host 127.0.0.1 --port 3000',
      cwd: path.resolve(rootDir, 'frontend'),
      env: {
        VITE_API_BASE_URL:
          process.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/',
      },
      port: 3000,
      reuseExistingServer: !process.env.CI,
      stdout: 'pipe',
      stderr: 'pipe',
      timeout: 120_000,
    },
  ],
})

export const bdd = defineBddConfig({
  features: ['features/**/*.feature'],
  steps: ['tests/bdd/steps/**/*.ts'],
  outputDir: 'tests/bdd/.generated',
})
