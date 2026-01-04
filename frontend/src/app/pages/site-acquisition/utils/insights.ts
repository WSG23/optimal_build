/**
 * Insight severity classification and visual styling functions
 *
 * Pure functions for determining insight severity levels and their visual representation.
 */

import type { InsightSeverity } from '../types'

// ============================================================================
// Tone Color Map (for rating/risk change display)
// ============================================================================

export type ToneType = 'positive' | 'negative' | 'neutral'

export const toneColorMap: Record<ToneType, string> = {
  positive: 'var(--ob-success-700)',
  negative: 'var(--ob-error-600)',
  neutral: 'var(--ob-neutral-500)',
}

// ============================================================================
// Severity Classification
// ============================================================================

/**
 * Classify a system's severity based on its rating and score delta
 * Returns 'neutral' if the system doesn't warrant special attention
 */
export function classifySystemSeverity(
  latestRating: string | null | undefined,
  delta: number | null,
): InsightSeverity | 'neutral' {
  if (!latestRating || typeof latestRating !== 'string') {
    return 'neutral'
  }
  const normalized = latestRating.toUpperCase()
  const negativeRating = normalized === 'D' || normalized === 'E'
  const warningRating = normalized === 'C'

  if (negativeRating) {
    return 'critical'
  }
  if (typeof delta === 'number') {
    if (delta <= -10) {
      return 'critical'
    }
    if (delta <= -5) {
      return 'warning'
    }
    if (delta >= 8) {
      return 'positive'
    }
  }
  if (warningRating) {
    return 'warning'
  }
  if (typeof delta === 'number' && delta >= 4) {
    return 'positive'
  }
  return 'neutral'
}

/**
 * Normalize a severity string from backend to a valid InsightSeverity
 */
export function normaliseInsightSeverity(
  value: string | undefined,
): InsightSeverity {
  const severity = (value ?? 'warning').toLowerCase()
  if (
    severity === 'critical' ||
    severity === 'warning' ||
    severity === 'positive' ||
    severity === 'info'
  ) {
    return severity as InsightSeverity
  }
  return 'warning'
}

// ============================================================================
// Insight Title Builders
// ============================================================================

/**
 * Build a human-readable title for a system insight based on severity and delta
 */
export function buildSystemInsightTitle(
  name: string,
  severity: InsightSeverity,
  delta: number | null,
): string {
  if (severity === 'critical') {
    if (typeof delta === 'number' && delta < 0) {
      return `${name} dropped ${Math.abs(delta)} points`
    }
    return `${name} requires attention`
  }
  if (severity === 'warning') {
    if (typeof delta === 'number' && delta < 0) {
      return `${name} trending down`
    }
    return `${name} rated watch`
  }
  if (severity === 'positive') {
    if (typeof delta === 'number' && delta > 0) {
      return `${name} improved ${delta} points`
    }
    return `${name} improving`
  }
  return name
}

/**
 * Get a specialist hint based on system name
 */
export function systemSpecialistHint(name: string): string | null {
  const lower = name.toLowerCase()
  if (lower.includes('struct')) {
    return 'Structural engineer'
  }
  if (
    lower.includes('mechanical') ||
    lower.includes('electrical') ||
    lower.includes('m&e')
  ) {
    return 'M&E engineer'
  }
  if (
    lower.includes('compliance') ||
    lower.includes('maintenance') ||
    lower.includes('envelope')
  ) {
    return 'Building surveyor'
  }
  return null
}

// ============================================================================
// Visual Styling
// ============================================================================

export type SeverityVisuals = {
  /** Card background - transparent for glass surface, or subtle tint */
  background: string
  /** Card border color */
  border: string
  /** Primary text color on the card */
  text: string
  /** Left border accent / indicator dot color (semantic: red/amber/green/indigo) */
  indicator: string
  /** Uppercase label text (e.g., "CRITICAL RISK") */
  label: string
  /** Badge background (subtle tint like --ob-error-100) */
  badgeBg: string
  /** Badge text color (darker like --ob-error-700) */
  badgeText: string
  /** Badge border color (medium like --ob-error-300) */
  badgeBorder: string
}

/**
 * Get visual styling (colors) for a given severity level.
 *
 * Uses design tokens from UI_STANDARDS.md:
 * - Card background: transparent (uses glass surface from card component)
 * - Left border accent: semantic color (--ob-error-500, --ob-warning-500, etc.)
 * - Badge: subtle background with darker text
 *
 * @see frontend/UI_STANDARDS.md - Functional Color Language
 */
export function getSeverityVisuals(
  severity: InsightSeverity | 'neutral',
): SeverityVisuals {
  switch (severity) {
    case 'critical':
      return {
        background: 'transparent',
        border: 'var(--ob-color-border-subtle)',
        text: 'var(--ob-color-text-primary)',
        indicator: 'var(--ob-error-500)',
        label: 'CRITICAL RISK',
        badgeBg: 'var(--ob-error-100)',
        badgeText: 'var(--ob-error-700)',
        badgeBorder: 'var(--ob-error-300)',
      }
    case 'warning':
      return {
        background: 'transparent',
        border: 'var(--ob-color-border-subtle)',
        text: 'var(--ob-color-text-primary)',
        indicator: 'var(--ob-warning-500)',
        label: 'WATCHLIST',
        badgeBg: 'var(--ob-warning-100)',
        badgeText: 'var(--ob-warning-700)',
        badgeBorder: 'var(--ob-warning-300)',
      }
    case 'info':
      return {
        background: 'transparent',
        border: 'var(--ob-color-border-subtle)',
        text: 'var(--ob-color-text-primary)',
        indicator: 'var(--ob-info-500)',
        label: 'HEADS-UP',
        badgeBg: 'var(--ob-info-100)',
        badgeText: 'var(--ob-info-700)',
        badgeBorder: 'var(--ob-info-300)',
      }
    case 'positive':
      return {
        background: 'transparent',
        border: 'var(--ob-color-border-subtle)',
        text: 'var(--ob-color-text-primary)',
        indicator: 'var(--ob-success-500)',
        label: 'POSITIVE',
        badgeBg: 'var(--ob-success-100)',
        badgeText: 'var(--ob-success-700)',
        badgeBorder: 'var(--ob-success-300)',
      }
    default:
      return {
        background: 'transparent',
        border: 'var(--ob-color-border-subtle)',
        text: 'var(--ob-color-text-primary)',
        indicator: 'var(--ob-neutral-500)',
        label: 'STABLE',
        badgeBg: 'var(--ob-neutral-100)',
        badgeText: 'var(--ob-neutral-700)',
        badgeBorder: 'var(--ob-neutral-300)',
      }
  }
}

export type DeltaVisuals = {
  background: string
  border: string
  text: string
}

/**
 * Get visual styling for a delta value (positive/negative/neutral).
 * Uses design tokens per UI_STANDARDS.md.
 */
export function getDeltaVisuals(delta: number | null): DeltaVisuals {
  if (delta === null || delta === 0) {
    return {
      background: 'var(--ob-neutral-100)',
      border: 'var(--ob-neutral-300)',
      text: 'var(--ob-neutral-700)',
    }
  }
  if (delta > 0) {
    return {
      background: 'var(--ob-success-100)',
      border: 'var(--ob-success-300)',
      text: 'var(--ob-success-700)',
    }
  }
  return {
    background: 'var(--ob-error-100)',
    border: 'var(--ob-error-300)',
    text: 'var(--ob-error-700)',
  }
}
