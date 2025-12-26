import { describe, it, expect, beforeAll } from 'vitest'
import fs from 'fs'
import path from 'path'

/**
 * Design Token Validation Tests
 *
 * These tests ensure the design token system is properly configured and
 * that all required tokens are defined in the canonical tokens.css file.
 */

describe('Design Token System', () => {
  let tokensCSS: string

  beforeAll(() => {
    // Read the canonical tokens.css file
    const tokensPath = path.resolve(
      __dirname,
      '../../../../core/design-tokens/tokens.css',
    )
    tokensCSS = fs.readFileSync(tokensPath, 'utf-8')
  })

  describe('Border Radius Tokens (Square Cyber-Minimalism)', () => {
    const requiredRadiusTokens = [
      { token: '--ob-radius-none', value: '0' },
      { token: '--ob-radius-xs', description: '2px - buttons, tags, chips' },
      { token: '--ob-radius-sm', description: '4px - cards, panels, tiles' },
      { token: '--ob-radius-md', description: '6px - inputs, select boxes' },
      { token: '--ob-radius-lg', description: '8px - modals, windows ONLY' },
      {
        token: '--ob-radius-pill',
        description: '9999px - avatars, circular icons',
      },
    ]

    requiredRadiusTokens.forEach(({ token, description }) => {
      it(`defines ${token} ${description ? `(${description})` : ''}`, () => {
        const regex = new RegExp(`${token}:\\s*[^;]+;`)
        expect(tokensCSS).toMatch(regex)
      })
    })

    it('defines --ob-radius-xs as 0.125rem (2px)', () => {
      expect(tokensCSS).toMatch(/--ob-radius-xs:\s*0\.125rem/)
    })

    it('defines --ob-radius-sm as 0.25rem (4px)', () => {
      expect(tokensCSS).toMatch(/--ob-radius-sm:\s*0\.25rem/)
    })

    it('defines --ob-radius-md as 0.375rem (6px)', () => {
      expect(tokensCSS).toMatch(/--ob-radius-md:\s*0\.375rem/)
    })

    it('defines --ob-radius-lg as 0.5rem (8px)', () => {
      expect(tokensCSS).toMatch(/--ob-radius-lg:\s*0\.5rem/)
    })

    it('defines --ob-radius-pill as 9999px', () => {
      expect(tokensCSS).toMatch(/--ob-radius-pill:\s*9999px/)
    })
  })

  describe('Spacing Tokens', () => {
    const requiredSpacingTokens = [
      '--ob-space-025', // 4px
      '--ob-space-050', // 8px
      '--ob-space-075', // 12px
      '--ob-space-100', // 16px
      '--ob-space-125', // 20px
      '--ob-space-150', // 24px
      '--ob-space-175', // 28px
      '--ob-space-200', // 32px
      '--ob-space-250', // 40px
      '--ob-space-300', // 48px
      '--ob-space-400', // 64px
    ]

    requiredSpacingTokens.forEach((token) => {
      it(`defines ${token}`, () => {
        const regex = new RegExp(`${token}:\\s*[^;]+;`)
        expect(tokensCSS).toMatch(regex)
      })
    })

    it('uses rem units for spacing tokens', () => {
      expect(tokensCSS).toMatch(/--ob-space-100:\s*1rem/)
    })
  })

  describe('Color Tokens', () => {
    describe('Background Colors', () => {
      const bgTokens = [
        '--ob-color-bg-root',
        '--ob-color-bg-surface',
        '--ob-color-bg-surface-elevated',
        '--ob-color-bg-muted',
      ]

      bgTokens.forEach((token) => {
        it(`defines ${token}`, () => {
          const regex = new RegExp(`${token}:\\s*[^;]+;`)
          expect(tokensCSS).toMatch(regex)
        })
      })
    })

    describe('Text Colors', () => {
      const textTokens = [
        '--ob-color-text',
        '--ob-color-text-primary',
        '--ob-color-text-secondary',
        '--ob-color-text-muted',
        '--ob-color-text-subtle',
        '--ob-color-text-inverse',
      ]

      textTokens.forEach((token) => {
        it(`defines ${token}`, () => {
          const regex = new RegExp(`${token}:\\s*[^;]+;`)
          expect(tokensCSS).toMatch(regex)
        })
      })
    })

    describe('Border Colors', () => {
      const borderTokens = [
        '--ob-color-border-subtle',
        '--ob-color-border-faint',
        '--ob-color-border-neutral',
        '--ob-color-border-strong',
        '--ob-color-border-focus',
      ]

      borderTokens.forEach((token) => {
        it(`defines ${token}`, () => {
          const regex = new RegExp(`${token}:\\s*[^;]+;`)
          expect(tokensCSS).toMatch(regex)
        })
      })
    })

    describe('Status Colors', () => {
      const statusTokens = [
        '--ob-color-status-success-bg',
        '--ob-color-status-success-text',
        '--ob-color-status-warning-bg',
        '--ob-color-status-warning-text',
        '--ob-color-status-error-bg',
        '--ob-color-status-error-text',
        '--ob-color-status-info-bg',
        '--ob-color-status-info-text',
      ]

      statusTokens.forEach((token) => {
        it(`defines ${token}`, () => {
          const regex = new RegExp(`${token}:\\s*[^;]+;`)
          expect(tokensCSS).toMatch(regex)
        })
      })
    })

    describe('Brand Colors', () => {
      const brandTokens = [
        '--ob-color-brand-primary',
        '--ob-color-brand-accent',
        '--ob-color-brand-soft',
        '--ob-color-brand-muted',
      ]

      brandTokens.forEach((token) => {
        it(`defines ${token}`, () => {
          const regex = new RegExp(`${token}:\\s*[^;]+;`)
          expect(tokensCSS).toMatch(regex)
        })
      })
    })
  })

  describe('Typography Tokens', () => {
    describe('Font Families', () => {
      it('defines --ob-font-family-base', () => {
        expect(tokensCSS).toMatch(/--ob-font-family-base:/)
      })

      it('defines --ob-font-family-mono', () => {
        expect(tokensCSS).toMatch(/--ob-font-family-mono:/)
      })
    })

    describe('Font Sizes', () => {
      const fontSizeTokens = [
        '--ob-font-size-2xs',
        '--ob-font-size-xs',
        '--ob-font-size-sm',
        '--ob-font-size-md',
        '--ob-font-size-base',
        '--ob-font-size-lg',
        '--ob-font-size-xl',
        '--ob-font-size-2xl',
        '--ob-font-size-3xl',
        '--ob-font-size-4xl',
        '--ob-font-size-5xl',
      ]

      fontSizeTokens.forEach((token) => {
        it(`defines ${token}`, () => {
          const regex = new RegExp(`${token}:\\s*[^;]+;`)
          expect(tokensCSS).toMatch(regex)
        })
      })

      it('uses rem units for font sizes', () => {
        expect(tokensCSS).toMatch(/--ob-font-size-base:\s*1rem/)
      })
    })

    describe('Font Weights', () => {
      const fontWeightTokens = [
        '--ob-font-weight-regular',
        '--ob-font-weight-medium',
        '--ob-font-weight-semibold',
        '--ob-font-weight-bold',
      ]

      fontWeightTokens.forEach((token) => {
        it(`defines ${token}`, () => {
          const regex = new RegExp(`${token}:\\s*[^;]+;`)
          expect(tokensCSS).toMatch(regex)
        })
      })
    })
  })

  describe('Shadow Tokens', () => {
    const shadowTokens = [
      '--ob-shadow-sm',
      '--ob-shadow-md',
      '--ob-shadow-lg',
      '--ob-shadow-xl',
      '--ob-shadow-glass',
      '--ob-shadow-glass-lg',
    ]

    shadowTokens.forEach((token) => {
      it(`defines ${token}`, () => {
        const regex = new RegExp(`${token}:\\s*[^;]+;`)
        expect(tokensCSS).toMatch(regex)
      })
    })
  })

  describe('Z-Index Tokens', () => {
    const zIndexTokens = [
      '--ob-z-base',
      '--ob-z-dropdown',
      '--ob-z-sticky',
      '--ob-z-fixed',
      '--ob-z-modal-backdrop',
      '--ob-z-modal',
      '--ob-z-popover',
      '--ob-z-tooltip',
    ]

    zIndexTokens.forEach((token) => {
      it(`defines ${token}`, () => {
        const regex = new RegExp(`${token}:\\s*[^;]+;`)
        expect(tokensCSS).toMatch(regex)
      })
    })

    it('defines z-index values in correct order', () => {
      const baseMatch = tokensCSS.match(/--ob-z-base:\s*(\d+)/)
      const dropdownMatch = tokensCSS.match(/--ob-z-dropdown:\s*(\d+)/)
      const modalMatch = tokensCSS.match(/--ob-z-modal:\s*(\d+)/)
      const tooltipMatch = tokensCSS.match(/--ob-z-tooltip:\s*(\d+)/)

      expect(baseMatch).toBeTruthy()
      expect(dropdownMatch).toBeTruthy()
      expect(modalMatch).toBeTruthy()
      expect(tooltipMatch).toBeTruthy()

      const base = parseInt(baseMatch![1])
      const dropdown = parseInt(dropdownMatch![1])
      const modal = parseInt(modalMatch![1])
      const tooltip = parseInt(tooltipMatch![1])

      expect(base).toBeLessThan(dropdown)
      expect(dropdown).toBeLessThan(modal)
      expect(modal).toBeLessThan(tooltip)
    })
  })

  describe('Blur Tokens', () => {
    const blurTokens = [
      '--ob-blur-sm',
      '--ob-blur-xs',
      '--ob-blur-md',
      '--ob-blur-xl',
      '--ob-blur-lg',
    ]

    blurTokens.forEach((token) => {
      it(`defines ${token}`, () => {
        const regex = new RegExp(`${token}:\\s*[^;]+;`)
        expect(tokensCSS).toMatch(regex)
      })
    })
  })

  describe('Size Tokens', () => {
    const sizeTokens = [
      '--ob-size-icon-sm',
      '--ob-size-icon-md',
      '--ob-size-icon-lg',
      '--ob-size-icon-xl',
      '--ob-max-width-content',
      '--ob-max-width-page',
      '--ob-max-height-panel',
      '--ob-max-height-table',
    ]

    sizeTokens.forEach((token) => {
      it(`defines ${token}`, () => {
        const regex = new RegExp(`${token}:\\s*[^;]+;`)
        expect(tokensCSS).toMatch(regex)
      })
    })
  })

  describe('Border Tokens', () => {
    const borderTokens = [
      '--ob-border-fine',
      '--ob-border-fine-strong',
      '--ob-border-fine-hover',
      '--ob-divider',
      '--ob-divider-strong',
    ]

    borderTokens.forEach((token) => {
      it(`defines ${token}`, () => {
        const regex = new RegExp(`${token}:\\s*[^;]+;`)
        expect(tokensCSS).toMatch(regex)
      })
    })
  })

  describe('Glow Tokens', () => {
    const glowTokens = [
      '--ob-glow-brand-subtle',
      '--ob-glow-brand-medium',
      '--ob-glow-brand-strong',
      '--ob-glow-gold',
      '--ob-glow-success',
      '--ob-glow-error',
      '--ob-glow-warning',
    ]

    glowTokens.forEach((token) => {
      it(`defines ${token}`, () => {
        const regex = new RegExp(`${token}:\\s*[^;]+;`)
        expect(tokensCSS).toMatch(regex)
      })
    })
  })

  describe('Light Theme Overrides', () => {
    it('defines light theme with data-theme attribute', () => {
      expect(tokensCSS).toMatch(/html\[data-theme=['"]light['"]\]/)
    })

    it('overrides background colors for light theme', () => {
      expect(tokensCSS).toMatch(
        /html\[data-theme=['"]light['"]\][\s\S]*--ob-color-bg-root:/,
      )
    })

    it('overrides text colors for light theme', () => {
      expect(tokensCSS).toMatch(
        /html\[data-theme=['"]light['"]\][\s\S]*--ob-color-text-primary:/,
      )
    })
  })

  describe('Token Naming Convention', () => {
    it('follows --ob-[category]-[property] naming pattern', () => {
      // All tokens should start with --ob-
      const tokenMatches = tokensCSS.match(/--ob-[a-z0-9-]+:/g)
      expect(tokenMatches).toBeTruthy()
      expect(tokenMatches!.length).toBeGreaterThan(50) // Should have many tokens

      // All tokens should follow naming convention
      tokenMatches!.forEach((token) => {
        expect(token).toMatch(/^--ob-[a-z]+(-[a-z0-9]+)*:$/)
      })
    })
  })

  describe('CSS Validity', () => {
    it('defines tokens within :root selector', () => {
      expect(tokensCSS).toMatch(/:root\s*\{/)
    })

    it('does not have unclosed braces', () => {
      const openBraces = (tokensCSS.match(/\{/g) || []).length
      const closeBraces = (tokensCSS.match(/\}/g) || []).length
      expect(openBraces).toBe(closeBraces)
    })

    it('all token definitions end with semicolon', () => {
      // Find all token definitions
      const tokenDefs = tokensCSS.match(/--ob-[a-z0-9-]+:\s*[^;]+/g)
      if (tokenDefs) {
        tokenDefs.forEach((def) => {
          // Each should be followed by a semicolon in the original
          const fullPattern = new RegExp(
            def.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ';',
          )
          expect(tokensCSS).toMatch(fullPattern)
        })
      }
    })
  })
})
