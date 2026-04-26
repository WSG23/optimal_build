import { Box, Typography, TableCell, TableRow } from '@mui/material'
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { GlassCard } from '../../../components/canonical/GlassCard'
import { AdvisoryTable } from './AdvisoryTable'
import type { AdvisoryAssetMixSegment } from '../../../api/advisory'

interface AssetMixPanelProps {
  totalGfa: number | null
  recommendations: AdvisoryAssetMixSegment[]
  notes: string[]
}

const COLORS = [
  'var(--ob-feasibility-asset-residential)',
  'var(--ob-feasibility-asset-commercial)',
  'var(--ob-feasibility-asset-office)',
  'var(--ob-feasibility-asset-retail)',
  'var(--ob-feasibility-asset-industrial)',
]

export function AssetMixPanel({
  totalGfa,
  recommendations,
  notes,
}: AssetMixPanelProps) {
  // Safe default colors if vars aren't loaded yet
  const getFill = (index: number) => COLORS[index % COLORS.length]

  const chartData = recommendations.map((r) => ({
    name: r.use,
    value: r.allocation_pct,
  }))

  return (
    <GlassCard className="advisory-panel">
      <Box
        sx={{
          p: 'var(--ob-space-200)',
          borderBottom: '1px solid var(--ob-color-border-subtle)',
        }}
      >
        <Typography
          variant="h6"
          sx={{
            fontSize: 'var(--ob-font-size-base)',
            fontWeight: 'var(--ob-font-weight-semibold)',
          }}
        >
          Asset Mix Strategy
        </Typography>
        <Typography
          variant="body2"
          sx={{
            color: 'var(--ob-color-text-secondary)',
            mt: 'var(--ob-space-050)',
          }}
        >
          Total Programmable GFA:{' '}
          <span style={{ color: 'var(--ob-color-text-primary)' }}>
            {totalGfa ? `${totalGfa.toLocaleString()} sqm` : '—'}
          </span>
        </Typography>
      </Box>

      <Box
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column', md: 'row' },
          gap: 'var(--ob-space-200)',
          p: 'var(--ob-space-200)',
        }}
      >
        {/* Left: Chart */}
        <Box
          sx={{
            width: { xs: '100%', md: '35%' },
            height: 250,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
                stroke="none"
              >
                {chartData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={getFill(index)} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(0,0,0,0.8)',
                  borderColor: 'var(--ob-color-border-subtle)',
                  borderRadius: 'var(--ob-radius-sm)',
                  color: 'var(--ob-color-text-on-dark, #fff)',
                }}
                itemStyle={{ color: 'var(--ob-color-text-on-dark, #fff)' }}
              />
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(value) => (
                  <span style={{ color: 'var(--ob-color-text-secondary)' }}>
                    {value}
                  </span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </Box>

        {/* Right: Table */}
        <Box sx={{ flex: 1 }}>
          <AdvisoryTable
            columns={[
              { id: 'use', label: 'Use', width: '25%' },
              { id: 'alloc', label: 'Allocation', width: '15%' },
              { id: 'gfa', label: 'Target GFA', width: '20%' },
              { id: 'rationale', label: 'Rationale' },
            ]}
          >
            {recommendations.map((row) => (
              <TableRow key={row.use}>
                <TableCell
                  sx={{
                    fontWeight: 'var(--ob-font-weight-medium)',
                    color: 'var(--ob-color-text-primary)',
                  }}
                >
                  {row.use}
                </TableCell>
                <TableCell>{row.allocation_pct}%</TableCell>
                <TableCell>
                  {row.target_gfa_sqm
                    ? row.target_gfa_sqm.toLocaleString()
                    : '—'}
                </TableCell>
                <TableCell
                  sx={{
                    color: 'var(--ob-color-text-secondary)',
                    fontSize: 'var(--ob-font-size-sm-minus)',
                  }}
                >
                  {row.rationale}
                </TableCell>
              </TableRow>
            ))}
          </AdvisoryTable>

          {notes.length > 0 && (
            <Box
              sx={{
                mt: 'var(--ob-space-200)',
                p: 'var(--ob-space-200)',
                bgcolor: 'var(--ob-background-surface-0)',
                borderRadius: 'var(--ob-radius-sm)',
                border: '1px solid var(--ob-color-border-subtle)',
              }}
            >
              <Typography
                variant="subtitle2"
                sx={{
                  color: 'var(--ob-color-text-secondary)',
                  mb: 'var(--ob-space-100)',
                  fontSize: 'var(--ob-font-size-xs)',
                  textTransform: 'uppercase',
                }}
              >
                Strategy Notes
              </Typography>
              <ul style={{ margin: 0, paddingLeft: 'var(--ob-space-125)' }}>
                {notes.map((note, i) => (
                  <li
                    key={i}
                    style={{
                      color: 'var(--ob-color-text-secondary)',
                      fontSize: 'var(--ob-font-size-sm)',
                      marginBottom: 'var(--ob-space-025)',
                    }}
                  >
                    {note}
                  </li>
                ))}
              </ul>
            </Box>
          )}
        </Box>
      </Box>
    </GlassCard>
  )
}
