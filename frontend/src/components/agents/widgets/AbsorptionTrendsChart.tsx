import React, { useMemo, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  ToggleButton,
  ToggleButtonGroup,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  ComposedChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import SpeedIcon from '@mui/icons-material/Speed';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import InventoryIcon from '@mui/icons-material/Inventory';
import { AbsorptionData } from '../../../types/market';
import { PropertyType } from '../../../types/property';
import { format, parseISO } from 'date-fns';

interface AbsorptionTrendsChartProps {
  absorptionData: AbsorptionData[];
  propertyType: PropertyType;
}

type ChartType = 'absorption' | 'velocity' | 'inventory';
type MetricType = 'sales' | 'leasing' | 'both';

const AbsorptionTrendsChart: React.FC<AbsorptionTrendsChartProps> = ({
  absorptionData,
  propertyType
}) => {
  const [chartType, setChartType] = useState<ChartType>('absorption');
  const [metricType, setMetricType] = useState<MetricType>('both');

  // Process data for charts
  const chartData = useMemo(() => {
    return absorptionData
      .sort((a, b) => new Date(a.tracking_date).getTime() - new Date(b.tracking_date).getTime())
      .map(data => ({
        date: format(parseISO(data.tracking_date), 'MMM yy'),
        salesAbsorption: data.sales_absorption_rate ? data.sales_absorption_rate * 100 : null,
        leasingAbsorption: data.leasing_absorption_rate ? data.leasing_absorption_rate * 100 : null,
        unitsSoldPeriod: data.units_sold_period || 0,
        unitsLaunched: data.units_launched || 0,
        nlLeasedPeriod: data.nla_leased_period || 0,
        velocityTrend: data.velocity_trend || 'stable'
      }));
  }, [absorptionData]);

  // Calculate statistics
  const statistics = useMemo(() => {
    if (absorptionData.length === 0) return null;

    const latestData = absorptionData[absorptionData.length - 1];
    const salesRates = absorptionData
      .filter(d => d.sales_absorption_rate)
      .map(d => d.sales_absorption_rate!);
    const leasingRates = absorptionData
      .filter(d => d.leasing_absorption_rate)
      .map(d => d.leasing_absorption_rate!);

    const avgSalesAbsorption = salesRates.length > 0
      ? salesRates.reduce((a, b) => a + b, 0) / salesRates.length
      : null;
    const avgLeasingAbsorption = leasingRates.length > 0
      ? leasingRates.reduce((a, b) => a + b, 0) / leasingRates.length
      : null;

    const totalUnitsSold = absorptionData.reduce((sum, d) => sum + (d.units_sold_period || 0), 0);
    const totalAreaLeased = absorptionData.reduce((sum, d) => sum + (d.nla_leased_period || 0), 0);

    return {
      currentSalesAbsorption: latestData.sales_absorption_rate 
        ? latestData.sales_absorption_rate * 100 
        : null,
      currentLeasingAbsorption: latestData.leasing_absorption_rate
        ? latestData.leasing_absorption_rate * 100
        : null,
      avgSalesAbsorption: avgSalesAbsorption ? avgSalesAbsorption * 100 : null,
      avgLeasingAbsorption: avgLeasingAbsorption ? avgLeasingAbsorption * 100 : null,
      totalUnitsSold,
      totalAreaLeased,
      velocityTrend: latestData.velocity_trend || 'stable'
    };
  }, [absorptionData]);

  const getVelocityColor = (trend: string) => {
    switch (trend) {
      case 'accelerating':
        return 'success';
      case 'decelerating':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatPercent = (value: number) => `${value.toFixed(1)}%`;
  const formatNumber = (value: number) => 
    new Intl.NumberFormat('en-SG', { maximumFractionDigits: 0 }).format(value);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <Paper sx={{ p: 1.5 }}>
          <Typography variant="body2" fontWeight="medium" gutterBottom>
            {label}
          </Typography>
          {payload.map((entry: any, index: number) => (
            <Typography key={index} variant="body2" color={entry.color}>
              {entry.name}: {
                entry.name.includes('Absorption') || entry.name.includes('Rate')
                  ? formatPercent(entry.value)
                  : formatNumber(entry.value)
              }
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
          {statistics.currentSalesAbsorption !== null && (
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Sales Absorption
                  </Typography>
                  <Typography variant="h5">
                    {formatPercent(statistics.currentSalesAbsorption)}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Avg: {statistics.avgSalesAbsorption 
                      ? formatPercent(statistics.avgSalesAbsorption)
                      : 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )}
          
          {statistics.currentLeasingAbsorption !== null && (
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Leasing Absorption
                  </Typography>
                  <Typography variant="h5">
                    {formatPercent(statistics.currentLeasingAbsorption)}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Avg: {statistics.avgLeasingAbsorption 
                      ? formatPercent(statistics.avgLeasingAbsorption)
                      : 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )}
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Box>
                    <Typography color="textSecondary" gutterBottom variant="body2">
                      Velocity Trend
                    </Typography>
                    <Chip
                      icon={<SpeedIcon />}
                      label={statistics.velocityTrend.charAt(0).toUpperCase() + 
                             statistics.velocityTrend.slice(1)}
                      color={getVelocityColor(statistics.velocityTrend) as any}
                      size="small"
                    />
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Total Activity
                </Typography>
                <Typography variant="body2">
                  {statistics.totalUnitsSold > 0 && `${formatNumber(statistics.totalUnitsSold)} units sold`}
                  {statistics.totalUnitsSold > 0 && statistics.totalAreaLeased > 0 && ' • '}
                  {statistics.totalAreaLeased > 0 && `${formatNumber(statistics.totalAreaLeased)} sqm leased`}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Chart Controls and Display */}
      <Paper sx={{ p: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h6">
            Absorption Analysis
          </Typography>
          
          <Box display="flex" gap={2} alignItems="center">
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Metric</InputLabel>
              <Select
                value={metricType}
                label="Metric"
                onChange={(e) => setMetricType(e.target.value as MetricType)}
              >
                <MenuItem value="both">Both</MenuItem>
                <MenuItem value="sales">Sales Only</MenuItem>
                <MenuItem value="leasing">Leasing Only</MenuItem>
              </Select>
            </FormControl>
            
            <ToggleButtonGroup
              value={chartType}
              exclusive
              onChange={(e, newType) => newType && setChartType(newType)}
              size="small"
            >
              <ToggleButton value="absorption">
                Absorption
              </ToggleButton>
              <ToggleButton value="velocity">
                Velocity
              </ToggleButton>
              <ToggleButton value="inventory">
                Inventory
              </ToggleButton>
            </ToggleButtonGroup>
          </Box>
        </Box>

        <Box height={400}>
          {chartType === 'absorption' && (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis tickFormatter={(value) => `${value}%`} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                
                {/* Reference lines for benchmarks */}
                {statistics?.avgSalesAbsorption && metricType !== 'leasing' && (
                  <ReferenceLine 
                    y={statistics.avgSalesAbsorption} 
                    stroke="#8884d8"
                    strokeDasharray="3 3"
                    label="Avg Sales"
                  />
                )}
                {statistics?.avgLeasingAbsorption && metricType !== 'sales' && (
                  <ReferenceLine 
                    y={statistics.avgLeasingAbsorption} 
                    stroke="#82ca9d"
                    strokeDasharray="3 3"
                    label="Avg Leasing"
                  />
                )}
                
                {metricType !== 'leasing' && (
                  <Line
                    type="monotone"
                    dataKey="salesAbsorption"
                    stroke="#8884d8"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    name="Sales Absorption Rate"
                    connectNulls
                  />
                )}
                {metricType !== 'sales' && (
                  <Line
                    type="monotone"
                    dataKey="leasingAbsorption"
                    stroke="#82ca9d"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    name="Leasing Absorption Rate"
                    connectNulls
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          )}

          {chartType === 'velocity' && (
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" tickFormatter={(value) => `${value}%`} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                
                {metricType !== 'leasing' && (
                  <Bar
                    yAxisId="left"
                    dataKey="unitsSoldPeriod"
                    fill="#8884d8"
                    name="Units Sold"
                  />
                )}
                {metricType !== 'sales' && (
                  <Bar
                    yAxisId="left"
                    dataKey="nlLeasedPeriod"
                    fill="#82ca9d"
                    name="Area Leased (sqm)"
                  />
                )}
                {metricType !== 'leasing' && (
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="salesAbsorption"
                    stroke="#ff7300"
                    strokeWidth={2}
                    name="Sales Rate"
                    connectNulls
                  />
                )}
              </ComposedChart>
            </ResponsiveContainer>
          )}

          {chartType === 'inventory' && (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                
                <Area
                  type="monotone"
                  dataKey="unitsLaunched"
                  stackId="1"
                  fill="#8884d8"
                  fillOpacity={0.6}
                  name="Units Launched"
                />
                <Area
                  type="monotone"
                  dataKey="unitsSoldPeriod"
                  stackId="2"
                  fill="#82ca9d"
                  fillOpacity={0.6}
                  name="Units Sold"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </Box>
      </Paper>
    </Box>
  );
};

export default AbsorptionTrendsChart;