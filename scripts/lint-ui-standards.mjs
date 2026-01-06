#!/usr/bin/env node
/**
 * Targeted UI Standards linter.
 *
 * Why this exists:
 * - Repo-wide enforcement isn't feasible yet (legacy UI has many violations).
 * - We still want strict enforcement for canonical primitives and the
 *   Multi-Scenario/Feasibility north-star module.
 *
 * Current rules (strict for scoped files):
 * - No raw font stacks (e.g. "ui-monospace", "Inter") in CSS/TSX; use tokens.
 * - No numeric/"bold" fontWeight in TSX inline styles; use token vars.
 * - No mono font-family on label-like selectors (titles/subtitles/labels).
 */
import { readFile, readdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { dirname, extname, resolve } from 'node:path'
import process from 'node:process'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const projectRoot = resolve(__dirname, '..')

const SCOPED_DIRS = [
  resolve(projectRoot, 'frontend/src/components/canonical'),
  resolve(
    projectRoot,
    'frontend/src/app/pages/site-acquisition/components/multi-scenario-comparison'
  ),
]

const SCOPED_FILES = [resolve(projectRoot, 'frontend/src/styles/site-acquisition.css')]

const ALLOWED_FONT_FAMILY_VALUE = /^\s*(var\(--ob-font-family-[^)]+\)|inherit|unset|initial)\s*$/i
const RAW_FONT_FAMILY_MARKERS = [
  'ui-monospace',
  'SFMono-Regular',
  'Menlo',
  'Monaco',
  'JetBrains Mono',
  'Roboto Mono',
  "'Inter'",
  '"Inter"',
  'Inter,',
]

const LABEL_SELECTOR = /__(title|subtitle|label|header|heading|section-title)\b/i
const TECHNICAL_SELECTOR = /__(id|code|timestamp|marker|meta|telemetry)\b/i

function isHiddenDir(name) {
  return name.startsWith('.') || name === 'node_modules' || name === 'dist'
}

async function walk(dir) {
  const out = []
  const entries = await readdir(dir, { withFileTypes: true })
  for (const entry of entries) {
    if (entry.isDirectory()) {
      if (isHiddenDir(entry.name)) continue
      out.push(...(await walk(resolve(dir, entry.name))))
      continue
    }
    out.push(resolve(dir, entry.name))
  }
  return out
}

function formatViolation({ path, line, rule, snippet }) {
  return `${path}:${line} [${rule}] ${snippet}`
}

function checkTsxTypography(path, content) {
  const violations = []
  const lines = content.split(/\r?\n/)

  const fontFamilyRe = /fontFamily\s*:\s*(['"`])([^'"`]+)\1/g
  const fontWeightRe = /fontWeight\s*:\s*(['"`])?([0-9]{3}|bold|normal)\1?/g

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    if (line.trim().startsWith('//')) continue

    for (const marker of RAW_FONT_FAMILY_MARKERS) {
      if (line.includes(marker) && line.includes('fontFamily')) {
        violations.push({
          path,
          line: i + 1,
          rule: 'no-raw-font-family',
          snippet: line.trim(),
        })
        break
      }
    }

    let match
    while ((match = fontFamilyRe.exec(line)) !== null) {
      const value = match[2].trim()
      if (!value.includes('var(--ob-font-family-') && value !== 'inherit') {
        violations.push({
          path,
          line: i + 1,
          rule: 'font-family-must-use-token',
          snippet: line.trim(),
        })
      }
    }

    while ((match = fontWeightRe.exec(line)) !== null) {
      const value = match[2].trim()
      if (/^\d{3}$/.test(value) || value === 'bold' || value === 'normal') {
        violations.push({
          path,
          line: i + 1,
          rule: 'font-weight-must-use-token',
          snippet: line.trim(),
        })
      }
    }
  }

  return violations
}

function checkCssTypography(path, content, { selectorScope }) {
  const violations = []
  const lines = content.split(/\r?\n/)

  const stack = []
  let pendingSelector = ''

  function currentRuleSelector() {
    for (let i = stack.length - 1; i >= 0; i--) {
      if (stack[i].type === 'rule') return stack[i].selector
    }
    return null
  }

  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i]
    const line = raw.trim()
    if (!line) continue
    if (line.startsWith('/*') || line.startsWith('*') || line.startsWith('//')) continue

    const openCount = (raw.match(/{/g) || []).length
    const closeCount = (raw.match(/}/g) || []).length

    if (openCount > 0) {
      const before = raw.split('{')[0].trim()
      const selectorText = `${pendingSelector} ${before}`.trim()
      pendingSelector = ''
      stack.push({
        type: selectorText.startsWith('@') ? 'at' : 'rule',
        selector: selectorText,
      })
    } else if (line.endsWith(',') || (!line.includes(':') && !line.includes(';') && !line.includes('}'))) {
      // likely multi-line selector continuation
      pendingSelector = `${pendingSelector} ${line}`.trim()
    }

    const selector = currentRuleSelector()
    const inScope = selector && selectorScope.test(selector)

    if (inScope) {
      const decl = line.match(/font-family\s*:\s*([^;]+);/i)
      if (decl) {
        const value = decl[1].trim()
        if (!ALLOWED_FONT_FAMILY_VALUE.test(value)) {
          violations.push({
            path,
            line: i + 1,
            rule: 'font-family-must-use-token',
            snippet: raw.trim(),
          })
        }

        const usesMono = value.includes('var(--ob-font-family-mono)')
        const labelLike = LABEL_SELECTOR.test(selector) && !TECHNICAL_SELECTOR.test(selector)
        if (usesMono && labelLike) {
          violations.push({
            path,
            line: i + 1,
            rule: 'labels-must-not-be-mono',
            snippet: `${selector} → ${raw.trim()}`,
          })
        }

        for (const marker of RAW_FONT_FAMILY_MARKERS) {
          if (value.includes(marker)) {
            violations.push({
              path,
              line: i + 1,
              rule: 'no-raw-font-family',
              snippet: raw.trim(),
            })
            break
          }
        }
      }
    }

    if (closeCount > 0) {
      for (let c = 0; c < closeCount; c++) stack.pop()
    }
  }

  return violations
}

async function run() {
  const files = []
  for (const dir of SCOPED_DIRS) {
    files.push(...(await walk(dir)))
  }
  files.push(...SCOPED_FILES)

  const scopedFiles = files.filter((p) => {
    const ext = extname(p)
    return ext === '.tsx' || ext === '.ts' || ext === '.css'
  })

  const violations = []

  for (const path of scopedFiles) {
    const content = await readFile(path, 'utf8')
    const ext = extname(path)
    if (ext === '.css') {
      violations.push(...checkCssTypography(path, content, { selectorScope: /.*/ }))
      continue
    }
    violations.push(...checkTsxTypography(path, content))
  }

  if (violations.length > 0) {
    console.error('UI standards lint failed (typography/tokenization).')
    for (const v of violations.slice(0, 80)) console.error(`  ${formatViolation(v)}`)
    if (violations.length > 80) console.error(`  ... and ${violations.length - 80} more`)
    process.exit(1)
  }
}

run().catch((error) => {
  console.error('UI standards lint failed to run:', error)
  process.exit(1)
})
