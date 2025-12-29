/**
 * AssetMixChart - Contextual Intelligence & Visualization Component
 *
 * Implements UX Friction Solution #4: Dry Data vs Strategic Insights
 * - Pie/donut chart instead of text lists for asset allocation
 * - AI-generated strategic recommendations
 * - Indigo styling for AI insights
 *
 * @see frontend/UX_ARCHITECTURE.md - Problem 4: Dry Data vs Strategic Insights
 */

import { Box, Typography, SxProps, Theme } from '@mui/material'
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts'
import { GlassCard } from '../../../../../components/canonical/GlassCard'

export interface AssetMixItem {
  /** Asset type label (e.g., "Residential", "Commercial") */
  label: string
  /** Allocation percentage (0-100) */
  value: number
  /** Optional allocated GFA in sqm */
  allocatedGfa?: number
  /** Optional estimated revenue */
  estimatedRevenue?: number
  /** Optional risk level */
  riskLevel?: 'low' | 'medium' | 'high'
}

export interface AssetMixChartProps {
  /** Asset mix data */
  data: AssetMixItem[]
  /** Card title */
  title?: string
  /** Optional AI-generated insight text */
  aiInsight?: string
  /** Currency symbol for display */
  currencySymbol?: string
  /** Number formatter function */
  formatNumber?: (value: number, options?: Intl.NumberFormatOptions) => string
  /** Additional styles */
  sx?: SxProps<Theme>
}

// Cyber-minimalism color palette for pie chart segments
const CHART_COLORS = [
  'var(--ob-color-neon-cyan)', // Primary - Cyan
  'var(--ob-success-500)', // Secondary - Green
  'var(--ob-info-500)', // Tertiary - Indigo
  'var(--ob-warning-500)', // Quaternary - Amber
  'var(--ob-neutral-500)', // Quinary - Gray
  'var(--ob-color-neon-magenta)', // Senary - Magenta
]

export function AssetMixChart({
  data,
  title = 'Recommended Asset Mix',
  aiInsight,
  currencySymbol = 'S$',
  formatNumber = (v, opts) => v.toLocaleString('en-SG', opts),
  sx = {},
}: AssetMixChartProps) {
  if (data.length === 0) {
    return null
  }

  // Calculate total for percentage normalization
  const total = data.reduce((sum, item) => sum + item.value, 0)

  // Format for pie chart
  const chartData = data.map((item) => ({
    name: item.label,
    value: item.value,
    percentage: total > 0 ? (item.value / total) * 100 : 0,
  }))

  // Custom tooltip
  const CustomTooltip = ({
    active,
    payload,
  }: {
    active?: boolean
    payload?: Array<{
      name: string
      value: number
      payload: { percentage: number }
    }>
  }) => {
    if (active && payload && payload.length) {
      const item = payload[0]
      const sourceItem = data.find((d) => d.label === item.name)

      return (
        <Box
          sx={{
            bgcolor: 'var(--ob-surface-glass)',
            backdropFilter: 'blur(var(--ob-blur-md))',
            border: '1px solid var(--ob-color-border-subtle)',
            borderRadius: 'var(--ob-radius-sm)',
            p: 'var(--ob-space-100)',
            boxShadow: 'var(--ob-shadow-lg)',
          }}
        >
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-sm)',
              fontWeight: 600,
              color: 'var(--ob-color-text-primary)',
              mb: 'var(--ob-space-025)',
            }}
          >
            {item.name}
          </Typography>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              color: 'var(--ob-text-secondary)',
            }}
          >
            {formatNumber(item.payload.percentage, {
              maximumFractionDigits: 1,
            })}
            %
            {sourceItem?.allocatedGfa && (
              <> • {formatNumber(sourceItem.allocatedGfa)} sqm</>
            )}
          </Typography>
          {sourceItem?.estimatedRevenue && (
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'var(--ob-success-500)',
                mt: 'var(--ob-space-025)',
              }}
            >
              {currencySymbol}
              {formatNumber(sourceItem.estimatedRevenue / 1_000_000, {
                maximumFractionDigits: 1,
              })}
              M revenue
            </Typography>
          )}
        </Box>
      )
    }
    return null
  }

  // Custom legend
  const renderLegend = (props: {
    payload?: Array<{ value: string; color: string }>
  }) => {
    const { payload } = props
    if (!payload) return null

    return (
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 'var(--ob-space-100)',
          justifyContent: 'center',
          mt: 'var(--ob-space-100)',
        }}
      >
        {payload.map((entry, index) => {
          const sourceItem = data.find((d) => d.label === entry.value)
          return (
            <Box
              key={`legend-${index}`}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-050)',
              }}
            >
              <Box
                sx={{
                  width: 10,
                  height: 10,
                  borderRadius: 'var(--ob-radius-xs)',
                  bgcolor: entry.color,
                }}
              />
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-xs)',
                  color: 'var(--ob-text-secondary)',
                }}
              >
                {entry.value}{' '}
                <Box
                  component="span"
                  sx={{
                    fontWeight: 600,
                    color: 'var(--ob-color-text-primary)',
                  }}
                >
                  {sourceItem
                    ? formatNumber(sourceItem.value, {
                        maximumFractionDigits: 0,
                      })
                    : 0}
                  %
                </Box>
              </Typography>
            </Box>
          )
        })}
      </Box>
    )
  }

  return (
    <GlassCard
      sx={{
        p: 'var(--ob-space-150)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-100)',
        ...sx,
      }}
    >
      {/* Title */}
      <Typography
        sx={{
          fontSize: 'var(--ob-font-size-lg)',
          fontWeight: 700,
          color: 'var(--ob-color-text-primary)',
          letterSpacing: '-0.01em',
        }}
      >
        {title}
      </Typography>

      {/* Donut Chart */}
      <Box sx={{ height: 200, width: '100%' }}>
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={80}
              paddingAngle={2}
              dataKey="value"
              stroke="none"
            >
              {chartData.map((_, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={CHART_COLORS[index % CHART_COLORS.length]}
                  style={{
                    filter: `drop-shadow(0 0 4px ${CHART_COLORS[index % CHART_COLORS.length]}40)`,
                  }}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend content={renderLegend} />
          </PieChart>
        </ResponsiveContainer>
      </Box>

      {/* AI Insight Panel */}
      {aiInsight && (
        <Box
          sx={{
            mt: 'var(--ob-space-100)',
            p: 'var(--ob-space-100)',
            bgcolor: 'rgba(99, 102, 241, 0.08)', // Indigo background
            borderLeft: '3px solid',
            borderColor: 'info.main',
            borderRadius: 'var(--ob-radius-xs)',
          }}
        >
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-2xs)',
              fontWeight: 700,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: 'info.main',
              mb: 'var(--ob-space-025)',
            }}
          >
            AI INSIGHT
          </Typography>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-sm)',
              color: 'var(--ob-text-secondary)',
              lineHeight: 1.5,
            }}
          >
            {aiInsight}
          </Typography>
        </Box>
      )}
    </GlassCard>
  )
}
