/**
 * Shared base URL utilities for API clients.
 * Centralizes URL normalization and construction logic.
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
 * Normalizes a base URL string, returning '/' for empty/invalid values.
 */
export function normaliseBaseUrl(value: string | undefined | null): string {
  if (typeof value !== 'string') {
    return '/'
  }
  const trimmed = value.trim()
  return trimmed === '' ? '/' : trimmed
}

/**
 * The resolved API base URL from environment variables.
 */
export const apiBaseUrl = normaliseBaseUrl(rawApiBaseUrl)

/**
 * Builds a full URL from a path and optional base.
 * Handles both absolute URLs and relative paths.
 */
export function buildUrl(path: string, base: string = apiBaseUrl): string {
  // Already absolute URL
  if (/^https?:/i.test(path)) {
    return path
  }

  const trimmedPath = path.startsWith('/') ? path.slice(1) : path
  const normalisedBase = normaliseBaseUrl(base)

  // Base is absolute URL
  if (/^https?:/i.test(normalisedBase)) {
    const baseWithSlash = normalisedBase.endsWith('/')
      ? normalisedBase
      : `${normalisedBase}/`
    return new URL(trimmedPath, baseWithSlash).toString()
  }

  // Relative base
  const baseWithSlash = normalisedBase.endsWith('/')
    ? normalisedBase
    : `${normalisedBase}/`
  return `${baseWithSlash}${trimmedPath}`
}

/**
 * Builds a URL with simple path joining (no URL parsing).
 * Useful when base URL may be relative.
 */
export function buildSimpleUrl(
  path: string,
  base: string = apiBaseUrl,
): string {
  const normalised = base.endsWith('/') ? base.slice(0, -1) : base
  if (path.startsWith('/')) {
    return `${normalised}${path}`
  }
  return `${normalised}/${path}`
}
