import { useMemo } from 'react'
import {
  Box,
  Chip,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemText,
  Stack,
  Typography,
} from '@mui/material'
import { BarChart } from '@mui/icons-material'
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type {
  ValueType,
  NameType,
  Formatter,
} from 'recharts/types/component/DefaultTooltipContent'
import type { AnalyticsMetric, BenchmarkEntry, TrendPoint } from '../types'

interface AnalyticsPanelProps {
  metrics: AnalyticsMetric[]
  trend: TrendPoint[]
  benchmarks: BenchmarkEntry[]
}

import { MetricTile } from '../../../../components/canonical/MetricTile'
import { Card } from '../../../../components/canonical/Card'

// ... existing imports ... (Assuming they are preserved or I need to handle them carefully if I'm replacing a chunk)

export function AnalyticsPanel({
  metrics,
  trend,
  benchmarks,
}: AnalyticsPanelProps) {
  const chartData = useMemo(
    () =>
      trend.map((point) => ({
        label: point.label,
        gross: point.gross ?? 0,
        weighted: point.weighted ?? 0,
        conversion: point.conversion !== null ? point.conversion * 100 : null,
        cycle: point.cycle,
      })),
    [trend],
  )

  return (
    <Box className="bp-analytics">
      <Grid
        container
        spacing="var(--ob-space-200)"
        className="bp-analytics__metrics"
        sx={{ mb: 'var(--ob-space-400)' }}
      >
        {metrics.map((metric) => (
          <Grid item xs={12} sm={6} md={4} key={metric.key}>
            <MetricTile
              label={metric.label}
              value={metric.value}
              variant="default"
            />
          </Grid>
        ))}
      </Grid>

      <Box className="bp-analytics__trend">
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          mb="var(--ob-space-100)"
        >
          <Typography variant="h6">30-day trend</Typography>
          <Typography variant="caption" color="text.secondary">
            Gross & weighted pipeline vs conversion + cycle time
          </Typography>
        </Stack>
        <Card
          variant="glass"
          className="bp-analytics__chart"
          sx={{ height: 300, position: 'relative', p: 'var(--ob-space-200)' }}
        >
          {chartData.length === 0 ? (
            <Stack
              alignItems="center"
              justifyContent="center"
              spacing="var(--ob-space-200)"
              sx={{
                height: '100%',
                color: 'text.secondary',
                opacity: 0.6,
              }}
            >
              <BarChart sx={{ fontSize: 64, opacity: 0.5 }} />
              <Box textAlign="center">
                <Typography variant="h6" color="text.primary">
                  Connect data to see pipeline trends
                </Typography>
                <Typography variant="body2">
                  Historical performance will populate here daily.
                </Typography>
              </Box>
            </Stack>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart
                data={chartData}
                margin={{
                  top: 'var(--ob-space-800)',
                  right: 24,
                  bottom: '0',
                  left: 0,
                }}
              >
                {/* ... Chart Content Preserved ... */}
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                  stroke="var(--ob-color-surface-overlay)"
                />
                <XAxis
                  dataKey="label"
                  tick={{ fontSize: 12, fill: 'var(--ob-color-text-tertiary)' }}
                  minTickGap={32}
                />
                <YAxis
                  yAxisId="left"
                  tickFormatter={(value: number) => `${value.toFixed(1)}m`}
                  tick={{ fontSize: 12, fill: 'var(--ob-color-text-tertiary)' }}
                  label={{
                    value: 'Pipeline (SGD millions)',
                    angle: -90,
                    position: 'insideLeft',
                    fill: 'var(--ob-color-text-tertiary)',
                    fontSize: 12,
                  }}
                />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  tickFormatter={(value: number) => `${value.toFixed(0)}`}
                  tick={{ fontSize: 12, fill: 'var(--ob-color-text-tertiary)' }}
                  label={{
                    value: 'Conversion % / Cycle days',
                    angle: 90,
                    position: 'insideRight',
                    fill: 'var(--ob-color-text-tertiary)',
                    fontSize: 12,
                  }}
                />
                <RechartsTooltip
                  formatter={formatTooltipValue}
                  labelStyle={{
                    fontWeight: 600,
                    color: 'var(--ob-color-bg-inverse)',
                  }}
                  contentStyle={{
                    borderRadius: 'var(--ob-radius-sm)', // Square Cyber-Minimalism: sm for tooltips
                    border: 'none',
                    boxShadow:
                      '0 4px 6px -1px var(--ob-color-action-active-light)',
                  }}
                />
                <Legend iconType="circle" />
                <Area
                  yAxisId="left"
                  type="monotone"
                  dataKey="gross"
                  name="Gross pipeline"
                  fill="url(#colorGross)"
                  stroke="#3B82F6"
                  fillOpacity={1}
                />
                <Area
                  yAxisId="left"
                  type="monotone"
                  dataKey="weighted"
                  name="Weighted pipeline"
                  fill="url(#colorWeighted)"
                  stroke="#10B981"
                  fillOpacity={1}
                />
                <defs>
                  <linearGradient id="colorGross" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient
                    id="colorWeighted"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="conversion"
                  name="Conversion rate"
                  stroke="#F59E0B"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="cycle"
                  name="Cycle time (days)"
                  stroke="#8B5CF6"
                  strokeDasharray="4 2"
                  strokeWidth={2}
                  dot={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          )}
        </Card>
      </Box>

      <Divider sx={{ my: 'var(--ob-space-200)' }} />

      <Box className="bp-analytics__benchmarks">
        <Typography variant="h6" gutterBottom>
          Benchmark comparison
        </Typography>
        <List disablePadding className="bp-benchmark-list">
          {benchmarks.map((entry) => (
            <ListItem key={entry.key} className="bp-benchmark-list__item">
              <ListItemText
                primary={
                  <Stack
                    direction="row"
                    spacing="var(--ob-space-100)"
                    alignItems="center"
                  >
                    <Typography variant="subtitle1">{entry.label}</Typography>
                    {entry.deltaText && (
                      <Chip
                        size="small"
                        color={entry.deltaPositive ? 'success' : 'error'}
                        label={entry.deltaText}
                      />
                    )}
                  </Stack>
                }
                secondary={
                  <Stack
                    direction="row"
                    spacing="var(--ob-space-100)"
                    flexWrap="wrap"
                  >
                    <Typography variant="body2" fontWeight={600}>
                      {entry.actual}
                    </Typography>
                    {entry.benchmark && entry.cohort && (
                      <Typography variant="body2" color="text.secondary">
                        vs {entry.cohort}: {entry.benchmark}
                      </Typography>
                    )}
                  </Stack>
                }
              />
            </ListItem>
          ))}
          {benchmarks.length === 0 && (
            <ListItem>
              <ListItemText
                primary="No benchmarks available yet"
                secondary="Benchmarks sync nightly with cohort analytics."
              />
            </ListItem>
          )}
        </List>
      </Box>
    </Box>
  )
}

const formatTooltipValue: Formatter<ValueType, NameType> = (
  rawValue,
  rawName,
) => {
  const label = typeof rawName === 'string' ? rawName : String(rawName ?? '')
  const numericValue =
    typeof rawValue === 'number' ? rawValue : Number(rawValue ?? NaN)

  if (!Number.isFinite(numericValue)) {
    return ['Not available yet', label]
  }
  if (label.toLowerCase().includes('pipeline')) {
    return [`${numericValue.toFixed(1)}m`, label]
  }
  if (label.toLowerCase().includes('conversion')) {
    return [`${numericValue.toFixed(1)}%`, label]
  }
  if (label.toLowerCase().includes('cycle')) {
    return [`${numericValue.toFixed(0)} days`, label]
  }
  return [numericValue.toString(), label]
}
