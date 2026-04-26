import { type ReactNode } from 'react'
import { Box } from '@mui/material'

export interface KbdProps {
  children: ReactNode
}

/**
 * Keyboard shortcut badge — renders a styled `<kbd>` element
 * using design tokens for consistent shortcut hints across the UI.
 */
export function Kbd({ children }: KbdProps) {
  return (
    <Box
      component="kbd"
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        minWidth: 'var(--ob-space-200)',
        px: 'var(--ob-space-050)',
        py: 'var(--ob-space-025)',
        fontSize: 'var(--ob-font-size-xs)',
        fontFamily: 'var(--ob-font-family-mono)',
        borderRadius: 'var(--ob-radius-xs)',
        border: '1px solid',
        borderColor: 'divider',
        bgcolor: 'action.hover',
        lineHeight: 'var(--ob-line-height-snug)',
      }}
    >
      {children}
    </Box>
  )
}
