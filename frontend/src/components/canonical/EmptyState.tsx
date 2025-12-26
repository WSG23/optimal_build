import { Box, Typography, SxProps, Theme } from '@mui/material'
import { ReactNode } from 'react'
import { Button } from './Button'

export interface EmptyStateProps {
  /**
   * Icon to display
   */
  icon?: ReactNode
  /**
   * Main title
   */
  title: string
  /**
   * Description text
   */
  description?: string
  /**
   * Primary action button label
   */
  actionLabel?: string
  /**
   * Primary action handler
   */
  onAction?: () => void
  /**
   * Secondary action button label
   */
  secondaryActionLabel?: string
  /**
   * Secondary action handler
   */
  onSecondaryAction?: () => void
  /**
   * Size variant
   */
  size?: 'sm' | 'md' | 'lg'
  /**
   * Additional styles
   */
  sx?: SxProps<Theme>
}

/**
 * EmptyState - Empty State Panel
 *
 * Geometry: 4px border radius (--ob-radius-sm)
 * Border: 1px dashed fine line
 *
 * Used when there's no content to display.
 */
export function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  onAction,
  secondaryActionLabel,
  onSecondaryAction,
  size = 'md',
  sx = {},
}: EmptyStateProps) {
  const sizeMap = {
    sm: {
      padding: 'var(--ob-space-150)',
      iconSize: 32,
      titleSize: 'var(--ob-font-size-base)',
      descSize: 'var(--ob-font-size-sm)',
    },
    md: {
      padding: 'var(--ob-space-200)',
      iconSize: 48,
      titleSize: 'var(--ob-font-size-lg)',
      descSize: 'var(--ob-font-size-sm)',
    },
    lg: {
      padding: 'var(--ob-space-300)',
      iconSize: 64,
      titleSize: 'var(--ob-font-size-xl)',
      descSize: 'var(--ob-font-size-base)',
    },
  }

  const config = sizeMap[size]

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        p: config.padding,
        borderRadius: 'var(--ob-radius-sm)', // 4px
        border: '1px dashed rgba(255, 255, 255, 0.12)',
        background: 'var(--ob-color-surface-strong)',
        ...sx,
      }}
    >
      {icon && (
        <Box
          sx={{
            color: 'var(--ob-color-text-muted)',
            mb: 'var(--ob-space-100)',
            '& svg': {
              fontSize: config.iconSize,
            },
          }}
        >
          {icon}
        </Box>
      )}

      <Typography
        sx={{
          color: 'var(--ob-color-text-primary)',
          fontWeight: 'var(--ob-font-weight-semibold)',
          fontSize: config.titleSize,
          mb: description ? 'var(--ob-space-050)' : 0,
        }}
      >
        {title}
      </Typography>

      {description && (
        <Typography
          sx={{
            color: 'var(--ob-color-text-secondary)',
            fontSize: config.descSize,
            maxWidth: '40ch',
            mb: actionLabel || secondaryActionLabel ? 'var(--ob-space-150)' : 0,
          }}
        >
          {description}
        </Typography>
      )}

      {(actionLabel || secondaryActionLabel) && (
        <Box
          sx={{
            display: 'flex',
            gap: 'var(--ob-space-075)',
            flexWrap: 'wrap',
            justifyContent: 'center',
          }}
        >
          {actionLabel && onAction && (
            <Button variant="primary" size="sm" onClick={onAction}>
              {actionLabel}
            </Button>
          )}
          {secondaryActionLabel && onSecondaryAction && (
            <Button variant="secondary" size="sm" onClick={onSecondaryAction}>
              {secondaryActionLabel}
            </Button>
          )}
        </Box>
      )}
    </Box>
  )
}
