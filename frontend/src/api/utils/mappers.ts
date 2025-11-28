/**
 * Shared data mapping utilities for API responses.
 * Converts between snake_case API payloads and camelCase client types.
 */

/**
 * Safely converts a value to number or returns null.
 * Handles strings, numbers, null, and undefined.
 */
export function toNumberOrNull(value: unknown): number | null {
  if (typeof value === 'number') {
    return Number.isNaN(value) ? null : value
  }
  if (value === null || value === undefined) {
    return null
  }
  const parsed = Number(value)
  return Number.isNaN(parsed) ? null : parsed
}

/**
 * Converts a value to string or undefined.
 * Trims whitespace and returns undefined for empty strings.
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
 * Safely extracts a string or null from a payload field.
 */
export function toStringOrNull(value: unknown): string | null {
  if (typeof value === 'string') {
    return value
  }
  if (value === null || value === undefined) {
    return null
  }
  return String(value)
}

/**
 * Safely extracts an object as Record<string, unknown> or empty object.
 */
export function toRecord(value: unknown): Record<string, unknown> {
  if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
    return value as Record<string, unknown>
  }
  return {}
}

/**
 * Safely extracts an array or returns empty array.
 */
export function toArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? value : []
}
