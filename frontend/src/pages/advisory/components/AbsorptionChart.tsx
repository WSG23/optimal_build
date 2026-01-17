import { Box, Typography } from '@mui/material'
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { GlassCard } from '../../../components/canonical/GlassCard'
import type { AbsorptionForecast } from '../../api/advisory'

interface AbsorptionChartProps {
  data: AbsorptionForecast
}

export function AbsorptionChart({ data }: AbsorptionChartProps) {
  // Transform data for chart if needed. Currently assumes timeline matches chart needs.
  // We want to verify structure: { milestone, month, expected_absorption_pct }
  // We'll calculate cumulative absorption for the line
  let cumulative = 0
  const chartData = data.timeline.map((item) => {
    cumulative += item.expected_absorption_pct
    return {
      month: item.month, // X-axis
      absorption: item.expected_absorption_pct, // Bar
      total: Math.min(cumulative, 100), // Line
      milestone: item.milestone,
    }
  })

  return (
    <GlassCard className="advisory-panel">
      <Box
        sx={{ p: 2, borderBottom: '1px solid var(--ob-color-border-subtle)' }}
      >
        <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600 }}>
          Absorption Forecast
        </Typography>
        <Typography
          variant="body2"
          sx={{ color: 'var(--ob-color-text-secondary)', mt: 0.5 }}
        >
          Expected Stabilisation:{' '}
          <strong style={{ color: 'var(--ob-color-text-primary)' }}>
            {data.expected_months_to_stabilize} Months
          </strong>{' '}
          • Target Velocity:{' '}
          <strong style={{ color: 'var(--ob-color-text-primary)' }}>
            {data.monthly_velocity_target} units/mo
          </strong>
        </Typography>
      </Box>

      <Box sx={{ p: 3, height: 400 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={chartData}
            margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--ob-color-border-subtle)"
              vertical={false}
            />
            <XAxis
              dataKey="month"
              stroke="var(--ob-color-text-secondary)"
              tick={{ fontSize: 12 }}
            />
            <YAxis
              yAxisId="left"
              stroke="var(--ob-color-text-secondary)"
              tick={{ fontSize: 12 }}
              unit="%"
              label={{
                value: 'Monthly %',
                angle: -90,
                position: 'insideLeft',
                style: { fill: 'var(--ob-color-text-secondary)' },
              }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              stroke="var(--ob-color-brand-primary)"
              tick={{ fontSize: 12 }}
              unit="%"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(0,0,0,0.85)',
                borderColor: 'var(--ob-color-border-subtle)',
                color: '#fff',
              }}
            />
            <Legend wrapperStyle={{ paddingTop: 10 }} />
            <Bar
              yAxisId="left"
              dataKey="absorption"
              name="Monthly Absorption"
              fill="var(--ob-color-brand-secondary)"
              barSize={30}
              radius={[4, 4, 0, 0]}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="total"
              name="Cumulative Total"
              stroke="var(--ob-color-brand-primary)"
              strokeWidth={3}
              dot={{ r: 4 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </Box>
    </GlassCard>
  )
}
