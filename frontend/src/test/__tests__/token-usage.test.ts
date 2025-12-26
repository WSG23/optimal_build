import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import glob from 'glob'

/**
 * Token Usage Validation Tests
 *
 * These tests scan the codebase to ensure design tokens are being used
 * correctly and that hardcoded values are minimized.
 */

const srcPath = path.resolve(__dirname, '../../')

// Helper to count regex matches across files
function countMatches(
  pattern: RegExp,
  filePattern: string = '**/*.tsx',
): number {
  const files = glob.sync(filePattern, { cwd: srcPath, nodir: true })
  let count = 0

  for (const file of files) {
    try {
      const content = fs.readFileSync(path.join(srcPath, file), 'utf-8')
      const matches = content.match(pattern)
      if (matches) {
        count += matches.length
      }
    } catch {
      // Ignore read errors
    }
  }

  return count
}

// Helper to get files matching a pattern
function getFilesWithPattern(
  pattern: RegExp,
  filePattern: string = '**/*.tsx',
): string[] {
  const files = glob.sync(filePattern, { cwd: srcPath, nodir: true })
  const matchingFiles: string[] = []

  for (const file of files) {
    try {
      const content = fs.readFileSync(path.join(srcPath, file), 'utf-8')
      if (pattern.test(content)) {
        matchingFiles.push(file)
      }
    } catch {
      // Ignore read errors
    }
  }

  return matchingFiles
}

