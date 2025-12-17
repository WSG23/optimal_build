/**
 * CapitalStackChart - Recharts stacked bar chart for capital stack comparison
 *
 * Follows UI_STANDARDS.md:
 * - Uses Recharts with ResponsiveContainer
 * - Colors from theme palette (dark mode compatible)
 * - Bar radius matches --ob-radius-sm
 * - Axis lines disabled
 * - Height constrained to --ob-max-height-panel
 */

import { useMemo } from 'react'

import { Box, Typography, alpha, useTheme } from '@mui/material'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  TooltipProps,
} from 'recharts'

import { useTranslation } from '../../../i18n'
import type { FinanceScenarioSummary } from '../../../api/finance'
import {
  getChartColors,
  getAxisProps,
  getGridProps,
  getTooltipStyle,
  getBarRadius,
  chartSizes,
  formatCurrencyShort,
  formatCurrencyFull,
} from '../utils/chartTheme'

interface CapitalStackChartProps {
  scenarios: FinanceScenarioSummary[]
}

interface ChartDataPoint {
  name: string
  equity: number
  seniorDebt: number
  mezzanine: number
  bridge: number
  other: number
  total: number
}

function toNumber(value: string | null | undefined): number {
  if (typeof value !== 'string') return 0
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

export function CapitalStackChart({ scenarios }: CapitalStackChartProps) {
  const { t } = useTranslation()
  const theme = useTheme()
  const colors = getChartColors(theme)
  const axisProps = getAxisProps(theme)
  const gridProps = getGridProps(theme)
  const tooltipStyle = getTooltipStyle(theme)

  const data = useMemo<ChartDataPoint[]>(() => {
    return scenarios
      .filter((s) => s.capitalStack)
      .map((scenario) => {
        const stack = scenario.capitalStack!
        let equity = 0
        let seniorDebt = 0
        let mezzanine = 0
        let bridge = 0
        let other = 0

        for (const slice of stack.slices) {
          const amount = toNumber(slice.amount)
          const name = slice.name.toLowerCase()
          const category = slice.category?.toLowerCase() ?? ''

          if (category === 'equity' || name.includes('equity')) {
            equity += amount
          } else if (name.includes('senior')) {
            seniorDebt += amount
          } else if (name.includes('mezzanine') || name.includes('mezz')) {
            mezzanine += amount
          } else if (name.includes('bridge')) {
            bridge += amount
          } else {
            other += amount
          }
        }

        return {
          name: scenario.scenarioName,
          equity,
          seniorDebt,
          mezzanine,
          bridge,
          other,
          total: toNumber(stack.total),
        }
      })
  }, [scenarios])

  const CustomTooltip = ({
    active,
    payload,
    label,
  }: TooltipProps<number, string>) => {
    if (!active || !payload || payload.length === 0) return null

    const total = payload.reduce((sum, entry) => sum + (entry.value ?? 0), 0)

    return (
      <Box
        sx={{
          ...tooltipStyle,
          minWidth: 200,
        }}
      >
        <Typography
          sx={{
            fontWeight: 700,
            fontSize: 'var(--ob-font-size-sm)',
            mb: 'var(--ob-space-050)',
            color: 'text.primary',
          }}
        >
          {label}
        </Typography>
        {payload.map((entry) => {
          if (!entry.value || entry.value === 0) return null
          return (
            <Box
              key={entry.dataKey}
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                gap: 'var(--ob-space-100)',
                mb: 'var(--ob-space-025)',
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--ob-space-050)',
                }}
              >
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: 'var(--ob-radius-xs)',
                    bgcolor: entry.color,
                  }}
                />
                <Typography
                  sx={{
                    fontSize: 'var(--ob-font-size-sm)',
                    color: 'text.secondary',
                  }}
                >
                  {entry.name}
                </Typography>
              </Box>
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-sm)',
                  fontWeight: 500,
                  fontFamily: 'var(--ob-font-family-mono)',
                  color: 'text.primary',
                }}
              >
                {formatCurrencyFull(entry.value)}
              </Typography>
            </Box>
          )
        })}
        <Box
          sx={{
            borderTop: 1,
            borderColor: 'divider',
            mt: 'var(--ob-space-050)',
            pt: 'var(--ob-space-050)',
            display: 'flex',
            justifyContent: 'space-between',
          }}
        >
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-sm)',
              fontWeight: 700,
              color: 'text.primary',
            }}
          >
            {t('common.total')}
          </Typography>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-sm)',
              fontWeight: 700,
              fontFamily: 'var(--ob-font-family-mono)',
              color: 'text.primary',
            }}
          >
            {formatCurrencyFull(total)}
          </Typography>
        </Box>
      </Box>
    )
  }

  if (data.length === 0) {
    return (
      <Box
        sx={{
          height: 'var(--ob-max-height-panel)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Typography color="text.secondary">
          {t('finance.charts.noData')}
        </Typography>
      </Box>
    )
  }

  return (
    <Box sx={{ width: '100%' }}>
      {/* Chart Title - matches Gemini design */}
      <Typography
        variant="h6"
        sx={{
          fontWeight: 600,
          fontSize: 'var(--ob-font-size-lg)',
          color: 'text.primary',
          mb: 'var(--ob-space-150)',
          px: 'var(--ob-space-050)',
        }}
      >
        {t('finance.charts.scenarioComparison')}
      </Typography>
      <Box sx={{ height: 350, width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            barSize={chartSizes.barSize}
          >
            <CartesianGrid {...gridProps} />
            <XAxis dataKey="name" {...axisProps} tickMargin={10} />
            <YAxis
              {...axisProps}
              tickFormatter={(value) => formatCurrencyShort(value)}
            />
            <Tooltip
              content={<CustomTooltip />}
              cursor={{ fill: alpha(theme.palette.text.primary, 0.04) }}
            />
            <Legend
              wrapperStyle={{ paddingTop: chartSizes.legendPaddingTop }}
            />

            {/* Stack order: bottom to top */}
            <Bar
              dataKey="seniorDebt"
              name={t('finance.charts.seniorDebt')}
              stackId="stack"
              fill={colors.seniorDebt}
              radius={getBarRadius('bottom')}
            />
            <Bar
              dataKey="mezzanine"
              name={t('finance.charts.mezzanine')}
              stackId="stack"
              fill={colors.mezzanine}
              radius={getBarRadius('middle')}
            />
            <Bar
              dataKey="bridge"
              name={t('finance.charts.bridge')}
              stackId="stack"
              fill={colors.bridge}
              radius={getBarRadius('middle')}
            />
            <Bar
              dataKey="other"
              name={t('finance.charts.other')}
              stackId="stack"
              fill={colors.other}
              radius={getBarRadius('middle')}
            />
            <Bar
              dataKey="equity"
              name={t('finance.charts.equity')}
              stackId="stack"
              fill={colors.equity}
              radius={getBarRadius('top')}
            />
          </BarChart>
        </ResponsiveContainer>
      </Box>
    </Box>
  )
}

export default CapitalStackChart
