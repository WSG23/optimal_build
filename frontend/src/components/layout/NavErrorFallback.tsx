import { Box, Button, Typography } from '@mui/material'

/**
 * Compact inline fallback for ErrorBoundary wrapping nav-bar components.
 * Fits within the ~32px nav bar height.
 */
export function NavErrorFallback() {
  return (
    <Box
      role="alert"
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 'var(--ob-space-075)',
        px: 'var(--ob-space-100)',
        height: 'var(--ob-space-250)',
      }}
    >
      <Typography
        component="span"
        sx={{
          fontSize: 'var(--ob-font-size-xs)',
          color: 'text.disabled',
          whiteSpace: 'nowrap',
        }}
      >
        Failed to load
      </Typography>
      <Button
        variant="text"
        size="small"
        onClick={() => {
          window.location.reload()
        }}
        sx={{
          fontSize: 'var(--ob-font-size-xs)',
          minWidth: 0,
          px: 'var(--ob-space-075)',
          py: 'var(--ob-space-025)',
          borderRadius: 'var(--ob-radius-xs)',
          color: 'var(--ob-color-brand-primary)',
          textTransform: 'none',
          lineHeight: 'var(--ob-line-height-tight)',
        }}
      >
        Retry
      </Button>
    </Box>
  )
}
