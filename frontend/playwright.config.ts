import { defineConfig } from '@playwright/test'
import path from 'node:path'

const rootDir = path.resolve(__dirname, '..')

export default defineConfig({
  testDir: path.resolve(__dirname, 'tests/e2e'),
  timeout: 120_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: 'http://127.0.0.1:4173',
    trace: 'on-first-retry',
  },
  webServer: [
    {
      command: 'uvicorn app.main:app --host 127.0.0.1 --port 8000',
      cwd: path.resolve(rootDir, 'backend'),
      env: {
        PYTHONPATH: path.resolve(rootDir, 'backend'),
      },
      port: 8000,
      reuseExistingServer: !process.env.CI,
      stdout: 'pipe',
      stderr: 'pipe',
      timeout: 120_000,
    },
    {
      command: 'pnpm dev -- --host 127.0.0.1 --port 4173',
      cwd: path.resolve(rootDir, 'frontend'),
      env: {
        VITE_API_BASE_URL: process.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/',
      },
      port: 4173,
      reuseExistingServer: !process.env.CI,
      stdout: 'pipe',
      stderr: 'pipe',
      timeout: 120_000,
    },
  ],
})
