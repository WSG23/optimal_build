import { Paper, useTheme, alpha, SxProps, Theme } from '@mui/material'
import type { ReactNode } from 'react'

export interface GlassCardProps {
  children: ReactNode
  className?: string
  elevation?: number
  blur?: number
  opacity?: number
  hoverEffect?: boolean
  sx?: SxProps<Theme>
  onClick?: () => void
}

export function GlassCard({
  children,
  className,
  elevation = 0,
  blur = 20,
  opacity = 0.85,
  hoverEffect = false,
  sx = {},
  onClick
}: GlassCardProps) {
  const theme = useTheme()

  return (
    <Paper
      className={className}
      elevation={elevation}
      onClick={onClick}
      sx={{
        background: alpha(theme.palette.background.paper, opacity),
        backdropFilter: `blur(${blur}px)`,
        border: `1px solid ${theme.palette.divider}`,
        borderRadius: 4, // var(--ob-radius-lg)
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        overflow: 'hidden',
        cursor: onClick ? 'pointer' : 'default',
        ...(hoverEffect && {
            '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: theme.shadows[4],
                borderColor: theme.palette.primary.main,
            }
        }),
        ...sx
      }}
    >
      {children}
    </Paper>
  )
}
