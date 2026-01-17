/**
 * Shared request utilities for API clients.
 */

import { applyIdentityHeaders } from '../identity'
import { buildUrl, apiBaseUrl } from './baseUrl'
import {
  ApiError,
  createApiError,
  createNetworkError,
  isAbortError,
  isNetworkError,
} from './errors'

export interface RequestOptions {
  signal?: AbortSignal
  headers?: Record<string, string>
}

export interface JsonRequestOptions extends RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
}

/**
 * Makes a JSON API request with identity headers.
 * Throws ApiError for non-OK responses or network failures.
 */
export async function jsonRequest<T>(
  path: string,
  options: JsonRequestOptions = {},
): Promise<T> {
  const { method = 'GET', body, signal, headers: customHeaders = {} } = options

  const headers = applyIdentityHeaders({
    'Content-Type': 'application/json',
    ...customHeaders,
  })

  const init: RequestInit = {
    method,
    headers,
    signal,
  }

  if (body !== undefined) {
    init.body = JSON.stringify(body)
  }

  let response: Response
  try {
    response = await fetch(buildUrl(path, apiBaseUrl), init)
  } catch (error) {
    // Network error (server unreachable, CORS, etc.)
    if (isAbortError(error)) {
      throw error
    }
    if (isNetworkError(error)) {
      throw createNetworkError()
    }
    throw error
  }

  if (!response.ok) {
    throw await createApiError(response)
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

/**
 * Makes a GET request returning JSON.
 */
export async function getJson<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  return jsonRequest<T>(path, { method: 'GET', ...options })
}

/**
 * Makes a POST request with JSON body.
 */
export async function postJson<T>(
  path: string,
  body: unknown,
  options: RequestOptions = {},
): Promise<T> {
  return jsonRequest<T>(path, { method: 'POST', body, ...options })
}

/**
 * Makes a PATCH request with JSON body.
 */
export async function patchJson<T>(
  path: string,
  body: unknown,
  options: RequestOptions = {},
): Promise<T> {
  return jsonRequest<T>(path, { method: 'PATCH', body, ...options })
}

/**
 * Makes a DELETE request.
 */
export async function deleteRequest(
  path: string,
  options: RequestOptions = {},
): Promise<void> {
  return jsonRequest<void>(path, { method: 'DELETE', ...options })
}

/**
 * Wraps an async function with network error fallback.
 * If the request fails due to network issues, calls the fallback.
 */
export async function withFallback<T>(
  request: () => Promise<T>,
  fallback: () => T,
  logPrefix?: string,
): Promise<T> {
  try {
    return await request()
  } catch (error) {
    if (isAbortError(error)) {
      throw error
    }
    if (error instanceof TypeError) {
      if (logPrefix) {
        console.warn(`[${logPrefix}] request failed, using fallback`, error)
      }
      return fallback()
    }
    throw error
  }
}

export { ApiError, isAbortError }
