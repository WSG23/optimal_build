/**
 * CaptureRecommendationSection - Recommendation card and starter model assumptions card
 *
 * Extracted from DeveloperResults to reduce file size.
 */

import { Box, Typography } from '@mui/material'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import ViewInArIcon from '@mui/icons-material/ViewInAr'

import type { DevelopmentScenario } from '../../../../api/agents'
import { Card } from '../../../../components/canonical/Card'
import { Button } from '../../../../components/canonical/Button'

import type {
  StarterModelAssumptionLine,
  StarterModelAssumptionBuckets,
} from './useStarterModelMemos'

export interface CaptureRecommendationSectionProps {
  recommendationCardTitle: string
  formatScenarioLabel: (
    scenario: DevelopmentScenario | 'all' | null | undefined,
  ) => string
  recommendedScenario: DevelopmentScenario
  userOverride: boolean
  defaultRecommendationLabel: string
  explanation: string
  overrideModeLine: string
  overrideIntentGuidance: string | null
  overrideIntent: string | null | undefined
  currentProject: { id: string; name: string } | null
  confidence: string
  scenarioFitSummary: {
    comparisonSummary: string
    headroomSummary: string
    heritageSummary: string
  }
  reasonCodes: string[]
  handleSaveProjectOverride: () => void
  handleClearProjectOverride: () => void
  starterModelAssumptionSourceLine: string
  starterModelAssumptionFallbackReason: string | null
  starterModelOverridePreviewNotice: string | null
  starterModelAssumptionBuckets: StarterModelAssumptionBuckets
  starterModelAssumptionLines: StarterModelAssumptionLine[]
}

export function CaptureRecommendationSection({
  recommendationCardTitle,
  formatScenarioLabel,
  recommendedScenario,
  userOverride,
  defaultRecommendationLabel,
  explanation,
  overrideModeLine,
  overrideIntentGuidance,
  overrideIntent,
  currentProject,
  confidence,
  scenarioFitSummary,
  reasonCodes,
  handleSaveProjectOverride,
  handleClearProjectOverride,
  starterModelAssumptionSourceLine,
  starterModelAssumptionFallbackReason,
  starterModelOverridePreviewNotice,
  starterModelAssumptionBuckets,
  starterModelAssumptionLines,
}: CaptureRecommendationSectionProps) {
  return (
    <section className="site-acquisition__capture-summary">
      <Box
        sx={{
          mb: 'var(--ob-space-150)',
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', xl: '1fr 1fr' },
          gap: 'var(--ob-space-150)',
        }}
      >
        <Card
          sx={{
            p: 'var(--ob-space-125)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--ob-space-075)',
          }}
        >
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--ob-space-050)',
            }}
          >
            <AutoAwesomeIcon
              sx={{
                fontSize: 'var(--ob-size-icon-sm)',
                color: 'info.main',
              }}
            />
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                fontWeight: 'var(--ob-font-weight-semibold)',
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
                color: 'text.secondary',
              }}
            >
              {recommendationCardTitle}
            </Typography>
          </Box>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-lg)',
              fontWeight: 'var(--ob-font-weight-bold)',
              color: 'text.primary',
            }}
          >
            {formatScenarioLabel(recommendedScenario)}
          </Typography>
          {userOverride ? (
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
              }}
            >
              Capture recommended: {defaultRecommendationLabel}
            </Typography>
          ) : null}
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-sm)',
              color: 'text.secondary',
              lineHeight: 1.5,
            }}
          >
            {explanation}
          </Typography>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              color: 'text.secondary',
            }}
          >
            Mode: {overrideModeLine}
          </Typography>
          {overrideIntentGuidance ? (
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
                lineHeight: 1.5,
              }}
            >
              {overrideIntentGuidance}
            </Typography>
          ) : null}
          {overrideIntent === 'exploratory' && currentProject ? (
            <Button
              variant="secondary"
              size="sm"
              onClick={handleSaveProjectOverride}
            >
              Save as Project Override
            </Button>
          ) : null}
          {overrideIntent === 'saved' && currentProject ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearProjectOverride}
            >
              Clear Saved Override
            </Button>
          ) : null}
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              color: 'text.secondary',
            }}
          >
            Confidence: {confidence.replace(/_/g, ' ')}
          </Typography>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              color: 'text.secondary',
              lineHeight: 1.5,
            }}
          >
            Code fit: {scenarioFitSummary.comparisonSummary}
          </Typography>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              color: 'text.secondary',
              lineHeight: 1.5,
            }}
          >
            Envelope check: {scenarioFitSummary.headroomSummary}
          </Typography>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              color: 'text.secondary',
              lineHeight: 1.5,
            }}
          >
            {scenarioFitSummary.heritageSummary}
          </Typography>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              color: 'text.secondary',
            }}
          >
            Reasons:{' '}
            {reasonCodes
              .map((code) => code.replace(/_/g, ' ').toLowerCase())
              .join(', ')}
          </Typography>
        </Card>

        <Card
          sx={{
            p: 'var(--ob-space-125)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--ob-space-075)',
          }}
        >
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--ob-space-050)',
            }}
          >
            <ViewInArIcon
              sx={{
                fontSize: 'var(--ob-size-icon-sm)',
                color: 'info.main',
              }}
            />
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                fontWeight: 'var(--ob-font-weight-semibold)',
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
                color: 'text.secondary',
              }}
            >
              Starter Model Assumptions
            </Typography>
          </Box>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-sm)',
              color: 'text.secondary',
              lineHeight: 1.5,
            }}
          >
            These defaults shape the first scenario-specific model before deeper
            engineering inputs are added.
          </Typography>
          <Typography
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              color: 'text.secondary',
              lineHeight: 1.5,
            }}
          >
            {starterModelAssumptionSourceLine}
          </Typography>
          {starterModelAssumptionFallbackReason ? (
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
                lineHeight: 1.5,
              }}
            >
              {starterModelAssumptionFallbackReason}
            </Typography>
          ) : null}
          {starterModelOverridePreviewNotice ? (
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
                lineHeight: 1.5,
              }}
            >
              {starterModelOverridePreviewNotice}
            </Typography>
          ) : null}
          {starterModelAssumptionBuckets.pinned.length > 0 ? (
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
                lineHeight: 1.5,
              }}
            >
              Pinned by site facts:{' '}
              {starterModelAssumptionBuckets.pinned.join(', ')}.
            </Typography>
          ) : null}
          {starterModelAssumptionBuckets.tunable.length > 0 ? (
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
                lineHeight: 1.5,
              }}
            >
              Starter defaults still tunable:{' '}
              {starterModelAssumptionBuckets.tunable.join(', ')}.
            </Typography>
          ) : null}
          {starterModelAssumptionLines.map((line) => (
            <Typography
              key={line.text}
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
                lineHeight: 1.5,
              }}
            >
              {line.text}
              {line.sourceDetail ? ` (${line.sourceDetail})` : ''}
            </Typography>
          ))}
        </Card>
      </Box>
    </section>
  )
}
