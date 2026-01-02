/**
 * AssetMixChart - Unified Intelligence Widget Component
 *
 * Implements UX Friction Solution #4: Dry Data vs Strategic Insights
 * - Donut chart with center metric display (Total GFA or primary financial metric)
 * - Interactive data-legend hybrid with hover sync
 * - Horizontal 40/60 layout (chart | legend) for desktop
 * - AI-generated strategic recommendations
 *
 * Design Principles:
 * - Clean Density: Tight vertical spacing, no internal scrolling
 * - Typography: Small caps/bold labels to distinguish from data
 * - Visual Sync: Hover on chart highlights legend row (Cyan-500/10 glow)
 * - Dashboard Terminal: Single cohesive "Intelligence Widget" look
 *
 * @see frontend/UX_ARCHITECTURE.md - Problem 4: Dry Data vs Strategic Insights
 */

import { useState, useCallback, useMemo } from 'react'
import { Box, Typography, SxProps, Theme } from '@mui/material'
import { PieChart, Pie, Cell, ResponsiveContainer, Sector } from 'recharts'
import type { PieSectorDataItem } from 'recharts/types/polar/Pie'
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
  /** Total GFA to display in center (optional) */
  totalGfa?: number
  /** Primary financial metric to display in center (optional, overrides GFA) */
  primaryMetric?: { label: string; value: string }
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

// Resolved color values for Recharts (CSS variables don't work in SVG filters)
const CHART_COLORS_RESOLVED = [
  '#00f3ff', // Cyan
  '#22c55e', // Green
  '#6366f1', // Indigo
  '#f59e0b', // Amber
  '#64748b', // Gray
  '#ec4899', // Magenta
]

/**
 * Active shape renderer for hover state on donut segments
 */
function renderActiveShape(props: PieSectorDataItem) {
  const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill } = props

  return (
    <g>
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius}
        outerRadius={(outerRadius ?? 0) + 6}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
        style={{
          filter: `drop-shadow(0 0 8px ${fill})`,
          transition: 'all 0.2s ease-out',
        }}
      />
    </g>
  )
}

