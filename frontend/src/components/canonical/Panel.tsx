import { Box, Typography, SxProps, Theme } from '@mui/material'
import { forwardRef, ReactNode } from 'react'
import { Card } from './Card'

export interface PanelProps {
  children: ReactNode
  /**
   * Panel title (optional)
   */
  title?: string
  /**
   * Panel subtitle (optional)
   */
  subtitle?: string
  /**
   * Action element for header (button, icon, etc.)
   */
  headerAction?: ReactNode
  /**
   * Visual variant - Panel is always elevated
   */
  variant?: 'default' | 'glass'
  /**
   * Padding inside the panel
   * - 'none': No padding (for custom layouts)
   * - 'compact': 16px (--ob-space-100)
   * - 'default': 24px (--ob-space-150)
   */
  padding?: 'none' | 'compact' | 'default'
  /**
   * Enable entrance animation
   */
  animated?: boolean
  /**
   * Additional styles
   */
  sx?: SxProps<Theme>
  className?: string
}

/**
 * Panel - Elevated Section Container
 *
 * Geometry: 4px border radius (--ob-radius-sm)
 * Border: 1px fine line strong
 * Elevation: Level 1 (elevated background)
 *
 * Use for distinct sections within a page.
 */
export const Panel = forwardRef<HTMLDivElement, PanelProps>(
  (
    {
      children,
      title,
      subtitle,
      headerAction,
      variant = 'default',
      padding = 'default',
      animated = false,
      sx = {},
      className,
    },
    ref,
  ) => {
    const paddingMap = {
      none: 0,
      compact: 'var(--ob-space-100)', // 16px
      default: 'var(--ob-space-150)', // 24px
    }

    const hasHeader = title || headerAction

    return (
      <Card
        ref={ref}
        variant={variant === 'glass' ? 'glass' : 'default'}
        hover="none"
        animated={animated}
        className={className}
        sx={{
          border: 'var(--ob-border-fine-strong)',
          background:
            variant === 'glass'
              ? 'var(--ob-surface-glass-2)'
              : 'var(--ob-color-bg-surface-elevated)',
          ...sx,
        }}
      >
        {/* Header */}
        {hasHeader && (
          <Box
            sx={{
              px: paddingMap[padding] || paddingMap.default,
              py: 'var(--ob-space-100)',
              borderBottom: 'var(--ob-divider)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              background: 'rgba(0, 0, 0, 0.1)',
            }}
          >
            <Box>
              {title && (
                <Typography
                  variant="h6"
                  sx={{
                    color: 'var(--ob-color-text-primary)',
                    fontWeight: 'var(--ob-font-weight-semibold)',
                    fontSize: 'var(--ob-font-size-lg)',
                    lineHeight: 1.2,
                  }}
                >
                  {title}
                </Typography>
              )}
              {subtitle && (
                <Typography
                  variant="body2"
                  sx={{
                    color: 'var(--ob-color-text-secondary)',
                    mt: 0.25,
                  }}
                >
                  {subtitle}
                </Typography>
              )}
            </Box>
            {headerAction && <Box sx={{ ml: 2 }}>{headerAction}</Box>}
          </Box>
        )}

        {/* Content */}
        <Box sx={{ p: paddingMap[padding] }}>{children}</Box>
      </Card>
    )
  },
)

Panel.displayName = 'Panel'
