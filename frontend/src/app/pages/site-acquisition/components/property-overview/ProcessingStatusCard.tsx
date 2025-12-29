/**
 * ProcessingStatusCard - Active Status Feedback Component
 *
 * Implements UX Friction Solution #2: "Black Box" Processing
 * - Progress bars instead of text-only status
 * - Shows what step is happening, not just "Processing"
 * - Green = complete, Cyan = active/processing, Amber = waiting
 *
 * @see frontend/UX_ARCHITECTURE.md - Problem 2: "Black Box" Processing
 */

import { Box, LinearProgress, Typography, SxProps, Theme } from '@mui/material'
import { GlassCard } from '../../../../../components/canonical/GlassCard'
import { PulsingStatusDot } from '../../../../../components/canonical/PulsingStatusDot'

export type ProcessingStatus =
  | 'pending'
  | 'processing'
  | 'ready'
  | 'failed'
  | 'expired'

export interface ProcessingStatusCardProps {
  /** Card title (e.g., "Preview Generation") */
  title: string
  /** Current status */
  status: ProcessingStatus
  /** Progress percentage (0-100) for determinate progress */
  progress?: number
  /** Status message describing current step */
  statusMessage?: string
  /** Timestamp of when processing started */
  startedAt?: string
  /** Estimated time remaining */
  estimatedTimeRemaining?: string
  /** Additional details */
  details?: Array<{ label: string; value: string }>
  /** Additional styles */
  sx?: SxProps<Theme>
}

const statusConfig = {
  pending: {
    dotStatus: 'warning' as const,
    label: 'PENDING',
    color: 'var(--ob-warning-500)',
    progressColor: 'var(--ob-warning-500)',
  },
  processing: {
    dotStatus: 'live' as const,
    label: 'PROCESSING',
    color: 'var(--ob-color-neon-cyan)',
    progressColor: 'var(--ob-color-neon-cyan)',
  },
  ready: {
    dotStatus: 'success' as const,
    label: 'READY',
    color: 'var(--ob-success-500)',
    progressColor: 'var(--ob-success-500)',
  },
  failed: {
    dotStatus: 'error' as const,
    label: 'FAILED',
    color: 'var(--ob-error-500)',
    progressColor: 'var(--ob-error-500)',
  },
  expired: {
    dotStatus: 'inactive' as const,
    label: 'EXPIRED',
    color: 'var(--ob-text-tertiary)',
    progressColor: 'var(--ob-neutral-500)',
  },
}

export function ProcessingStatusCard({
  title,
  status,
  progress,
  statusMessage,
  startedAt,
  estimatedTimeRemaining,
  details = [],
  sx = {},
}: ProcessingStatusCardProps) {
  const config = statusConfig[status]
  const isComplete = status === 'ready'
  const isProcessing = status === 'processing' || status === 'pending'
  const displayProgress =
    progress ?? (isComplete ? 100 : isProcessing ? undefined : 0)

  return (
    <GlassCard
      sx={{
        p: 'var(--ob-space-150)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-100)',
        ...sx,
      }}
    >
      {/* Header: Status dot + Title + Status label */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 'var(--ob-space-100)',
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--ob-space-075)',
          }}
        >
          <PulsingStatusDot
            status={config.dotStatus}
            size="md"
            pulse={isProcessing}
          />
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-base)',
              fontWeight: 600,
              color: 'var(--ob-color-text-primary)',
            }}
          >
            {title}
          </Typography>
        </Box>
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-2xs)',
            fontWeight: 700,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            color: config.color,
            px: 'var(--ob-space-075)',
            py: 'var(--ob-space-025)',
            bgcolor: `color-mix(in srgb, ${config.color} 15%, transparent)`,
            borderRadius: 'var(--ob-radius-xs)',
          }}
        >
          {config.label}
        </Typography>
      </Box>

      {/* Progress bar */}
      <Box sx={{ mt: 'var(--ob-space-050)' }}>
        <LinearProgress
          variant={
            displayProgress !== undefined ? 'determinate' : 'indeterminate'
          }
          value={displayProgress}
          sx={{
            height: 6,
            borderRadius: 'var(--ob-radius-xs)',
            bgcolor: 'var(--ob-surface-glass-subtle)',
            '& .MuiLinearProgress-bar': {
              bgcolor: config.progressColor,
              borderRadius: 'var(--ob-radius-xs)',
            },
          }}
        />
        {displayProgress !== undefined && (
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              fontWeight: 600,
              color: config.color,
              textAlign: 'right',
              mt: 'var(--ob-space-025)',
            }}
          >
            {Math.round(displayProgress)}%
          </Typography>
        )}
      </Box>

      {/* Status message */}
      {statusMessage && (
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-sm)',
            color: 'var(--ob-text-secondary)',
          }}
        >
          {statusMessage}
        </Typography>
      )}

      {/* Timing info */}
      {(startedAt || estimatedTimeRemaining) && (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            gap: 'var(--ob-space-100)',
          }}
        >
          {startedAt && (
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'var(--ob-text-tertiary)',
              }}
            >
              Started: {startedAt}
            </Typography>
          )}
          {estimatedTimeRemaining && isProcessing && (
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'var(--ob-color-neon-cyan)',
              }}
            >
              ~{estimatedTimeRemaining} remaining
            </Typography>
          )}
        </Box>
      )}

      {/* Additional details */}
      {details.length > 0 && (
        <Box
          sx={{
            mt: 'var(--ob-space-075)',
            pt: 'var(--ob-space-075)',
            borderTop: '1px solid var(--ob-color-border-subtle)',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
            gap: 'var(--ob-space-075)',
          }}
        >
          {details.map((detail) => (
            <Box key={detail.label}>
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-2xs)',
                  fontWeight: 600,
                  letterSpacing: '0.06em',
                  textTransform: 'uppercase',
                  color: 'var(--ob-text-tertiary)',
                }}
              >
                {detail.label}
              </Typography>
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-sm)',
                  color: 'var(--ob-color-text-primary)',
                }}
              >
                {detail.value}
              </Typography>
            </Box>
          ))}
        </Box>
      )}
    </GlassCard>
  )
}