export function AssetMixChart({
  data,
  title = 'Asset Allocation',
  aiInsight,
  currencySymbol = 'S$',
  formatNumber = (v, opts) => v.toLocaleString('en-SG', opts),
  totalGfa,
  primaryMetric,
  sx = {},
}: AssetMixChartProps) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null)

  // Calculate totals
  const { totalPercentage, calculatedTotalGfa, calculatedTotalRevenue } =
    useMemo(() => {
      const pct = data.reduce((sum, item) => sum + item.value, 0)
      const gfa = data.reduce((sum, item) => sum + (item.allocatedGfa ?? 0), 0)
      const rev = data.reduce(
        (sum, item) => sum + (item.estimatedRevenue ?? 0),
        0,
      )
      return {
        totalPercentage: pct,
        calculatedTotalGfa: totalGfa ?? gfa,
        calculatedTotalRevenue: rev,
      }
    }, [data, totalGfa])

  // Format for pie chart
  const chartData = useMemo(
    () =>
      data.map((item, index) => ({
        name: item.label,
        value: item.value,
        percentage:
          totalPercentage > 0 ? (item.value / totalPercentage) * 100 : 0,
        allocatedGfa: item.allocatedGfa,
        estimatedRevenue: item.estimatedRevenue,
        riskLevel: item.riskLevel,
        color: CHART_COLORS[index % CHART_COLORS.length],
        colorResolved:
          CHART_COLORS_RESOLVED[index % CHART_COLORS_RESOLVED.length],
        originalIndex: index,
      })),
    [data, totalPercentage],
  )

  // Handlers for hover sync
  const handlePieEnter = useCallback((_: unknown, index: number) => {
    setActiveIndex(index)
  }, [])

  const handlePieLeave = useCallback(() => {
    setActiveIndex(null)
  }, [])

  const handleLegendEnter = useCallback((index: number) => {
    setActiveIndex(index)
  }, [])

  const handleLegendLeave = useCallback(() => {
    setActiveIndex(null)
  }, [])

  if (data.length === 0) {
    return null
  }

  // Determine center metric display
  const centerMetric = primaryMetric ?? {
    label: 'Total GFA',
    value:
      calculatedTotalGfa > 0
        ? `${formatNumber(calculatedTotalGfa, { maximumFractionDigits: 0 })} sqm`
        : calculatedTotalRevenue > 0
          ? `${currencySymbol}${formatNumber(calculatedTotalRevenue / 1_000_000, { maximumFractionDigits: 1 })}M`
          : '—',
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
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-base)',
            fontWeight: 700,
            color: 'var(--ob-color-text-primary)',
            letterSpacing: '-0.01em',
          }}
        >
          {title}
        </Typography>
        {/* Asset count badge */}
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-2xs)',
            fontWeight: 600,
            color: 'var(--ob-text-secondary)',
            bgcolor: 'var(--ob-surface-glass-subtle)',
            px: 'var(--ob-space-075)',
            py: 'var(--ob-space-025)',
            borderRadius: 'var(--ob-radius-xs)',
          }}
        >
          {data.length} ASSET{data.length !== 1 ? 'S' : ''}
        </Typography>
      </Box>

      {/* Main content: Donut (40%) + Legend (60%) - horizontal on desktop */}
      <Box
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column', md: 'row' },
          gap: 'var(--ob-space-150)',
          alignItems: { xs: 'center', md: 'stretch' },
        }}
      >
        {/* Donut Chart with Center Metric - 40% width on desktop */}
        <Box
          sx={{
            flex: { xs: '1 1 auto', md: '0 0 40%' },
            position: 'relative',
            height: { xs: 180, md: 160 },
            width: { xs: '100%', md: 'auto' },
            minWidth: { md: 160 },
          }}
        >
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius="55%"
                outerRadius="85%"
                paddingAngle={2}
                dataKey="value"
                stroke="none"
                activeIndex={activeIndex ?? undefined}
                activeShape={renderActiveShape}
                onMouseEnter={handlePieEnter}
                onMouseLeave={handlePieLeave}
              >
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.color}
                    style={{
                      filter:
                        activeIndex === index
                          ? `drop-shadow(0 0 8px ${entry.colorResolved})`
                          : `drop-shadow(0 0 3px ${entry.colorResolved}40)`,
                      transition: 'filter 0.2s ease-out',
                      cursor: 'pointer',
                    }}
                  />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>

          {/* Center Metric Overlay */}
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              textAlign: 'center',
              pointerEvents: 'none',
            }}
          >
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-2xs)',
                fontWeight: 600,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                color: 'var(--ob-text-secondary)',
                lineHeight: 1,
              }}
            >
              {centerMetric.label}
            </Typography>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-base)',
                fontWeight: 700,
                color: 'var(--ob-color-text-primary)',
                lineHeight: 1.2,
                mt: 'var(--ob-space-025)',
              }}
            >
              {centerMetric.value}
            </Typography>
          </Box>
        </Box>

        {/* Simplified Legend Grid - 60% width on desktop (GFA removed - shown in Master Table) */}
        <Box
          sx={{
            flex: { xs: '1 1 auto', md: '1 1 60%' },
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--ob-space-050)',
            width: '100%',
          }}
        >
          {/* Column Headers - simplified: Name + Mix% only */}
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: 'auto 1fr auto',
              gap: 'var(--ob-space-075)',
              alignItems: 'center',
              pb: 'var(--ob-space-050)',
              borderBottom: '1px solid var(--ob-color-border-subtle)',
            }}
          >
            <Box sx={{ width: 'var(--ob-space-100)' }} />{' '}
            {/* Color swatch column */}
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-2xs)',
                fontWeight: 700,
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                color: 'var(--ob-text-secondary)',
              }}
            >
              Asset Class
            </Typography>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-2xs)',
                fontWeight: 700,
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                color: 'var(--ob-text-secondary)',
                textAlign: 'right',
              }}
            >
              Mix
            </Typography>
          </Box>

          {/* Data Rows - simplified without GFA column */}
          {chartData.map((item, index) => {
            const isActive = activeIndex === index
            return (
              <Box
                key={item.name}
                onMouseEnter={() => handleLegendEnter(index)}
                onMouseLeave={handleLegendLeave}
                sx={{
                  display: 'grid',
                  gridTemplateColumns: 'auto 1fr auto',
                  gap: 'var(--ob-space-075)',
                  alignItems: 'center',
                  py: 'var(--ob-space-050)',
                  px: 'var(--ob-space-050)',
                  mx: 'calc(-1 * var(--ob-space-050))',
                  borderRadius: 'var(--ob-radius-xs)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease-out',
                  bgcolor: isActive
                    ? 'color-mix(in srgb, var(--ob-color-neon-cyan) 10%, transparent)'
                    : 'transparent',
                  boxShadow: isActive
                    ? 'inset 0 0 0 1px color-mix(in srgb, var(--ob-color-neon-cyan) 30%, transparent)'
                    : 'none',
                }}
              >
                {/* Color Swatch */}
                <Box
                  sx={{
                    width: 'var(--ob-space-100)',
                    height: 'var(--ob-space-100)',
                    borderRadius: 'var(--ob-radius-xs)',
                    bgcolor: item.color,
                    boxShadow: isActive
                      ? `0 0 8px ${item.colorResolved}`
                      : 'none',
                    transition: 'box-shadow 0.15s ease-out',
                  }}
                />

                {/* Asset Class Name */}
                <Typography
                  sx={{
                    fontSize: 'var(--ob-font-size-sm)',
                    fontWeight: isActive ? 600 : 500,
                    color: isActive
                      ? 'var(--ob-color-text-primary)'
                      : 'var(--ob-text-secondary)',
                    transition: 'all 0.15s ease-out',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {item.name}
                </Typography>

                {/* Percentage */}
                <Typography
                  sx={{
                    fontSize: 'var(--ob-font-size-sm)',
                    fontWeight: 700,
                    color: isActive
                      ? 'var(--ob-color-neon-cyan)'
                      : 'var(--ob-color-text-primary)',
                    textAlign: 'right',
                    fontVariantNumeric: 'tabular-nums',
                    transition: 'color 0.15s ease-out',
                  }}
                >
                  {formatNumber(item.value, { maximumFractionDigits: 0 })}%
                </Typography>
              </Box>
            )
          })}
        </Box>
      </Box>

      {/* AI Insight Panel - Compact footer */}
      {aiInsight && (
        <Box
          sx={{
            mt: 'var(--ob-space-050)',
            p: 'var(--ob-space-100)',
            bgcolor: 'var(--ob-color-status-info-bg)',
            borderLeft: '3px solid',
            borderColor: 'info.main',
            borderRadius: 'var(--ob-radius-xs)',
          }}
        >
          <Box
            sx={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 'var(--ob-space-075)',
            }}
          >
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-2xs)',
                fontWeight: 700,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                color: 'info.main',
                whiteSpace: 'nowrap',
              }}
            >
              NOTE
            </Typography>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'var(--ob-text-secondary)',
                lineHeight: 1.4,
              }}
            >
              {aiInsight}
            </Typography>
          </Box>
        </Box>
      )}
    </GlassCard>
  )
}
