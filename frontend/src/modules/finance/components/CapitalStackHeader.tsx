/**
 * CapitalStackHeader - Page header with title and subtitle
 *
 * Matches Gemini design:
 * - "Capital Stack Overview" title
 * - Descriptive subtitle
 *
 * Follows UI_STANDARDS.md for design tokens.
 */

import { Box, Typography } from '@mui/material'

import { useTranslation } from '../../../i18n'

interface CapitalStackHeaderProps {
  title?: string
  subtitle?: string
}

export function CapitalStackHeader({
  title,
  subtitle,
}: CapitalStackHeaderProps) {
  const { t } = useTranslation()

  return (
    <Box sx={{ mb: 'var(--ob-space-200)' }}>
      <Typography
        variant="h4"
        sx={{
          fontWeight: 700,
          color: 'text.primary',
          fontSize: 'var(--ob-font-size-3xl)',
          letterSpacing: '-0.02em',
        }}
      >
        {title ?? t('finance.capitalStack.overview.title')}
      </Typography>
      <Typography
        sx={{
          mt: 'var(--ob-space-050)',
          color: 'text.secondary',
          fontSize: 'var(--ob-font-size-lg)',
        }}
      >
        {subtitle ?? t('finance.capitalStack.overview.subtitle')}
      </Typography>
    </Box>
  )
}

export default CapitalStackHeader
