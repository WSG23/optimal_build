/**
 * Deal Score Card Component
 *
 * Displays AI-generated deal scoring with factor breakdown.
 */

import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  LinearProgress,
  Skeleton,
  Tooltip,
} from '@mui/material'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import TrendingDownIcon from '@mui/icons-material/TrendingDown'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'

import { Card } from '../canonical/Card'
import { scoreDeal, DealScoreResponse, FactorScore } from '../../api/ai'

interface DealScoreCardProps {
  dealId: string
  compact?: boolean
  onScoreLoaded?: (score: DealScoreResponse) => void
}

function getGradeColor(grade: string): string {
  const colors: Record<string, string> = {
    'A+': 'var(--ob-color-semantic-success)',
    A: 'var(--ob-color-semantic-success)',
    'A-': 'var(--ob-color-semantic-success)',
    'B+': 'var(--ob-color-neon-cyan)',
    B: 'var(--ob-color-neon-cyan)',
    'B-': 'var(--ob-color-neon-cyan)',
    'C+': 'var(--ob-color-semantic-warning)',
    C: 'var(--ob-color-semantic-warning)',
    'C-': 'var(--ob-color-semantic-warning)',
    D: 'var(--ob-color-semantic-error)',
    F: 'var(--ob-color-semantic-error)',
  }
  return colors[grade] || 'var(--ob-color-text-secondary)'
}

function getScoreColor(score: number): string {
  if (score >= 80) return 'var(--ob-color-semantic-success)'
  if (score >= 60) return 'var(--ob-color-neon-cyan)'
  if (score >= 40) return 'var(--ob-color-semantic-warning)'
  return 'var(--ob-color-semantic-error)'
}

function FactorScoreBar({ factor }: { factor: FactorScore }) {
  const color = getScoreColor(factor.score)

  return (
    <Box sx={{ mb: 'var(--ob-space-150)' }}>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
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
          {factor.factor.replace(/_/g, ' ')}
        </Typography>
        <Tooltip title={factor.rationale} placement="top">
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Typography variant="caption" sx={{ color, fontWeight: 600 }}>
              {factor.score.toFixed(0)}
            </Typography>
            <InfoOutlinedIcon
              sx={{ fontSize: 12, color: 'var(--ob-color-text-tertiary)' }}
            />
          </Box>
        </Tooltip>
      </Box>
      <LinearProgress
        variant="determinate"
        value={factor.score}
        sx={{
          height: 4,
          borderRadius: 'var(--ob-radius-xs)',
          backgroundColor: 'var(--ob-color-bg-elevated)',
          '& .MuiLinearProgress-bar': {
            backgroundColor: color,
            borderRadius: 'var(--ob-radius-xs)',
          },
        }}
      />
    </Box>
  )
}

