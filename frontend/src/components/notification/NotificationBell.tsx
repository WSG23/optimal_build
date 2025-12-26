import { useState, useEffect, useCallback } from 'react'
import {
  IconButton,
  Badge,
  Popover,
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Button,
  CircularProgress,
  Tooltip,
  useTheme,
  alpha,
} from '@mui/material'
import {
  Notifications as NotificationsIcon,
  GroupAdd as TeamInviteIcon,
  PersonAdd as MemberJoinedIcon,
  Assignment as WorkflowIcon,
  CheckCircle as ApprovedIcon,
  Warning as UrgentIcon,
  Info as InfoIcon,
  Campaign as AnnouncementIcon,
  Gavel as RegulatoryIcon,
  MarkEmailRead as MarkReadIcon,
} from '@mui/icons-material'
import {
  notificationApi,
  Notification,
  NotificationType,
  NotificationPriority,
} from '../../api/notification'

const getNotificationIcon = (type: NotificationType) => {
  switch (type) {
    case 'team_invitation':
      return <TeamInviteIcon color="primary" />
    case 'team_member_joined':
      return <MemberJoinedIcon color="success" />
    case 'team_member_removed':
      return <MemberJoinedIcon color="error" />
    case 'workflow_created':
    case 'workflow_step_assigned':
    case 'workflow_step_completed':
    case 'workflow_completed':
      return <WorkflowIcon color="info" />
    case 'workflow_approval_needed':
      return <ApprovedIcon color="warning" />
    case 'workflow_rejected':
      return <WorkflowIcon color="error" />
    case 'project_update':
    case 'project_milestone':
      return <InfoIcon color="info" />
    case 'regulatory_status_change':
    case 'regulatory_rfi':
      return <RegulatoryIcon color="warning" />
    case 'system_announcement':
      return <AnnouncementIcon color="primary" />
    default:
      return <InfoIcon />
  }
}

const getPriorityColor = (priority: NotificationPriority): string => {
  switch (priority) {
    case 'urgent':
      return 'error.main'
    case 'high':
      return 'warning.main'
    case 'normal':
      return 'info.main'
    case 'low':
      return 'text.secondary'
    default:
      return 'text.primary'
  }
}

const formatTimeAgo = (dateString: string): string => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

