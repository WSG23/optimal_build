/**
 * Notification context for managing in-app notifications.
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'
import {
  Notification,
  NotificationListResponse,
  notificationsApi,
} from '../api/notifications'
import { resolveDefaultUserId } from '../api/identity'

interface NotificationContextValue {
  notifications: Notification[]
  unreadCount: number
  total: number
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
  markAsRead: (notificationIds: string[]) => Promise<void>
  markAllAsRead: () => Promise<void>
  dismiss: (notificationIds: string[]) => Promise<void>
  dismissAll: () => Promise<void>
}

const NotificationContext = createContext<NotificationContextValue | null>(null)

interface NotificationProviderProps {
  children: React.ReactNode
  pollIntervalMs?: number
}

export function NotificationProvider({
  children,
  pollIntervalMs = 30000, // Poll every 30 seconds
}: NotificationProviderProps) {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const userId = resolveDefaultUserId()

  const refresh = useCallback(async () => {
    if (!userId) {
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response: NotificationListResponse =
        await notificationsApi.getNotifications(userId, {
          pageSize: 50,
        })

      setNotifications(response.items)
      setUnreadCount(response.unreadCount)
      setTotal(response.total)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load notifications',
      )
    } finally {
      setLoading(false)
    }
  }, [userId])

  const markAsRead = useCallback(
    async (notificationIds: string[]) => {
      if (!userId) return

      try {
        await notificationsApi.markNotificationsRead(userId, {
          notificationIds,
        })

        // Update local state
        setNotifications((prev) =>
          prev.map((n) =>
            notificationIds.includes(n.id)
              ? { ...n, isRead: true, readAt: new Date().toISOString() }
              : n,
          ),
        )
        setUnreadCount((prev) => Math.max(0, prev - notificationIds.length))
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to mark notifications as read',
        )
      }
    },
    [userId],
  )

  const markAllAsRead = useCallback(async () => {
    if (!userId) return

    try {
      await notificationsApi.markNotificationsRead(userId, {
        markAll: true,
      })

      // Update local state
      setNotifications((prev) =>
        prev.map((n) => ({
          ...n,
          isRead: true,
          readAt: n.readAt || new Date().toISOString(),
        })),
      )
      setUnreadCount(0)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to mark all notifications as read',
      )
    }
  }, [userId])

  const dismiss = useCallback(
    async (notificationIds: string[]) => {
      if (!userId) return

      try {
        await notificationsApi.dismissNotifications(userId, {
          notificationIds,
        })

        // Remove from local state
        setNotifications((prev) =>
          prev.filter((n) => !notificationIds.includes(n.id)),
        )
        // Recalculate unread count
        setUnreadCount((prev) => {
          const dismissedUnread = notifications.filter(
            (n) => notificationIds.includes(n.id) && !n.isRead,
          ).length
          return Math.max(0, prev - dismissedUnread)
        })
        setTotal((prev) => Math.max(0, prev - notificationIds.length))
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to dismiss notifications',
        )
      }
    },
    [userId, notifications],
  )

  const dismissAll = useCallback(async () => {
    if (!userId) return

    try {
      await notificationsApi.dismissNotifications(userId, {
        dismissAll: true,
      })

      // Clear local state
      setNotifications([])
      setUnreadCount(0)
      setTotal(0)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to dismiss all notifications',
      )
    }
  }, [userId])

  // Initial load
  useEffect(() => {
    void refresh()
  }, [refresh])

  // Polling for updates
  useEffect(() => {
    if (!userId || pollIntervalMs <= 0) return

    const interval = setInterval(() => {
      void refresh()
    }, pollIntervalMs)

    return () => clearInterval(interval)
  }, [userId, pollIntervalMs, refresh])

  const value = useMemo(
    () => ({
      notifications,
      unreadCount,
      total,
      loading,
      error,
      refresh,
      markAsRead,
      markAllAsRead,
      dismiss,
      dismissAll,
    }),
    [
      notifications,
      unreadCount,
      total,
      loading,
      error,
      refresh,
      markAsRead,
      markAllAsRead,
      dismiss,
      dismissAll,
    ],
  )

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useNotifications(): NotificationContextValue {
  const context = useContext(NotificationContext)
  if (!context) {
    throw new Error(
      'useNotifications must be used within a NotificationProvider',
    )
  }
  return context
}
