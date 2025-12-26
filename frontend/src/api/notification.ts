import { z } from 'zod'

import { ApiClient } from './client'

// ============================================================================
// Constants
// ============================================================================

/** Default page number for pagination */
export const DEFAULT_PAGE = 1

/** Default number of items per page */
export const DEFAULT_PAGE_SIZE = 20

/** Maximum number of IDs allowed in bulk operations */
export const MAX_BULK_IDS = 100

/** Default retry configuration */
export const DEFAULT_RETRY_OPTIONS: RetryOptions = {
  maxAttempts: 3,
  baseDelayMs: 1000,
  maxDelayMs: 10000,
}

// ============================================================================
// Branded Types
// ============================================================================

/**
 * Branded type for notification IDs.
 * Provides compile-time safety to prevent mixing notification IDs with other string IDs.
 *
 * @example
 * ```typescript
 * const notifId = 'notif-123' as NotificationId
 * const userId = 'user-456' as UserId
 *
 * // This would be a type error:
 * // api.getNotification(userId) // Error: UserId is not assignable to NotificationId
 * ```
 */
export type NotificationId = string & { readonly __brand: 'NotificationId' }

/**
 * Branded type for user IDs.
 * Provides compile-time safety to prevent mixing user IDs with other string IDs.
 */
export type UserId = string & { readonly __brand: 'UserId' }

/**
 * Branded type for project IDs.
 * Provides compile-time safety to prevent mixing project IDs with other string IDs.
 */
export type ProjectId = string & { readonly __brand: 'ProjectId' }

/**
 * Helper to create a NotificationId from a string.
 * Use this when you have a trusted notification ID source.
 *
 * @example
 * ```typescript
 * const id = notificationId('notif-123')
 * await api.getNotification(id)
 * ```
 */
export function notificationId(id: string): NotificationId {
  return id as NotificationId
}

/**
 * Helper to create a UserId from a string.
 */
export function userId(id: string): UserId {
  return id as UserId
}

/**
 * Helper to create a ProjectId from a string.
 */
export function projectId(id: string): ProjectId {
  return id as ProjectId
}

// ============================================================================
// Zod Schemas (Runtime Validation)
// ============================================================================

/**
 * All supported notification types.
 * These must match the backend NotificationType enum values.
 */
export const NotificationTypeSchema = z.enum([
  'team_invitation',
  'team_member_joined',
  'team_member_removed',
  'workflow_created',
  'workflow_step_assigned',
  'workflow_step_completed',
  'workflow_completed',
  'workflow_approval_needed',
  'workflow_rejected',
  'project_update',
  'project_milestone',
  'regulatory_status_change',
  'regulatory_rfi',
  'system_announcement',
])

/**
 * All supported notification priority levels.
 * These must match the backend NotificationPriority enum values.
 */
export const NotificationPrioritySchema = z.enum([
  'low',
  'normal',
  'high',
  'urgent',
])

/**
 * Zod schema for validating a Notification object at runtime.
 * Use this to ensure API responses conform to the expected shape.
 *
 * @example
 * ```typescript
 * const response = await fetch('/notifications/123')
 * const data = await response.json()
 * const notification = NotificationSchema.parse(data) // Throws if invalid
 * ```
 */
export const NotificationSchema = z.object({
  id: z.string().min(1),
  user_id: z.string().min(1),
  notification_type: NotificationTypeSchema,
  title: z.string(),
  message: z.string(),
  priority: NotificationPrioritySchema,
  project_id: z.string().optional(),
  related_entity_type: z.string().optional(),
  related_entity_id: z.string().optional(),
  is_read: z.boolean(),
  read_at: z.string().optional(),
  created_at: z.string(),
  expires_at: z.string().optional(),
})

/**
 * Zod schema for validating a paginated notification list.
 */
export const NotificationListSchema = z.object({
  notifications: z.array(NotificationSchema),
  total: z.number().int().nonnegative(),
  unread_count: z.number().int().nonnegative(),
  page: z.number().int().positive(),
  page_size: z.number().int().positive(),
  has_more: z.boolean(),
})

/**
 * Zod schema for validating notification count response.
 */
export const NotificationCountSchema = z.object({
  total: z.number().int().nonnegative(),
  unread: z.number().int().nonnegative(),
})

