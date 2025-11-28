/**
 * Insight severity classification and visual styling functions
 *
 * Pure functions for determining insight severity levels and their visual representation.
 */

import type { InsightSeverity } from '../types'

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
export function normaliseInsightSeverity(value: string | undefined): InsightSeverity {
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
  background: string
  border: string
  text: string
  indicator: string
  label: string
}

/**
 * Get visual styling (colors) for a given severity level
 */
export function getSeverityVisuals(severity: InsightSeverity | 'neutral'): SeverityVisuals {
  switch (severity) {
    case 'critical':
      return {
        background: '#fef2f2',
        border: '#fecaca',
        text: '#991b1b',
        indicator: '#dc2626',
        label: 'Critical risk',
      }
    case 'warning':
      return {
        background: '#fef3c7',
        border: '#fde68a',
        text: '#92400e',
        indicator: '#f97316',
        label: 'Watchlist',
      }
    case 'info':
      return {
        background: '#eef2ff',
        border: '#c7d2fe',
        text: '#312e81',
        indicator: '#6366f1',
        label: 'Heads-up',
      }
    case 'positive':
      return {
        background: '#dcfce7',
        border: '#bbf7d0',
        text: '#166534',
        indicator: '#22c55e',
        label: 'Improving',
      }
    default:
      return {
        background: '#f5f5f7',
        border: '#e5e5e7',
        text: '#3a3a3c',
        indicator: '#6e6e73',
        label: 'Stable',
      }
  }
}

export type DeltaVisuals = {
  background: string
  border: string
  text: string
}

/**
 * Get visual styling for a delta value (positive/negative/neutral)
 */
export function getDeltaVisuals(delta: number | null): DeltaVisuals {
  if (delta === null || delta === 0) {
    return {
      background: '#f5f5f7',
      border: '#e5e5e7',
      text: '#3a3a3c',
    }
  }
  if (delta > 0) {
    return {
      background: '#dcfce7',
      border: '#bbf7d0',
      text: '#166534',
    }
  }
  return {
    background: '#fee2e2',
    border: '#fecaca',
    text: '#b91c1c',
  }
}
