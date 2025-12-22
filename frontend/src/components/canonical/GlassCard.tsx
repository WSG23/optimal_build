import {
  Paper,
  type PaperProps,
  useTheme,
  alpha,
  SxProps,
  Theme,
} from '@mui/material'
import type { ReactNode } from 'react'

export interface GlassCardProps extends Omit<PaperProps, 'children' | 'sx'> {
  children: ReactNode
  className?: string
  elevation?: number
  blur?: number
  opacity?: number
  hoverEffect?: boolean
  sx?: SxProps<Theme>
}

export function GlassCard({
  children,
  className,
  elevation = 0,
  blur = 20,
  opacity = 0.85,
  hoverEffect = false,
  sx = {},
  onClick,
  ...paperProps
}: GlassCardProps) {
  const theme = useTheme()

  const baseSx: SxProps<Theme> = {
    background: alpha(theme.palette.background.paper, opacity),
    backdropFilter: `blur(${blur}px)`,
    border: `1px solid ${theme.palette.divider}`,
    borderRadius: 'var(--ob-radius-sm)', // 4px - cards, panels, tiles
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    overflow: 'hidden',
    cursor: onClick ? 'pointer' : 'default',
    ...(hoverEffect && {
      '&:hover': {
        transform: 'translateY(-4px)',
        boxShadow: theme.shadows[4],
        borderColor: theme.palette.primary.main,
      },
    }),
  }

  const resolvedSx = Array.isArray(sx) ? sx : [sx]

  return (
    <Paper
      className={className}
      elevation={elevation}
      onClick={onClick}
      {...paperProps}
      sx={[baseSx, ...resolvedSx]}
    >
      {children}
    </Paper>
  )
}
