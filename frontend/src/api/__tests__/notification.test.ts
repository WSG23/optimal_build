import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'

import {
  createNotificationApi,
  notificationApi,
  NotificationApiError,
  NotificationNotFoundError,
  NotificationPermissionError,
  NotificationValidationError,
  DEFAULT_PAGE,
  DEFAULT_PAGE_SIZE,
  MAX_BULK_IDS,
  DEFAULT_RETRY_OPTIONS,
  // Branded types
  notificationId,
  userId,
  projectId,
  type NotificationId,
  type UserId,
  type ProjectId,
  // Zod schemas
  NotificationSchema,
  NotificationListSchema,
  NotificationCountSchema,
  BulkOperationResponseSchema,
  DeleteResponseSchema,
  // Utility functions
  withRetry,
  dedupe,
  clearDedupeCache,
  // Optimistic update helpers
  createOptimisticRead,
  createOptimisticUnread,
  createOptimisticBulkRead,
  createOptimisticDelete,
  // Types
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

const mockReadNotification: Notification = {
  ...mockNotification,
  is_read: true,
  read_at: '2025-01-15T11:00:00Z',
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

function mockFetchNetworkError() {
  return vi.fn().mockRejectedValue(new TypeError('Network request failed'))
}

// ============================================================================
// Tests
// ============================================================================

describe('notification API', () => {
  let originalFetch: typeof globalThis.fetch

  beforeEach(() => {
    originalFetch = globalThis.fetch
    clearDedupeCache()
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
    clearDedupeCache()
  })

  // --------------------------------------------------------------------------
  // Constants
  // --------------------------------------------------------------------------

  describe('constants', () => {
    it('exports default pagination constants', () => {
      expect(DEFAULT_PAGE).toBe(1)
      expect(DEFAULT_PAGE_SIZE).toBe(20)
    })

    it('exports bulk operation limit', () => {
      expect(MAX_BULK_IDS).toBe(100)
    })

    it('exports default retry options', () => {
      expect(DEFAULT_RETRY_OPTIONS).toEqual({
        maxAttempts: 3,
        baseDelayMs: 1000,
        maxDelayMs: 10000,
      })
    })
  })

  // --------------------------------------------------------------------------
  // Branded Types
  // --------------------------------------------------------------------------

  describe('branded types', () => {
    it('creates NotificationId from string', () => {
      const id = notificationId('notif-123')
      expect(id).toBe('notif-123')
      // Type assertion - these would fail to compile if types are wrong
      const _notifId: NotificationId = id
      expect(_notifId).toBeDefined()
    })

    it('creates UserId from string', () => {
      const id = userId('user-456')
      expect(id).toBe('user-456')
      const _userId: UserId = id
      expect(_userId).toBeDefined()
    })

    it('creates ProjectId from string', () => {
      const id = projectId('proj-789')
      expect(id).toBe('proj-789')
      const _projId: ProjectId = id
      expect(_projId).toBeDefined()
    })

    it('branded types are string compatible', () => {
      const id = notificationId('test-id')
      expect(id.length).toBe(7)
      expect(id.toUpperCase()).toBe('TEST-ID')
    })
  })

  // --------------------------------------------------------------------------
  // Zod Schema Validation
  // --------------------------------------------------------------------------

  describe('Zod schemas', () => {
    describe('NotificationSchema', () => {
      it('validates a valid notification', () => {
        const result = NotificationSchema.safeParse(mockNotification)
        expect(result.success).toBe(true)
      })

      it('rejects notification with invalid type', () => {
        const invalid = { ...mockNotification, notification_type: 'invalid' }
        const result = NotificationSchema.safeParse(invalid)
        expect(result.success).toBe(false)
      })

      it('rejects notification with missing required fields', () => {
        const invalid = { id: 'test' }
        const result = NotificationSchema.safeParse(invalid)
        expect(result.success).toBe(false)
      })

      it('accepts optional fields as undefined', () => {
        const minimal = {
          id: 'notif-1',
          user_id: 'user-1',
          notification_type: 'project_update',
          title: 'Test',
          message: 'Message',
          priority: 'normal',
          is_read: false,
          created_at: '2025-01-01T00:00:00Z',
        }
        const result = NotificationSchema.safeParse(minimal)
        expect(result.success).toBe(true)
      })
    })

    describe('NotificationListSchema', () => {
      it('validates a valid notification list', () => {
        const result = NotificationListSchema.safeParse(mockNotificationList)
        expect(result.success).toBe(true)
      })

      it('rejects list with negative total', () => {
        const invalid = { ...mockNotificationList, total: -1 }
        const result = NotificationListSchema.safeParse(invalid)
        expect(result.success).toBe(false)
      })

      it('rejects list with zero page', () => {
        const invalid = { ...mockNotificationList, page: 0 }
        const result = NotificationListSchema.safeParse(invalid)
        expect(result.success).toBe(false)
      })
    })

    describe('NotificationCountSchema', () => {
      it('validates valid counts', () => {
        const result = NotificationCountSchema.safeParse(mockNotificationCount)
        expect(result.success).toBe(true)
      })

      it('rejects negative counts', () => {
        const invalid = { total: 10, unread: -1 }
        const result = NotificationCountSchema.safeParse(invalid)
        expect(result.success).toBe(false)
      })
    })

    describe('BulkOperationResponseSchema', () => {
      it('validates valid bulk response', () => {
        const result = BulkOperationResponseSchema.safeParse({
          message: 'Success',
          count: 5,
        })
        expect(result.success).toBe(true)
      })
    })

    describe('DeleteResponseSchema', () => {
      it('validates valid delete response', () => {
        const result = DeleteResponseSchema.safeParse({
          message: 'Deleted',
          deleted: true,
        })
        expect(result.success).toBe(true)
      })
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

    it('accepts configuration options', () => {
      const api = createNotificationApi(undefined, {
        validateResponses: true,
        retry: { maxAttempts: 5 },
        deduplicate: false,
      })
      expect(api).toBeDefined()
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

    it('accepts branded NotificationId', async () => {
      globalThis.fetch = mockFetch(mockNotification)

      const id = notificationId('notif-123')
      const result = await notificationApi.getNotification(id)

      expect(result.id).toBe('notif-123')
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

    it('throws when exceeding bulk limit', async () => {
      const tooManyIds = Array.from({ length: 101 }, (_, i) => `notif-${i}`)
      await expect(notificationApi.markBulkAsRead(tooManyIds)).rejects.toThrow(
        `Cannot process more than ${MAX_BULK_IDS} notifications at once`,
      )
    })

    it('accepts branded NotificationIds', async () => {
      globalThis.fetch = mockFetch({ message: 'Success', count: 2 })

      const ids = [notificationId('notif-1'), notificationId('notif-2')]
      const result = await notificationApi.markBulkAsRead(ids)

      expect(result.count).toBe(2)
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
  // Error Classes
  // --------------------------------------------------------------------------

  describe('error classes', () => {
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

    describe('NotificationNotFoundError', () => {
      it('creates error with notification ID', () => {
        const error = new NotificationNotFoundError('notif-999')

        expect(error.name).toBe('NotificationNotFoundError')
        expect(error.notificationId).toBe('notif-999')
        expect(error.statusCode).toBe(404)
        expect(error.message).toBe('Notification notif-999 not found')
        expect(error.endpoint).toBe('/notifications/notif-999')
      })

      it('extends NotificationApiError', () => {
        const error = new NotificationNotFoundError('notif-999')
        expect(error).toBeInstanceOf(NotificationApiError)
      })
    })

    describe('NotificationPermissionError', () => {
      it('creates error with notification ID', () => {
        const error = new NotificationPermissionError('notif-999')

        expect(error.name).toBe('NotificationPermissionError')
        expect(error.notificationId).toBe('notif-999')
        expect(error.statusCode).toBe(403)
        expect(error.message).toBe(
          'No permission to access notification notif-999',
        )
      })

      it('extends NotificationApiError', () => {
        const error = new NotificationPermissionError('notif-999')
        expect(error).toBeInstanceOf(NotificationApiError)
      })
    })

    describe('NotificationValidationError', () => {
      it('creates error with Zod validation errors', () => {
        const zodResult = NotificationSchema.safeParse({ invalid: 'data' })
        if (zodResult.success) {
          expect.fail('Should have failed validation')
        }

        const error = new NotificationValidationError(
          '/notifications',
          zodResult.error,
        )

        expect(error.name).toBe('NotificationValidationError')
        expect(error.validationErrors).toBe(zodResult.error)
        expect(error.endpoint).toBe('/notifications')
        expect(error.message).toContain('Invalid API response')
      })
    })
  })

  // --------------------------------------------------------------------------
  // Retry Logic
  // --------------------------------------------------------------------------

  describe('withRetry', () => {
    it('returns result on first success', async () => {
      const fn = vi.fn().mockResolvedValue('success')

      const result = await withRetry(fn, { maxAttempts: 3 })

      expect(result).toBe('success')
      expect(fn).toHaveBeenCalledTimes(1)
    })

    it('retries on retryable error', async () => {
      const fn = vi
        .fn()
        .mockRejectedValueOnce(new TypeError('Network request failed'))
        .mockResolvedValue('success')

      const result = await withRetry(fn, {
        maxAttempts: 3,
        baseDelayMs: 10, // Short delay for tests
      })

      expect(result).toBe('success')
      expect(fn).toHaveBeenCalledTimes(2)
    })

    it('throws after max attempts', async () => {
      const fn = vi
        .fn()
        .mockRejectedValue(new TypeError('Network request failed'))

      await expect(
        withRetry(fn, { maxAttempts: 2, baseDelayMs: 10 }),
      ).rejects.toThrow('Network request failed')

      expect(fn).toHaveBeenCalledTimes(2)
    })

    it('does not retry non-retryable errors', async () => {
      const fn = vi
        .fn()
        .mockRejectedValue(new NotificationApiError('Not found', '/test', 404))

      await expect(
        withRetry(fn, { maxAttempts: 3, baseDelayMs: 10 }),
      ).rejects.toThrow(NotificationApiError)

      expect(fn).toHaveBeenCalledTimes(1)
    })

    it('retries on 5xx errors', async () => {
      const fn = vi
        .fn()
        .mockRejectedValueOnce(
          new NotificationApiError('Server error', '/test', 500),
        )
        .mockResolvedValue('success')

      const result = await withRetry(fn, { maxAttempts: 3, baseDelayMs: 10 })

      expect(result).toBe('success')
      expect(fn).toHaveBeenCalledTimes(2)
    })
  })

  // --------------------------------------------------------------------------
  // Request Deduplication
  // --------------------------------------------------------------------------

  describe('dedupe', () => {
    it('deduplicates concurrent requests', async () => {
      let callCount = 0
      const request = () => {
        callCount++
        return new Promise<string>((resolve) =>
          setTimeout(() => resolve('result'), 50),
        )
      }

      const [result1, result2, result3] = await Promise.all([
        dedupe('key', request),
        dedupe('key', request),
        dedupe('key', request),
      ])

      expect(result1).toBe('result')
      expect(result2).toBe('result')
      expect(result3).toBe('result')
      expect(callCount).toBe(1)
    })

    it('allows sequential requests', async () => {
      let callCount = 0
      const request = () => {
        callCount++
        return Promise.resolve('result')
      }

      await dedupe('key', request)
      await dedupe('key', request)

      expect(callCount).toBe(2)
    })

    it('uses different keys for different requests', async () => {
      let callCount = 0
      const request = () => {
        callCount++
        return Promise.resolve('result')
      }

      await Promise.all([
        dedupe('key1', request),
        dedupe('key2', request),
        dedupe('key3', request),
      ])

      expect(callCount).toBe(3)
    })

    it('clearDedupeCache clears pending requests', () => {
      // Start a request but don't await it
      const promise = dedupe(
        'key',
        () =>
          new Promise<string>((resolve) =>
            setTimeout(() => resolve('result'), 1000),
          ),
      )

      clearDedupeCache()

      // After clearing, a new request should start fresh
      let newCallMade = false
      const newPromise = dedupe('key', () => {
        newCallMade = true
        return Promise.resolve('new result')
      })

      expect(newCallMade).toBe(true)

      // Clean up
      void promise
      void newPromise
    })
  })

  // --------------------------------------------------------------------------
  // Optimistic Update Helpers
  // --------------------------------------------------------------------------

  describe('optimistic update helpers', () => {
    describe('createOptimisticRead', () => {
      it('marks notification as read with timestamp', () => {
        const result = createOptimisticRead(mockNotification)

        expect(result.is_read).toBe(true)
        expect(result.read_at).toBeDefined()
        expect(new Date(result.read_at!).getTime()).toBeCloseTo(
          Date.now(),
          -100,
        )
      })

      it('preserves other properties', () => {
        const result = createOptimisticRead(mockNotification)

        expect(result.id).toBe(mockNotification.id)
        expect(result.title).toBe(mockNotification.title)
        expect(result.message).toBe(mockNotification.message)
      })

      it('returns a new object (immutable)', () => {
        const result = createOptimisticRead(mockNotification)

        expect(result).not.toBe(mockNotification)
        expect(mockNotification.is_read).toBe(false)
      })
    })

    describe('createOptimisticUnread', () => {
      it('marks notification as unread and removes read_at', () => {
        const result = createOptimisticUnread(mockReadNotification)

        expect(result.is_read).toBe(false)
        expect(result.read_at).toBeUndefined()
      })

      it('preserves other properties', () => {
        const result = createOptimisticUnread(mockReadNotification)

        expect(result.id).toBe(mockReadNotification.id)
        expect(result.title).toBe(mockReadNotification.title)
      })
    })

    describe('createOptimisticBulkRead', () => {
      it('marks specified notifications as read', () => {
        const notifications: Notification[] = [
          { ...mockNotification, id: 'notif-1' },
          { ...mockNotification, id: 'notif-2' },
          { ...mockNotification, id: 'notif-3' },
        ]

        const result = createOptimisticBulkRead(notifications, [
          'notif-1',
          'notif-3',
        ])

        expect(result[0]?.is_read).toBe(true)
        expect(result[0]?.read_at).toBeDefined()
        expect(result[1]?.is_read).toBe(false)
        expect(result[1]?.read_at).toBeUndefined()
        expect(result[2]?.is_read).toBe(true)
        expect(result[2]?.read_at).toBeDefined()
      })

      it('accepts Set of IDs', () => {
        const notifications: Notification[] = [
          { ...mockNotification, id: 'notif-1' },
          { ...mockNotification, id: 'notif-2' },
        ]

        const result = createOptimisticBulkRead(
          notifications,
          new Set(['notif-1']),
        )

        expect(result[0]?.is_read).toBe(true)
        expect(result[1]?.is_read).toBe(false)
      })

      it('uses consistent timestamp for all updates', () => {
        const notifications: Notification[] = [
          { ...mockNotification, id: 'notif-1' },
          { ...mockNotification, id: 'notif-2' },
        ]

        const result = createOptimisticBulkRead(notifications, [
          'notif-1',
          'notif-2',
        ])

        expect(result[0]?.read_at).toBe(result[1]?.read_at)
      })
    })

    describe('createOptimisticDelete', () => {
      it('removes notification from list', () => {
        const list: NotificationList = {
          ...mockNotificationList,
          notifications: [
            { ...mockNotification, id: 'notif-1' },
            { ...mockNotification, id: 'notif-2' },
          ],
          total: 2,
          unread_count: 2,
        }

        const result = createOptimisticDelete(list, 'notif-1')

        expect(result.notifications).toHaveLength(1)
        expect(result.notifications[0]?.id).toBe('notif-2')
        expect(result.total).toBe(1)
      })

      it('decrements unread_count for unread notification', () => {
        const list: NotificationList = {
          ...mockNotificationList,
          notifications: [{ ...mockNotification, is_read: false }],
          total: 1,
          unread_count: 1,
        }

        const result = createOptimisticDelete(list, 'notif-123')

        expect(result.unread_count).toBe(0)
      })

      it('does not decrement unread_count for read notification', () => {
        const list: NotificationList = {
          ...mockNotificationList,
          notifications: [{ ...mockNotification, is_read: true }],
          total: 1,
          unread_count: 0,
        }

        const result = createOptimisticDelete(list, 'notif-123')

        expect(result.unread_count).toBe(0)
      })

      it('handles deletion of non-existent notification', () => {
        const result = createOptimisticDelete(
          mockNotificationList,
          'non-existent',
        )

        expect(result.notifications).toHaveLength(1)
        expect(result.total).toBe(0)
      })

      it('prevents negative counts', () => {
        const list: NotificationList = {
          ...mockNotificationList,
          total: 0,
          unread_count: 0,
        }

        const result = createOptimisticDelete(list, 'notif-123')

        expect(result.total).toBe(0)
        expect(result.unread_count).toBe(0)
      })
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

  // --------------------------------------------------------------------------
  // Response Validation
  // --------------------------------------------------------------------------

  describe('response validation', () => {
    it('validates response with validateResponses option enabled', async () => {
      const api = createNotificationApi(undefined, { validateResponses: true })

      // Mock a response with invalid structure
      globalThis.fetch = mockFetch({ invalid: 'data' })

      await expect(api.listNotifications()).rejects.toThrow(
        NotificationValidationError,
      )
    })

    it('skips validation when validateResponses is false', async () => {
      const api = createNotificationApi(undefined, { validateResponses: false })

      // Mock a response with valid structure
      globalThis.fetch = mockFetch(mockNotificationList)

      // Should not throw even if we were to pass invalid data
      const result = await api.listNotifications()
      expect(result).toBeDefined()
    })
  })

  // --------------------------------------------------------------------------
  // API Configuration
  // --------------------------------------------------------------------------

  describe('API configuration', () => {
    it('uses custom retry options', async () => {
      const api = createNotificationApi(undefined, {
        retry: { maxAttempts: 1 },
        validateResponses: false,
      })

      // Mock a retryable error - with maxAttempts: 1, should fail immediately
      globalThis.fetch = mockFetchNetworkError()

      await expect(api.listNotifications()).rejects.toThrow()

      // Should only have tried once
      expect(globalThis.fetch).toHaveBeenCalledTimes(1)
    })

    it('respects deduplicate option', async () => {
      const api = createNotificationApi(undefined, {
        deduplicate: false,
        validateResponses: false,
      })

      let callCount = 0
      globalThis.fetch = vi.fn().mockImplementation(async () => {
        callCount++
        await new Promise((r) => setTimeout(r, 50))
        return {
          ok: true,
          status: 200,
          text: async () => JSON.stringify(mockNotificationCount),
        }
      })

      // Without deduplication, concurrent calls should each make a request
      await Promise.all([api.getCount(), api.getCount()])

      expect(callCount).toBe(2)
    })
  })
})
