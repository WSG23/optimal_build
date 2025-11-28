/**
 * Shared API utilities.
 * Import from this barrel file for convenience.
 */

// Base URL utilities
export {
  normaliseBaseUrl,
  apiBaseUrl,
  buildUrl,
  buildSimpleUrl,
} from './baseUrl'

// Data mapping utilities
export {
  toNumberOrNull,
  toOptionalString,
  toStringOrNull,
  toRecord,
  toArray,
} from './mappers'

// Error handling utilities
export {
  isAbortError,
  isNetworkError,
  getErrorMessage,
  ApiError,
  createApiError,
} from './errors'

// Request utilities
export {
  jsonRequest,
  getJson,
  postJson,
  patchJson,
  deleteRequest,
  withFallback,
} from './request'
export type { RequestOptions, JsonRequestOptions } from './request'
