/**
 * Notification API client for in-app notifications.
 */

import { applyIdentityHeaders } from './identity'

const API_BASE = '/api/v1/notifications'

export type NotificationType =
  | 'team_invite'
  | 'team_invite_accepted'
  | 'team_member_joined'
  | 'team_member_left'
  | 'workflow_created'
  | 'workflow_approval_pending'
  | 'workflow_approved'
  | 'workflow_rejected'
  | 'workflow_step_completed'
  | 'submission_status_changed'
  | 'submission_approved'
  | 'submission_rejected'
  | 'submission_rfi'
  | 'system'
  | 'reminder'

export type NotificationPriority = 'low' | 'normal' | 'high' | 'urgent'

export interface Notification {
  id: string
  userId: string
  notificationType: NotificationType
  title: string
  message: string
  priority: NotificationPriority
  relatedEntityType: string | null
  relatedEntityId: string | null
  actionUrl: string | null
  isRead: boolean
  isDismissed: boolean
  createdAt: string
  readAt: string | null
  dismissedAt: string | null
}

export interface NotificationListResponse {
  items: Notification[]
  total: number
  unreadCount: number
  page: number
  pageSize: number
  hasMore: boolean
}

export interface NotificationCountResponse {
  total: number
  unread: number
  byType: Record<string, number>
}

export interface MarkReadRequest {
  notificationIds?: string[]
  markAll?: boolean
}

export interface DismissRequest {
  notificationIds?: string[]
  dismissAll?: boolean
}

// Convert snake_case API response to camelCase
function transformNotification(data: Record<string, unknown>): Notification {
  return {
    id: data.id as string,
    userId: data.user_id as string,
    notificationType: data.notification_type as NotificationType,
    title: data.title as string,
    message: data.message as string,
    priority: data.priority as NotificationPriority,
    relatedEntityType: data.related_entity_type as string | null,
    relatedEntityId: data.related_entity_id as string | null,
    actionUrl: data.action_url as string | null,
    isRead: data.is_read as boolean,
    isDismissed: data.is_dismissed as boolean,
    createdAt: data.created_at as string,
    readAt: data.read_at as string | null,
    dismissedAt: data.dismissed_at as string | null,
  }
}

/**
 * Fetch user notifications with pagination.
 */
export async function getNotifications(
  userId: string,
  options: {
    includeDismissed?: boolean
    notificationType?: NotificationType
    page?: number
    pageSize?: number
  } = {},
): Promise<NotificationListResponse> {
  const params = new URLSearchParams({ user_id: userId })

  if (options.includeDismissed) {
    params.set('include_dismissed', 'true')
  }
  if (options.notificationType) {
    params.set('notification_type', options.notificationType)
  }
  if (options.page) {
    params.set('page', String(options.page))
  }
  if (options.pageSize) {
    params.set('page_size', String(options.pageSize))
  }

  const response = await fetch(`${API_BASE}?${params.toString()}`, {
    headers: applyIdentityHeaders({}),
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch notifications: ${response.statusText}`)
  }

  const data = await response.json()
  return {
    items: data.items.map(transformNotification),
    total: data.total,
    unreadCount: data.unread_count,
    page: data.page,
    pageSize: data.page_size,
    hasMore: data.has_more,
  }
}

/**
 * Get notification counts for a user.
 */
export async function getNotificationCounts(
  userId: string,
): Promise<NotificationCountResponse> {
  const params = new URLSearchParams({ user_id: userId })

  const response = await fetch(`${API_BASE}/count?${params.toString()}`, {
    headers: applyIdentityHeaders({}),
  })

  if (!response.ok) {
    throw new Error(
      `Failed to fetch notification counts: ${response.statusText}`,
    )
  }

  const data = await response.json()
  return {
    total: data.total,
    unread: data.unread,
    byType: data.by_type,
  }
}

/**
 * Mark notifications as read.
 */
export async function markNotificationsRead(
  userId: string,
  request: MarkReadRequest,
): Promise<{ markedCount: number }> {
  const params = new URLSearchParams({ user_id: userId })

  const response = await fetch(`${API_BASE}/mark-read?${params.toString()}`, {
    method: 'POST',
    headers: applyIdentityHeaders({
      'Content-Type': 'application/json',
    }),
    body: JSON.stringify({
      notification_ids: request.notificationIds || [],
      mark_all: request.markAll || false,
    }),
  })

  if (!response.ok) {
    throw new Error(
      `Failed to mark notifications as read: ${response.statusText}`,
    )
  }

  const data = await response.json()
  return { markedCount: data.marked_count }
}

/**
 * Dismiss notifications.
 */
export async function dismissNotifications(
  userId: string,
  request: DismissRequest,
): Promise<{ dismissedCount: number }> {
  const params = new URLSearchParams({ user_id: userId })

  const response = await fetch(`${API_BASE}/dismiss?${params.toString()}`, {
    method: 'POST',
    headers: applyIdentityHeaders({
      'Content-Type': 'application/json',
    }),
    body: JSON.stringify({
      notification_ids: request.notificationIds || [],
      dismiss_all: request.dismissAll || false,
    }),
  })

  if (!response.ok) {
    throw new Error(`Failed to dismiss notifications: ${response.statusText}`)
  }

  const data = await response.json()
  return { dismissedCount: data.dismissed_count }
}

/**
 * Delete a notification permanently.
 */
export async function deleteNotification(
  userId: string,
  notificationId: string,
): Promise<void> {
  const params = new URLSearchParams({ user_id: userId })

  const response = await fetch(
    `${API_BASE}/${notificationId}?${params.toString()}`,
    {
      method: 'DELETE',
      headers: applyIdentityHeaders({}),
    },
  )

  if (!response.ok) {
    throw new Error(`Failed to delete notification: ${response.statusText}`)
  }
}

export const notificationsApi = {
  getNotifications,
  getNotificationCounts,
  markNotificationsRead,
  dismissNotifications,
  deleteNotification,
}
