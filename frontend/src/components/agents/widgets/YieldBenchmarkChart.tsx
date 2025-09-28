import React, { useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  ToggleButton,
  ToggleButtonGroup
} from '@mui/material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  ComposedChart
} from 'recharts';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat';
import { YieldBenchmark } from '../../../types/market';
import { PropertyType } from '../../../types/property';
import { format, parseISO } from 'date-fns';

interface YieldBenchmarkChartProps {
  benchmarks: YieldBenchmark[];
  propertyType: PropertyType;
}

type ChartType = 'trend' | 'distribution' | 'comparison';

const YieldBenchmarkChart: React.FC<YieldBenchmarkChartProps> = ({
  benchmarks,
  propertyType
}) => {
  const [chartType, setChartType] = React.useState<ChartType>('trend');

  // Process data for trend chart
  const trendData = useMemo(() => {
    return benchmarks
      .sort((a, b) => new Date(a.benchmark_date).getTime() - new Date(b.benchmark_date).getTime())
      .map(benchmark => ({
        date: format(parseISO(benchmark.benchmark_date), 'MMM yy'),
        capRate: benchmark.cap_rate_median * 100,
        capRateMean: benchmark.cap_rate_mean ? benchmark.cap_rate_mean * 100 : undefined,
        rentalYield: benchmark.rental_yield_median ? benchmark.rental_yield_median * 100 : undefined,
        spread: benchmark.cap_rate_max && benchmark.cap_rate_min 
          ? (benchmark.cap_rate_max - benchmark.cap_rate_min) * 100 
          : undefined
      }));
  }, [benchmarks]);

  // Process data for distribution chart
  const distributionData = useMemo(() => {
    const latestBenchmarks = benchmarks
      .filter(b => b.district)
      .reduce((acc, benchmark) => {
        const district = benchmark.district!;
        if (!acc[district] || new Date(benchmark.benchmark_date) > new Date(acc[district].benchmark_date)) {
          acc[district] = benchmark;
        }
        return acc;
      }, {} as Record<string, YieldBenchmark>);

    return Object.entries(latestBenchmarks)
      .map(([district, benchmark]) => ({
        district,
        capRate: benchmark.cap_rate_median * 100,
        min: benchmark.cap_rate_min ? benchmark.cap_rate_min * 100 : undefined,
        max: benchmark.cap_rate_max ? benchmark.cap_rate_max * 100 : undefined,
        sampleSize: benchmark.sample_size
      }))
      .sort((a, b) => b.capRate - a.capRate);
  }, [benchmarks]);

  // Calculate statistics
  const statistics = useMemo(() => {
    if (benchmarks.length === 0) return null;

    const latestBenchmark = benchmarks
      .sort((a, b) => new Date(b.benchmark_date).getTime() - new Date(a.benchmark_date).getTime())[0];

    const previousBenchmark = benchmarks[1];
    
    let trend: 'up' | 'down' | 'flat' = 'flat';
    let changePercent = 0;
    
    if (previousBenchmark) {
      const change = latestBenchmark.cap_rate_median - previousBenchmark.cap_rate_median;
      changePercent = (change / previousBenchmark.cap_rate_median) * 100;
      
      if (Math.abs(changePercent) < 0.1) {
        trend = 'flat';
      } else {
        trend = change > 0 ? 'up' : 'down';
      }
    }

    return {
      currentCapRate: latestBenchmark.cap_rate_median * 100,
      currentRentalYield: latestBenchmark.rental_yield_median 
        ? latestBenchmark.rental_yield_median * 100 
        : null,
      trend,
      changePercent,
      date: latestBenchmark.benchmark_date
    };
  }, [benchmarks]);

  const getTrendIcon = (trend: 'up' | 'down' | 'flat') => {
    switch (trend) {
      case 'up':
        return <TrendingUpIcon color="error" />;
      case 'down':
        return <TrendingDownIcon color="success" />;
      default:
        return <TrendingFlatIcon color="action" />;
    }
  };

  const formatPercent = (value: number) => `${value.toFixed(2)}%`;

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <Paper sx={{ p: 1.5 }}>
          <Typography variant="body2" fontWeight="medium">
            {label}
          </Typography>
          {payload.map((entry: any, index: number) => (
            <Typography key={index} variant="body2" color={entry.color}>
              {entry.name}: {formatPercent(entry.value)}
            </Typography>
          ))}
        </Paper>
      );
    }
    return null;
  };

  return (
    <Box>
      {/* Statistics Cards */}
      {statistics && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={4}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Box>
                    <Typography color="textSecondary" gutterBottom variant="body2">
                      Current Cap Rate
                    </Typography>
                    <Typography variant="h5">
                      {formatPercent(statistics.currentCapRate)}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      {statistics.trend !== 'flat' && (
                        `${Math.abs(statistics.changePercent).toFixed(2)}% ${statistics.trend === 'up' ? 'increase' : 'decrease'}`
                      )}
                    </Typography>
                  </Box>
                  {getTrendIcon(statistics.trend)}
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          {statistics.currentRentalYield && (
            <Grid item xs={12} sm={6} md={4}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Current Rental Yield
                  </Typography>
                  <Typography variant="h5">
                    {formatPercent(statistics.currentRentalYield)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )}
          
          <Grid item xs={12} sm={6} md={4}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Yield Trend
                </Typography>
                <Chip
                  label={
                    statistics.trend === 'up' ? 'Expanding' :
                    statistics.trend === 'down' ? 'Compressing' :
                    'Stable'
                  }
                  color={
                    statistics.trend === 'up' ? 'error' :
                    statistics.trend === 'down' ? 'success' :
                    'default'
                  }
                  size="small"
                />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Chart Selection and Display */}
      <Paper sx={{ p: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h6">
            Yield Analysis
          </Typography>
          
          <ToggleButtonGroup
            value={chartType}
            exclusive
            onChange={(e, newType) => newType && setChartType(newType)}
            size="small"
          >
            <ToggleButton value="trend">
              Trend
            </ToggleButton>
            <ToggleButton value="distribution">
              Distribution
            </ToggleButton>
            <ToggleButton value="comparison">
              Comparison
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>

        <Box height={400}>
          {chartType === 'trend' && (
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={trendData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis tickFormatter={(value) => `${value}%`} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="spread"
                  fill="#8884d8"
                  fillOpacity={0.3}
                  stroke="none"
                  name="Spread"
                />
                <Line
                  type="monotone"
                  dataKey="capRate"
                  stroke="#8884d8"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  name="Cap Rate (Median)"
                />
                {trendData.some(d => d.capRateMean) && (
                  <Line
                    type="monotone"
                    dataKey="capRateMean"
                    stroke="#82ca9d"
                    strokeDasharray="5 5"
                    dot={false}
                    name="Cap Rate (Mean)"
                  />
                )}
                {trendData.some(d => d.rentalYield) && (
                  <Line
                    type="monotone"
                    dataKey="rentalYield"
                    stroke="#ffc658"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    name="Rental Yield"
                  />
                )}
              </ComposedChart>
            </ResponsiveContainer>
          )}

          {chartType === 'distribution' && (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={distributionData} margin={{ top: 5, right: 30, left: 20, bottom: 50 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="district" 
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis tickFormatter={(value) => `${value}%`} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="capRate" fill="#8884d8" name="Cap Rate" />
              </BarChart>
            </ResponsiveContainer>
          )}

          {chartType === 'comparison' && (
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="capRate" 
                  name="Cap Rate"
                  tickFormatter={(value) => `${value}%`}
                />
                <YAxis 
                  dataKey="sampleSize" 
                  name="Sample Size"
                />
                <Tooltip 
                  cursor={{ strokeDasharray: '3 3' }}
                  content={<CustomTooltip />}
                />
                <Scatter 
                  name="Districts" 
                  data={distributionData} 
                  fill="#8884d8"
                />
              </ScatterChart>
            </ResponsiveContainer>
          )}
        </Box>
      </Paper>
    </Box>
  );
};

export default YieldBenchmarkChart;