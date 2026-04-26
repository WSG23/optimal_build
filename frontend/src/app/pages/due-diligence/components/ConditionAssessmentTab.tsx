import { Box, Typography } from '@mui/material'

import type { ConditionAssessment } from '../../../../api/siteAcquisition'
import { formatDeltaValue } from '../../site-acquisition/utils/formatters'
import {
  classifySystemSeverity,
  getDeltaVisuals,
  getSeverityVisuals,
} from '../../site-acquisition/utils/insights'
import { AIInsightPanel } from '../../site-acquisition/components/condition-assessment/AIInsightPanel'
import {
  ImmediateActionsGrid,
  type ImmediateAction,
} from '../../site-acquisition/components/condition-assessment/ImmediateActionsGrid'
import { InsightCard } from '../../site-acquisition/components/condition-assessment/InsightCard'
import { OverallAssessmentCard } from '../../site-acquisition/components/condition-assessment/OverallAssessmentCard'
import { SystemRatingCard } from '../../site-acquisition/components/condition-assessment/SystemRatingCard'
import type { ConditionInsightView } from '../../site-acquisition/types'

type SystemComparisonEntry = {
  previous: { rating: string; score: number } | null
  scoreDelta: number | null | undefined
}

export interface ConditionAssessmentTabProps {
  conditionAssessment: ConditionAssessment | null
  isLoadingCondition: boolean
  assessmentSaveMessage: string | null
  immediateActions: ImmediateAction[]
  combinedConditionInsights: ConditionInsightView[]
  insightSubtitle: string
  systemComparisonMap: Map<string, SystemComparisonEntry>
  formatRecordedTimestamp: (timestamp?: string | null) => string
}

export function ConditionAssessmentTab({
  conditionAssessment,
  isLoadingCondition,
  assessmentSaveMessage,
  immediateActions,
  combinedConditionInsights,
  insightSubtitle,
  systemComparisonMap,
  formatRecordedTimestamp,
}: ConditionAssessmentTabProps) {
  if (isLoadingCondition) {
    return (
      <Box
        className="ob-seamless-panel ob-seamless-panel--glass"
        sx={{ p: 'var(--ob-space-150)' }}
      >
        <Typography color="text.secondary">
          Analysing building condition...
        </Typography>
      </Box>
    )
  }

  if (!conditionAssessment) {
    return (
      <Box
        className="ob-seamless-panel ob-seamless-panel--glass"
        sx={{ p: 'var(--ob-space-150)' }}
      >
        <Typography
          variant="h6"
          sx={{ m: 0, fontWeight: 'var(--ob-font-weight-semibold)' }}
        >
          Condition assessment unavailable
        </Typography>
        <Typography color="text.secondary" sx={{ mt: 'var(--ob-space-050)' }}>
          Capture or refresh a property to load the latest diligence signals.
        </Typography>
      </Box>
    )
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-150)',
      }}
    >
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', lg: 'minmax(280px, 360px) 1fr' },
          gap: 'var(--ob-space-150)',
          alignItems: 'start',
        }}
      >
        <OverallAssessmentCard
          rating={conditionAssessment.overallRating}
          score={conditionAssessment.overallScore}
          riskLevel={conditionAssessment.riskLevel}
          summary={conditionAssessment.summary}
          scenarioContext={conditionAssessment.scenarioContext ?? null}
          inspectorName={conditionAssessment.inspectorName ?? null}
          recordedAtLabel={
            conditionAssessment.recordedAt
              ? formatRecordedTimestamp(conditionAssessment.recordedAt)
              : null
          }
          attachments={conditionAssessment.attachments.map((attachment) => ({
            label: attachment.label,
            url: attachment.url ?? null,
          }))}
        />

        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--ob-space-125)',
          }}
        >
          <ImmediateActionsGrid actions={immediateActions} />

          {conditionAssessment.summary ? (
            <AIInsightPanel
              insight={`${conditionAssessment.summary} Review highlighted systems before locking the next diligence milestone.`}
            />
          ) : null}

          {assessmentSaveMessage ? (
            <Box
              className="ob-seamless-panel"
              sx={{
                p: 'var(--ob-space-100)',
                border: '1px solid',
                borderColor: 'success.main',
              }}
            >
              <Typography sx={{ fontSize: 'var(--ob-font-size-sm)' }}>
                {assessmentSaveMessage}
              </Typography>
            </Box>
          ) : null}
        </Box>
      </Box>

      {combinedConditionInsights.length > 0 ? (
        <Box
          className="ob-seamless-panel ob-seamless-panel--glass"
          sx={{
            p: 'var(--ob-space-150)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--ob-space-100)',
          }}
        >
          <Box>
            <Typography
              variant="h6"
              sx={{ m: 0, fontWeight: 'var(--ob-font-weight-semibold)' }}
            >
              Condition insights
            </Typography>
            <Typography
              color="text.secondary"
              sx={{ mt: 'var(--ob-space-025)' }}
            >
              {insightSubtitle}
            </Typography>
          </Box>
          <Box
            sx={{
              display: 'grid',
              gap: 'var(--ob-space-100)',
              gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            }}
          >
            {combinedConditionInsights.map((insight) => (
              <InsightCard
                key={insight.id}
                id={insight.id}
                visuals={getSeverityVisuals(insight.severity)}
                title={insight.title}
                detail={insight.detail}
                isChecklistInsight={insight.id.startsWith('checklist-')}
                specialist={insight.specialist ?? null}
              />
            ))}
          </Box>
        </Box>
      ) : null}

      <Box
        sx={{
          display: 'grid',
          gap: 'var(--ob-space-150)',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
        }}
      >
        {conditionAssessment.systems.map((system) => {
          const comparison = systemComparisonMap.get(system.name)
          const delta =
            comparison && typeof comparison.scoreDelta === 'number'
              ? comparison.scoreDelta
              : null
          const previousRating = comparison?.previous?.rating ?? null
          const previousScore =
            typeof comparison?.previous?.score === 'number'
              ? comparison.previous.score
              : null
          const severity = classifySystemSeverity(system.rating, delta)

          return (
            <SystemRatingCard
              key={system.name}
              systemName={system.name}
              rating={system.rating}
              score={system.score}
              notes={system.notes}
              recommendedActions={system.recommendedActions}
              previousRating={previousRating}
              previousScore={previousScore}
              delta={delta}
              formattedDelta={formatDeltaValue(delta)}
              badgeVisuals={getSeverityVisuals(severity)}
              deltaVisuals={getDeltaVisuals(delta)}
            />
          )
        })}
      </Box>
    </Box>
  )
}
