/**
 * Inspection History Summary Component
 *
 * Seamless panel for displaying inspection history summary.
 * Uses Zero-Card architecture with glass background and hairline border.
 * Designed for 6-column grid placement (AI Studio pattern).
 *
 * Design tokens:
 * - Padding: --ob-space-125 (20px)
 * - Glass surface: --ob-surface-glass-1
 * - Typography: --ob-font-size-* tokens
 */

import { Box, Typography } from '@mui/material'

import type { ConditionAssessmentEntry } from '../../../../api/siteAcquisition'

// ============================================================================
// Types
// ============================================================================

export interface InspectionHistorySummaryProps {
  /** Whether a property is captured (enables log inspection button) */
  hasProperty: boolean
  /** Loading state for assessment history */
  isLoading: boolean
  /** Error message if history failed to load */
  error: string | null
  /** Most recent assessment entry */
  latestEntry: ConditionAssessmentEntry | null
  /** Previous assessment entry for comparison */
  previousEntry: ConditionAssessmentEntry | null
  /** Format scenario key to display label - accepts various scenario type unions */
  formatScenario: (scenario: string | null | undefined) => string
  /** Format timestamp for display */
  formatTimestamp: (timestamp: string | null | undefined) => string
  /** Handler to open history modal */
  onViewTimeline: () => void
  /** Handler to open assessment editor */
  onLogInspection: () => void
}

// ============================================================================
// Component
// ============================================================================

export function InspectionHistorySummary({
  hasProperty,
  isLoading,
  error,
  latestEntry,
  previousEntry,
  formatScenario,
  formatTimestamp,
  onViewTimeline,
  onLogInspection,
}: InspectionHistorySummaryProps) {
  return (
    <Box
      className="ob-seamless-panel ob-seamless-panel--glass"
      sx={{
        p: 'var(--ob-space-125)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-100)',
        height: '100%',
      }}
    >
      {/* Header row */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          gap: 'var(--ob-space-075)',
          flexWrap: 'wrap',
        }}
      >
        <Box>
          <Typography
            variant="h4"
            sx={{
              m: 0,
              fontSize: 'var(--ob-font-size-base)',
              fontWeight: 600,
              color: 'text.primary',
            }}
          >
            Inspection History
          </Typography>
          <Typography
            sx={{
              mt: 'var(--ob-space-025)',
              fontSize: 'var(--ob-font-size-xs)',
              color: 'text.secondary',
            }}
          >
            Track developer inspections saved for this property.
          </Typography>
        </Box>
        <Box
          sx={{ display: 'flex', gap: 'var(--ob-space-075)', flexWrap: 'wrap' }}
        >
          <button
            type="button"
            onClick={onViewTimeline}
            className="condition-assessment__export-btn condition-assessment__export-btn--primary"
          >
            View timeline
          </button>
          <button
            type="button"
            onClick={onLogInspection}
            disabled={!hasProperty}
            className="condition-assessment__export-btn condition-assessment__export-btn--secondary"
          >
            Log inspection
          </button>
        </Box>
      </Box>

      {/* Content */}
      {error ? (
        <Typography
          sx={{
            m: 0,
            fontSize: 'var(--ob-font-size-sm)',
            color: 'error.main',
          }}
        >
          {error}
        </Typography>
      ) : isLoading ? (
        <Typography
          sx={{
            m: 0,
            fontSize: 'var(--ob-font-size-sm)',
            color: 'text.secondary',
          }}
        >
          Loading inspection history...
        </Typography>
      ) : latestEntry ? (
        <Box
          className="ob-seamless-panel"
          sx={{
            p: 'var(--ob-space-100)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--ob-space-050)',
          }}
        >
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-2xs)',
              fontWeight: 600,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: 'text.secondary',
            }}
          >
            Most recent inspection
          </Typography>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              gap: 'var(--ob-space-075)',
              flexWrap: 'wrap',
            }}
          >
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--ob-space-025)',
              }}
            >
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-sm)',
                  fontWeight: 600,
                  color: 'text.primary',
                }}
              >
                {formatScenario(latestEntry.scenario)}
              </Typography>
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-xs)',
                  color: 'text.secondary',
                }}
              >
                {formatTimestamp(latestEntry.recordedAt)}
              </Typography>
            </Box>
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--ob-space-025)',
              }}
            >
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-xs)',
                  color: 'text.secondary',
                }}
              >
                Rating: <strong>{latestEntry.overallRating}</strong>
              </Typography>
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-xs)',
                  color: 'text.secondary',
                }}
              >
                Score: <strong>{latestEntry.overallScore}/100</strong>
              </Typography>
              <Typography
                sx={{
                  fontSize: 'var(--ob-font-size-xs)',
                  color: 'text.secondary',
                  textTransform: 'capitalize',
                }}
              >
                Risk: <strong>{latestEntry.riskLevel}</strong>
              </Typography>
            </Box>
          </Box>
          <Typography
            sx={{
              m: 0,
              fontSize: 'var(--ob-font-size-xs)',
              color: 'text.secondary',
              lineHeight: 1.4,
            }}
          >
            {latestEntry.summary || 'No summary recorded.'}
          </Typography>
          {previousEntry && (
            <Typography
              sx={{
                m: 0,
                mt: 'var(--ob-space-050)',
                fontSize: 'var(--ob-font-size-2xs)',
                color: 'text.secondary',
              }}
            >
              Last change:{' '}
              <strong>
                {formatScenario(previousEntry.scenario)} —{' '}
                {formatTimestamp(previousEntry.recordedAt)}
              </strong>
            </Typography>
          )}
        </Box>
      ) : (
        <Box
          className="ob-seamless-panel"
          sx={{
            p: 'var(--ob-space-100)',
          }}
        >
          <Typography
            sx={{
              m: 0,
              fontSize: 'var(--ob-font-size-sm)',
              color: 'text.secondary',
            }}
          >
            No developer inspections recorded yet. Save an inspection to begin
            the audit trail.
          </Typography>
        </Box>
      )}
    </Box>
  )
}
