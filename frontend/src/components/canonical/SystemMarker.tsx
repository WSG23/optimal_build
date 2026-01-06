import {
  Typography,
  type TypographyProps,
  type SxProps,
  type Theme,
} from '@mui/material'
import type { ReactNode } from 'react'

export interface SystemMarkerProps extends Omit<TypographyProps, 'children'> {
  children: ReactNode
  active?: boolean
  sx?: SxProps<Theme>
}

export function SystemMarker({
  children,
  active = false,
  sx,
  ...typographyProps
}: SystemMarkerProps) {
  return (
    <Typography
      component="span"
      {...typographyProps}
      sx={{
        fontFamily: 'var(--ob-font-family-mono)',
        fontSize: 'var(--ob-font-size-xs)',
        fontWeight: 'var(--ob-font-weight-bold)',
        letterSpacing: 'var(--ob-letter-spacing-widest)',
        color: active ? 'var(--ob-color-neon-cyan)' : 'var(--ob-text-tertiary)',
        ...sx,
      }}
    >
      {children}
    </Typography>
  )
}
