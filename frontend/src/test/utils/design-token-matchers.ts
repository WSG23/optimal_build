import { expect } from 'vitest'

/**
 * Design Token Test Utilities
 *
 * Custom matchers and utilities for testing design token compliance
 * in React components.
 */

// Expected token values for validation
export const TOKEN_VALUES = {
  radius: {
    none: '0',
    xs: 'var(--ob-radius-xs)',
    sm: 'var(--ob-radius-sm)',
    md: 'var(--ob-radius-md)',
    lg: 'var(--ob-radius-lg)',
    pill: 'var(--ob-radius-pill)',
  },
  space: {
    '025': 'var(--ob-space-025)',
    '050': 'var(--ob-space-050)',
    '075': 'var(--ob-space-075)',
    '100': 'var(--ob-space-100)',
    '125': 'var(--ob-space-125)',
    '150': 'var(--ob-space-150)',
    '200': 'var(--ob-space-200)',
    '250': 'var(--ob-space-250)',
    '300': 'var(--ob-space-300)',
    '400': 'var(--ob-space-400)',
  },
  fontSize: {
    '2xs': 'var(--ob-font-size-2xs)',
    xs: 'var(--ob-font-size-xs)',
    sm: 'var(--ob-font-size-sm)',
    md: 'var(--ob-font-size-md)',
    base: 'var(--ob-font-size-base)',
    lg: 'var(--ob-font-size-lg)',
    xl: 'var(--ob-font-size-xl)',
    '2xl': 'var(--ob-font-size-2xl)',
  },
  blur: {
    sm: 'var(--ob-blur-sm)',
    xs: 'var(--ob-blur-xs)',
    md: 'var(--ob-blur-md)',
    xl: 'var(--ob-blur-xl)',
    lg: 'var(--ob-blur-lg)',
  },
} as const

/**
 * Component style requirements for Square Cyber-Minimalism
 */
export const COMPONENT_RADIUS_REQUIREMENTS = {
  // Buttons use xs (2px)
  button: 'var(--ob-radius-xs)',
  chip: 'var(--ob-radius-xs)',
  tag: 'var(--ob-radius-xs)',

  // Cards/Panels use sm (4px)
  card: 'var(--ob-radius-sm)',
  panel: 'var(--ob-radius-sm)',
  tile: 'var(--ob-radius-sm)',
  input: 'var(--ob-radius-md)', // 6px for inputs

  // Modals use lg (8px)
  modal: 'var(--ob-radius-lg)',
  dialog: 'var(--ob-radius-lg)',
  window: 'var(--ob-radius-lg)',

  // Circular elements use pill
  avatar: 'var(--ob-radius-pill)',
  dot: 'var(--ob-radius-pill)',
  spinner: 'var(--ob-radius-pill)',
} as const

/**
 * Assert that an element uses a specific design token for border-radius
 */
export function expectTokenRadius(
  element: HTMLElement,
  expectedToken: keyof typeof TOKEN_VALUES.radius,
): void {
  const expectedValue = TOKEN_VALUES.radius[expectedToken]
  expect(element).toHaveStyle({ borderRadius: expectedValue })
}

/**
 * Assert that an element uses a specific design token for spacing
 */
export function expectTokenSpacing(
  element: HTMLElement,
  property: 'padding' | 'margin' | 'gap',
  expectedToken: keyof typeof TOKEN_VALUES.space,
): void {
  const expectedValue = TOKEN_VALUES.space[expectedToken]
  expect(element).toHaveStyle({ [property]: expectedValue })
}

/**
 * Assert that an element uses correct radius for its component type
 */
export function expectCorrectRadiusForType(
  element: HTMLElement,
  componentType: keyof typeof COMPONENT_RADIUS_REQUIREMENTS,
): void {
  const expectedRadius = COMPONENT_RADIUS_REQUIREMENTS[componentType]
  expect(element).toHaveStyle({ borderRadius: expectedRadius })
}

/**
 * Validate that a style object uses design tokens instead of hardcoded values
 */
export function validateNoHardcodedRadius(
  styles: Record<string, unknown>,
): string[] {
  const violations: string[] = []

  Object.entries(styles).forEach(([key, value]) => {
    if (key.toLowerCase().includes('radius') && typeof value === 'string') {
      // Check for hardcoded pixel values
      if (/^\d+px$/.test(value) && value !== '0px') {
        violations.push(`${key}: ${value} should use a design token`)
      }
      // Check for hardcoded percentages (except intentional 50%)
      if (/^\d+%$/.test(value) && value !== '50%' && value !== '0%') {
        violations.push(`${key}: ${value} should use a design token`)
      }
      // Check for hardcoded numbers
      if (/^\d+$/.test(value) && value !== '0') {
        violations.push(`${key}: ${value} should use a design token`)
      }
    }
  })

  return violations
}

/**
 * Check if a value is using a design token
 */
export function isDesignToken(value: unknown): boolean {
  if (typeof value !== 'string') return false
  return value.startsWith('var(--ob-')
}

/**
 * Get the token name from a CSS variable value
 */
export function getTokenName(value: string): string | null {
  const match = value.match(/var\((--ob-[a-z0-9-]+)\)/)
  return match ? match[1] : null
}

/**
 * Test utility to create a snapshot of component styles
 */
export function captureStyleSnapshot(
  element: HTMLElement,
): Record<string, string> {
  const computedStyle = window.getComputedStyle(element)
  return {
    borderRadius: computedStyle.borderRadius,
    padding: computedStyle.padding,
    margin: computedStyle.margin,
    gap: computedStyle.gap,
    fontSize: computedStyle.fontSize,
    backgroundColor: computedStyle.backgroundColor,
    color: computedStyle.color,
    border: computedStyle.border,
  }
}
