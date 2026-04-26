import { useCallback, useEffect, useState } from 'react'
import { Box, Dialog, Stack, Typography } from '@mui/material'
import { Kbd } from './canonical/Kbd'

interface ShortcutEntry {
  keys: string[]
  description: string
}

const isMac =
  typeof navigator !== 'undefined' &&
  /Mac|iPhone|iPad/.test(navigator.userAgent)

const SHORTCUTS: ShortcutEntry[] = [
  {
    keys: [isMac ? '\u2318K' : 'Ctrl+K'],
    description: 'Search commands',
  },
  { keys: ['Esc'], description: 'Close dialog / palette' },
  { keys: ['\u2191\u2193'], description: 'Navigate results' },
  { keys: ['\u21B5'], description: 'Open selected' },
  { keys: ['Shift+?'], description: 'This help' },
]

export function ShortcutOverlay() {
  const [open, setOpen] = useState(false)

  const handleClose = useCallback(() => setOpen(false), [])

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === '?' && e.shiftKey && !e.metaKey && !e.ctrlKey) {
        // Don't trigger if user is typing in an input/textarea
        const tag = (e.target as HTMLElement)?.tagName
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return
        e.preventDefault()
        setOpen((prev) => !prev)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth={false}
      slotProps={{
        backdrop: {
          sx: {
            backgroundColor: 'rgba(0, 0, 0, 0.6)',
            backdropFilter: 'blur(2px)',
          },
        },
      }}
      PaperProps={{
        sx: {
          width: '100%',
          maxWidth: 420,
          borderRadius: 'var(--ob-radius-lg)',
          bgcolor: 'background.paper',
          border: '1px solid',
          borderColor: 'divider',
          overflow: 'hidden',
        },
      }}
    >
      <Box
        sx={{
          px: 'var(--ob-space-200)',
          py: 'var(--ob-space-150)',
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Typography
          variant="overline"
          sx={{
            fontSize: 'var(--ob-font-size-xs)',
            fontWeight: 'var(--ob-font-weight-bold)',
            letterSpacing: 'var(--ob-letter-spacing-wider)',
            color: 'text.primary',
          }}
        >
          Keyboard Shortcuts
        </Typography>
      </Box>

      <Stack sx={{ px: 'var(--ob-space-200)', py: 'var(--ob-space-150)' }}>
        {SHORTCUTS.map((shortcut) => (
          <Box
            key={shortcut.description}
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              py: 'var(--ob-space-075)',
              borderBottom: '1px solid',
              borderColor: 'divider',
              '&:last-child': { borderBottom: 'none' },
            }}
          >
            <Typography
              variant="body2"
              sx={{
                fontSize: 'var(--ob-font-size-sm)',
                color: 'text.secondary',
              }}
            >
              {shortcut.description}
            </Typography>
            <Stack direction="row" spacing="var(--ob-space-050)">
              {shortcut.keys.map((key) => (
                <Kbd key={key}>{key}</Kbd>
              ))}
            </Stack>
          </Box>
        ))}
      </Stack>

      <Box
        sx={{
          display: 'flex',
          justifyContent: 'flex-end',
          px: 'var(--ob-space-200)',
          py: 'var(--ob-space-075)',
          borderTop: '1px solid',
          borderColor: 'divider',
          fontSize: 'var(--ob-font-size-xs)',
          color: 'text.secondary',
        }}
      >
        <Box
          component="span"
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--ob-space-050)',
          }}
        >
          <Kbd>esc</Kbd> close
        </Box>
      </Box>
    </Dialog>
  )
}
