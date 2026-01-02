/**
 * AI Insight Panel Component
 *
 * Displays AI-generated insights in a callout box styled per UX_ARCHITECTURE.md:
 * - Indigo left border (info color)
 * - Subtle background
 * - AI INSIGHT label
 *
 * Follows AI Studio's compact insight pattern.
 */

import { Box, Typography } from '@mui/material'
import LightbulbIcon from '@mui/icons-material/Lightbulb'

// ============================================================================
// Types
// ============================================================================

export interface AIInsightPanelProps {
  /** The insight text to display */
  insight: string
  /** Optional title override (defaults to "AI INSIGHT") */
  title?: string
  /** Optional icon (defaults to Lightbulb) */
  icon?: React.ReactNode
}

// ============================================================================
// Component
// ============================================================================

export function AIInsightPanel({
  insight,
  title = 'AI Insight',
  icon,
}: AIInsightPanelProps) {
  return (
    <Box
      sx={{
        p: 'var(--ob-space-125)',
        bgcolor: 'var(--ob-color-info-soft)',
        borderLeft: 3,
        borderColor: 'var(--ob-info-500)',
        borderRadius: 'var(--ob-radius-xs)',
        display: 'flex',
        gap: 'var(--ob-space-100)',
        alignItems: 'flex-start',
      }}
    >
      <Box
        sx={{
          color: 'var(--ob-info-500)',
          display: 'flex',
          flexShrink: 0,
          mt: '2px',
        }}
      >
        {icon || <LightbulbIcon sx={{ fontSize: 18 }} />}
      </Box>
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-050)',
        }}
      >
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-2xs)',
            fontWeight: 600,
            color: 'var(--ob-info-600)',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
          }}
        >
          {title}
        </Typography>
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-sm)',
            color: 'text.secondary',
            lineHeight: 1.5,
          }}
        >
          {insight}
        </Typography>
      </Box>
    </Box>
  )
}
