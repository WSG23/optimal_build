/**
 * Notification bell component with dropdown menu.
 */

import React, { useState } from 'react'
import {
  Badge,
  Box,
  Button,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Menu,
  Typography,
} from '@mui/material'
import NotificationsIcon from '@mui/icons-material/Notifications'
import CheckIcon from '@mui/icons-material/Check'
import CloseIcon from '@mui/icons-material/Close'
import PeopleIcon from '@mui/icons-material/People'
import TaskAltIcon from '@mui/icons-material/TaskAlt'
import AssignmentIcon from '@mui/icons-material/Assignment'
import InfoIcon from '@mui/icons-material/Info'
import { useNotifications } from '../../contexts/NotificationContext'
import { Notification, NotificationType } from '../../api/notifications'

function getNotificationIcon(type: NotificationType): React.ReactNode {
  switch (type) {
    case 'team_invite':
    case 'team_invite_accepted':
    case 'team_member_joined':
    case 'team_member_left':
      return <PeopleIcon fontSize="small" color="primary" />
    case 'workflow_created':
    case 'workflow_approval_pending':
    case 'workflow_approved':
    case 'workflow_rejected':
    case 'workflow_step_completed':
      return <TaskAltIcon fontSize="small" color="success" />
    case 'submission_status_changed':
    case 'submission_approved':
    case 'submission_rejected':
    case 'submission_rfi':
      return <AssignmentIcon fontSize="small" color="warning" />
    default:
      return <InfoIcon fontSize="small" color="action" />
  }
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

interface NotificationItemProps {
  notification: Notification
  onMarkRead: (id: string) => void
  onDismiss: (id: string) => void
  onClick: (notification: Notification) => void
}

function NotificationItem({
  notification,
  onMarkRead,
  onDismiss,
  onClick,
}: NotificationItemProps) {
  return (
    <ListItem
      disablePadding
      sx={{
        bgcolor: notification.isRead ? 'transparent' : 'action.hover',
      }}
      secondaryAction={
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          {!notification.isRead && (
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation()
                onMarkRead(notification.id)
              }}
              title="Mark as read"
            >
              <CheckIcon fontSize="small" />
            </IconButton>
          )}
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation()
              onDismiss(notification.id)
            }}
            title="Dismiss"
          >
            <CloseIcon fontSize="small" />
          </IconButton>
        </Box>
      }
    >
      <ListItemButton onClick={() => onClick(notification)}>
        <Box sx={{ mr: 1.5, display: 'flex', alignItems: 'center' }}>
          {getNotificationIcon(notification.notificationType)}
        </Box>
        <ListItemText
          primary={
            <Typography
              variant="body2"
              fontWeight={notification.isRead ? 'normal' : 'medium'}
              sx={{ pr: 6 }}
            >
              {notification.title}
            </Typography>
          }
          secondary={
            <Box component="span">
              <Typography
                variant="caption"
                color="text.secondary"
                component="span"
                sx={{
                  display: 'block',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  pr: 6,
                }}
              >
                {notification.message}
              </Typography>
              <Typography
                variant="caption"
                color="text.disabled"
                component="span"
              >
                {formatTimeAgo(notification.createdAt)}
              </Typography>
            </Box>
          }
        />
      </ListItemButton>
    </ListItem>
  )
}

export function NotificationBell() {
  const {
    notifications,
    unreadCount,
    loading,
    markAsRead,
    markAllAsRead,
    dismiss,
    dismissAll,
  } = useNotifications()

  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null)
  const open = Boolean(anchorEl)

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const handleNotificationClick = (notification: Notification) => {
    // Mark as read
    if (!notification.isRead) {
      void markAsRead([notification.id])
    }

    // Navigate if there's an action URL
    if (notification.actionUrl) {
      window.location.href = notification.actionUrl
    }

    handleClose()
  }

  const handleMarkRead = (id: string) => {
    void markAsRead([id])
  }

  const handleDismiss = (id: string) => {
    void dismiss([id])
  }

  const handleMarkAllRead = () => {
    void markAllAsRead()
  }

  const handleDismissAll = () => {
    void dismissAll()
    handleClose()
  }

  return (
    <>
      <IconButton
        color="inherit"
        onClick={handleClick}
        aria-label={`${unreadCount} unread notifications`}
        aria-controls={open ? 'notification-menu' : undefined}
        aria-haspopup="true"
        aria-expanded={open ? 'true' : undefined}
      >
        <Badge badgeContent={unreadCount} color="error" max={99}>
          <NotificationsIcon />
        </Badge>
      </IconButton>

      <Menu
        id="notification-menu"
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        PaperProps={{
          sx: {
            width: 380,
            maxHeight: 480,
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            px: 2,
            py: 1,
          }}
        >
          <Typography variant="subtitle1" fontWeight="bold">
            Notifications
          </Typography>
          {unreadCount > 0 && (
            <Button size="small" onClick={handleMarkAllRead}>
              Mark all read
            </Button>
          )}
        </Box>

        <Divider />

        {loading && notifications.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography color="text.secondary">Loading...</Typography>
          </Box>
        ) : notifications.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <NotificationsIcon
              sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }}
            />
            <Typography color="text.secondary">No notifications</Typography>
          </Box>
        ) : (
          <>
            <List
              dense
              disablePadding
              sx={{ maxHeight: 320, overflow: 'auto' }}
            >
              {notifications.map((notification) => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  onMarkRead={handleMarkRead}
                  onDismiss={handleDismiss}
                  onClick={handleNotificationClick}
                />
              ))}
            </List>

            <Divider />

            <Box sx={{ p: 1, display: 'flex', justifyContent: 'center' }}>
              <Button size="small" color="inherit" onClick={handleDismissAll}>
                Clear all
              </Button>
            </Box>
          </>
        )}
      </Menu>
    </>
  )
}
