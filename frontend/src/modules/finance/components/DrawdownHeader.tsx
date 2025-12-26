/**
 * DrawdownHeader - Page header with action buttons
 *
 * Contains:
 * - Title and subtitle
 * - "Export Report" (outlined) and "Save Scenario" (contained) buttons
 *
 * Follows UI_STANDARDS.md for design tokens.
 */

import { Box, Button, Typography } from '@mui/material'
import {
  FileDownload as FileDownloadIcon,
  Save as SaveIcon,
} from '@mui/icons-material'

import { useTranslation } from '../../../i18n'

interface DrawdownHeaderProps {
  title?: string
  subtitle?: string
  onExportReport?: () => void
  onSaveScenario?: () => void
}

export function DrawdownHeader({
  title,
  subtitle,
  onExportReport,
  onSaveScenario,
}: DrawdownHeaderProps) {
  const { t } = useTranslation()

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: { xs: 'column', md: 'row' },
        justifyContent: 'space-between',
        alignItems: { xs: 'flex-start', md: 'center' },
        gap: 'var(--ob-space-100)',
        mb: 'var(--ob-space-200)',
      }}
    >
      <Box>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 700,
            color: 'text.primary',
            fontSize: 'var(--ob-font-size-3xl)',
          }}
        >
          {title ?? t('finance.drawdown.title')}
        </Typography>
        <Typography
          sx={{
            color: 'text.secondary',
            mt: 'var(--ob-space-025)',
            fontSize: 'var(--ob-font-size-md)',
          }}
        >
          {subtitle ?? t('finance.drawdown.subtitle')}
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', gap: 'var(--ob-space-100)' }}>
        <Button
          variant="outlined"
          startIcon={<FileDownloadIcon />}
          onClick={onExportReport}
          sx={{
            borderRadius: 'var(--ob-radius-sm)',
            textTransform: 'none',
            fontWeight: 500,
            px: 'var(--ob-space-100)',
            py: 'var(--ob-space-050)',
          }}
        >
          {t('finance.actions.exportReport')}
        </Button>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={onSaveScenario}
          sx={{
            borderRadius: 'var(--ob-radius-sm)',
            textTransform: 'none',
            fontWeight: 500,
            px: 'var(--ob-space-100)',
            py: 'var(--ob-space-050)',
          }}
        >
          {t('finance.actions.saveScenario')}
        </Button>
      </Box>
    </Box>
  )
}

export default DrawdownHeader
