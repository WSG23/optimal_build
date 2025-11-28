/**
 * Pure formatting and conversion functions for SiteAcquisitionPage
 *
 * These functions have no side effects and no runtime dependencies on React.
 */

import type { ConditionAttachment, GeometryDetailLevel } from '../../../../api/siteAcquisition'
import { PREVIEW_DETAIL_LABELS } from '../constants'

// ============================================================================
// Date & Time Formatters
// ============================================================================

/**
 * Format an ISO timestamp to a locale-aware date-time string
 */
export function formatTimestamp(isoValue: string | null | undefined): string {
  if (!isoValue) {
    return 'Unknown'
  }
  const date = new Date(isoValue)
  if (Number.isNaN(date.getTime())) {
    return isoValue
  }
  return date.toLocaleString()
}

/**
 * Convert ISO timestamp to HTML datetime-local input format (YYYY-MM-DDTHH:MM)
 */
export function formatDateTimeLocalInput(isoValue: string | null | undefined): string {
  if (!isoValue) {
    return ''
  }
  const date = new Date(isoValue)
  if (Number.isNaN(date.getTime())) {
    return ''
  }
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

/**
 * Convert HTML datetime-local input value to ISO 8601 string
 */
export function convertLocalToISO(localValue: string): string | null {
  if (!localValue) {
    return null
  }
  const date = new Date(localValue)
  if (Number.isNaN(date.getTime())) {
    return null
  }
  return date.toISOString()
}

// ============================================================================
// Text Formatters
// ============================================================================

/**
 * Convert snake_case or kebab-case to Title Case
 */
export function toTitleCase(value: string): string {
  return value
    .split(/[\s_-]+/)
    .filter(Boolean)
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1).toLowerCase())
    .join(' ')
}

/**
 * Format a category identifier (snake_case) as a human-readable name
 */
export function formatCategoryName(category: string): string {
  return category
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

/**
 * Create a URL-safe slug from a string
 */
export function slugify(value: string): string {
  return (
    value
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .replace(/-{2,}/g, '-') || 'insight'
  )
}

// ============================================================================
// Score & Delta Formatters
// ============================================================================

/**
 * Format a score delta as a human-readable phrase
 * e.g., "improved by 5 points", "dropped 3 points", "held steady"
 */
export function formatScoreDelta(delta: number): string {
  if (delta === 0) {
    return 'held steady'
  }
  if (delta > 0) {
    return `improved by ${delta} points`
  }
  return `dropped ${Math.abs(delta)} points`
}

/**
 * Format a delta value with +/- prefix
 * e.g., +5, -3, 0
 */
export function formatDeltaValue(delta: number | null): string {
  if (delta === null) {
    return '0'
  }
  if (delta > 0) {
    return `+${delta}`
  }
  if (delta < 0) {
    return `${delta}`
  }
  return '0'
}

// ============================================================================
// Number Parsers
// ============================================================================

/**
 * Safely parse a value to a number, returning null for invalid input
 */
export function safeNumber(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value
  }
  if (typeof value === 'string') {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

// ============================================================================
// Attachment Parsers
// ============================================================================

/**
 * Parse a multi-line text input into attachment objects
 * Format: "Label|URL" per line, or just "Label" for label-only attachments
 */
export function parseAttachmentsText(value: string): ConditionAttachment[] {
  return value
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => {
      const [labelPart, urlPart] = line.split('|')
      const label = (labelPart ?? '').trim()
      const url = (urlPart ?? '').trim()
      return {
        label: label || url || 'Attachment',
        url: url.length > 0 ? url : null,
      }
    })
}

/**
 * Convert attachment objects back to multi-line text format
 */
export function formatAttachmentsText(attachments: ConditionAttachment[]): string {
  return attachments
    .map((attachment) => {
      if (attachment.url) {
        return `${attachment.label}|${attachment.url}`
      }
      return attachment.label
    })
    .join('\n')
}

// ============================================================================
// Preview Detail Level Formatter
// ============================================================================

/**
 * Get a human-readable description of a geometry detail level
 */
export function describeDetailLevel(level: GeometryDetailLevel | null | undefined): string {
  if (level && PREVIEW_DETAIL_LABELS[level]) {
    return PREVIEW_DETAIL_LABELS[level]
  }
  return PREVIEW_DETAIL_LABELS.medium
}
