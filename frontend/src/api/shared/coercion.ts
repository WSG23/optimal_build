/**
 * Shared type coercion utilities for API response normalization
 */

/**
 * Coerce a value to a number or null
 */
export function coerceNumber(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value
  }
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

/**
 * Coerce a value to a non-empty string or null
 */
export function coerceString(value: unknown): string | null {
  if (typeof value === 'string' && value.trim() !== '') {
    return value
  }
  return null
}

/**
 * Coerce a value to a boolean
 * Handles: boolean, number (0 = false), string ('true', 't', 'yes', 'y', '1')
 */
export function coerceBoolean(value: unknown): boolean {
  if (typeof value === 'boolean') {
    return value
  }
  if (typeof value === 'number') {
    return value !== 0
  }
  if (typeof value === 'string') {
    const normalised = value.trim().toLowerCase()
    return ['true', 't', 'yes', 'y', '1'].includes(normalised)
  }
  return false
}

/**
 * Alias for coerceBoolean - backward compatibility with siteAcquisition.ts
 */
export const boolish = coerceBoolean

/**
 * Convert value to optional string (undefined if empty/null)
 * Used for building request payloads where undefined omits the field
 */
export function toOptionalString(value: unknown): string | undefined {
  if (value == null) {
    return undefined
  }
  const stringValue = typeof value === 'string' ? value : String(value)
  const trimmed = stringValue.trim()
  return trimmed === '' ? undefined : trimmed
}

/**
 * Round a number to 2 decimal places, preserving null
 */
export function roundOptional(value: number | null): number | null {
  if (value === null) {
    return null
  }
  return Math.round(value * 100) / 100
}