/**
 * Zod schema for validating bulk operation response.
 */
export const BulkOperationResponseSchema = z.object({
  message: z.string(),
  count: z.number().int().nonnegative(),
})

/**
 * Zod schema for validating delete operation response.
 */
export const DeleteResponseSchema = z.object({
  message: z.string(),
  deleted: z.boolean(),
})

// ============================================================================
// Types (Inferred from Zod Schemas)
// ============================================================================

/**
 * Notification types supported by the system.
 * Inferred from the Zod schema for type safety and runtime validation.
 */
export type NotificationType = z.infer<typeof NotificationTypeSchema>

/**
 * Notification priority levels.
 * Inferred from the Zod schema for type safety and runtime validation.
 */
export type NotificationPriority = z.infer<typeof NotificationPrioritySchema>

/**
 * Notification entity representing a user notification.
 * Inferred from the Zod schema for type safety and runtime validation.
 */
export type Notification = z.infer<typeof NotificationSchema>

/**
 * Paginated list of notifications with metadata.
 * Inferred from the Zod schema for type safety and runtime validation.
 */
export type NotificationList = z.infer<typeof NotificationListSchema>

/**
 * Notification count summary.
 * Inferred from the Zod schema for type safety and runtime validation.
 */
export type NotificationCount = z.infer<typeof NotificationCountSchema>

/**
 * Response for bulk operations.
 * Inferred from the Zod schema for type safety and runtime validation.
 */
export type BulkOperationResponse = z.infer<typeof BulkOperationResponseSchema>

/**
 * Response for delete operations.
 * Inferred from the Zod schema for type safety and runtime validation.
 */
export type DeleteResponse = z.infer<typeof DeleteResponseSchema>

/**
 * Filter options for listing notifications.
 */
export interface NotificationFilters {
  page?: number
  page_size?: number
  unread_only?: boolean
  notification_type?: NotificationType
  project_id?: string
}

/**
 * Configuration options for retry behavior.
 */
export interface RetryOptions {
  /** Maximum number of retry attempts (default: 3) */
  maxAttempts: number
  /** Base delay in milliseconds between retries (default: 1000) */
  baseDelayMs: number
  /** Maximum delay in milliseconds (default: 10000) */
  maxDelayMs: number
}

/**
 * Configuration options for the notification API.
 */
export interface NotificationApiOptions {
  /** Whether to enable runtime validation of API responses (default: true in development) */
  validateResponses?: boolean
  /** Retry configuration for failed requests */
  retry?: Partial<RetryOptions>
  /** Whether to enable request deduplication (default: true) */
  deduplicate?: boolean
}

// ============================================================================
// Error Classes
// ============================================================================

/**
 * Base error class for notification API errors with additional context.
 * Provides structured error information for debugging and error handling.
 *
 * @example
 * ```typescript
 * try {
 *   await api.getNotification(notificationId('invalid'))
 * } catch (error) {
 *   if (error instanceof NotificationApiError) {
 *     console.error(`API Error: ${error.message}`)
 *     console.error(`Endpoint: ${error.endpoint}`)
 *     console.error(`Status: ${error.statusCode}`)
 *   }
 * }
 * ```
 */
export class NotificationApiError extends Error {
  public readonly statusCode?: number
  public readonly endpoint: string
  public readonly originalError?: Error

  constructor(
    message: string,
    endpoint: string,
    statusCode?: number,
    originalError?: Error,
  ) {
    super(message)
    this.name = 'NotificationApiError'
    this.endpoint = endpoint
    this.statusCode = statusCode
    this.originalError = originalError
  }
}

/**
 * Error thrown when a notification is not found.
 *
 * @example
 * ```typescript
 * try {
 *   await api.getNotification(notificationId('nonexistent'))
 * } catch (error) {
 *   if (error instanceof NotificationNotFoundError) {
 *     console.log(`Notification ${error.notificationId} not found`)
 *   }
 * }
 * ```
 */
export class NotificationNotFoundError extends NotificationApiError {
  public readonly notificationId: string

  constructor(notificationIdValue: string) {
    super(
      `Notification ${notificationIdValue} not found`,
      `/notifications/${notificationIdValue}`,
      404,
    )
    this.name = 'NotificationNotFoundError'
    this.notificationId = notificationIdValue
  }
}

