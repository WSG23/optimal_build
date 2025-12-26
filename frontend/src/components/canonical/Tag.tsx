import { Box, Typography, SxProps, Theme } from '@mui/material'
import { ReactNode } from 'react'

export interface TagProps {
  /**
   * Tag content (text or element)
   */
  children: ReactNode
  /**
   * Color variant
   */
  color?: 'default' | 'brand' | 'success' | 'warning' | 'error' | 'info'
  /**
   * Tag size
   */
  size?: 'sm' | 'md'
  /**
   * Leading icon
   */
  icon?: ReactNode
  /**
   * Removable - shows close button
   */
  onRemove?: () => void
  /**
   * Click handler - makes tag interactive
   */
  onClick?: () => void
  /**
   * Additional styles
   */
  sx?: SxProps<Theme>
}

const colorMap = {
  default: {
    bg: 'var(--ob-color-surface-strong)',
    text: 'var(--ob-color-text-secondary)',
    border: 'var(--ob-border-fine)',
  },
  brand: {
    bg: 'var(--ob-color-brand-soft)',
    text: 'var(--ob-color-brand-primary)',
    border: '1px solid rgba(59, 130, 246, 0.2)',
  },
  success: {
    bg: 'var(--ob-color-success-soft)',
    text: 'var(--ob-color-status-success-text)',
    border: '1px solid rgba(34, 197, 94, 0.2)',
  },
  warning: {
    bg: 'var(--ob-color-warning-soft)',
    text: 'var(--ob-color-status-warning-text)',
    border: '1px solid rgba(234, 179, 8, 0.2)',
  },
  error: {
    bg: 'var(--ob-color-error-soft)',
    text: 'var(--ob-color-status-error-text)',
    border: '1px solid rgba(239, 68, 68, 0.2)',
  },
  info: {
    bg: 'var(--ob-color-info-soft)',
    text: 'var(--ob-color-status-info-text)',
    border: '1px solid rgba(59, 130, 246, 0.2)',
  },
}

/**
 * Tag - Square Label/Badge Component
 *
 * Geometry: 2px border radius (--ob-radius-xs)
 * Height: 24px (default), 20px (sm)
 *
 * REPLACES pill-shaped badges/labels throughout the UI.
 * NOT for avatars - those keep circular shape.
 */
export function Tag({
  children,
  color = 'default',
  size = 'md',
  icon,
  onRemove,
  onClick,
  sx = {},
}: TagProps) {
  const colors = colorMap[color]
  const height = size === 'sm' ? '20px' : '24px'
  const fontSize =
    size === 'sm' ? 'var(--ob-font-size-xs)' : 'var(--ob-font-size-sm)'
  const px = size === 'sm' ? 'var(--ob-space-050)' : 'var(--ob-space-075)'

  return (
    <Box
      onClick={onClick}
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        height,
        px,
        gap: 'var(--ob-space-025)',
        borderRadius: 'var(--ob-radius-xs)', // 2px - ENFORCED
        background: colors.bg,
        border: colors.border,
        cursor: onClick || onRemove ? 'pointer' : 'default',
        transition: 'all 0.2s ease',
        '&:hover': onClick
          ? {
              filter: 'brightness(1.1)',
            }
          : {},
        ...sx,
      }}
    >
      {icon && (
        <Box
          sx={{
            display: 'flex',
            color: colors.text,
            '& svg': { fontSize: size === 'sm' ? 12 : 14 },
          }}
        >
          {icon}
        </Box>
      )}
      <Typography
        component="span"
        sx={{
          color: colors.text,
          fontSize,
          fontWeight: 'var(--ob-font-weight-medium)',
          lineHeight: 1,
          whiteSpace: 'nowrap',
        }}
      >
        {children}
      </Typography>
      {onRemove && (
        <Box
          component="button"
          onClick={(e) => {
            e.stopPropagation()
            onRemove()
          }}
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: size === 'sm' ? 14 : 16,
            height: size === 'sm' ? 14 : 16,
            ml: 'var(--ob-space-025)',
            p: 0,
            border: 'none',
            background: 'transparent',
            color: colors.text,
            cursor: 'pointer',
            borderRadius: 'var(--ob-radius-xs)',
            opacity: 0.7,
            transition: 'opacity 0.2s',
            '&:hover': {
              opacity: 1,
              background: 'rgba(255, 255, 255, 0.1)',
            },
            '&::before': {
              content: '"×"',
              fontSize: size === 'sm' ? 12 : 14,
              fontWeight: 'bold',
            },
          }}
        />
      )}
    </Box>
  )
}
