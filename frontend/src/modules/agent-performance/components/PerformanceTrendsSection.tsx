import { Grid, Typography } from '@mui/material'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { Card } from '../../../components/canonical/Card'
import { formatShortCurrency } from '../utils/formatters'
import type { TrendDataPoint } from '../types'

interface PerformanceTrendsSectionProps {
  trendData: TrendDataPoint[]
  pipelineHeading: string
  conversionHeading: string
  locale: string
  primaryCurrency: string
}

export function PerformanceTrendsSection({
  trendData,
  pipelineHeading,
  conversionHeading,
  locale,
  primaryCurrency,
}: PerformanceTrendsSectionProps) {
  return (
    <Grid container spacing="var(--ob-space-200)">
      <Grid item xs={12} md={6}>
        <Card variant="default" sx={{ p: 'var(--ob-space-200)', height: 320 }}>
          <Typography variant="h6" gutterBottom>
            {pipelineHeading}
          </Typography>
          <ResponsiveContainer width="100%" height="90%">
            <AreaChart data={trendData}>
              <defs>
                <linearGradient id="colorGross" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="label" tick={{ fontSize: 12 }} />
              <YAxis
                tick={{ fontSize: 12 }}
                tickFormatter={(val) =>
                  formatShortCurrency(val, primaryCurrency, locale)
                }
              />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="gross"
                stroke="#3B82F6"
                fillOpacity={1}
                fill="url(#colorGross)"
              />
              <Area
                type="monotone"
                dataKey="weighted"
                stroke="#10B981"
                fillOpacity={0}
                strokeDasharray="4 4"
              />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      </Grid>
      <Grid item xs={12} md={6}>
        <Card variant="default" sx={{ p: 'var(--ob-space-200)', height: 320 }}>
          <Typography variant="h6" gutterBottom>
            {conversionHeading}
          </Typography>
          <ResponsiveContainer width="100%" height="90%">
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="label" tick={{ fontSize: 12 }} />
              <YAxis
                tick={{ fontSize: 12 }}
                tickFormatter={(val) => `${val}%`}
              />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="conversion"
                stroke="#F59E0B"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="cycle"
                stroke="#8B5CF6"
                strokeWidth={2}
                strokeDasharray="4 4"
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </Grid>
    </Grid>
  )
}
