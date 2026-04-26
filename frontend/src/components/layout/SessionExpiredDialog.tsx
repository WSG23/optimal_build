import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from '@mui/material'

interface SessionExpiredDialogProps {
  open: boolean
  onDismiss: () => void
}

/**
 * Modal dialog shown when a 401 response is detected,
 * indicating the user's session has expired.
 */
export function SessionExpiredDialog({
  open,
  onDismiss,
}: SessionExpiredDialogProps) {
  const handleSignIn = () => {
    window.location.href = '/login'
  }

  return (
    <Dialog
      open={open}
      onClose={onDismiss}
      aria-labelledby="session-expired-title"
      PaperProps={{
        sx: {
          borderRadius: 'var(--ob-radius-lg)',
          bgcolor: 'background.paper',
          border: 'var(--ob-border-fine)',
          minWidth: 'var(--ob-space-400)',
          maxWidth: 360,
        },
      }}
    >
      <DialogTitle
        id="session-expired-title"
        sx={{
          fontSize: 'var(--ob-font-size-md)',
          fontWeight: 'var(--ob-font-weight-bold)',
          pb: 'var(--ob-space-050)',
        }}
      >
        Session expired
      </DialogTitle>
      <DialogContent>
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-sm)',
            color: 'text.secondary',
          }}
        >
          Your session has expired. Sign in again to continue.
        </Typography>
      </DialogContent>
      <DialogActions
        sx={{
          px: 'var(--ob-space-150)',
          pb: 'var(--ob-space-150)',
          gap: 'var(--ob-space-075)',
        }}
      >
        <Button
          variant="text"
          onClick={onDismiss}
          sx={{
            fontSize: 'var(--ob-font-size-sm)',
            borderRadius: 'var(--ob-radius-xs)',
            textTransform: 'none',
            color: 'text.secondary',
          }}
        >
          Dismiss
        </Button>
        <Button
          variant="contained"
          onClick={handleSignIn}
          sx={{
            fontSize: 'var(--ob-font-size-sm)',
            borderRadius: 'var(--ob-radius-xs)',
            textTransform: 'none',
            bgcolor: 'var(--ob-color-brand-primary)',
            '&:hover': {
              bgcolor: 'var(--ob-color-brand-primary)',
              opacity: 0.9,
            },
          }}
        >
          Sign in
        </Button>
      </DialogActions>
    </Dialog>
  )
}
