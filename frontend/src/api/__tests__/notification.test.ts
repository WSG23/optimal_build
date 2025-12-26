import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'

import {
  createNotificationApi,
  notificationApi,
  NotificationApiError,
  DEFAULT_PAGE,
  DEFAULT_PAGE_SIZE,
  type Notification,
  type NotificationList,
  type NotificationCount,
} from '../notification'

// ============================================================================
// Test Fixtures
// ============================================================================

const mockNotification: Notification = {
  id: 'notif-123',
  user_id: 'user-456',
  notification_type: 'project_update',
  title: 'Project Updated',
  message: 'Your project has been updated',
  priority: 'normal',
  project_id: 'proj-789',
  is_read: false,
  created_at: '2025-01-15T10:00:00Z',
}

const mockNotificationList: NotificationList = {
  notifications: [mockNotification],
  total: 1,
  unread_count: 1,
  page: 1,
  page_size: 20,
  has_more: false,
}

const mockNotificationCount: NotificationCount = {
  total: 10,
  unread: 3,
}

// ============================================================================
// Helper Functions
// ============================================================================

function mockFetch<T>(
  response: T,
  options?: { status?: number; ok?: boolean },
) {
  return vi.fn().mockResolvedValue({
    ok: options?.ok ?? true,
    status: options?.status ?? 200,
    text: async () => JSON.stringify(response),
    json: async () => response,
  })
}

function mockFetchError(errorMessage: string) {
  return vi.fn().mockRejectedValue(new Error(errorMessage))
}

// ============================================================================
// Tests
// ============================================================================

