/**
 * AI Insights Panel Component
 *
 * A sidebar panel showing AI-generated insights, alerts, and recommendations.
 */

import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  IconButton,
  Collapse,
  Chip,
  Skeleton,
  Divider,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import ExpandLessIcon from '@mui/icons-material/ExpandLess'
import WarningAmberIcon from '@mui/icons-material/WarningAmber'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import LightbulbIcon from '@mui/icons-material/Lightbulb'
import RefreshIcon from '@mui/icons-material/Refresh'

import { Card } from '../canonical/Card'
import {
  detectAnomalies,
  AnomalyAlert,
  predictMarket,
  MarketPredictionResponse,
} from '../../api/ai'

interface AIInsightsPanelProps {
  dealId?: string
  propertyId?: string
  projectId?: string
  district?: string
  showMarketInsights?: boolean
  showAnomalies?: boolean
}

function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    critical: 'var(--ob-color-semantic-error)',
    high: 'var(--ob-color-semantic-warning)',
    medium: 'var(--ob-color-neon-cyan)',
    low: 'var(--ob-color-text-secondary)',
  }
  return colors[severity] || 'var(--ob-color-text-secondary)'
}

function AnomalyAlertItem({ alert }: { alert: AnomalyAlert }) {
  const [expanded, setExpanded] = useState(false)
  const color = getSeverityColor(alert.severity)

  return (
    <Box
      sx={{
        p: 'var(--ob-space-150)',
        borderRadius: 'var(--ob-radius-xs)',
        background: 'var(--ob-color-bg-elevated)',
        borderLeft: `3px solid ${color}`,
        mb: 'var(--ob-space-100)',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          cursor: 'pointer',
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <Box sx={{ display: 'flex', gap: 'var(--ob-space-100)' }}>
          <WarningAmberIcon sx={{ color, fontSize: 18, mt: 0.25 }} />
          <Box>
            <Typography
              variant="body2"
              sx={{ color: 'var(--ob-color-text-primary)', fontWeight: 500 }}
            >
              {alert.title}
            </Typography>
            <Chip
              label={alert.severity}
              size="small"
              sx={{
                mt: 0.5,
                height: 18,
                fontSize: '0.65rem',
                backgroundColor: `${color}20`,
                color,
                borderColor: color,
              }}
              variant="outlined"
            />
          </Box>
        </Box>
        <IconButton size="small">
          {expanded ? (
            <ExpandLessIcon fontSize="small" />
          ) : (
            <ExpandMoreIcon fontSize="small" />
          )}
        </IconButton>
      </Box>

      <Collapse in={expanded}>
        <Box sx={{ mt: 'var(--ob-space-150)', pl: 'var(--ob-space-400)' }}>
          <Typography
            variant="caption"
            sx={{ color: 'var(--ob-color-text-secondary)', display: 'block' }}
          >
            {alert.description}
          </Typography>
          <Box
            sx={{
              mt: 'var(--ob-space-100)',
              p: 'var(--ob-space-100)',
              borderRadius: 'var(--ob-radius-xs)',
              background: 'var(--ob-surface-glass-1)',
            }}
          >
            <Typography
              variant="caption"
              sx={{ color: 'var(--ob-color-neon-cyan)', fontWeight: 500 }}
            >
              Recommendation:
            </Typography>
            <Typography
              variant="caption"
              sx={{ color: 'var(--ob-color-text-primary)', display: 'block' }}
            >
              {alert.recommendation}
            </Typography>
          </Box>
        </Box>
      </Collapse>
    </Box>
  )
}

function MarketInsightItem({
  prediction,
}: {
  prediction: MarketPredictionResponse
}) {
  const [expanded, setExpanded] = useState(true)

  return (
    <Box sx={{ mb: 'var(--ob-space-200)' }}>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          mb: 'var(--ob-space-100)',
          cursor: 'pointer',
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--ob-space-100)',
          }}
        >
          <TrendingUpIcon
            sx={{ color: 'var(--ob-color-neon-cyan)', fontSize: 18 }}
          />
          <Typography
            variant="body2"
            sx={{ color: 'var(--ob-color-text-primary)', fontWeight: 500 }}
          >
            Market Outlook
          </Typography>
        </Box>
        <IconButton size="small">
          {expanded ? (
            <ExpandLessIcon fontSize="small" />
          ) : (
            <ExpandMoreIcon fontSize="small" />
          )}
        </IconButton>
      </Box>

      <Collapse in={expanded}>
        {prediction.predictions.map((item, idx) => (
          <Box
            key={idx}
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              p: 'var(--ob-space-100)',
              borderRadius: 'var(--ob-radius-xs)',
              background: 'var(--ob-color-bg-elevated)',
              mb: 'var(--ob-space-50)',
            }}
          >
            <Typography
              variant="caption"
              sx={{
                color: 'var(--ob-color-text-secondary)',
                textTransform: 'capitalize',
              }}
            >
              {item.prediction_type.replace(/_/g, ' ')}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              {item.change_percentage !== null && (
                <Typography
                  variant="caption"
                  sx={{
                    color:
                      item.change_percentage >= 0
                        ? 'var(--ob-color-semantic-success)'
                        : 'var(--ob-color-semantic-error)',
                    fontWeight: 600,
                    fontFamily: 'var(--ob-font-mono)',
                  }}
                >
                  {item.change_percentage >= 0 ? '+' : ''}
                  {item.change_percentage.toFixed(1)}%
                </Typography>
              )}
              <Chip
                label={`${(item.confidence * 100).toFixed(0)}%`}
                size="small"
                sx={{
                  height: 16,
                  fontSize: '0.6rem',
                  ml: 0.5,
                }}
              />
            </Box>
          </Box>
        ))}

        <Box
          sx={{
            mt: 'var(--ob-space-150)',
            p: 'var(--ob-space-100)',
            borderRadius: 'var(--ob-radius-xs)',
            background: 'var(--ob-surface-glass-1)',
          }}
        >
          <Typography
            variant="caption"
            sx={{ color: 'var(--ob-color-text-secondary)' }}
          >
            {prediction.summary}
          </Typography>
        </Box>
      </Collapse>
    </Box>
  )
}

