/**
 * Shared error handling utilities for API clients.
 */

/**
 * Checks if an error is an AbortError (request was cancelled).
 */
export function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError'
}

/**
 * Checks if an error is a network/fetch TypeError.
 * These typically indicate network issues or CORS problems.
 */
export function isNetworkError(error: unknown): boolean {
  return error instanceof TypeError
}

/**
 * Extracts a user-friendly error message from an error.
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  if (typeof error === 'string') {
    return error
  }
  return 'Unknown error'
}

/**
 * Creates a standardized API error with status code.
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly statusText?: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/**
 * Returns a user-friendly message for common HTTP status codes.
 */
function getFriendlyStatusMessage(status: number): string | null {
  switch (status) {
    case 400:
      return 'Invalid request. Please check your input.'
    case 401:
      return 'You need to sign in to perform this action.'
    case 403:
      return 'You do not have permission to perform this action.'
    case 404:
      return 'The requested resource was not found.'
    case 409:
      return 'This operation conflicts with existing data.'
    case 422:
      return 'The provided data is invalid.'
    case 429:
      return 'Too many requests. Please wait a moment and try again.'
    case 500:
      return 'Something went wrong on the server. Please try again later.'
    case 502:
    case 503:
    case 504:
      return 'The server is temporarily unavailable. Please try again later.'
    default:
      return null
  }
}

/**
 * Creates an ApiError from a fetch Response.
 */
export async function createApiError(
  response: Response,
  fallbackMessage?: string,
): Promise<ApiError> {
  const text = await response.text().catch(() => '')

  // Try to parse JSON error detail from FastAPI
  let detail: string | null = null
  if (text) {
    try {
      const json = JSON.parse(text)
      if (typeof json.detail === 'string') {
        detail = json.detail
      }
    } catch {
      // Not JSON, use text as-is if it's short and readable
      if (text.length < 200 && !text.includes('<')) {
        detail = text
      }
    }
  }

  // Prefer: parsed detail > friendly message > fallback > generic
  const message =
    detail ||
    getFriendlyStatusMessage(response.status) ||
    fallbackMessage ||
    `Request failed with status ${response.status}`

  return new ApiError(message, response.status, response.statusText)
}

/**
 * Creates an ApiError for network failures (server unreachable).
 */
export function createNetworkError(): ApiError {
  return new ApiError(
    'Unable to connect to the server. Please check your connection.',
    0,
    'Network Error',
  )
}
