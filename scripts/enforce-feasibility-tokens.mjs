#!/usr/bin/env node
import { readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const projectRoot = resolve(__dirname, '..')

const filesToCheck = [
  {
    path: resolve(projectRoot, 'frontend/src/index.css'),
    filter: (line) => line.includes('feasibility') || line.includes('finance'),
  },
  {
    path: resolve(projectRoot, 'frontend/src/modules/feasibility/FeasibilityWizard.tsx'),
    filter: () => true,
  },
  {
    path: resolve(projectRoot, 'frontend/src/modules/finance/FinanceWorkspace.tsx'),
    filter: () => true,
  },
]

const HEX_PATTERN = /#[0-9a-fA-F]{3,6}/

async function run() {
  const failures = []

  for (const { path, filter } of filesToCheck) {
    const content = await readFile(path, 'utf8')
    const lines = content.split(/\r?\n/)

    lines.forEach((line, index) => {
      if (!filter(line)) {
        return
      }
      if (HEX_PATTERN.test(line)) {
        failures.push({
          path,
          line: index + 1,
          snippet: line.trim(),
        })
      }
    })
  }

  if (failures.length > 0) {
    console.error('Design token lint failed. Replace raw hex values with shared tokens in the feasibility module.')
    failures.forEach(({ path, line, snippet }) => {
      console.error(`  ${path}:${line} → ${snippet}`)
    })
    process.exit(1)
  }
}

run().catch((error) => {
  console.error('Token enforcement script failed:', error)
  process.exit(1)
})