/**
 * Error thrown when the user lacks permission to access a notification.
 */
export class NotificationPermissionError extends NotificationApiError {
  public readonly notificationId: string

  constructor(notificationIdValue: string) {
    super(
      `No permission to access notification ${notificationIdValue}`,
      `/notifications/${notificationIdValue}`,
      403,
    )
    this.name = 'NotificationPermissionError'
    this.notificationId = notificationIdValue
  }
}

/**
 * Error thrown when API response validation fails.
 */
export class NotificationValidationError extends NotificationApiError {
  public readonly validationErrors: z.ZodError

  constructor(endpoint: string, validationErrors: z.ZodError) {
    super(
      `Invalid API response from ${endpoint}: ${validationErrors.message}`,
      endpoint,
    )
    this.name = 'NotificationValidationError'
    this.validationErrors = validationErrors
  }
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Delay execution for the specified number of milliseconds.
 */
function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * Determines if an error is retryable (network errors, 5xx status codes).
 */
function isRetryableError(error: unknown): boolean {
  if (error instanceof NotificationApiError) {
    // Retry on server errors (5xx) but not client errors (4xx)
    if (error.statusCode !== undefined) {
      return error.statusCode >= 500 && error.statusCode < 600
    }
  }
  // Retry on network errors (TypeError is commonly thrown for fetch failures)
  if (error instanceof TypeError) {
    const message = error.message.toLowerCase()
    return (
      message.includes('fetch') ||
      message.includes('network') ||
      message.includes('request failed')
    )
  }
  if (error instanceof Error) {
    const message = error.message.toLowerCase()
    return (
      message.includes('network') ||
      message.includes('timeout') ||
      message.includes('econnrefused') ||
      message.includes('econnreset')
    )
  }
  return false
}

/**
 * Executes an async function with exponential backoff retry.
 *
 * @param fn - The async function to execute
 * @param options - Retry configuration options
 * @returns The result of the function
 * @throws The last error if all retries fail
 *
 * @example
 * ```typescript
 * const result = await withRetry(
 *   () => api.listNotifications(),
 *   { maxAttempts: 3, baseDelayMs: 1000 }
 * )
 * ```
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  options: Partial<RetryOptions> = {},
): Promise<T> {
  const { maxAttempts, baseDelayMs, maxDelayMs } = {
    ...DEFAULT_RETRY_OPTIONS,
    ...options,
  }

  let lastError: unknown

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error

      // Don't retry if it's the last attempt or error is not retryable
      if (attempt === maxAttempts || !isRetryableError(error)) {
        throw error
      }

      // Calculate delay with exponential backoff and jitter
      const exponentialDelay = baseDelayMs * Math.pow(2, attempt - 1)
      const jitter = Math.random() * 0.3 * exponentialDelay
      const actualDelay = Math.min(exponentialDelay + jitter, maxDelayMs)

      await delay(actualDelay)
    }
  }

  // Should never reach here, but TypeScript needs this
  throw lastError
}

// ============================================================================
// Request Deduplication
// ============================================================================

/** Map of pending requests for deduplication */
const pendingRequests = new Map<string, Promise<unknown>>()

/**
 * Deduplicates concurrent requests to the same endpoint.
 * If a request with the same key is already in-flight, returns the existing promise.
 *
 * @param key - Unique key for the request (e.g., endpoint + params)
 * @param request - The request function to execute
 * @returns The result of the request
 *
 * @example
 * ```typescript
 * // These two calls will only make one actual request
 * const [result1, result2] = await Promise.all([
 *   dedupe('getCount', () => api.getCount()),
 *   dedupe('getCount', () => api.getCount()),
 * ])
 * ```
 */
export function dedupe<T>(key: string, request: () => Promise<T>): Promise<T> {
  const existing = pendingRequests.get(key)
  if (existing) {
    return existing as Promise<T>
  }

  const promise = request().finally(() => {
    pendingRequests.delete(key)
  })

  pendingRequests.set(key, promise)
  return promise
}

/**
 * Clears all pending deduplicated requests.
 * Useful for testing or when resetting state.
 */
export function clearDedupeCache(): void {
  pendingRequests.clear()
}

// ============================================================================
// Optimistic Update Helpers
// ============================================================================

/**
 * Creates an optimistic version of a notification marked as read.
 * Use this for immediate UI updates before the server confirms.
 *
 * @param notification - The original notification
 * @returns A new notification object with is_read=true and read_at set
 *
 * @example
 * ```typescript
 * // Optimistic update pattern
 * const optimistic = createOptimisticRead(notification)
 * setNotifications(prev => prev.map(n => n.id === notification.id ? optimistic : n))
 *
 * try {
 *   const confirmed = await api.markAsRead(notificationId(notification.id))
 *   setNotifications(prev => prev.map(n => n.id === notification.id ? confirmed : n))
 * } catch (error) {
 *   // Rollback on error
 *   setNotifications(prev => prev.map(n => n.id === notification.id ? notification : n))
 * }
 * ```
 */
export function createOptimisticRead(notification: Notification): Notification {
  return {
    ...notification,
    is_read: true,
    read_at: new Date().toISOString(),
  }
}

/**
 * Creates an optimistic version of a notification marked as unread.
 *
 * @param notification - The original notification
 * @returns A new notification object with is_read=false and read_at undefined
 */
export function createOptimisticUnread(
  notification: Notification,
): Notification {
  return {
    ...notification,
    is_read: false,
    read_at: undefined,
  }
}

/**
 * Creates optimistic versions of multiple notifications marked as read.
 *
 * @param notifications - Array of notifications to mark as read
 * @param idsToMark - Set or array of notification IDs to mark as read
 * @returns New array with matching notifications marked as read
 */
export function createOptimisticBulkRead(
  notifications: Notification[],
  idsToMark: string[] | Set<string>,
): Notification[] {
  const idSet = idsToMark instanceof Set ? idsToMark : new Set(idsToMark)
  const now = new Date().toISOString()

  return notifications.map((notification) =>
    idSet.has(notification.id)
      ? { ...notification, is_read: true, read_at: now }
      : notification,
  )
}

/**
 * Creates an optimistic notification list after removing a notification.
 *
 * @param list - The original notification list
 * @param idToRemove - The ID of the notification to remove
 * @returns A new list with the notification removed and counts updated
 */
export function createOptimisticDelete(
  list: NotificationList,
  idToRemove: string,
): NotificationList {
  const notification = list.notifications.find((n) => n.id === idToRemove)
  const wasUnread = notification && !notification.is_read

  return {
    ...list,
    notifications: list.notifications.filter((n) => n.id !== idToRemove),
    total: Math.max(0, list.total - 1),
    unread_count: wasUnread
      ? Math.max(0, list.unread_count - 1)
      : list.unread_count,
  }
}

// ============================================================================
// Validation Helpers
// ============================================================================

/**
 * Validates that a notification ID is a non-empty string.
 * @param notificationIdValue - The ID to validate
 * @throws NotificationApiError if validation fails
 */
function validateNotificationId(notificationIdValue: string): void {
  if (!notificationIdValue || typeof notificationIdValue !== 'string') {
    throw new NotificationApiError(
      'Notification ID must be a non-empty string',
      'validation',
    )
  }
  if (notificationIdValue.trim().length === 0) {
    throw new NotificationApiError(
      'Notification ID cannot be empty or whitespace',
      'validation',
    )
  }
}

/**
 * Validates that an array of notification IDs is valid.
 * @param notificationIds - The IDs to validate
 * @throws NotificationApiError if validation fails
 */
function validateNotificationIds(notificationIds: string[]): void {
  if (!Array.isArray(notificationIds)) {
    throw new NotificationApiError(
      'Notification IDs must be an array',
      'validation',
    )
  }
  if (notificationIds.length === 0) {
    throw new NotificationApiError(
      'Notification IDs array cannot be empty',
      'validation',
    )
  }
  if (notificationIds.length > MAX_BULK_IDS) {
    throw new NotificationApiError(
      `Cannot process more than ${MAX_BULK_IDS} notifications at once`,
      'validation',
    )
  }
  for (const id of notificationIds) {
    validateNotificationId(id)
  }
}

// ============================================================================
// Query Parameter Builder
// ============================================================================

/**
 * Builds query parameters for the list notifications endpoint.
 * Handles proper type coercion and omits undefined values.
 */
function buildListParams(filters: NotificationFilters): Record<string, string> {
  const params: Record<string, string> = {}

  // Use defaults for pagination
  params.page = String(filters.page ?? DEFAULT_PAGE)
  params.page_size = String(filters.page_size ?? DEFAULT_PAGE_SIZE)

  // Only include unread_only if explicitly true (avoid sending 'false' unnecessarily)
  if (filters.unread_only === true) {
    params.unread_only = 'true'
  }

  // Include optional filters only if provided
  if (filters.notification_type) {
    params.notification_type = filters.notification_type
  }
  if (filters.project_id) {
    params.project_id = filters.project_id
  }

  return params
}

/**
 * Creates a cache key for request deduplication.
 */
function createCacheKey(
  method: string,
  endpoint: string,
  params?: Record<string, string>,
): string {
  const paramStr = params ? JSON.stringify(params) : ''
  return `${method}:${endpoint}:${paramStr}`
}

// ============================================================================
// API Factory
// ============================================================================

/**
 * Creates a notification API instance with dependency injection support.
 * This enables easier testing and custom client configurations.
 *
 * @param client - Optional ApiClient instance (defaults to new ApiClient())
 * @param options - Optional configuration options
 * @returns Notification API methods
 *
 * @example
 * ```typescript
 * // Basic usage with default client
 * const api = createNotificationApi()
 *
 * // With custom client for testing
 * const mockClient = new MockApiClient()
 * const testApi = createNotificationApi(mockClient)
 *
 * // With options
 * const api = createNotificationApi(undefined, {
 *   validateResponses: true,
 *   retry: { maxAttempts: 5 },
 *   deduplicate: true,
 * })
 * ```
 */
export function createNotificationApi(
  client: ApiClient = new ApiClient(),
  options: NotificationApiOptions = {},
) {
  const {
    validateResponses = typeof process !== 'undefined' &&
      process.env?.NODE_ENV !== 'production',
    retry = {},
    deduplicate = true,
  } = options

  const retryOptions = { ...DEFAULT_RETRY_OPTIONS, ...retry }

  /**
   * Validates a response against a Zod schema if validation is enabled.
   */
  function validate<T>(
    schema: z.ZodType<T>,
    data: unknown,
    endpoint: string,
  ): T {
    if (!validateResponses) {
      return data as T
    }

    const result = schema.safeParse(data)
    if (!result.success) {
      throw new NotificationValidationError(endpoint, result.error)
    }
    return result.data
  }

  /**
   * Wraps a request with optional retry and deduplication.
   */
  async function wrapRequest<T>(
    cacheKey: string,
    request: () => Promise<T>,
    enableRetry = true,
  ): Promise<T> {
    const execute = enableRetry
      ? () => withRetry(request, retryOptions)
      : request

    if (deduplicate) {
      return dedupe(cacheKey, execute)
    }

    return execute()
  }

  return {
    /**
     * List notifications for the current user with pagination and filters.
     *
     * @param filters - Optional filters for pagination and filtering
     * @param signal - Optional AbortSignal for request cancellation
     * @returns Paginated list of notifications
     * @throws NotificationApiError on API or network errors
     * @throws NotificationValidationError if response validation fails
     *
     * @example
     * ```typescript
     * // Get first page with defaults
     * const list = await api.listNotifications()
     *
     * // With filters
     * const unread = await api.listNotifications({
     *   unread_only: true,
     *   notification_type: 'workflow_created',
     *   page: 2,
     *   page_size: 50,
     * })
     *
     * // With cancellation
     * const controller = new AbortController()
     * const list = await api.listNotifications({}, controller.signal)
     * // Later: controller.abort()
     * ```
     */
    listNotifications: async (
      filters: NotificationFilters = {},
      signal?: AbortSignal,
    ): Promise<NotificationList> => {
      const params = buildListParams(filters)
      const endpoint = '/notifications'
      const cacheKey = createCacheKey('GET', endpoint, params)

      return wrapRequest(cacheKey, async () => {
        try {
          const { data } = await client.get<NotificationList>(endpoint, {
            params,
            signal,
          })
          return validate(NotificationListSchema, data, endpoint)
        } catch (error) {
          if (error instanceof NotificationApiError) throw error
          throw new NotificationApiError(
            error instanceof Error
              ? error.message
              : 'Failed to list notifications',
            endpoint,
            undefined,
            error instanceof Error ? error : undefined,
          )
        }
      })
    },

    /**
     * Get notification counts (total and unread).
     *
     * @param signal - Optional AbortSignal for request cancellation
     * @returns Notification count summary
     * @throws NotificationApiError on API or network errors
     * @throws NotificationValidationError if response validation fails
     *
     * @example
     * ```typescript
     * const counts = await api.getCount()
     * console.log(`You have ${counts.unread} unread notifications`)
     * ```
     */
    getCount: async (signal?: AbortSignal): Promise<NotificationCount> => {
      const endpoint = '/notifications/count'
      const cacheKey = createCacheKey('GET', endpoint)

      return wrapRequest(cacheKey, async () => {
        try {
          const { data } = await client.get<NotificationCount>(endpoint, {
            signal,
          })
          return validate(NotificationCountSchema, data, endpoint)
        } catch (error) {
          if (error instanceof NotificationApiError) throw error
          throw new NotificationApiError(
            error instanceof Error
              ? error.message
              : 'Failed to get notification count',
            endpoint,
            undefined,
            error instanceof Error ? error : undefined,
          )
        }
      })
    },

    /**
     * Get a specific notification by ID.
     *
     * @param notificationIdValue - The notification ID to fetch
     * @param signal - Optional AbortSignal for request cancellation
     * @returns The notification
     * @throws NotificationApiError on validation, API, or network errors
     * @throws NotificationNotFoundError if the notification doesn't exist
     * @throws NotificationValidationError if response validation fails
     *
     * @example
     * ```typescript
     * const notification = await api.getNotification(notificationId('notif-123'))
     * console.log(notification.title)
     * ```
     */
    getNotification: async (
      notificationIdValue: string | NotificationId,
      signal?: AbortSignal,
    ): Promise<Notification> => {
      validateNotificationId(notificationIdValue)
      const endpoint = `/notifications/${notificationIdValue}`
      const cacheKey = createCacheKey('GET', endpoint)

      return wrapRequest(cacheKey, async () => {
        try {
          const { data } = await client.get<Notification>(endpoint, { signal })
          return validate(NotificationSchema, data, endpoint)
        } catch (error) {
          if (error instanceof NotificationApiError) {
            // Convert 404 to specific error type
            if (error.statusCode === 404) {
              throw new NotificationNotFoundError(notificationIdValue)
            }
            if (error.statusCode === 403) {
              throw new NotificationPermissionError(notificationIdValue)
            }
            throw error
          }
          throw new NotificationApiError(
            error instanceof Error
              ? error.message
              : 'Failed to get notification',
            endpoint,
            undefined,
            error instanceof Error ? error : undefined,
          )
        }
      })
    },

    /**
     * Mark a specific notification as read.
     *
     * @param notificationIdValue - The notification ID to mark as read
     * @param signal - Optional AbortSignal for request cancellation
     * @returns The updated notification
     * @throws NotificationApiError on validation, API, or network errors
     *
     * @example
     * ```typescript
     * // Simple usage
     * const updated = await api.markAsRead(notificationId('notif-123'))
     *
     * // With optimistic update
     * const optimistic = createOptimisticRead(notification)
     * updateUI(optimistic)
     * try {
     *   const confirmed = await api.markAsRead(notificationId(notification.id))
     *   updateUI(confirmed)
     * } catch {
     *   rollbackUI(notification)
     * }
     * ```
     */
    markAsRead: async (
      notificationIdValue: string | NotificationId,
      signal?: AbortSignal,
    ): Promise<Notification> => {
      validateNotificationId(notificationIdValue)
      const endpoint = `/notifications/${notificationIdValue}/read`

      // Don't deduplicate write operations
      try {
        const { data } = await withRetry(
          () => client.patch<Notification>(endpoint, undefined, { signal }),
          retryOptions,
        )
        return validate(NotificationSchema, data, endpoint)
      } catch (error) {
        if (error instanceof NotificationApiError) throw error
        throw new NotificationApiError(
          error instanceof Error
            ? error.message
            : 'Failed to mark notification as read',
          endpoint,
          undefined,
          error instanceof Error ? error : undefined,
        )
      }
    },

    /**
     * Mark all notifications as read.
     *
     * @param signal - Optional AbortSignal for request cancellation
     * @returns Operation result with count of updated notifications
     * @throws NotificationApiError on API or network errors
     *
     * @example
     * ```typescript
     * const result = await api.markAllAsRead()
     * console.log(`Marked ${result.count} notifications as read`)
     * ```
     */
    markAllAsRead: async (
      signal?: AbortSignal,
    ): Promise<BulkOperationResponse> => {
      const endpoint = '/notifications/read-all'

      try {
        const { data } = await withRetry(
          () =>
            client.post<BulkOperationResponse>(endpoint, undefined, { signal }),
          retryOptions,
        )
        return validate(BulkOperationResponseSchema, data, endpoint)
      } catch (error) {
        if (error instanceof NotificationApiError) throw error
        throw new NotificationApiError(
          error instanceof Error
            ? error.message
            : 'Failed to mark all notifications as read',
          endpoint,
          undefined,
          error instanceof Error ? error : undefined,
        )
      }
    },

    /**
     * Mark multiple notifications as read.
     *
     * @param notificationIds - Array of notification IDs to mark as read (max 100)
     * @param signal - Optional AbortSignal for request cancellation
     * @returns Operation result with count of updated notifications
     * @throws NotificationApiError on validation, API, or network errors
     *
     * @example
     * ```typescript
     * const result = await api.markBulkAsRead(['notif-1', 'notif-2', 'notif-3'])
     * console.log(`Marked ${result.count} notifications as read`)
     * ```
     */
    markBulkAsRead: async (
      notificationIds: (string | NotificationId)[],
      signal?: AbortSignal,
    ): Promise<BulkOperationResponse> => {
      validateNotificationIds(notificationIds as string[])
      const endpoint = '/notifications/read-bulk'

      try {
        const { data } = await withRetry(
          () =>
            client.post<BulkOperationResponse>(
              endpoint,
              { notification_ids: notificationIds },
              { signal },
            ),
          retryOptions,
        )
        return validate(BulkOperationResponseSchema, data, endpoint)
      } catch (error) {
        if (error instanceof NotificationApiError) throw error
        throw new NotificationApiError(
          error instanceof Error
            ? error.message
            : 'Failed to mark notifications as read',
          endpoint,
          undefined,
          error instanceof Error ? error : undefined,
        )
      }
    },

    /**
     * Delete a notification.
     *
     * @param notificationIdValue - The notification ID to delete
     * @param signal - Optional AbortSignal for request cancellation
     * @returns Delete operation result
     * @throws NotificationApiError on validation, API, or network errors
     *
     * @example
     * ```typescript
     * const result = await api.deleteNotification(notificationId('notif-123'))
     * if (result.deleted) {
     *   console.log('Notification deleted successfully')
     * }
     * ```
     */
    deleteNotification: async (
      notificationIdValue: string | NotificationId,
      signal?: AbortSignal,
    ): Promise<DeleteResponse> => {
      validateNotificationId(notificationIdValue)
      const endpoint = `/notifications/${notificationIdValue}`

      try {
        const { data } = await withRetry(
          () => client.delete<DeleteResponse>(endpoint, { signal }),
          retryOptions,
        )
        return validate(DeleteResponseSchema, data, endpoint)
      } catch (error) {
        if (error instanceof NotificationApiError) throw error
        throw new NotificationApiError(
          error instanceof Error
            ? error.message
            : 'Failed to delete notification',
          endpoint,
          undefined,
          error instanceof Error ? error : undefined,
        )
      }
    },
  }
}

// ============================================================================
// Default Export (Backward Compatible)
// ============================================================================

/**
 * Default notification API instance for convenience.
 * For testing or custom configurations, use createNotificationApi() instead.
 *
 * @example
 * ```typescript
 * import { notificationApi } from './notification'
 *
 * // Use the default instance
 * const notifications = await notificationApi.listNotifications()
 * ```
 */
export const notificationApi = createNotificationApi()
