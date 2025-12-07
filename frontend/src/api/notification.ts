import { ApiClient } from './client'

const apiClient = new ApiClient()

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

export type NotificationPriority = 'low' | 'normal' | 'high' | 'urgent'

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

export interface NotificationList {
  notifications: Notification[]
  total: number
  unread_count: number
  page: number
  page_size: number
  has_more: boolean
}

export interface NotificationCount {
  total: number
  unread: number
}

export interface NotificationFilters {
  page?: number
  page_size?: number
  unread_only?: boolean
  notification_type?: NotificationType
  project_id?: string
}

export const notificationApi = {
  /**
   * List notifications for the current user with pagination and filters.
   */
  listNotifications: async (
    filters: NotificationFilters = {},
  ): Promise<NotificationList> => {
    const { data } = await apiClient.get<NotificationList>('/notifications', {
      params: {
        page: filters.page || 1,
        page_size: filters.page_size || 20,
        unread_only: filters.unread_only || false,
        notification_type: filters.notification_type,
        project_id: filters.project_id,
      },
    })
    return data
  },

  /**
   * Get notification counts (total and unread).
   */
  getCount: async (): Promise<NotificationCount> => {
    const { data } = await apiClient.get<NotificationCount>(
      '/notifications/count',
    )
    return data
  },

  /**
   * Get a specific notification by ID.
   */
  getNotification: async (notificationId: string): Promise<Notification> => {
    const { data } = await apiClient.get<Notification>(
      `/notifications/${notificationId}`,
    )
    return data
  },

  /**
   * Mark a specific notification as read.
   */
  markAsRead: async (notificationId: string): Promise<Notification> => {
    const { data } = await apiClient.patch<Notification>(
      `/notifications/${notificationId}/read`,
    )
    return data
  },

  /**
   * Mark all notifications as read.
   */
  markAllAsRead: async (): Promise<{ message: string; count: number }> => {
    const { data } = await apiClient.post<{ message: string; count: number }>(
      '/notifications/read-all',
    )
    return data
  },

  /**
   * Mark multiple notifications as read.
   */
  markBulkAsRead: async (
    notificationIds: string[],
  ): Promise<{ message: string; count: number }> => {
    const { data } = await apiClient.post<{ message: string; count: number }>(
      '/notifications/read-bulk',
      { notification_ids: notificationIds, is_read: true },
    )
    return data
  },

  /**
   * Delete a notification.
   */
  deleteNotification: async (
    notificationId: string,
  ): Promise<{ message: string; deleted: boolean }> => {
    const { data } = await apiClient.delete<{
      message: string
      deleted: boolean
    }>(`/notifications/${notificationId}`)
    return data
  },
}
