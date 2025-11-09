import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Chip,
  LinearProgress
} from '@mui/material';
import { styled } from '@mui/material/styles';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat';
import { MarketCyclePosition } from '../../../types/market';
import { PropertyType } from '../../../types/property';

interface MarketCycleIndicatorProps {
  cycleData?: MarketCyclePosition | null;
  propertyType: PropertyType;
}

const CyclePhases = ['recovery', 'expansion', 'hyper_supply', 'recession'] as const;

const PhaseColors: Record<string, string> = {
  recovery: '#4caf50',
  expansion: '#2196f3',
  hyper_supply: '#ff9800',
  recession: '#f44336'
};

const CycleContainer = styled(Box)(() => ({
  position: 'relative',
  width: 280,
  height: 280,
  margin: '0 auto',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center'
}));

const CenterInfo = styled(Box)(() => ({
  textAlign: 'center',
  position: 'relative',
  zIndex: 2
}));

const MarketCycleIndicator: React.FC<MarketCycleIndicatorProps> = ({
  cycleData,
  propertyType
}) => {
  if (!cycleData) {
    return (
      <Paper sx={{ p: 3, height: 500 }}>
        <Typography variant="h6" gutterBottom>
          Market Cycle Position
        </Typography>
        <Box display="flex" justifyContent="center" alignItems="center" height={400}>
          <Typography color="textSecondary">No cycle data available</Typography>
        </Box>
      </Paper>
    );
  }

  const formatPercent = (value?: number | null, decimals: number = 1) => {
    if (value === undefined || value === null || Number.isNaN(value)) return '—';
    const percentValue = Math.abs(value) <= 1 ? value * 100 : value;
    return `${percentValue.toFixed(decimals)}%`;
  };

  const getMomentumIcon = (momentum?: number | null) => {
    if (momentum === undefined || momentum === null || Number.isNaN(momentum)) {
      return <TrendingFlatIcon />;
    }
    if (momentum > 0.05) return <ArrowUpwardIcon color="success" />;
    if (momentum < -0.05) return <ArrowDownwardIcon color="error" />;
    return <TrendingFlatIcon />;
  };

  return (
    <Paper sx={{ p: 3, height: 500 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6" gutterBottom>
          Market Cycle Position
        </Typography>
        <Typography variant="caption" color="textSecondary">
          {propertyType.replace(/_/g, ' ').toUpperCase()}
        </Typography>
      </Box>

      <CycleContainer>
        <svg
          width="280"
          height="280"
          viewBox="0 0 280 280"
          style={{ position: 'absolute', transform: 'rotate(-90deg)' }}
        >
          {CyclePhases.map((phase, index) => {
            const isActive = cycleData.current_phase === phase;
            const startAngle = (index * 90) * Math.PI / 180;
            const endAngle = ((index + 1) * 90) * Math.PI / 180;
            const radius = 130;
            const centerX = 140;
            const centerY = 140;

            const x1 = centerX + radius * Math.cos(startAngle);
            const y1 = centerY + radius * Math.sin(startAngle);
            const x2 = centerX + radius * Math.cos(endAngle);
            const y2 = centerY + radius * Math.sin(endAngle);

            const path = `
              M ${centerX} ${centerY}
              L ${x1} ${y1}
              A ${radius} ${radius} 0 0 1 ${x2} ${y2}
              Z
            `;

            return (
              <path
                key={phase}
                d={path}
                fill={PhaseColors[phase]}
                opacity={isActive ? 1 : 0.2}
                stroke="white"
                strokeWidth="2"
              />
            );
          })}
        </svg>

        <CenterInfo>
          <Typography variant="h5" fontWeight="bold" color="primary">
            {cycleData.current_phase.replace(/_/g, ' ').toUpperCase()}
          </Typography>
          <Typography variant="body2" color="textSecondary">
            {cycleData.phase_strength !== undefined
              ? `${formatPercent(cycleData.phase_strength)} confidence`
              : 'Confidence N/A'}
          </Typography>
        </CenterInfo>
      </CycleContainer>

      <Typography variant="body2" color="textSecondary" align="center" sx={{ mt: 2, mb: 3 }}>
        {cycleData.outlook?.next_12_months ?? 'No outlook available'}
      </Typography>

      <Grid container spacing={2}>
        <Grid item xs={6}>
          <Box>
            <Box display="flex" alignItems="center" gap={1} mb={1}>
              <Typography variant="body2" color="textSecondary">
                Price Momentum
              </Typography>
              {getMomentumIcon(cycleData.indicators.price_momentum)}
            </Box>
            {cycleData.indicators.price_momentum != null && (
              <Chip
                label={formatPercent(cycleData.indicators.price_momentum)}
                size="small"
                color={
                  cycleData.indicators.price_momentum > 0.05
                    ? 'success'
                    : cycleData.indicators.price_momentum < -0.05
                      ? 'error'
                      : 'default'
                }
              />
            )}
          </Box>
        </Grid>

        <Grid item xs={6}>
          <Box>
            <Box display="flex" alignItems="center" gap={1} mb={1}>
              <Typography variant="body2" color="textSecondary">
                Rental Momentum
              </Typography>
              {getMomentumIcon(cycleData.indicators.rental_momentum)}
            </Box>
            {cycleData.indicators.rental_momentum != null && (
              <Chip
                label={formatPercent(cycleData.indicators.rental_momentum)}
                size="small"
                color={
                  cycleData.indicators.rental_momentum > 0.05
                    ? 'success'
                    : cycleData.indicators.rental_momentum < -0.05
                      ? 'error'
                      : 'default'
                }
              />
            )}
          </Box>
        </Grid>

        {cycleData.indicators.supply_demand_ratio != null && (
          <Grid item xs={12}>
            <Box>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Supply / Demand Balance
              </Typography>
              <LinearProgress
                variant="determinate"
                value={Math.min(100, cycleData.indicators.supply_demand_ratio * 50)}
                sx={{ height: 8, borderRadius: 4 }}
                color={
                  cycleData.indicators.supply_demand_ratio > 1.2
                    ? 'error'
                    : cycleData.indicators.supply_demand_ratio < 0.8
                      ? 'success'
                      : 'primary'
                }
              />
              <Box display="flex" justifyContent="space-between" mt={0.5}>
                <Typography variant="caption">Under supply</Typography>
                <Typography variant="caption">Oversupply</Typography>
              </Box>
            </Box>
          </Grid>
        )}

        {cycleData.index_trends && (
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
                Index Trends
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Current index: {cycleData.index_trends.current_index?.toFixed(1) ?? '—'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                MoM: {formatPercent(cycleData.index_trends.mom_change, 1)} • QoQ: {formatPercent(cycleData.index_trends.qoq_change, 1)} • YoY: {formatPercent(cycleData.index_trends.yoy_change, 1)}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Trend: {cycleData.index_trends.trend ?? 'n/a'}
              </Typography>
            </Paper>
          </Grid>
        )}

        {cycleData.outlook && (
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
                Outlook Drivers
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Pipeline impact: {formatPercent(cycleData.outlook.pipeline_impact, 1)}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Demand forecast: {formatPercent(cycleData.outlook.demand_forecast, 1)}
              </Typography>
            </Paper>
          </Grid>
        )}
      </Grid>
    </Paper>
  );
};

export default MarketCycleIndicator;
