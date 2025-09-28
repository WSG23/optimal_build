import React from 'react';
import {
  Box,
  Paper,
  Typography,
  CircularProgress,
  Grid,
  Chip,
  LinearProgress
} from '@mui/material';
import { styled } from '@mui/material/styles';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat';
import { MarketCycle } from '../../../types/market';
import { PropertyType } from '../../../types/property';

interface MarketCycleIndicatorProps {
  cycleData?: MarketCycle;
  propertyType: PropertyType;
}

const CyclePhases = ['recovery', 'expansion', 'hyper_supply', 'recession'] as const;

const PhaseColors: Record<string, string> = {
  recovery: '#4caf50',
  expansion: '#2196f3',
  hyper_supply: '#ff9800',
  recession: '#f44336'
};

const CycleContainer = styled(Box)(({ theme }) => ({
  position: 'relative',
  width: 280,
  height: 280,
  margin: '0 auto',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center'
}));

const PhaseSegment = styled(Box)<{ phase: string; isActive: boolean }>(({ phase, isActive }) => ({
  position: 'absolute',
  width: '100%',
  height: '100%',
  borderRadius: '50%',
  border: `4px solid ${PhaseColors[phase]}`,
  opacity: isActive ? 1 : 0.3,
  transition: 'opacity 0.3s ease'
}));

const CenterInfo = styled(Box)(({ theme }) => ({
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
          <Typography color="textSecondary">
            No cycle data available
          </Typography>
        </Box>
      </Paper>
    );
  }

  const getPhaseDescription = (phase: string): string => {
    switch (phase) {
      case 'recovery':
        return 'Market recovering from bottom, opportunities emerging';
      case 'expansion':
        return 'Strong growth phase, increasing demand and prices';
      case 'hyper_supply':
        return 'Supply exceeding demand, price growth slowing';
      case 'recession':
        return 'Market correction phase, prices declining';
      default:
        return 'Market phase undefined';
    }
  };

  const getMomentumIcon = (momentum?: number) => {
    if (!momentum) return <TrendingFlatIcon />;
    if (momentum > 0.05) return <ArrowUpwardIcon color="success" />;
    if (momentum < -0.05) return <ArrowDownwardIcon color="error" />;
    return <TrendingFlatIcon />;
  };

  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

  return (
    <Paper sx={{ p: 3, height: 500 }}>
      <Typography variant="h6" gutterBottom>
        Market Cycle Position
      </Typography>

      <CycleContainer>
        <svg
          width="280"
          height="280"
          viewBox="0 0 280 280"
          style={{ position: 'absolute', transform: 'rotate(-90deg)' }}
        >
          {CyclePhases.map((phase, index) => {
            const isActive = cycleData.cycle_phase === phase;
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
            {cycleData.cycle_phase.replace(/_/g, ' ').toUpperCase()}
          </Typography>
          <Typography variant="body2" color="textSecondary">
            {cycleData.model_confidence && `${(cycleData.model_confidence * 100).toFixed(0)}% confidence`}
          </Typography>
        </CenterInfo>
      </CycleContainer>

      <Typography variant="body2" color="textSecondary" align="center" sx={{ mt: 2, mb: 3 }}>
        {getPhaseDescription(cycleData.cycle_phase)}
      </Typography>

      <Grid container spacing={2}>
        <Grid item xs={6}>
          <Box>
            <Box display="flex" alignItems="center" gap={1} mb={1}>
              <Typography variant="body2" color="textSecondary">
                Price Momentum
              </Typography>
              {getMomentumIcon(cycleData.price_momentum)}
            </Box>
            {cycleData.price_momentum !== undefined && (
              <Chip
                label={formatPercent(cycleData.price_momentum)}
                size="small"
                color={
                  cycleData.price_momentum > 0.05 ? 'success' :
                  cycleData.price_momentum < -0.05 ? 'error' : 'default'
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
              {getMomentumIcon(cycleData.rental_momentum)}
            </Box>
            {cycleData.rental_momentum !== undefined && (
              <Chip
                label={formatPercent(cycleData.rental_momentum)}
                size="small"
                color={
                  cycleData.rental_momentum > 0.05 ? 'success' :
                  cycleData.rental_momentum < -0.05 ? 'error' : 'default'
                }
              />
            )}
          </Box>
        </Grid>

        {cycleData.supply_demand_ratio !== undefined && (
          <Grid item xs={12}>
            <Box>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Supply/Demand Balance
              </Typography>
              <LinearProgress
                variant="determinate"
                value={Math.min(100, cycleData.supply_demand_ratio * 50)}
                sx={{ height: 8, borderRadius: 4 }}
                color={
                  cycleData.supply_demand_ratio > 1.2 ? 'error' :
                  cycleData.supply_demand_ratio < 0.8 ? 'success' : 'primary'
                }
              />
              <Box display="flex" justifyContent="space-between" mt={0.5}>
                <Typography variant="caption">Under Supply</Typography>
                <Typography variant="caption">Over Supply</Typography>
              </Box>
            </Box>
          </Grid>
        )}

        {cycleData.phase_duration_months && (
          <Grid item xs={12}>
            <Box display="flex" justifyContent="space-between">
              <Typography variant="body2" color="textSecondary">
                Phase Duration
              </Typography>
              <Typography variant="body2">
                {cycleData.phase_duration_months} months
              </Typography>
            </Box>
          </Grid>
        )}

        {cycleData.cycle_outlook && (
          <Grid item xs={12}>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Outlook
            </Typography>
            <Typography variant="body2">
              {cycleData.cycle_outlook}
            </Typography>
          </Grid>
        )}
      </Grid>
    </Paper>
  );
};

export default MarketCycleIndicator;