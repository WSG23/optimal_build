import { Box, Typography, IconButton, SxProps, Theme } from '@mui/material'
import { Close, CheckCircle, Warning, Error, Info } from '@mui/icons-material'
import { ReactNode } from 'react'

export interface AlertBlockProps {
  /**
   * Alert type determines color and default icon
   */
  type: 'success' | 'warning' | 'error' | 'info'
  /**
   * Alert title
   */
  title?: string
  /**
   * Alert message content
   */
  children: ReactNode
  /**
   * Custom icon (overrides default)
   */
  icon?: ReactNode
  /**
   * Hide icon
   */
  hideIcon?: boolean
  /**
   * Dismissible - shows close button
   */
  onDismiss?: () => void
  /**
   * Action element (button, link)
   */
  action?: ReactNode
  /**
   * Variant
   * - 'filled': Solid background
   * - 'outlined': Border only
   */
  variant?: 'filled' | 'outlined'
  /**
   * Additional styles
   */
  sx?: SxProps<Theme>
}

const typeConfig = {
  success: {
    bg: 'var(--ob-color-success-soft)',
    border: 'var(--ob-success-500)',
    text: 'var(--ob-color-status-success-text)',
    icon: <CheckCircle />,
  },
  warning: {
    bg: 'var(--ob-color-warning-soft)',
    border: 'var(--ob-warning-500)',
    text: 'var(--ob-color-status-warning-text)',
    icon: <Warning />,
  },
  error: {
    bg: 'var(--ob-color-error-soft)',
    border: 'var(--ob-error-500)',
    text: 'var(--ob-color-status-error-text)',
    icon: <Error />,
  },
  info: {
    bg: 'var(--ob-color-info-soft)',
    border: 'var(--ob-info-500)',
    text: 'var(--ob-color-status-info-text)',
    icon: <Info />,
  },
}

/**
 * AlertBlock - Notification/Alert Container
 *
 * Geometry: 4px border radius (--ob-radius-sm)
 * Border: 1px colored based on type
 *
 * Used for inline alerts, notifications, and feedback messages.
 */
export function AlertBlock({
  type,
  title,
  children,
  icon,
  hideIcon = false,
  onDismiss,
  action,
  variant = 'filled',
  sx = {},
}: AlertBlockProps) {
  const config = typeConfig[type]

  return (
    <Box
      role="alert"
      sx={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 'var(--ob-space-075)',
        p: 'var(--ob-space-100)',
        borderRadius: 'var(--ob-radius-sm)', // 4px
        border: `1px solid ${config.border}`,
        background: variant === 'filled' ? config.bg : 'transparent',
        ...sx,
      }}
    >
      {/* Icon */}
      {!hideIcon && (
        <Box
          sx={{
            color: config.text,
            display: 'flex',
            flexShrink: 0,
            mt: '2px',
            '& svg': { fontSize: 20 },
          }}
        >
          {icon || config.icon}
        </Box>
      )}

      {/* Content */}
      <Box sx={{ flex: 1, minWidth: 0 }}>
        {title && (
          <Typography
            sx={{
              color: config.text,
              fontWeight: 'var(--ob-font-weight-semibold)',
              fontSize: 'var(--ob-font-size-sm)',
              mb: 'var(--ob-space-025)',
            }}
          >
            {title}
          </Typography>
        )}
        <Typography
          component="div"
          sx={{
            color: 'var(--ob-color-text-primary)',
            fontSize: 'var(--ob-font-size-sm)',
            lineHeight: 1.5,
            '& a': {
              color: config.text,
              textDecoration: 'underline',
            },
          }}
        >
          {children}
        </Typography>

        {/* Action */}
        {action && <Box sx={{ mt: 'var(--ob-space-075)' }}>{action}</Box>}
      </Box>

      {/* Dismiss button */}
      {onDismiss && (
        <IconButton
          size="small"
          onClick={onDismiss}
          sx={{
            color: 'var(--ob-color-text-secondary)',
            p: 'var(--ob-space-025)',
            borderRadius: 'var(--ob-radius-xs)', // 2px for buttons
            '&:hover': {
              color: 'var(--ob-color-text-primary)',
              background: 'var(--ob-color-action-hover)',
            },
          }}
        >
          <Close fontSize="small" />
        </IconButton>
      )}
    </Box>
  )
}
