/**
 * Compliance Summary Cards
 *
 * Three summary cards for the compliance timeline: overall progress,
 * completed steps, and estimated total duration.
 * Extracted from CompliancePathTimeline for component size management.
 */

import React from 'react'
import { Box, LinearProgress } from '@mui/material'
import { Card } from '../../../../components/canonical/Card'

export interface ComplianceSummaryCardsProps {
  overallProgress: number
  completedSteps: number
  totalSteps: number
  totalDuration: number
}

export const ComplianceSummaryCards: React.FC<ComplianceSummaryCardsProps> = ({
  overallProgress,
  completedSteps,
  totalSteps,
  totalDuration,
}) => {
  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' },
        gap: 'var(--ob-space-150)',
        mb: 'var(--ob-space-200)',
      }}
    >
      <Card
        variant="default"
        sx={{
          p: 'var(--ob-space-150)',
          background:
            'linear-gradient(135deg, var(--ob-brand-700) 0%, var(--ob-brand-400) 100%)',
        }}
      >
        <Box
          component="span"
          sx={{
            fontSize: 'var(--ob-font-size-xs)',
            color: 'var(--ob-neutral-200)',
            display: 'block',
          }}
        >
          Overall Progress
        </Box>
        <Box
          component="span"
          sx={{
            fontSize: 'var(--ob-font-size-3xl)',
            fontWeight: 700,
            color: 'var(--ob-neutral-50)',
            display: 'block',
          }}
        >
          {overallProgress}%
        </Box>
        <LinearProgress
          variant="determinate"
          value={overallProgress}
          sx={{
            mt: 'var(--ob-space-075)',
            bgcolor: 'rgba(255 255 255 / 0.3)',
            borderRadius: 'var(--ob-radius-xs)',
            height: 4,
            '& .MuiLinearProgress-bar': {
              bgcolor: 'var(--ob-neutral-50)',
              borderRadius: 'var(--ob-radius-xs)',
            },
          }}
        />
      </Card>

      <Card
        variant="default"
        sx={{
          p: 'var(--ob-space-150)',
          background:
            'linear-gradient(135deg, var(--ob-success-700) 0%, var(--ob-success-400) 100%)',
        }}
      >
        <Box
          component="span"
          sx={{
            fontSize: 'var(--ob-font-size-xs)',
            color: 'var(--ob-neutral-200)',
            display: 'block',
          }}
        >
          Completed Steps
        </Box>
        <Box
          component="span"
          sx={{
            fontSize: 'var(--ob-font-size-3xl)',
            fontWeight: 700,
            color: 'var(--ob-neutral-50)',
            display: 'block',
          }}
        >
          {completedSteps}/{totalSteps}
        </Box>
      </Card>

      <Card
        variant="default"
        sx={{
          p: 'var(--ob-space-150)',
          background:
            'linear-gradient(135deg, var(--ob-info-700) 0%, var(--ob-info-400) 100%)',
        }}
      >
        <Box
          component="span"
          sx={{
            fontSize: 'var(--ob-font-size-xs)',
            color: 'var(--ob-neutral-200)',
            display: 'block',
          }}
        >
          Est. Total Duration
        </Box>
        <Box
          component="span"
          sx={{
            fontSize: 'var(--ob-font-size-3xl)',
            fontWeight: 700,
            color: 'var(--ob-neutral-50)',
            display: 'block',
          }}
        >
          {totalDuration} days
        </Box>
      </Card>
    </Box>
  )
}
