/**
 * CapitalStackFacilityTable - Enhanced tranche/facility detail table
 *
 * Matches Gemini design:
 * - GlassCard wrapper with header row
 * - "Tranche / Facility Detail" title + scenario name
 * - Type badges (Equity = green, Debt = blue) using StatusChip
 * - Styled table headers (uppercase, tracking-wider)
 * - Total row with gray background
 * - Right-alignment for numeric columns
 *
 * Follows UI_STANDARDS.md for design tokens.
 */

import { Box, Typography, useTheme, alpha } from '@mui/material'

import { GlassCard } from '../../../components/canonical/GlassCard'
import { StatusChip } from '../../../components/canonical/StatusChip'
import { useTranslation } from '../../../i18n'
import type { FinanceScenarioSummary } from '../../../api/finance'
import { formatCurrencyFull, formatPercent } from '../utils/chartTheme'

interface CapitalStackFacilityTableProps {
  scenario: FinanceScenarioSummary | null
}

type SliceMetadata = Record<string, unknown>

function toNumber(value: string | null | undefined): number | null {
  if (typeof value !== 'string') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function extractFacilityMetadata(metadata?: SliceMetadata): SliceMetadata {
  if (!metadata) {
    return {}
  }
  if (metadata.facility && typeof metadata.facility === 'object') {
    return metadata.facility as SliceMetadata
  }
  if (metadata.detail && typeof metadata.detail === 'object') {
    const detail = metadata.detail as SliceMetadata
    if (detail.facility && typeof detail.facility === 'object') {
      return detail.facility as SliceMetadata
    }
    return detail
  }
  return metadata
}

function normaliseNumber(value: unknown): number | null {
  if (value === null || value === undefined) {
    return null
  }
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

export function CapitalStackFacilityTable({
  scenario,
}: CapitalStackFacilityTableProps) {
  const { t, i18n } = useTranslation()
  const theme = useTheme()
  const locale = i18n.language
  const fallback = t('common.fallback.dash')

  if (!scenario?.capitalStack) {
    return null
  }

  const { capitalStack } = scenario
  const { slices } = capitalStack
  const currency = scenario.currency ?? 'SGD'

  const total = toNumber(capitalStack.total)

  const formatCurrency = (value: string | null | undefined): string => {
    const numeric = toNumber(value)
    if (numeric === null) return fallback
    return formatCurrencyFull(numeric, currency, locale)
  }

  const formatPercentValue = (value: string | null | undefined): string => {
    const numeric = toNumber(value)
    if (numeric === null) return fallback
    return formatPercent(numeric)
  }

  return (
    <GlassCard sx={{ overflow: 'hidden' }}>
      {/* Header */}
      <Box
        sx={{
          px: 'var(--ob-space-150)',
          py: 'var(--ob-space-125)',
          borderBottom: 'var(--ob-space-100)',
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
          {t('finance.capitalStack.tranches.title')}
        </Typography>
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-sm)',
            color: 'text.secondary',
          }}
        >
          {scenario.scenarioName} —{' '}
          {scenario.description || t('finance.capitalStack.baseCase')}
        </Typography>
      </Box>

      {/* Table */}
      <Box sx={{ overflowX: 'auto', maxWidth: '100%' }}>
        <Box
          component="table"
          sx={{
            width: '100%',
            borderCollapse: 'collapse',
            '& th': {
              px: 'var(--ob-space-150)',
              py: 'var(--ob-space-075)',
              fontSize: 'var(--ob-font-size-xs)',
              fontWeight: 600,
              color: 'text.secondary',
              textTransform: 'uppercase',
              letterSpacing: 'var(--ob-letter-spacing-wider)',
              borderBottom: 'var(--ob-space-100)',
              borderColor: 'divider',
              bgcolor: alpha(theme.palette.background.default, 0.5),
              textAlign: 'left',
            },
            '& td': {
              px: 'var(--ob-space-150)',
              py: 'var(--ob-space-100)',
              fontSize: 'var(--ob-font-size-sm)',
              borderBottom: 'var(--ob-space-100)',
              borderColor: alpha(theme.palette.divider, 0.5),
            },
            // Right-align numeric columns (Amount, Share, Rate, etc.)
            '& th:nth-of-type(n+3), & td:nth-of-type(n+3)': {
              textAlign: 'right',
            },
            '& th:nth-of-type(6), & td:nth-of-type(6)': {
              textAlign: 'center',
            },
            '& th:nth-of-type(n+7), & td:nth-of-type(n+7)': {
              textAlign: 'center',
            },
            '& tbody tr': {
              transition: 'background-color 0.15s ease',
              '&:hover': {
                bgcolor: alpha(theme.palette.action.hover, 0.5),
              },
            },
          }}
        >
          <thead>
            <tr>
              <th scope="col">
                {t('finance.capitalStack.tranches.headers.facility')}
              </th>
              <th scope="col">
                {t('finance.capitalStack.tranches.headers.type')}
              </th>
              <th scope="col">
                {t('finance.capitalStack.tranches.headers.amount')}
              </th>
              <th scope="col">
                {t('finance.capitalStack.tranches.headers.share')}
              </th>
              <th scope="col">
                {t('finance.capitalStack.tranches.headers.rate')}
              </th>
              <th scope="col">
                {t('finance.capitalStack.tranches.headers.periods')}
              </th>
              <th scope="col">
                {t('finance.capitalStack.tranches.headers.capitalised')}
              </th>
              <th scope="col">
                {t('finance.capitalStack.tranches.headers.upfront')}
              </th>
              <th scope="col">
                {t('finance.capitalStack.tranches.headers.exit')}
              </th>
              <th scope="col">
                {t('finance.capitalStack.tranches.headers.reserve')}
              </th>
              <th scope="col">
                {t('finance.capitalStack.tranches.headers.amort')}
              </th>
            </tr>
          </thead>
          <tbody>
            {slices.map((slice) => {
              const metadata = slice.metadata as SliceMetadata | undefined
              const facilityMeta = extractFacilityMetadata(metadata)

              const upfront =
                facilityMeta.upfront_fee_pct ??
                facilityMeta.upfrontFeePct ??
                null
              const exitFee =
                facilityMeta.exit_fee_pct ?? facilityMeta.exitFeePct ?? null
              const reserveMonths = normaliseNumber(
                facilityMeta.reserve_months ?? facilityMeta.reserveMonths,
              )
              const amortMonths = normaliseNumber(
                facilityMeta.amortisation_months ??
                  facilityMeta.amortisationMonths,
              )
              const periodsPerYear = normaliseNumber(
                facilityMeta.periods_per_year ?? facilityMeta.periodsPerYear,
              )
              const capitalisedInterest =
                typeof facilityMeta.capitalise_interest === 'boolean'
                  ? facilityMeta.capitalise_interest
                  : typeof facilityMeta.capitaliseInterest === 'boolean'
                    ? facilityMeta.capitaliseInterest
                    : null

              const isEquity =
                slice.category?.toLowerCase() === 'equity' ||
                slice.name.toLowerCase().includes('equity')

              return (
                <tr key={`${slice.name}-${slice.trancheOrder ?? 0}`}>
                  <td>
                    <Typography sx={{ fontWeight: 500, color: 'text.primary' }}>
                      {slice.name}
                    </Typography>
                  </td>
                  <td>
                    <StatusChip
                      status={isEquity ? 'success' : 'info'}
                      size="sm"
                    >
                      {t(`finance.capitalStack.categories.${slice.category}`, {
                        defaultValue: slice.category,
                      })}
                    </StatusChip>
                  </td>
                  <td>
                    <Typography
                      sx={{
                        fontFamily: 'var(--ob-font-family-mono)',
                        color: 'text.primary',
                      }}
                    >
                      {formatCurrency(slice.amount)}
                    </Typography>
                  </td>
                  <td>
                    <Typography sx={{ color: 'text.secondary' }}>
                      {formatPercentValue(slice.share)}
                    </Typography>
                  </td>
                  <td>
                    <Typography sx={{ color: 'text.secondary' }}>
                      {formatPercentValue(slice.rate)}
                    </Typography>
                  </td>
                  <td>
                    <Typography sx={{ color: 'text.disabled' }}>
                      {periodsPerYear ?? fallback}
                    </Typography>
                  </td>
                  <td>
                    <Typography sx={{ color: 'text.disabled' }}>
                      {capitalisedInterest === null
                        ? fallback
                        : capitalisedInterest
                          ? t(
                              'finance.capitalStack.tranches.values.capitalised.yes',
                            )
                          : t(
                              'finance.capitalStack.tranches.values.capitalised.no',
                            )}
                    </Typography>
                  </td>
                  <td>
                    <Typography sx={{ color: 'text.disabled' }}>
                      {upfront ? `${upfront}%` : fallback}
                    </Typography>
                  </td>
                  <td>
                    <Typography sx={{ color: 'text.disabled' }}>
                      {exitFee ? `${exitFee}%` : fallback}
                    </Typography>
                  </td>
                  <td>
                    <Typography sx={{ color: 'text.disabled' }}>
                      {reserveMonths ?? fallback}
                    </Typography>
                  </td>
                  <td>
                    <Typography sx={{ color: 'text.disabled' }}>
                      {amortMonths ?? fallback}
                    </Typography>
                  </td>
                </tr>
              )
            })}
            {/* Total Row */}
            <Box
              component="tr"
              sx={{
                bgcolor: alpha(theme.palette.background.default, 0.5),
              }}
            >
              <td>
                <Typography sx={{ fontWeight: 600, color: 'text.primary' }}>
                  {t('common.total')}
                </Typography>
              </td>
              <td></td>
              <td>
                <Typography
                  sx={{
                    fontWeight: 600,
                    fontFamily: 'var(--ob-font-family-mono)',
                    color: 'text.primary',
                  }}
                >
                  {total !== null
                    ? formatCurrencyFull(total, currency, locale)
                    : fallback}
                </Typography>
              </td>
              <td>
                <Typography sx={{ fontWeight: 600, color: 'text.primary' }}>
                  100.00%
                </Typography>
              </td>
              <td colSpan={6}></td>
            </Box>
          </tbody>
        </Box>
      </Box>
    </GlassCard>
  )
}

export default CapitalStackFacilityTable
