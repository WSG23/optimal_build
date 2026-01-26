/**
 * DrawdownChart - ComposedChart showing funding mix over time
 *
 * Follows UI_STANDARDS.md:
 * - Uses Recharts ComposedChart (Bar + Line)
 * - Colors from theme palette (dark mode compatible)
 * - Bar radius matches --ob-radius-sm
 * - Dual Y-axis: left for draws, right for outstanding debt
 * - Height constrained to --ob-max-height-panel
 */

import { useMemo } from 'react'

import { Box, Typography, alpha, useTheme } from '@mui/material'
import {
  ComposedChart,
  Bar,
  Line,
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

interface DrawdownChartProps {
  scenarios: FinanceScenarioSummary[]
  /** Which scenario to display (defaults to primary or first) */
  scenarioId?: number
}

interface ChartDataPoint {
  period: string
  equityDraw: number
  debtDraw: number
  outstandingDebt: number
}

function toNumber(value: string | undefined): number {
  if (typeof value !== 'string') return 0
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

export function DrawdownChart({ scenarios, scenarioId }: DrawdownChartProps) {
  const { t } = useTranslation()
  const theme = useTheme()
  const colors = getChartColors(theme)
  const axisProps = getAxisProps(theme)
  const gridProps = getGridProps(theme)
  const tooltipStyle = getTooltipStyle(theme)

  // Select scenario
  const scenario = useMemo(() => {
    if (scenarioId !== undefined) {
      return scenarios.find((s) => s.scenarioId === scenarioId)
    }
    // Default to primary scenario or first one
    const primary = scenarios.find((s) => s.isPrimary)
    return primary ?? scenarios[0]
  }, [scenarios, scenarioId])

  const data = useMemo<ChartDataPoint[]>(() => {
    if (!scenario?.drawdownSchedule?.entries) return []

    return scenario.drawdownSchedule.entries.map((entry) => ({
      period: entry.period,
      equityDraw: toNumber(entry.equityDraw),
      debtDraw: toNumber(entry.debtDraw),
      outstandingDebt: toNumber(entry.outstandingDebt),
    }))
  }, [scenario])

  const CustomTooltip = ({
    active,
    payload,
    label,
  }: TooltipProps<number, string>) => {
    if (!active || !payload || payload.length === 0) return null

    return (
      <Box sx={{ ...tooltipStyle, minWidth: 220 }}>
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
        {payload.map((entry) => (
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
                  height: entry.dataKey === 'outstandingDebt' ? 3 : 12,
                  borderRadius:
                    entry.dataKey === 'outstandingDebt'
                      ? 0
                      : 'var(--ob-radius-xs)',
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
              {formatCurrencyFull(entry.value ?? 0)}
            </Typography>
          </Box>
        ))}
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
    <Box sx={{ height: 'var(--ob-max-height-panel)', width: '100%' }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={data}
          margin={{
            top: 'var(--ob-space-800)',
            right: 30,
            left: 20,
            bottom: 'var(--ob-space-500)',
          }}
        >
          <CartesianGrid {...gridProps} />
          <XAxis dataKey="period" {...axisProps} tickMargin={10} />
          <YAxis
            yAxisId="left"
            {...axisProps}
            tickFormatter={(value) => formatCurrencyShort(value)}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            {...axisProps}
            tickFormatter={(value) => formatCurrencyShort(value)}
          />
          <Tooltip
            content={<CustomTooltip />}
            cursor={{ fill: alpha(theme.palette.text.primary, 0.04) }}
          />
          <Legend wrapperStyle={{ paddingTop: chartSizes.legendPaddingTop }} />

          {/* Stacked bars for periodic draws */}
          <Bar
            yAxisId="left"
            dataKey="equityDraw"
            name={t('finance.charts.equityDraw')}
            stackId="draws"
            fill={colors.equity}
            barSize={chartSizes.barSizeNarrow}
            radius={getBarRadius('bottom')}
          />
          <Bar
            yAxisId="left"
            dataKey="debtDraw"
            name={t('finance.charts.debtDraw')}
            stackId="draws"
            fill={colors.seniorDebt}
            barSize={chartSizes.barSizeNarrow}
            radius={getBarRadius('top')}
          />

          {/* Line for cumulative outstanding debt */}
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="outstandingDebt"
            name={t('finance.charts.outstandingDebt')}
            stroke={colors.line}
            strokeWidth={chartSizes.lineStrokeWidth}
            dot={{
              r: chartSizes.lineDotRadius,
              fill: colors.lineDot,
              strokeWidth: 2,
              stroke: theme.palette.background.paper,
            }}
            activeDot={{
              r: chartSizes.lineDotRadius + 2,
              fill: colors.lineDot,
              strokeWidth: 2,
              stroke: theme.palette.background.paper,
            }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </Box>
  )
}

export default DrawdownChart
