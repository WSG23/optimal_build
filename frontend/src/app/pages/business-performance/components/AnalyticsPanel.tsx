import { useMemo } from 'react'
import {
  Box,
  Card,
  CardContent,
  Chip,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemText,
  Stack,
  Typography,
} from '@mui/material'
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
      <Grid container spacing={2} className="bp-analytics__metrics">
        {metrics.map((metric) => (
          <Grid item xs={12} sm={6} md={4} key={metric.key}>
            <Card variant="outlined" className="bp-metric-card">
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary">
                  {metric.label}
                </Typography>
                <Typography variant="h5" className="bp-metric-card__value">
                  {metric.value}
                </Typography>
                {metric.helperText && (
                  <Typography variant="body2" color="text.secondary">
                    {metric.helperText}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Box className="bp-analytics__trend">
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
          <Typography variant="h6">30-day trend</Typography>
          <Typography variant="caption" color="text.secondary">
            Gross & weighted pipeline vs conversion + cycle time
          </Typography>
        </Stack>
        <Box className="bp-analytics__chart">
          {chartData.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              Trend data will appear once daily snapshots run.
            </Typography>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart
                data={chartData}
                margin={{ top: 16, right: 24, bottom: 0, left: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" tick={{ fontSize: 12 }} minTickGap={32} />
                <YAxis
                  yAxisId="left"
                  tickFormatter={(value: number) => `${value.toFixed(1)}m`}
                  label={{
                    value: 'Pipeline (SGD millions)',
                    angle: -90,
                    position: 'insideLeft',
                  }}
                />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  tickFormatter={(value: number) => `${value.toFixed(0)}`}
                  label={{
                    value: 'Conversion % / Cycle days',
                    angle: 90,
                    position: 'insideRight',
                  }}
                />
                <RechartsTooltip
                  formatter={formatTooltipValue}
                  labelStyle={{ fontWeight: 600 }}
                />
                <Legend />
                <Area
                  yAxisId="left"
                  type="monotone"
                  dataKey="gross"
                  name="Gross pipeline"
                  fill="#90caf9"
                  stroke="#42a5f5"
                  fillOpacity={0.3}
                />
                <Area
                  yAxisId="left"
                  type="monotone"
                  dataKey="weighted"
                  name="Weighted pipeline"
                  fill="#a5d6a7"
                  stroke="#66bb6a"
                  fillOpacity={0.3}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="conversion"
                  name="Conversion rate"
                  stroke="#ff7043"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="cycle"
                  name="Cycle time (days)"
                  stroke="#ab47bc"
                  strokeDasharray="4 2"
                  strokeWidth={2}
                  dot={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          )}
        </Box>
      </Box>

      <Divider sx={{ my: 2 }} />

      <Box className="bp-analytics__benchmarks">
        <Typography variant="h6" gutterBottom>
          Benchmark comparison
        </Typography>
        <List disablePadding className="bp-benchmark-list">
          {benchmarks.map((entry) => (
            <ListItem key={entry.key} className="bp-benchmark-list__item">
              <ListItemText
                primary={
                  <Stack direction="row" spacing={1} alignItems="center">
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
                  <Stack direction="row" spacing={1} flexWrap="wrap">
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

const formatTooltipValue: Formatter<ValueType, NameType> = (rawValue, rawName) => {
  const label = typeof rawName === 'string' ? rawName : String(rawName ?? '')
  const numericValue = typeof rawValue === 'number' ? rawValue : Number(rawValue ?? NaN)

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
