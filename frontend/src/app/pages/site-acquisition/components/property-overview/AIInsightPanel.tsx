/**
 * AIInsightPanel - Strategic Intelligence Component
 *
 * Implements UX Friction Solution #4: Dry Data vs Strategic Insights
 * - AI-generated strategic recommendations
 * - Indigo left border and "AI INSIGHT" label
 * - Concise 1-2 sentence insights
 *
 * @see frontend/UX_ARCHITECTURE.md - Problem 4: Dry Data vs Strategic Insights
 */

import { Box, Typography, SxProps, Theme } from '@mui/material'
import { ReactNode } from 'react'

export type InsightVariant = 'info' | 'success' | 'warning' | 'error'

export interface AIInsightPanelProps {
  /** Insight text or content */
  children: ReactNode
  /** Label text (defaults to "AI INSIGHT") */
  label?: string
  /** Variant determines color styling */
  variant?: InsightVariant
  /** Optional icon */
  icon?: ReactNode
  /** Compact mode */
  compact?: boolean
  /** Additional styles */
  sx?: SxProps<Theme>
}

const variantStyles = {
  info: {
    bgcolor: 'color-mix(in srgb, var(--ob-info-500) 8%, transparent)',
    borderColor: 'info.main',
    labelColor: 'info.main',
  },
  success: {
    bgcolor: 'color-mix(in srgb, var(--ob-success-500) 8%, transparent)',
    borderColor: 'success.main',
    labelColor: 'success.main',
  },
  warning: {
    bgcolor: 'color-mix(in srgb, var(--ob-warning-500) 8%, transparent)',
    borderColor: 'warning.main',
    labelColor: 'warning.main',
  },
  error: {
    bgcolor: 'color-mix(in srgb, var(--ob-error-500) 8%, transparent)',
    borderColor: 'error.main',
    labelColor: 'error.main',
  },
}

export function AIInsightPanel({
  children,
  label = 'AI INSIGHT',
  variant = 'info',
  icon,
  compact = false,
  sx = {},
}: AIInsightPanelProps) {
  const styles = variantStyles[variant]

  return (
    <Box
      sx={{
        p: compact ? 'var(--ob-space-075)' : 'var(--ob-space-100)',
        bgcolor: styles.bgcolor,
        borderLeft: '3px solid',
        borderColor: styles.borderColor,
        borderRadius: 'var(--ob-radius-xs)',
        ...sx,
      }}
    >
      {/* Label */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--ob-space-050)',
          mb: 'var(--ob-space-025)',
        }}
      >
        {icon && (
          <Box
            sx={{
              color: styles.labelColor,
              display: 'flex',
              fontSize: 'var(--ob-font-size-sm)',
            }}
          >
            {icon}
          </Box>
        )}
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-2xs)',
            fontWeight: 700,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            color: styles.labelColor,
          }}
        >
          {label}
        </Typography>
      </Box>

      {/* Content */}
      <Box
        sx={{
          fontSize: compact
            ? 'var(--ob-font-size-xs)'
            : 'var(--ob-font-size-sm)',
          color: 'var(--ob-text-secondary)',
          lineHeight: 1.5,
          '& p': {
            margin: 0,
          },
          '& p + p': {
            mt: 'var(--ob-space-050)',
          },
        }}
      >
        {typeof children === 'string' ? (
          <Typography
            sx={{
              fontSize: 'inherit',
              color: 'inherit',
              lineHeight: 'inherit',
            }}
          >
            {children}
          </Typography>
        ) : (
          children
        )}
      </Box>
    </Box>
  )
}

/**
 * Standalone insight card with glass surface
 */
export interface AIInsightCardProps extends AIInsightPanelProps {
  /** Card title */
  title?: string
}

export function AIInsightCard({
  title,
  children,
  label = 'AI INSIGHT',
  variant = 'info',
  icon,
  compact = false,
  sx = {},
}: AIInsightCardProps) {
  return (
    <Box
      sx={{
        bgcolor: 'var(--ob-surface-glass)',
        backdropFilter: 'blur(var(--ob-blur-md))',
        border: '1px solid var(--ob-color-border-subtle)',
        borderRadius: 'var(--ob-radius-sm)',
        p: 'var(--ob-space-150)',
        ...sx,
      }}
    >
      {title && (
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-base)',
            fontWeight: 600,
            color: 'var(--ob-color-text-primary)',
            mb: 'var(--ob-space-100)',
          }}
        >
          {title}
        </Typography>
      )}
      <AIInsightPanel
        label={label}
        variant={variant}
        icon={icon}
        compact={compact}
      >
        {children}
      </AIInsightPanel>
    </Box>
  )
}
