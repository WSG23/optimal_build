/**
 * DrawdownDetailsPanel - Enhanced table panel for drawdown schedule
 *
 * Features:
 * - Header with title + period count badge
 * - Row numbers in gray circles
 * - Styled table with hover states
 * - Total row with bold values
 * - "View Full Forecast →" link at bottom
 *
 * Follows UI_STANDARDS.md for design tokens.
 */

import { Box, Button, Typography, useTheme, alpha } from '@mui/material'
import { ArrowForward as ArrowForwardIcon } from '@mui/icons-material'

import { GlassCard } from '../../../components/canonical/GlassCard'
import { StatusChip } from '../../../components/canonical/StatusChip'
import { useTranslation } from '../../../i18n'
import type { FinanceScenarioSummary } from '../../../api/finance'
import { formatCurrencyFull } from '../utils/chartTheme'

interface DrawdownDetailsPanelProps {
  scenario: FinanceScenarioSummary | null
  onViewFullForecast?: () => void
}

function toNumber(value: string | null | undefined): number | null {
  if (typeof value !== 'string') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

export function DrawdownDetailsPanel({
  scenario,
  onViewFullForecast,
}: DrawdownDetailsPanelProps) {
  const { t, i18n } = useTranslation()
  const theme = useTheme()
  const locale = i18n.language
  const fallback = t('common.fallback.dash')

  if (!scenario?.drawdownSchedule) {
    return null
  }

  const { drawdownSchedule } = scenario
  const currency = scenario.currency ?? 'SGD'
  const entries = drawdownSchedule.entries ?? []

  const totalEquity = toNumber(drawdownSchedule.totalEquity)
  const totalDebt = toNumber(drawdownSchedule.totalDebt)

  const formatCurrency = (value: string | null | undefined): string => {
    const numeric = toNumber(value)
    if (numeric === null) return fallback
    return formatCurrencyFull(numeric, currency, locale)
  }

  return (
    <GlassCard
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <Box
        sx={{
          px: 'var(--ob-space-150)',
          py: 'var(--ob-space-125)',
          borderBottom: 1,
          borderColor: 'divider',
          bgcolor: alpha(theme.palette.background.default, 0.5),
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Typography
          variant="h6"
          sx={{
            fontWeight: 600,
            fontSize: 'var(--ob-font-size-lg)',
            color: 'text.primary',
          }}
        >
          {t('finance.drawdown.details.title')}
        </Typography>
        <StatusChip status="info" size="sm">
          {entries.length} {t('finance.drawdown.details.periods')}
        </StatusChip>
      </Box>

      {/* Table */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        <Box
          component="table"
          sx={{
            width: '100%',
            borderCollapse: 'collapse',
            '& th, & td': {
              px: 'var(--ob-space-150)',
              py: 'var(--ob-space-100)',
              textAlign: 'right',
              fontSize: 'var(--ob-font-size-sm)',
            },
            '& th': {
              fontWeight: 600,
              color: 'text.secondary',
              textTransform: 'uppercase',
              fontSize: 'var(--ob-font-size-xs)',
              bgcolor: alpha(theme.palette.background.default, 0.5),
              borderBottom: 1,
              borderColor: 'divider',
            },
            '& th:first-of-type, & td:first-of-type': {
              textAlign: 'left',
            },
            '& tbody tr': {
              transition: 'background-color 0.15s ease',
              '&:hover': {
                bgcolor: alpha(theme.palette.action.hover, 0.5),
              },
            },
            '& tbody tr:not(:last-child)': {
              borderBottom: 1,
              borderColor: alpha(theme.palette.divider, 0.5),
            },
          }}
        >
          <thead>
            <tr>
              <th scope="col">{t('finance.drawdown.headers.period')}</th>
              <th scope="col">{t('finance.drawdown.headers.equity')}</th>
              <th scope="col">{t('finance.drawdown.headers.debt')}</th>
              <th scope="col">{t('finance.drawdown.headers.outstanding')}</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry, index) => (
              <tr key={entry.period}>
                <td>
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 'var(--ob-space-050)',
                    }}
                  >
                    <Box
                      sx={{
                        width: 24,
                        height: 24,
                        borderRadius: 'var(--ob-radius-xs)',
                        bgcolor: 'action.hover',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 'var(--ob-font-size-xs)',
                        color: 'text.secondary',
                        fontWeight: 500,
                      }}
                    >
                      {index + 1}
                    </Box>
                    <Typography
                      component="span"
                      sx={{
                        fontWeight: 500,
                        color: 'text.primary',
                      }}
                    >
                      {entry.period}
                    </Typography>
                  </Box>
                </td>
                <td>
                  <Typography
                    component="span"
                    sx={{
                      fontFamily: 'var(--ob-font-family-mono)',
                      color: 'text.secondary',
                    }}
                  >
                    {formatCurrency(entry.equityDraw)}
                  </Typography>
                </td>
                <td>
                  <Typography
                    component="span"
                    sx={{
                      fontFamily: 'var(--ob-font-family-mono)',
                      color: 'text.secondary',
                    }}
                  >
                    {formatCurrency(entry.debtDraw)}
                  </Typography>
                </td>
                <td>
                  <Typography
                    component="span"
                    sx={{
                      fontFamily: 'var(--ob-font-family-mono)',
                      fontWeight: 500,
                      color: 'text.primary',
                      bgcolor: alpha(theme.palette.background.default, 0.3),
                      px: 'var(--ob-space-050)',
                      py: 'var(--ob-space-025)',
                      borderRadius: 'var(--ob-radius-xs)',
                    }}
                  >
                    {formatCurrency(entry.outstandingDebt)}
                  </Typography>
                </td>
              </tr>
            ))}
            {/* Total Row */}
            <Box
              component="tr"
              sx={{
                borderTop: 1,
                borderColor: 'divider',
                bgcolor: alpha(theme.palette.background.default, 0.5),
              }}
            >
              <td>
                <Typography
                  component="span"
                  sx={{ fontWeight: 600, color: 'text.primary' }}
                >
                  {t('common.total')}
                </Typography>
              </td>
              <td>
                <Typography
                  component="span"
                  sx={{
                    fontFamily: 'var(--ob-font-family-mono)',
                    fontWeight: 600,
                    color: 'text.primary',
                  }}
                >
                  {totalEquity !== null
                    ? formatCurrencyFull(totalEquity, currency, locale)
                    : fallback}
                </Typography>
              </td>
              <td>
                <Typography
                  component="span"
                  sx={{
                    fontFamily: 'var(--ob-font-family-mono)',
                    fontWeight: 600,
                    color: 'text.primary',
                  }}
                >
                  {totalDebt !== null
                    ? formatCurrencyFull(totalDebt, currency, locale)
                    : fallback}
                </Typography>
              </td>
              <td>
                <Typography
                  component="span"
                  sx={{
                    fontFamily: 'var(--ob-font-family-mono)',
                    color: 'text.disabled',
                    fontStyle: 'italic',
                  }}
                >
                  —
                </Typography>
              </td>
            </Box>
          </tbody>
        </Box>
      </Box>

      {/* Footer with View Full Forecast link */}
      <Box
        sx={{
          p: 'var(--ob-space-100)',
          borderTop: 1,
          borderColor: 'divider',
          bgcolor: alpha(theme.palette.background.default, 0.5),
          display: 'flex',
          justifyContent: 'flex-end',
        }}
      >
        <Button
          endIcon={<ArrowForwardIcon />}
          onClick={onViewFullForecast}
          sx={{
            color: 'primary.main',
            fontSize: 'var(--ob-font-size-sm)',
            fontWeight: 500,
            textTransform: 'none',
            '&:hover': {
              bgcolor: alpha(theme.palette.primary.main, 0.08),
            },
          }}
        >
          {t('finance.drawdown.details.viewFull')}
        </Button>
      </Box>
    </GlassCard>
  )
}

export default DrawdownDetailsPanel
