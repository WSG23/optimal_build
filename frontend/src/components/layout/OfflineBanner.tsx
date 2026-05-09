import { useCallback, useEffect, useState } from 'react'
import { Box, Button, Typography, alpha, useTheme } from '@mui/material'

/**
 * Thin banner shown below the nav bar when the browser goes offline.
 * Slides in/out with a CSS transition and announces to screen readers.
 */
export function OfflineBanner() {
  const theme = useTheme()
  const [isOffline, setIsOffline] = useState(
    () => typeof navigator !== 'undefined' && !navigator.onLine,
  )
  const [isDismissed, setIsDismissed] = useState(false)

  useEffect(() => {
    const handleOffline = () => {
      setIsOffline(true)
      setIsDismissed(false)
    }
    const handleOnline = () => {
      setIsOffline(false)
    }

    window.addEventListener('offline', handleOffline)
    window.addEventListener('online', handleOnline)
    return () => {
      window.removeEventListener('offline', handleOffline)
      window.removeEventListener('online', handleOnline)
    }
  }, [])

  const handleDismiss = useCallback(() => {
    setIsDismissed(true)
  }, [])

  const visible = isOffline && !isDismissed

  return (
    <Box
      aria-live="polite"
      role="status"
      sx={{
        overflow: 'hidden',
        maxHeight: visible ? 'var(--ob-space-250)' : 0,
        opacity: visible ? 1 : 0,
        transition: 'max-height 250ms ease, opacity 200ms ease',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 'var(--ob-space-100)',
          px: 'var(--ob-space-150)',
          py: 'var(--ob-space-050)',
          bgcolor: 'var(--ob-color-warning-soft)',
          borderBottom: '1px solid var(--ob-color-warning-strong)',
        }}
      >
        <Typography
          component="span"
          sx={{
            fontSize: 'var(--ob-font-size-xs)',
            color: 'var(--ob-color-warning-strong)',
            fontWeight: 'var(--ob-font-weight-semibold)',
          }}
        >
          You're offline — some features may be unavailable
        </Typography>
        <Button
          variant="text"
          size="small"
          onClick={handleDismiss}
          aria-label="Dismiss offline notice"
          sx={{
            fontSize: 'var(--ob-font-size-xs)',
            minWidth: 0,
            px: 'var(--ob-space-075)',
            py: 0,
            borderRadius: 'var(--ob-radius-xs)',
            color: 'var(--ob-color-warning-strong)',
            textTransform: 'none',
            lineHeight: 'var(--ob-line-height-tight)',
            '&:hover': {
              bgcolor: alpha(theme.palette.action.hover, 0.5),
            },
          }}
        >
          Dismiss
        </Button>
      </Box>
    </Box>
  )
}
