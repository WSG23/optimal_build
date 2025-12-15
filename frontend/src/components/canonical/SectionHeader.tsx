import { Box, Typography, SxProps, Theme } from '@mui/material'
import { ReactNode } from 'react'
import { Button } from './Button'

export interface SectionHeaderProps {
  title: string
  subtitle?: string
  action?: ReactNode
  actionLabel?: string
  onAction?: () => void
  /**
   * Size variant
   */
  size?: 'sm' | 'md'
  sx?: SxProps<Theme>
}

/**
 * SectionHeader - Square Cyber-Minimalism Section Divider
 *
 * Use at the top of a major section (e.g., inside a panel or page block).
 * Features fine line divider and consistent typography.
 */
export function SectionHeader({
  title,
  subtitle,
  action,
  actionLabel,
  onAction,
  size = 'md',
  sx = {},
}: SectionHeaderProps) {
  const titleSize =
    size === 'sm' ? 'var(--ob-font-size-base)' : 'var(--ob-font-size-lg)'

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        borderBottom: 'var(--ob-divider-strong)', // Fine line
        pb: 'var(--ob-space-075)',
        mb: 'var(--ob-space-100)',
        ...sx,
      }}
    >
      <Box>
        <Typography
          variant="h6"
          sx={{
            color: 'var(--ob-color-text-primary)',
            fontWeight: 'var(--ob-font-weight-semibold)',
            fontSize: titleSize,
            lineHeight: 1.2,
          }}
        >
          {title}
        </Typography>
        {subtitle && (
          <Typography
            variant="body2"
            sx={{
              color: 'var(--ob-color-text-secondary)',
              mt: 'var(--ob-space-025)',
              maxWidth: '60ch',
              fontSize: 'var(--ob-font-size-sm)',
            }}
          >
            {subtitle}
          </Typography>
        )}
      </Box>

      {/* Render explicit action node OR a standard button if label provided */}
      {action ? (
        <Box sx={{ ml: 'var(--ob-space-100)' }}>{action}</Box>
      ) : actionLabel && onAction ? (
        <Button variant="secondary" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      ) : null}
    </Box>
  )
}
