#!/usr/bin/env node

import { readdirSync, statSync } from 'node:fs'
import path from 'node:path'
import { spawn } from 'node:child_process'

const coverageFlag = '--coverage'
const coverageRequested = process.argv.includes(coverageFlag)

const workingDir = process.cwd()
const srcDir = path.join(workingDir, 'src')

const tests = []

function collectTests(directory) {
  const entries = readdirSync(directory, { withFileTypes: true })
  for (const entry of entries) {
    const fullPath = path.join(directory, entry.name)
    if (entry.isDirectory()) {
      collectTests(fullPath)
    } else if (/\.test\.(?:ts|tsx)$/.test(entry.name)) {
      tests.push(fullPath)
    }
  }
}

try {
  statSync(srcDir)
} catch (error) {
  console.error(`Unable to find src directory at ${srcDir}`)
  process.exit(1)
}

collectTests(srcDir)

if (tests.length === 0) {
  console.log('No frontend test files were found under src/.')
  process.exit(0)
}

tests.sort()

const command = process.platform === 'win32' ? 'npx.cmd' : 'npx'
const baseArgs = coverageRequested
  ? [
      'c8',
      '--reporter=text',
      '--reporter=lcov',
      '--check-coverage',
      '--lines=80',
      'tsx',
      '--test',
      ...tests,
    ]
  : ['tsx', '--test', ...tests]

const filteredArgs = coverageRequested
  ? process.argv.filter((arg) => arg !== coverageFlag)
  : process.argv.slice(2)

const child = spawn(command, baseArgs.concat(filteredArgs), {
  stdio: 'inherit',
  cwd: workingDir,
})

child.on('exit', (code) => {
  process.exit(code ?? 0)
})

child.on('error', (error) => {
  console.error(error)
  process.exit(1)
})
