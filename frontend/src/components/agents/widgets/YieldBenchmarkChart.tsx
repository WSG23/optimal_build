import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat';
import { YieldBenchmarks } from '../../../types/market';
import { PropertyType } from '../../../types/property';

interface YieldBenchmarkChartProps {
  yieldBenchmarks?: YieldBenchmarks | null;
  propertyType: PropertyType;
}

const YieldBenchmarkChart: React.FC<YieldBenchmarkChartProps> = ({
  yieldBenchmarks,
  propertyType
}) => {
  const formatPercent = (value?: number | null, fractionDigits = 2) => {
    if (value === undefined || value === null || Number.isNaN(value)) return '—';
    const percentValue = Math.abs(value) <= 1 ? value * 100 : value;
    return `${percentValue.toFixed(fractionDigits)}%`;
  };

  const statistics = yieldBenchmarks?.current_metrics;
  const yoy = yieldBenchmarks?.yoy_changes;
  const trends = yieldBenchmarks?.trends;

  const yoyData = [] as { label: string; value: number; unit: string }[];
  if (yoy?.cap_rate_change_bps !== undefined) {
    yoyData.push({ label: 'Cap Rate Δ', value: yoy.cap_rate_change_bps, unit: 'bps' });
  }
  if (yoy?.rental_change_pct !== undefined) {
    yoyData.push({ label: 'Rental Δ', value: yoy.rental_change_pct, unit: '%' });
  }
  if (yoy?.transaction_volume_change_pct !== undefined) {
    yoyData.push({ label: 'Volume Δ', value: yoy.transaction_volume_change_pct, unit: '%' });
  }

  const trendChip = (label: string, trend?: string | null) => {
    let icon = <TrendingFlatIcon fontSize="small" />;
    let color: 'default' | 'success' | 'error' | 'warning' = 'default';

    if (!trend) {
      return <Chip size="small" label={`${label}: n/a`} variant="outlined" />;
    }

    if (trend === 'increasing') {
      icon = <TrendingUpIcon fontSize="small" />;
      color = 'error';
    } else if (trend === 'decreasing') {
      icon = <TrendingDownIcon fontSize="small" />;
      color = 'success';
    }

    return <Chip size="small" icon={icon} label={`${label}: ${trend}`} color={color} variant={color === 'default' ? 'outlined' : 'filled'} />;
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Yield Benchmarks</Typography>
        <Typography variant="caption" color="textSecondary">
          {propertyType.replace(/_/g, ' ').toUpperCase()}
        </Typography>
      </Box>

      {statistics ? (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Median Cap Rate
                </Typography>
                <Typography variant="h5">
                  {formatPercent(statistics.cap_rate.median, 2)}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Range {formatPercent(statistics.cap_rate.range.p25, 2)} – {formatPercent(statistics.cap_rate.range.p75, 2)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Average Cap Rate
                </Typography>
                <Typography variant="h5">
                  {formatPercent(statistics.cap_rate.mean, 2)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Rental Median (psf/mo)
                </Typography>
                <Typography variant="h5">
                  ${statistics.rental_rates.median_psf?.toFixed(2) ?? '—'}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Occupancy {formatPercent(statistics.rental_rates.occupancy, 1)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Transaction Volume
                </Typography>
                <Typography variant="h5">
                  {statistics.transaction_volume.count} deals
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Total {statistics.transaction_volume.total_value.toLocaleString('en-SG', { style: 'currency', currency: 'SGD', maximumFractionDigits: 0 })}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      ) : (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography color="textSecondary">No yield benchmark data available.</Typography>
        </Paper>
      )}

      {trends && (
        <Box display="flex" gap={1} flexWrap="wrap" mb={3}>
          {trendChip('Cap Rate', trends.cap_rate_trend)}
          {trendChip('Rental', trends.rental_trend)}
          <Chip size="small" label={yieldBenchmarks?.market_position?.replace(/_/g, ' ') ?? 'market position n/a'} variant="outlined" />
        </Box>
      )}

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Year-over-year movement
        </Typography>
        {yoyData.length === 0 ? (
          <Typography color="textSecondary">No year-over-year analytics available.</Typography>
        ) : (
          <Box height={320}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={yoyData} margin={{ top: 20, right: 20, bottom: 20, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" />
                <YAxis tickFormatter={(value) => `${value}`}
                  label={{ value: 'Change', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip formatter={(value: number, _name, payload) => [`${value.toFixed(2)} ${payload.payload.unit}`, payload.payload.label]} />
                <Bar dataKey="value" fill="#1976d2" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default YieldBenchmarkChart;