export function NotificationBell() {
  const theme = useTheme()
  const [anchorEl, setAnchorEl] = useState<HTMLButtonElement | null>(null)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchNotifications = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await notificationApi.listNotifications({
        page: 1,
        page_size: 10,
      })
      const nextNotifications = Array.isArray(result.notifications)
        ? result.notifications
        : []
      setNotifications(nextNotifications)
      setUnreadCount(
        typeof result.unread_count === 'number' ? result.unread_count : 0,
      )
    } catch (err) {
      console.error('Failed to fetch notifications:', err)
      setError('Failed to load notifications')
    } finally {
      setLoading(false)
    }
  }, [])

  // Fetch on mount and poll every 30 seconds
  useEffect(() => {
    void fetchNotifications()
    const interval = setInterval(() => {
      void fetchNotifications()
    }, 30000)
    return () => clearInterval(interval)
  }, [fetchNotifications])

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget)
    void fetchNotifications()
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const handleMarkAsRead = async (notificationId: string) => {
    try {
      await notificationApi.markAsRead(notificationId)
      setNotifications((prev) =>
        prev.map((n) =>
          n.id === notificationId ? { ...n, is_read: true } : n,
        ),
      )
      setUnreadCount((prev) => Math.max(0, prev - 1))
    } catch (err) {
      console.error('Failed to mark notification as read:', err)
    }
  }

  const handleMarkAllAsRead = async () => {
    try {
      await notificationApi.markAllAsRead()
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
      setUnreadCount(0)
    } catch (err) {
      console.error('Failed to mark all as read:', err)
    }
  }

  const open = Boolean(anchorEl)
  const id = open ? 'notification-popover' : undefined

  const iconButtonStyle = {
    color: 'text.secondary',
    border: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
    borderRadius: '50%',
    width: '40px',
    height: '40px',
    background: alpha(theme.palette.background.paper, 0.05),
    backdropFilter: 'blur(4px)',
    '&:hover': {
      color: 'text.primary',
      background: alpha(theme.palette.text.primary, 0.05),
      borderColor: alpha(theme.palette.text.primary, 0.2),
    },
  }

  return (
    <>
      <Tooltip title="Notifications">
        <IconButton
          aria-describedby={id}
          onClick={handleClick}
          sx={iconButtonStyle}
        >
          <Badge
            badgeContent={unreadCount}
            color="error"
            max={99}
            sx={{
              '& .MuiBadge-badge': {
                fontSize: '0.7rem',
                height: '18px',
                minWidth: '18px',
              },
            }}
          >
            <NotificationsIcon fontSize="small" />
          </Badge>
        </IconButton>
      </Tooltip>

      <Popover
        id={id}
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        PaperProps={{
          elevation: 8,
          sx: {
            mt: 1,
            borderRadius: '12px',
            width: '380px',
            maxHeight: '500px',
            border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
            overflow: 'hidden',
          },
        }}
      >
        {/* Header */}
        <Box
          sx={{
            p: 2,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: `1px solid ${theme.palette.divider}`,
          }}
        >
          <Typography variant="h6" fontWeight={600}>
            Notifications
          </Typography>
          {unreadCount > 0 && (
            <Button
              size="small"
              startIcon={<MarkReadIcon />}
              onClick={handleMarkAllAsRead}
              sx={{ textTransform: 'none' }}
            >
              Mark all read
            </Button>
          )}
        </Box>

        {/* Content */}
        <Box sx={{ maxHeight: '400px', overflow: 'auto' }}>
          {loading && notifications.length === 0 ? (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <CircularProgress size={24} />
            </Box>
          ) : error ? (
            <Box sx={{ p: 3, textAlign: 'center' }}>
              <Typography color="error">{error}</Typography>
              <Button size="small" onClick={fetchNotifications} sx={{ mt: 1 }}>
                Retry
              </Button>
            </Box>
          ) : notifications.length === 0 ? (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <NotificationsIcon
                sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }}
              />
              <Typography color="text.secondary">
                No notifications yet
              </Typography>
            </Box>
          ) : (
            <List disablePadding>
              {notifications.map((notification, index) => (
                <Box key={notification.id}>
                  <ListItem
                    onClick={() =>
                      !notification.is_read && handleMarkAsRead(notification.id)
                    }
                    sx={{
                      cursor: notification.is_read ? 'default' : 'pointer',
                      bgcolor: notification.is_read
                        ? 'transparent'
                        : alpha(theme.palette.primary.main, 0.05),
                      '&:hover': {
                        bgcolor: alpha(theme.palette.action.hover, 0.1),
                      },
                      py: 1.5,
                      px: 2,
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 40 }}>
                      {notification.priority === 'urgent' ? (
                        <UrgentIcon color="error" />
                      ) : (
                        getNotificationIcon(notification.notification_type)
                      )}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 1,
                          }}
                        >
                          <Typography
                            variant="body2"
                            fontWeight={notification.is_read ? 400 : 600}
                            sx={{
                              color: notification.is_read
                                ? 'text.secondary'
                                : 'text.primary',
                            }}
                          >
                            {notification.title}
                          </Typography>
                          {notification.priority === 'urgent' && (
                            <Typography
                              variant="caption"
                              sx={{
                                color: 'error.main',
                                fontWeight: 600,
                                textTransform: 'uppercase',
                              }}
                            >
                              Urgent
                            </Typography>
                          )}
                        </Box>
                      }
                      secondary={
                        <>
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            component="span"
                            sx={{ display: 'block' }}
                          >
                            {notification.message}
                          </Typography>
                          <Typography
                            variant="caption"
                            sx={{
                              color: getPriorityColor(notification.priority),
                              mt: 0.5,
                              display: 'block',
                            }}
                          >
                            {formatTimeAgo(notification.created_at)}
                          </Typography>
                        </>
                      }
                    />
                    {!notification.is_read && (
                      <Box
                        sx={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          bgcolor: 'primary.main',
                          ml: 1,
                        }}
                      />
                    )}
                  </ListItem>
                  {index < notifications.length - 1 && (
                    <Divider component="li" />
                  )}
                </Box>
              ))}
            </List>
          )}
        </Box>

        {/* Footer */}
        {notifications.length > 0 && (
          <Box
            sx={{
              p: 1.5,
              borderTop: `1px solid ${theme.palette.divider}`,
              textAlign: 'center',
            }}
          >
            <Button size="small" sx={{ textTransform: 'none' }}>
              View all notifications
            </Button>
          </Box>
        )}
      </Popover>
    </>
  )
}
