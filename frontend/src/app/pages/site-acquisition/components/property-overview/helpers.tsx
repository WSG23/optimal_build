/**
 * Property Overview - Shared Helper Components
 *
 * Reusable sub-components for card layouts:
 * - CardHeader: Icon + title row
 * - ItemLabel: 10px uppercase label
 * - ItemValue: Styled value with variants (default, large, accent)
 * - CardNote: Italic footer note
 */

import { Box, Typography, SvgIconProps } from '@mui/material'
import { ComponentType, ReactNode } from 'react'

/**
 * Shared card header with icon
 */
export function CardHeader({
  title,
  icon: Icon,
}: {
  title: string
  icon: ComponentType<SvgIconProps>
}) {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--ob-space-075)',
        mb: 'var(--ob-space-100)',
      }}
    >
      <Box
        sx={{
          p: 'var(--ob-space-050)',
          bgcolor: 'color-mix(in srgb, var(--ob-info-500) 10%, transparent)',
          borderRadius: 'var(--ob-radius-sm)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'info.main',
        }}
      >
        <Icon sx={{ fontSize: 'var(--ob-size-icon-sm)' }} />
      </Box>
      <Typography
        sx={{
          fontSize: 'var(--ob-font-size-base)',
          fontWeight: 'var(--ob-font-weight-bold)',
          color: 'text.primary',
          letterSpacing: '-0.01em',
        }}
      >
        {title}
      </Typography>
    </Box>
  )
}

/**
 * Shared label component (10px uppercase)
 */
export function ItemLabel({ children }: { children: ReactNode }) {
  return (
    <Typography
      sx={{
        fontSize: 'var(--ob-font-size-2xs)',
        fontWeight: 'var(--ob-font-weight-semibold)',
        letterSpacing: '0.05em',
        textTransform: 'uppercase',
        color: 'text.secondary',
      }}
    >
      {children}
    </Typography>
  )
}

/**
 * Shared value component
 */
export function ItemValue({
  children,
  variant = 'default',
}: {
  children: ReactNode
  variant?: 'default' | 'large' | 'accent'
}) {
  const styles = {
    default: {
      fontSize: 'var(--ob-font-size-sm)',
      fontWeight: 'var(--ob-font-weight-semibold)',
      color: 'text.primary',
    },
    large: {
      fontSize: 'var(--ob-font-size-lg)',
      fontWeight: 'var(--ob-font-weight-bold)',
      color: 'text.primary',
    },
    accent: {
      fontSize: 'var(--ob-font-size-sm)',
      fontWeight: 'var(--ob-font-weight-bold)',
      color: 'info.main',
    },
  }

  return <Typography sx={styles[variant]}>{children}</Typography>
}

/**
 * Shared note component (italic footer)
 */
export function CardNote({ children }: { children: ReactNode }) {
  return (
    <Box
      sx={{
        mt: 'var(--ob-space-075)',
        p: 'var(--ob-space-050)',
        bgcolor: 'var(--ob-surface-glass-subtle)',
        borderRadius: 'var(--ob-radius-xs)',
      }}
    >
      <Typography
        sx={{
          fontSize: 'var(--ob-font-size-xs)',
          color: 'text.secondary',
          fontStyle: 'italic',
          lineHeight: 1.4,
        }}
      >
        {children}
      </Typography>
    </Box>
  )
}
