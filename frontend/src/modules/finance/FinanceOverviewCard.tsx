import { useCallback, useState } from 'react'

import { Box, IconButton, Stack, Typography } from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'

import { Card } from '../../components/canonical/Card'

const DISMISS_KEY = 'ob-finance-overview-dismissed'

export function FinanceOverviewCard() {
  const [dismissed, setDismissed] = useState(() => {
    try {
      return sessionStorage.getItem(DISMISS_KEY) === '1'
    } catch {
      return false
    }
  })

  const handleDismiss = useCallback(() => {
    setDismissed(true)
    try {
      sessionStorage.setItem(DISMISS_KEY, '1')
    } catch {
      // storage unavailable
    }
  }, [])

  if (dismissed) {
    return null
  }

  return (
    <Card
      variant="default"
      sx={{
        mb: 'var(--ob-space-150)',
        p: 'var(--ob-space-150)',
      }}
    >
      <Stack
        direction="row"
        spacing="var(--ob-space-100)"
        justifyContent="space-between"
        alignItems="flex-start"
      >
        <Box>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ fontSize: 'var(--ob-font-size-sm)' }}
          >
            Build a scenario from a deal screen, import a workbook, or start
            from an SG template. Export outputs are available in the header bar.
          </Typography>
        </Box>
        <IconButton
          size="small"
          onClick={handleDismiss}
          aria-label="Dismiss guide"
          sx={{ flexShrink: 0, color: 'text.secondary' }}
        >
          <CloseIcon fontSize="small" />
        </IconButton>
      </Stack>
    </Card>
  )
}