export function DealScoreCard({
  dealId,
  compact = false,
  onScoreLoaded,
}: DealScoreCardProps) {
  const [score, setScore] = useState<DealScoreResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true

    async function loadScore() {
      try {
        setLoading(true)
        setError(null)
        const result = await scoreDeal(dealId)
        if (mounted) {
          setScore(result)
          onScoreLoaded?.(result)
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Failed to load score')
        }
      } finally {
        if (mounted) {
          setLoading(false)
        }
      }
    }

    loadScore()

    return () => {
      mounted = false
    }
  }, [dealId, onScoreLoaded])

  if (loading) {
    return (
      <Card variant="glass" sx={{ p: 'var(--ob-space-200)' }}>
        <Skeleton variant="circular" width={60} height={60} sx={{ mb: 2 }} />
        <Skeleton variant="text" width="60%" />
        <Skeleton variant="text" width="80%" />
        {!compact && (
          <>
            <Skeleton variant="rectangular" height={8} sx={{ mt: 2 }} />
            <Skeleton variant="rectangular" height={8} sx={{ mt: 1 }} />
            <Skeleton variant="rectangular" height={8} sx={{ mt: 1 }} />
          </>
        )}
      </Card>
    )
  }

  if (error) {
    return (
      <Card variant="ghost" sx={{ p: 'var(--ob-space-200)' }}>
        <Typography
          variant="body2"
          sx={{ color: 'var(--ob-color-semantic-error)' }}
        >
          {error}
        </Typography>
      </Card>
    )
  }

  if (!score) return null

  const gradeColor = getGradeColor(score.grade)
  const scoreColor = getScoreColor(score.overall_score)
  const isPositive = score.overall_score >= 60

  return (
    <Card variant="glass" hover="subtle" sx={{ p: 'var(--ob-space-200)' }}>
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          mb: 'var(--ob-space-200)',
        }}
      >
        <Box>
          <Typography
            variant="overline"
            sx={{ color: 'var(--ob-color-text-tertiary)', letterSpacing: 1.5 }}
          >
            AI Deal Score
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1 }}>
            <Typography
              variant="h3"
              sx={{
                color: scoreColor,
                fontWeight: 700,
                fontFamily: 'var(--ob-font-mono)',
              }}
            >
              {score.overall_score.toFixed(0)}
            </Typography>
            <Typography
              variant="body2"
              sx={{ color: 'var(--ob-color-text-tertiary)' }}
            >
              / 100
            </Typography>
          </Box>
        </Box>

        {/* Grade Badge */}
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: 'var(--ob-radius-sm)',
              border: `2px solid ${gradeColor}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: `${gradeColor}15`,
            }}
          >
            <Typography
              variant="h5"
              sx={{
                color: gradeColor,
                fontWeight: 700,
                fontFamily: 'var(--ob-font-mono)',
              }}
            >
              {score.grade}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
            {isPositive ? (
              <TrendingUpIcon
                sx={{ fontSize: 14, color: 'var(--ob-color-semantic-success)' }}
              />
            ) : (
              <TrendingDownIcon
                sx={{ fontSize: 14, color: 'var(--ob-color-semantic-error)' }}
              />
            )}
          </Box>
        </Box>
      </Box>

      {/* Confidence */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--ob-space-100)',
          mb: 'var(--ob-space-200)',
        }}
      >
        <Typography
          variant="caption"
          sx={{ color: 'var(--ob-color-text-tertiary)' }}
        >
          Confidence:
        </Typography>
        <LinearProgress
          variant="determinate"
          value={score.confidence * 100}
          sx={{
            flex: 1,
            height: 4,
            borderRadius: 'var(--ob-radius-xs)',
            backgroundColor: 'var(--ob-color-bg-elevated)',
            '& .MuiLinearProgress-bar': {
              backgroundColor: 'var(--ob-color-neon-cyan)',
            },
          }}
        />
        <Typography
          variant="caption"
          sx={{
            color: 'var(--ob-color-text-secondary)',
            fontFamily: 'var(--ob-font-mono)',
          }}
        >
          {(score.confidence * 100).toFixed(0)}%
        </Typography>
      </Box>

      {/* Factor Scores (if not compact) */}
      {!compact && score.factor_scores.length > 0 && (
        <Box sx={{ mb: 'var(--ob-space-200)' }}>
          <Typography
            variant="caption"
            sx={{
              color: 'var(--ob-color-text-tertiary)',
              display: 'block',
              mb: 'var(--ob-space-150)',
              textTransform: 'uppercase',
              letterSpacing: 1,
            }}
          >
            Factor Breakdown
          </Typography>
          {score.factor_scores.map((factor) => (
            <FactorScoreBar key={factor.factor} factor={factor} />
          ))}
        </Box>
      )}

      {/* Recommendation */}
      <Box
        sx={{
          p: 'var(--ob-space-150)',
          borderRadius: 'var(--ob-radius-xs)',
          background: 'var(--ob-color-bg-elevated)',
          borderLeft: `3px solid ${gradeColor}`,
        }}
      >
        <Typography
          variant="caption"
          sx={{
            color: 'var(--ob-color-text-tertiary)',
            display: 'block',
            mb: 'var(--ob-space-50)',
          }}
        >
          AI Recommendation
        </Typography>
        <Typography
          variant="body2"
          sx={{ color: 'var(--ob-color-text-primary)' }}
        >
          {score.recommendation}
        </Typography>
      </Box>
    </Card>
  )
}

export default DealScoreCard