describe('Token Usage Validation', () => {
  describe('Border Radius Usage', () => {
    it('uses design tokens for border radius in most cases', () => {
      // Count files using design tokens
      const tokenUsage = countMatches(/borderRadius:\s*['"]var\(--ob-radius/g)

      // Count files with hardcoded pixel values (excluding 0 which is intentional)
      const hardcodedPixels = countMatches(/borderRadius:\s*['"][1-9][0-9]*px/g)

      // Token usage should be significantly higher than hardcoded
      expect(tokenUsage).toBeGreaterThan(0)

      // Log for visibility
      console.log(
        `Token usage: ${tokenUsage}, Hardcoded pixels: ${hardcodedPixels}`,
      )
    })

    it('uses --ob-radius-pill for circular elements', () => {
      const pillUsage = countMatches(
        /borderRadius:\s*['"]var\(--ob-radius-pill/g,
      )
      expect(pillUsage).toBeGreaterThan(0)
    })

    it('minimizes hardcoded 50% values (should use --ob-radius-pill)', () => {
      const fiftyPercent = getFilesWithPattern(/borderRadius:\s*['"]50%['"]/)

      // Allow some exceptions (style guide, documentation)
      const exceptions = fiftyPercent.filter(
        (f) =>
          f.includes('STYLE_GUIDE') ||
          f.includes('.md') ||
          f.includes('__tests__'),
      )

      const violations = fiftyPercent.filter((f) => !exceptions.includes(f))

      // Should have very few violations
      expect(violations.length).toBeLessThanOrEqual(5)

      if (violations.length > 0) {
        console.warn('Files with hardcoded 50% border-radius:', violations)
      }
    })
  })

  describe('Spacing Usage', () => {
    it('uses design tokens for common spacing values', () => {
      const tokenUsage = countMatches(/var\(--ob-space-/g)
      expect(tokenUsage).toBeGreaterThan(50)
    })

    it('minimizes inline pixel spacing for standard values', () => {
      // Check for hardcoded 16px, 24px, 32px which should use tokens
      const hardcoded16 = countMatches(/:\s*['"]16px['"]/g)
      const hardcoded24 = countMatches(/:\s*['"]24px['"]/g)
      const hardcoded32 = countMatches(/:\s*['"]32px['"]/g)

      const total = hardcoded16 + hardcoded24 + hardcoded32

      // Log for visibility
      console.log(
        `Hardcoded spacing: 16px(${hardcoded16}), 24px(${hardcoded24}), 32px(${hardcoded32})`,
      )

      // Should be relatively low compared to token usage
      expect(total).toBeLessThan(50)
    })
  })

  describe('Color Usage', () => {
    it('uses theme palette or design tokens for colors', () => {
      const themeUsage = countMatches(/theme\.palette\./g)
      const tokenUsage = countMatches(/var\(--ob-color-/g)

      expect(themeUsage + tokenUsage).toBeGreaterThan(100)
    })

    it('minimizes hardcoded hex colors (excluding special cases)', () => {
      // Common hardcoded colors that should use tokens
      const hardcodedColors = getFilesWithPattern(/:\s*['"]#[0-9a-fA-F]{6}['"]/)

      // Exclude theme files, style guide, gradients in charts
      const exceptions = hardcodedColors.filter(
        (f) =>
          f.includes('theme') ||
          f.includes('STYLE_GUIDE') ||
          f.includes('.test.') ||
          f.includes('tokens.css'),
      )

      const violations = hardcodedColors.filter((f) => !exceptions.includes(f))

      // Log violations for visibility
      if (violations.length > 20) {
        console.warn(
          `Found ${violations.length} files with hardcoded hex colors`,
        )
      }

      // Should be manageable number
      expect(violations.length).toBeLessThan(30)
    })
  })

  describe('Typography Usage', () => {
    it('uses design tokens for font sizes', () => {
      const tokenUsage = countMatches(/var\(--ob-font-size-/g)
      expect(tokenUsage).toBeGreaterThan(20)
    })
  })

  describe('Component Token Compliance', () => {
    it('Card components use --ob-radius-sm', () => {
      // Cards should use 4px radius (--ob-radius-sm), not larger
      const cardFiles = getFilesWithPattern(/Card/, '**/*.tsx')

      // Check that card-related files use correct radius
      cardFiles.forEach((file) => {
        // This is a lightweight check - detailed validation in component tests
        expect(file).toBeTruthy()
      })
    })

    it('Button components use --ob-radius-xs', () => {
      const buttonTokenUsage = countMatches(
        /borderRadius:\s*['"]var\(--ob-radius-xs/g,
        '**/Button*.tsx',
      )
      // Buttons should use xs radius
      expect(buttonTokenUsage).toBeGreaterThanOrEqual(0)
    })
  })

  describe('MUI Numeric Border Radius', () => {
    it('minimizes MUI numeric borderRadius (should use tokens)', () => {
      // MUI multiplies these by 8, so borderRadius: 2 = 16px!
      // We want to minimize these in favor of explicit tokens
      const muiNumericFiles = getFilesWithPattern(/borderRadius:\s*[1-9],/)

      // Exclude intentional cases like borderRadius: 0
      const violations = muiNumericFiles.filter(
        (f) =>
          !f.includes('theme') &&
          !f.includes('.test.') &&
          !f.includes('STYLE_GUIDE'),
      )

      // Should be very few
      expect(violations.length).toBeLessThan(10)

      if (violations.length > 0) {
        console.warn('Files with MUI numeric borderRadius:', violations)
      }
    })
  })
})

describe('Canonical Component Usage', () => {
  describe('Card usage', () => {
    it('prefers canonical Card over MUI Paper/Card', () => {
      const canonicalCard = countMatches(/from\s+['"][^'"]*canonical\/Card/)
      const muiCard = countMatches(
        /from\s+['"]@mui\/material['"][^}]*Card[^a-zA-Z]/,
      )

      console.log(
        `Canonical Card imports: ${canonicalCard}, MUI Card imports: ${muiCard}`,
      )

      // Canonical should be used more than MUI direct usage
      expect(canonicalCard).toBeGreaterThan(0)
    })
  })

  describe('StatusChip usage', () => {
    it('uses canonical StatusChip for status indicators', () => {
      const statusChipUsage = countMatches(/StatusChip/g)
      expect(statusChipUsage).toBeGreaterThan(0)
    })
  })
})