describe('notification API', () => {
  let originalFetch: typeof globalThis.fetch

  beforeEach(() => {
    originalFetch = globalThis.fetch
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
  })

  // --------------------------------------------------------------------------
  // Constants
  // --------------------------------------------------------------------------

  describe('constants', () => {
    it('exports default pagination constants', () => {
      expect(DEFAULT_PAGE).toBe(1)
      expect(DEFAULT_PAGE_SIZE).toBe(20)
    })
  })

  // --------------------------------------------------------------------------
  // Factory Function
  // --------------------------------------------------------------------------

  describe('createNotificationApi', () => {
    it('creates an API instance with all methods', () => {
      const api = createNotificationApi()

      expect(api.listNotifications).toBeInstanceOf(Function)
      expect(api.getCount).toBeInstanceOf(Function)
      expect(api.getNotification).toBeInstanceOf(Function)
      expect(api.markAsRead).toBeInstanceOf(Function)
      expect(api.markAllAsRead).toBeInstanceOf(Function)
      expect(api.markBulkAsRead).toBeInstanceOf(Function)
      expect(api.deleteNotification).toBeInstanceOf(Function)
    })

    it('exports a default notificationApi instance', () => {
      expect(notificationApi).toBeDefined()
      expect(notificationApi.listNotifications).toBeInstanceOf(Function)
    })
  })

  // --------------------------------------------------------------------------
  // listNotifications
  // --------------------------------------------------------------------------

  describe('listNotifications', () => {
    it('fetches notifications with default pagination', async () => {
      globalThis.fetch = mockFetch(mockNotificationList)

      const result = await notificationApi.listNotifications()

      expect(result.notifications).toHaveLength(1)
      expect(result.notifications[0]?.id).toBe('notif-123')
      expect(result.total).toBe(1)
      expect(result.unread_count).toBe(1)

      // Verify default params were used
      const fetchCall = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
        .calls[0]
      const url = fetchCall?.[0] as string
      expect(url).toContain('page=1')
      expect(url).toContain('page_size=20')
    })

    it('applies custom filters to the request', async () => {
      globalThis.fetch = mockFetch(mockNotificationList)

      await notificationApi.listNotifications({
        page: 2,
        page_size: 50,
        unread_only: true,
        notification_type: 'workflow_created',
        project_id: 'proj-abc',
      })

      const fetchCall = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
        .calls[0]
      const url = fetchCall?.[0] as string
      expect(url).toContain('page=2')
      expect(url).toContain('page_size=50')
      expect(url).toContain('unread_only=true')
      expect(url).toContain('notification_type=workflow_created')
      expect(url).toContain('project_id=proj-abc')
    })

    it('omits unread_only param when false', async () => {
      globalThis.fetch = mockFetch(mockNotificationList)

      await notificationApi.listNotifications({ unread_only: false })

      const fetchCall = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
        .calls[0]
      const url = fetchCall?.[0] as string
      expect(url).not.toContain('unread_only')
    })

    it('throws NotificationApiError on network failure', async () => {
      globalThis.fetch = mockFetchError('Network error')

      await expect(notificationApi.listNotifications()).rejects.toThrow(
        NotificationApiError,
      )
    })
  })

  // --------------------------------------------------------------------------
  // getCount
  // --------------------------------------------------------------------------

  describe('getCount', () => {
    it('fetches notification counts', async () => {
      globalThis.fetch = mockFetch(mockNotificationCount)

      const result = await notificationApi.getCount()

      expect(result.total).toBe(10)
      expect(result.unread).toBe(3)
    })

    it('throws NotificationApiError on failure', async () => {
      globalThis.fetch = mockFetchError('Server error')

      await expect(notificationApi.getCount()).rejects.toThrow(
        NotificationApiError,
      )
    })
  })

  // --------------------------------------------------------------------------
  // getNotification
  // --------------------------------------------------------------------------

  describe('getNotification', () => {
    it('fetches a single notification by ID', async () => {
      globalThis.fetch = mockFetch(mockNotification)

      const result = await notificationApi.getNotification('notif-123')

      expect(result.id).toBe('notif-123')
      expect(result.title).toBe('Project Updated')

      const fetchCall = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
        .calls[0]
      const url = fetchCall?.[0] as string
      expect(url).toContain('/notifications/notif-123')
    })

    it('throws on empty notification ID', async () => {
      await expect(notificationApi.getNotification('')).rejects.toThrow(
        NotificationApiError,
      )
      await expect(notificationApi.getNotification('')).rejects.toThrow(
        'Notification ID must be a non-empty string',
      )
    })

    it('throws on whitespace-only notification ID', async () => {
      await expect(notificationApi.getNotification('   ')).rejects.toThrow(
        NotificationApiError,
      )
      await expect(notificationApi.getNotification('   ')).rejects.toThrow(
        'Notification ID cannot be empty or whitespace',
      )
    })

    it('includes endpoint in error', async () => {
      globalThis.fetch = mockFetchError('Not found')

      try {
        await notificationApi.getNotification('notif-999')
        expect.fail('Should have thrown')
      } catch (error) {
        expect(error).toBeInstanceOf(NotificationApiError)
        expect((error as NotificationApiError).endpoint).toBe(
          '/notifications/notif-999',
        )
      }
    })
  })

  // --------------------------------------------------------------------------
  // markAsRead
  // --------------------------------------------------------------------------

  describe('markAsRead', () => {
    it('marks a notification as read', async () => {
      const readNotification = { ...mockNotification, is_read: true }
      globalThis.fetch = mockFetch(readNotification)

      const result = await notificationApi.markAsRead('notif-123')

      expect(result.is_read).toBe(true)

      const fetchCall = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
        .calls[0]
      const url = fetchCall?.[0] as string
      const options = fetchCall?.[1] as RequestInit
      expect(url).toContain('/notifications/notif-123/read')
      expect(options.method).toBe('PATCH')
    })

    it('validates notification ID before making request', async () => {
      const mockFn = vi.fn()
      globalThis.fetch = mockFn

      await expect(notificationApi.markAsRead('')).rejects.toThrow(
        NotificationApiError,
      )
      expect(mockFn).not.toHaveBeenCalled()
    })
  })

  // --------------------------------------------------------------------------
  // markAllAsRead
  // --------------------------------------------------------------------------

  describe('markAllAsRead', () => {
    it('marks all notifications as read', async () => {
      globalThis.fetch = mockFetch({ message: 'Success', count: 5 })

      const result = await notificationApi.markAllAsRead()

      expect(result.message).toBe('Success')
      expect(result.count).toBe(5)

      const fetchCall = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
        .calls[0]
      const url = fetchCall?.[0] as string
      const options = fetchCall?.[1] as RequestInit
      expect(url).toContain('/notifications/read-all')
      expect(options.method).toBe('POST')
    })
  })

  // --------------------------------------------------------------------------
  // markBulkAsRead
  // --------------------------------------------------------------------------

  describe('markBulkAsRead', () => {
    it('marks multiple notifications as read', async () => {
      globalThis.fetch = mockFetch({ message: 'Success', count: 3 })

      const result = await notificationApi.markBulkAsRead([
        'notif-1',
        'notif-2',
        'notif-3',
      ])

      expect(result.count).toBe(3)

      const fetchCall = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
        .calls[0]
      const options = fetchCall?.[1] as RequestInit
      expect(options.method).toBe('POST')
      expect(options.body).toContain('notification_ids')
      expect(options.body).not.toContain('is_read')
    })

    it('throws on empty array', async () => {
      await expect(notificationApi.markBulkAsRead([])).rejects.toThrow(
        NotificationApiError,
      )
      await expect(notificationApi.markBulkAsRead([])).rejects.toThrow(
        'Notification IDs array cannot be empty',
      )
    })

    it('throws on array with invalid ID', async () => {
      await expect(
        notificationApi.markBulkAsRead(['valid-id', '']),
      ).rejects.toThrow(NotificationApiError)
    })
  })

  // --------------------------------------------------------------------------
  // deleteNotification
  // --------------------------------------------------------------------------

  describe('deleteNotification', () => {
    it('deletes a notification', async () => {
      globalThis.fetch = mockFetch({ message: 'Deleted', deleted: true })

      const result = await notificationApi.deleteNotification('notif-123')

      expect(result.deleted).toBe(true)

      const fetchCall = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
        .calls[0]
      const url = fetchCall?.[0] as string
      const options = fetchCall?.[1] as RequestInit
      expect(url).toContain('/notifications/notif-123')
      expect(options.method).toBe('DELETE')
    })

    it('validates notification ID', async () => {
      await expect(notificationApi.deleteNotification('')).rejects.toThrow(
        NotificationApiError,
      )
    })
  })

  // --------------------------------------------------------------------------
  // Error Handling
  // --------------------------------------------------------------------------

  describe('NotificationApiError', () => {
    it('captures error context correctly', () => {
      const originalError = new Error('Original error')
      const apiError = new NotificationApiError(
        'API failed',
        '/notifications',
        500,
        originalError,
      )

      expect(apiError.name).toBe('NotificationApiError')
      expect(apiError.message).toBe('API failed')
      expect(apiError.endpoint).toBe('/notifications')
      expect(apiError.statusCode).toBe(500)
      expect(apiError.originalError).toBe(originalError)
    })

    it('works without optional fields', () => {
      const apiError = new NotificationApiError(
        'Validation failed',
        'validation',
      )

      expect(apiError.statusCode).toBeUndefined()
      expect(apiError.originalError).toBeUndefined()
    })
  })

  // --------------------------------------------------------------------------
  // AbortSignal Support
  // --------------------------------------------------------------------------

  describe('AbortSignal support', () => {
    it('accepts AbortSignal parameter for listNotifications', async () => {
      globalThis.fetch = mockFetch(mockNotificationList)
      const controller = new AbortController()

      // Verify the API accepts signal without throwing
      const result = await notificationApi.listNotifications(
        {},
        controller.signal,
      )
      expect(result.notifications).toHaveLength(1)
    })

    it('accepts AbortSignal parameter for getNotification', async () => {
      globalThis.fetch = mockFetch(mockNotification)
      const controller = new AbortController()

      // Verify the API accepts signal without throwing
      const result = await notificationApi.getNotification(
        'notif-123',
        controller.signal,
      )
      expect(result.id).toBe('notif-123')
    })

    it('accepts AbortSignal parameter for all methods', async () => {
      const controller = new AbortController()

      // Test getCount
      globalThis.fetch = mockFetch(mockNotificationCount)
      await notificationApi.getCount(controller.signal)

      // Test markAsRead
      globalThis.fetch = mockFetch({ ...mockNotification, is_read: true })
      await notificationApi.markAsRead('notif-123', controller.signal)

      // Test markAllAsRead
      globalThis.fetch = mockFetch({ message: 'Success', count: 1 })
      await notificationApi.markAllAsRead(controller.signal)

      // Test markBulkAsRead
      globalThis.fetch = mockFetch({ message: 'Success', count: 1 })
      await notificationApi.markBulkAsRead(['notif-123'], controller.signal)

      // Test deleteNotification
      globalThis.fetch = mockFetch({ message: 'Deleted', deleted: true })
      await notificationApi.deleteNotification('notif-123', controller.signal)

      // If we get here without throwing, signal is accepted by all methods
      expect(true).toBe(true)
    })
  })
})
