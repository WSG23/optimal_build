import { ApiClient } from './client'

// ============================================================================
// Constants
// ============================================================================

/** Default page number for pagination */
export const DEFAULT_PAGE = 1

/** Default number of items per page */
export const DEFAULT_PAGE_SIZE = 20

/** Default value for unread_only filter */
export const DEFAULT_UNREAD_ONLY = false

// ============================================================================
// Types
// ============================================================================

/**
 * Notification types supported by the system.
 * These should match the backend NotificationType enum values.
 */
export type NotificationType =
  | 'team_invitation'
  | 'team_member_joined'
  | 'team_member_removed'
  | 'workflow_created'
  | 'workflow_step_assigned'
  | 'workflow_step_completed'
  | 'workflow_completed'
  | 'workflow_approval_needed'
  | 'workflow_rejected'
  | 'project_update'
  | 'project_milestone'
  | 'regulatory_status_change'
  | 'regulatory_rfi'
  | 'system_announcement'

/**
 * Notification priority levels.
 * These should match the backend NotificationPriority enum values.
 */
export type NotificationPriority = 'low' | 'normal' | 'high' | 'urgent'

/**
 * Notification entity representing a user notification.
 */
export interface Notification {
  id: string
  user_id: string
  notification_type: NotificationType
  title: string
  message: string
  priority: NotificationPriority
  project_id?: string
  related_entity_type?: string
  related_entity_id?: string
  is_read: boolean
  read_at?: string
  created_at: string
  expires_at?: string
}

/**
 * Paginated list of notifications with metadata.
 */
export interface NotificationList {
  notifications: Notification[]
  total: number
  unread_count: number
  page: number
  page_size: number
  has_more: boolean
}

/**
 * Notification count summary.
 */
export interface NotificationCount {
  total: number
  unread: number
}

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
 * Response for bulk operations.
 */
export interface BulkOperationResponse {
  message: string
  count: number
}

/**
 * Response for delete operations.
 */
export interface DeleteResponse {
  message: string
  deleted: boolean
}

// ============================================================================
// Error Classes
// ============================================================================

/**
 * Custom error class for notification API errors with additional context.
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

// ============================================================================
// Validation Helpers
// ============================================================================

/**
 * Validates that a notification ID is a non-empty string.
 * @param notificationId - The ID to validate
 * @throws NotificationApiError if validation fails
 */
function validateNotificationId(notificationId: string): void {
  if (!notificationId || typeof notificationId !== 'string') {
    throw new NotificationApiError(
      'Notification ID must be a non-empty string',
      'validation',
    )
  }
  if (notificationId.trim().length === 0) {
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

// ============================================================================
// API Factory
// ============================================================================

/**
 * Creates a notification API instance with dependency injection support.
 * This enables easier testing and custom client configurations.
 *
 * @param client - Optional ApiClient instance (defaults to new ApiClient())
 * @returns Notification API methods
 */
export function createNotificationApi(client: ApiClient = new ApiClient()) {
  return {
    /**
     * List notifications for the current user with pagination and filters.
     *
     * @param filters - Optional filters for pagination and filtering
     * @param signal - Optional AbortSignal for request cancellation
     * @returns Paginated list of notifications
     * @throws NotificationApiError on API or network errors
     */
    listNotifications: async (
      filters: NotificationFilters = {},
      signal?: AbortSignal,
    ): Promise<NotificationList> => {
      const params = buildListParams(filters)
      try {
        const { data } = await client.get<NotificationList>('/notifications', {
          params,
          signal,
        })
        return data
      } catch (error) {
        throw new NotificationApiError(
          error instanceof Error
            ? error.message
            : 'Failed to list notifications',
          '/notifications',
          undefined,
          error instanceof Error ? error : undefined,
        )
      }
    },

    /**
     * Get notification counts (total and unread).
     *
     * @param signal - Optional AbortSignal for request cancellation
     * @returns Notification count summary
     * @throws NotificationApiError on API or network errors
     */
    getCount: async (signal?: AbortSignal): Promise<NotificationCount> => {
      try {
        const { data } = await client.get<NotificationCount>(
          '/notifications/count',
          { signal },
        )
        return data
      } catch (error) {
        throw new NotificationApiError(
          error instanceof Error
            ? error.message
            : 'Failed to get notification count',
          '/notifications/count',
          undefined,
          error instanceof Error ? error : undefined,
        )
      }
    },

    /**
     * Get a specific notification by ID.
     *
     * @param notificationId - The notification ID to fetch
     * @param signal - Optional AbortSignal for request cancellation
     * @returns The notification
     * @throws NotificationApiError on validation, API, or network errors
     */
    getNotification: async (
      notificationId: string,
      signal?: AbortSignal,
    ): Promise<Notification> => {
      validateNotificationId(notificationId)
      const endpoint = `/notifications/${notificationId}`
      try {
        const { data } = await client.get<Notification>(endpoint, { signal })
        return data
      } catch (error) {
        throw new NotificationApiError(
          error instanceof Error ? error.message : 'Failed to get notification',
          endpoint,
          undefined,
          error instanceof Error ? error : undefined,
        )
      }
    },

    /**
     * Mark a specific notification as read.
     *
     * @param notificationId - The notification ID to mark as read
     * @param signal - Optional AbortSignal for request cancellation
     * @returns The updated notification
     * @throws NotificationApiError on validation, API, or network errors
     */
    markAsRead: async (
      notificationId: string,
      signal?: AbortSignal,
    ): Promise<Notification> => {
      validateNotificationId(notificationId)
      const endpoint = `/notifications/${notificationId}/read`
      try {
        const { data } = await client.patch<Notification>(endpoint, undefined, {
          signal,
        })
        return data
      } catch (error) {
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
     */
    markAllAsRead: async (
      signal?: AbortSignal,
    ): Promise<BulkOperationResponse> => {
      const endpoint = '/notifications/read-all'
      try {
        const { data } = await client.post<BulkOperationResponse>(
          endpoint,
          undefined,
          { signal },
        )
        return data
      } catch (error) {
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
     * @param notificationIds - Array of notification IDs to mark as read
     * @param signal - Optional AbortSignal for request cancellation
     * @returns Operation result with count of updated notifications
     * @throws NotificationApiError on validation, API, or network errors
     */
    markBulkAsRead: async (
      notificationIds: string[],
      signal?: AbortSignal,
    ): Promise<BulkOperationResponse> => {
      validateNotificationIds(notificationIds)
      const endpoint = '/notifications/read-bulk'
      try {
        const { data } = await client.post<BulkOperationResponse>(
          endpoint,
          { notification_ids: notificationIds },
          { signal },
        )
        return data
      } catch (error) {
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
     * @param notificationId - The notification ID to delete
     * @param signal - Optional AbortSignal for request cancellation
     * @returns Delete operation result
     * @throws NotificationApiError on validation, API, or network errors
     */
    deleteNotification: async (
      notificationId: string,
      signal?: AbortSignal,
    ): Promise<DeleteResponse> => {
      validateNotificationId(notificationId)
      const endpoint = `/notifications/${notificationId}`
      try {
        const { data } = await client.delete<DeleteResponse>(endpoint, {
          signal,
        })
        return data
      } catch (error) {
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
 */
export const notificationApi = createNotificationApi()
