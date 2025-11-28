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
 * Creates an ApiError from a fetch Response.
 */
export async function createApiError(
  response: Response,
  fallbackMessage?: string,
): Promise<ApiError> {
  const text = await response.text().catch(() => '')
  const message =
    text || fallbackMessage || `Request failed with status ${response.status}`
  return new ApiError(message, response.status, response.statusText)
}