export function AIInsightsPanel({
  dealId,
  propertyId,
  projectId,
  district,
  showMarketInsights = true,
  showAnomalies = true,
}: AIInsightsPanelProps) {
  const [anomalies, setAnomalies] = useState<AnomalyAlert[]>([])
  const [marketPrediction, setMarketPrediction] =
    useState<MarketPredictionResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const loadInsights = async () => {
    setLoading(true)
    try {
      const promises: Promise<unknown>[] = []

      if (showAnomalies && (dealId || propertyId || projectId)) {
        promises.push(
          detectAnomalies({
            deal_id: dealId,
            property_id: propertyId,
            project_id: projectId,
          }).then((result) => setAnomalies(result.alerts)),
        )
      }

      if (showMarketInsights && (district || propertyId)) {
        promises.push(
          predictMarket({
            property_id: propertyId,
            district,
            forecast_months: 12,
          }).then((result) => setMarketPrediction(result)),
        )
      }

      await Promise.all(promises)
    } catch (error) {
      console.error('Failed to load AI insights:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadInsights()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dealId, propertyId, projectId, district])

  const handleRefresh = async () => {
    setRefreshing(true)
    await loadInsights()
    setRefreshing(false)
  }

  if (loading) {
    return (
      <Card variant="glass" sx={{ p: 'var(--ob-space-200)' }}>
        <Skeleton variant="text" width="60%" />
        <Skeleton variant="rectangular" height={60} sx={{ mt: 1 }} />
        <Skeleton variant="rectangular" height={60} sx={{ mt: 1 }} />
        <Skeleton variant="text" width="40%" sx={{ mt: 2 }} />
      </Card>
    )
  }

  const hasContent = anomalies.length > 0 || marketPrediction !== null

  if (!hasContent) {
    return (
      <Card variant="ghost" sx={{ p: 'var(--ob-space-200)' }}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            py: 'var(--ob-space-400)',
            color: 'var(--ob-color-text-tertiary)',
          }}
        >
          <LightbulbIcon sx={{ fontSize: 32, mb: 1, opacity: 0.5 }} />
          <Typography variant="body2">No insights available</Typography>
        </Box>
      </Card>
    )
  }

  return (
    <Card variant="glass" sx={{ p: 'var(--ob-space-200)' }}>
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          mb: 'var(--ob-space-200)',
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--ob-space-100)',
          }}
        >
          <LightbulbIcon
            sx={{ color: 'var(--ob-color-neon-cyan)', fontSize: 20 }}
          />
          <Typography
            variant="subtitle2"
            sx={{ color: 'var(--ob-color-text-primary)', fontWeight: 600 }}
          >
            AI Insights
          </Typography>
        </Box>
        <IconButton
          size="small"
          onClick={handleRefresh}
          disabled={refreshing}
          sx={{ color: 'var(--ob-color-text-secondary)' }}
        >
          <RefreshIcon
            fontSize="small"
            sx={{
              animation: refreshing ? 'spin 1s linear infinite' : 'none',
              '@keyframes spin': {
                '0%': { transform: 'rotate(0deg)' },
                '100%': { transform: 'rotate(360deg)' },
              },
            }}
          />
        </IconButton>
      </Box>

      {/* Anomalies */}
      {showAnomalies && anomalies.length > 0 && (
        <Box sx={{ mb: 'var(--ob-space-200)' }}>
          <Typography
            variant="caption"
            sx={{
              color: 'var(--ob-color-text-tertiary)',
              textTransform: 'uppercase',
              letterSpacing: 1,
              display: 'block',
              mb: 'var(--ob-space-100)',
            }}
          >
            Alerts ({anomalies.length})
          </Typography>
          {anomalies.map((alert) => (
            <AnomalyAlertItem key={alert.id} alert={alert} />
          ))}
        </Box>
      )}

      {showAnomalies &&
        anomalies.length > 0 &&
        showMarketInsights &&
        marketPrediction && (
          <Divider
            sx={{
              my: 'var(--ob-space-200)',
              borderColor: 'var(--ob-color-border-subtle)',
            }}
          />
        )}

      {/* Market Insights */}
      {showMarketInsights && marketPrediction && (
        <MarketInsightItem prediction={marketPrediction} />
      )}
    </Card>
  )
}

export default AIInsightsPanel
