/**
 * Shared URL building utilities for API clients
 * Uses the robust implementation from finance.ts
 */

const metaEnv =
  typeof import.meta !== 'undefined' && import.meta
    ? (import.meta as ImportMeta).env
    : undefined

const rawApiBaseUrl =
  metaEnv?.VITE_API_BASE_URL ??
  metaEnv?.VITE_API_URL ??
  metaEnv?.VITE_API_BASE ??
  null

/**
 * Normalise a base URL to ensure it ends with a slash
 * Returns '/' for empty/null values
 */
export function normaliseBaseUrl(value: string | undefined | null): string {
  if (typeof value !== 'string') {
    return '/'
  }
  const trimmed = value.trim()
  return trimmed === '' ? '/' : trimmed
}

/**
 * Build a full URL from a path and optional base
 * - Handles absolute URLs (https://) by returning them as-is
 * - Strips leading slashes from path
 * - Ensures proper joining with base URL
 */
export function buildUrl(path: string, base?: string): string {
  if (/^https?:/i.test(path)) {
    return path
  }

  const trimmed = path.startsWith('/') ? path.slice(1) : path
  const root = normaliseBaseUrl(base ?? apiBaseUrl)

  if (/^https?:/i.test(root)) {
    const normalisedRoot = root.endsWith('/') ? root : `${root}/`
    return new URL(trimmed, normalisedRoot).toString()
  }

  const normalisedRoot = root.endsWith('/') ? root : `${root}/`
  return `${normalisedRoot}${trimmed}`
}

/**
 * The computed API base URL, derived from environment variables
 * Single source of truth for all API clients
 */
export const apiBaseUrl = normaliseBaseUrl(rawApiBaseUrl)
