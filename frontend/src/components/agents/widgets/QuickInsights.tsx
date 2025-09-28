import React from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Alert
} from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import InfoIcon from '@mui/icons-material/Info';
import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { MarketReport } from '../../../types/market';

interface QuickInsightsProps {
  marketReport: MarketReport;
}

const QuickInsights: React.FC<QuickInsightsProps> = ({ marketReport }) => {
  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'bullish':
        return 'success';
      case 'bearish':
        return 'error';
      default:
        return 'default';
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'bullish':
        return <TrendingUpIcon />;
      case 'bearish':
        return <TrendingDownIcon />;
      default:
        return <InfoIcon />;
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-SG', {
      style: 'currency',
      currency: 'SGD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('en-SG', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPercent = (value: number) => {
    const sign = value > 0 ? '+' : '';
    return `${sign}${value.toFixed(1)}%`;
  };

  const { executive_summary } = marketReport;

  return (
    <Box sx={{ mb: 3 }}>
      {/* Market Sentiment Alert */}
      <Alert 
        severity={getSentimentColor(executive_summary.market_sentiment) as any}
        icon={getSentimentIcon(executive_summary.market_sentiment)}
        sx={{ mb: 2 }}
      >
        <Typography variant="subtitle1" fontWeight="medium">
          Market Sentiment: {executive_summary.market_sentiment.toUpperCase()}
        </Typography>
      </Alert>

      {/* Key Metrics Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={2}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Avg Price PSF
            </Typography>
            <Typography variant="h6">
              ${formatNumber(executive_summary.key_metrics.avg_price_psf)}
            </Typography>
            {executive_summary.key_metrics.yoy_price_change !== 0 && (
              <Chip
                size="small"
                label={formatPercent(executive_summary.key_metrics.yoy_price_change)}
                color={executive_summary.key_metrics.yoy_price_change > 0 ? 'success' : 'error'}
                sx={{ mt: 1 }}
              />
            )}
          </Paper>
        </Grid>
        
        <Grid item xs={12} sm={6} md={2}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Cap Rate
            </Typography>
            <Typography variant="h6">
              {(executive_summary.key_metrics.median_cap_rate * 100).toFixed(2)}%
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} sm={6} md={2}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Transaction Vol
            </Typography>
            <Typography variant="h6">
              {formatCurrency(executive_summary.key_metrics.total_transaction_volume)}
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} sm={6} md={2}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Vacancy Rate
            </Typography>
            <Typography variant="h6">
              {(executive_summary.key_metrics.vacancy_rate * 100).toFixed(1)}%
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} sm={6} md={2}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              New Supply
            </Typography>
            <Typography variant="h6">
              {formatNumber(executive_summary.key_metrics.new_supply_sqm)} sqm
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} sm={6} md={2}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Report Period
            </Typography>
            <Typography variant="h6">
              {marketReport.period_months} months
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Key Findings and Recommendations */}
      <Grid container spacing={2}>
        {executive_summary.key_findings.length > 0 && (
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, height: '100%' }}>
              <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
                Key Findings
              </Typography>
              <List dense>
                {executive_summary.key_findings.slice(0, 5).map((finding, index) => (
                  <ListItem key={index}>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <CheckCircleIcon color="primary" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={finding} />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>
        )}
        
        {marketReport.recommendations.length > 0 && (
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, height: '100%' }}>
              <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
                Recommendations
              </Typography>
              <List dense>
                {marketReport.recommendations.slice(0, 5).map((recommendation, index) => (
                  <ListItem key={index}>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <WarningIcon color="warning" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={recommendation} />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default QuickInsights;