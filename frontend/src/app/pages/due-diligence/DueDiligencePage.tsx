import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { SyntheticEvent } from 'react'
import { Box, Tab, Tabs, Typography } from '@mui/material'

import type {
  DevelopmentScenario,
  SiteAcquisitionResult,
} from '../../../api/siteAcquisition'
import { Button } from '../../../components/canonical/Button'
import { SegmentedGauge } from '../../../components/canonical/SegmentedGauge'
import { Link, useRouterParams } from '../../../router'
import { loadCaptureForProject } from '../capture/utils/captureStorage'
import {
  CONDITION_RISK_LEVELS,
  CONDITION_RATINGS,
} from '../site-acquisition/constants'
import { useChecklist } from '../site-acquisition/hooks/useChecklist'
import { useConditionAssessment } from '../site-acquisition/hooks/useConditionAssessment'
import { useDueDiligenceScenarioComparison } from '../site-acquisition/hooks/useDueDiligenceScenarioComparison'
import { formatDeltaValue } from '../site-acquisition/utils'
import {
  classifySystemSeverity,
  getDeltaVisuals,
  getSeverityVisuals,
} from '../site-acquisition/utils/insights'
import { DueDiligenceChecklistSection } from '../site-acquisition/components/checklist/DueDiligenceChecklistSection'
import { OverallAssessmentCard } from '../site-acquisition/components/condition-assessment/OverallAssessmentCard'
import {
  ImmediateActionsGrid,
  type ImmediateAction,
} from '../site-acquisition/components/condition-assessment/ImmediateActionsGrid'
import { AIInsightPanel } from '../site-acquisition/components/condition-assessment/AIInsightPanel'
import { InsightCard } from '../site-acquisition/components/condition-assessment/InsightCard'
import { SystemRatingCard } from '../site-acquisition/components/condition-assessment/SystemRatingCard'
import { InspectionHistorySummary } from '../site-acquisition/components/InspectionHistorySummary'
import { InspectionHistoryContent } from '../site-acquisition/components/inspection-history'

const CAPTURED_PROPERTY_STORAGE_KEY = 'site-acquisition:captured-property'

type DueDiligenceTab = 'checklist' | 'condition' | 'history' | 'overrides'

function getStoredCapturedProperty(): SiteAcquisitionResult | null {
  try {
    const stored = window.sessionStorage.getItem(CAPTURED_PROPERTY_STORAGE_KEY)
    if (!stored) {
      return null
    }
    return JSON.parse(stored) as SiteAcquisitionResult
  } catch {
    return null
  }
}

function buildImmediateActions(actions: string[]): ImmediateAction[] {
  return actions.slice(0, 4).map((action, index) => {
    const hasColon = action.includes(':')
    const title = hasColon ? action.split(':')[0].trim() : action.trim()
    const description = hasColon
      ? action.split(':').slice(1).join(':').trim()
      : ''
    return {
      id: `action-${index}`,
      title,
      description,
      priority:
        index === 0 ? 'critical' : index === 1 ? 'high' : ('medium' as const),
    }
  })
}

export function DueDiligencePage() {
  const { projectId } = useRouterParams()
  const [capturedProperty, setCapturedProperty] =
    useState<SiteAcquisitionResult | null>(null)
  const [activeTab, setActiveTab] = useState<DueDiligenceTab>('checklist')
  const scenarioComparisonRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    let resolved: SiteAcquisitionResult | null = null
    if (projectId) {
      resolved = loadCaptureForProject(projectId)
    }
    if (!resolved && typeof window !== 'undefined') {
      resolved = getStoredCapturedProperty()
    }
    setCapturedProperty(resolved)
  }, [projectId])

  const capturePath = projectId
    ? `/projects/${projectId}/capture`
    : '/app/capture'
  const propertyLabel =
    capturedProperty?.address?.fullAddress?.trim() ||
    capturedProperty?.propertyInfo?.propertyName?.trim() ||
    null
  const districtLabel = capturedProperty?.address?.district?.trim() || null
  const currencySymbol = capturedProperty?.currencySymbol ?? 'S$'

  const {
    checklistItems,
    isLoadingChecklist,
    selectedCategory,
    setSelectedCategory,
    activeScenario,
    setActiveScenario,
    availableChecklistScenarios,
    filteredChecklistItems,
    displaySummary,
    activeScenarioDetails,
    scenarioChecklistProgress,
    scenarioLookup,
    handleChecklistUpdate,
  } = useChecklist({ capturedProperty })

  const {
    conditionAssessment,
    isLoadingCondition,
    assessmentSaveMessage,
    assessmentHistory,
    isLoadingAssessmentHistory,
    assessmentHistoryError,
    historyViewMode,
    setHistoryViewMode,
    scenarioAssessments,
    isLoadingScenarioAssessments,
    scenarioAssessmentsError,
    isExportingReport,
    reportExportMessage,
    openAssessmentEditor,
    handleReportExport,
  } = useConditionAssessment({ capturedProperty, activeScenario })

  const {
    scenarioOverrideEntries,
    baseScenarioAssessment,
    scenarioComparisonEntries,
    systemComparisons,
    systemComparisonMap,
    combinedConditionInsights,
    insightSubtitle,
    recommendedActionDiff,
    comparisonSummary,
    latestAssessmentEntry,
    previousAssessmentEntry,
    scenarioComparisonTableRows,
    scenarioComparisonVisible,
    setScenarioComparisonBase,
    formatScenarioLabel,
  } = useDueDiligenceScenarioComparison({
    capturedProperty,
    activeScenario,
    conditionAssessment,
    assessmentHistory,
    scenarioAssessments,
    scenarioChecklistProgress,
    displaySummary,
    currencySymbol,
  })

  const scenarioOptions = useMemo(() => {
    const collected = new Set<DevelopmentScenario>()
    availableChecklistScenarios.forEach((scenario) => collected.add(scenario))
    capturedProperty?.quickAnalysis?.scenarios?.forEach((scenario) => {
      if (scenario?.scenario) {
        collected.add(scenario.scenario as DevelopmentScenario)
      }
    })
    scenarioOverrideEntries.forEach((assessment) => {
      if (assessment.scenario) {
        collected.add(assessment.scenario)
      }
    })
    return ['all', ...Array.from(collected)] as Array<
      'all' | DevelopmentScenario
    >
  }, [
    availableChecklistScenarios,
    capturedProperty?.quickAnalysis?.scenarios,
    scenarioOverrideEntries,
  ])

  const formatRecordedTimestamp = useCallback(
    (timestamp?: string | null): string => {
      if (!timestamp) {
        return '—'
      }
      try {
        const date = new Date(timestamp)
        return date.toLocaleDateString('en-SG', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        })
      } catch {
        return timestamp
      }
    },
    [],
  )

  const describeRatingChange = useCallback(
    (current: string, reference: string) => {
      const currentIndex = CONDITION_RATINGS.indexOf(
        current as (typeof CONDITION_RATINGS)[number],
      )
      const referenceIndex = CONDITION_RATINGS.indexOf(
        reference as (typeof CONDITION_RATINGS)[number],
      )
      if (currentIndex === -1 || referenceIndex === -1) {
        if (current === reference) {
          return { text: 'Rating unchanged.', tone: 'neutral' as const }
        }
        return {
          text: `Rating changed from ${reference} to ${current}.`,
          tone: 'neutral' as const,
        }
      }
      if (currentIndex < referenceIndex) {
        return {
          text: `Rating improved from ${reference} to ${current}.`,
          tone: 'positive' as const,
        }
      }
      if (currentIndex > referenceIndex) {
        return {
          text: `Rating declined from ${reference} to ${current}.`,
          tone: 'negative' as const,
        }
      }
      return { text: 'Rating unchanged.', tone: 'neutral' as const }
    },
    [],
  )

  const describeRiskChange = useCallback(
    (current: string, reference: string) => {
      const currentIndex = CONDITION_RISK_LEVELS.indexOf(
        current as (typeof CONDITION_RISK_LEVELS)[number],
      )
      const referenceIndex = CONDITION_RISK_LEVELS.indexOf(
        reference as (typeof CONDITION_RISK_LEVELS)[number],
      )
      if (currentIndex === -1 || referenceIndex === -1) {
        if (current === reference) {
          return { text: 'Risk level unchanged.', tone: 'neutral' as const }
        }
        return {
          text: `Risk level changed from ${reference} to ${current}.`,
          tone: 'neutral' as const,
        }
      }
      if (currentIndex < referenceIndex) {
        return {
          text: `Risk level improved from ${reference} to ${current}.`,
          tone: 'positive' as const,
        }
      }
      if (currentIndex > referenceIndex) {
        return {
          text: `Risk level worsened from ${reference} to ${current}.`,
          tone: 'negative' as const,
        }
      }
      return { text: 'Risk level unchanged.', tone: 'neutral' as const }
    },
    [],
  )

  const immediateActions = useMemo(
    () => buildImmediateActions(conditionAssessment?.recommendedActions ?? []),
    [conditionAssessment?.recommendedActions],
  )

  const dueDiligenceMatrixRows = useMemo(
    () =>
      scenarioComparisonTableRows.filter(
        (row) =>
          row.conditionScore !== null ||
          row.checklistPercent !== null ||
          row.riskLevel !== null,
      ),
    [scenarioComparisonTableRows],
  )

  const dueDiligenceMatrixSummary = useMemo(() => {
    const conditionScores = dueDiligenceMatrixRows
      .map((row) => row.conditionScore)
      .filter((score): score is number => score !== null)
    const avgCondition =
      conditionScores.length > 0
        ? Math.round(
            conditionScores.reduce((sum, score) => sum + score, 0) /
              conditionScores.length,
          )
        : null
    const elevatedRiskCount = dueDiligenceMatrixRows.filter((row) =>
      ['elevated', 'high', 'critical'].includes(
        row.riskLevel?.toLowerCase() ?? '',
      ),
    ).length

    return {
      avgCondition,
      elevatedRiskCount,
      trackedPaths: dueDiligenceMatrixRows.length,
    }
  }, [dueDiligenceMatrixRows])

  const aiInsight = useMemo(() => {
    if (!conditionAssessment?.summary) {
      return null
    }
    const focusSystems =
      conditionAssessment.systems
        .filter((system) => system.rating === 'D' || system.rating === 'F')
        .map((system) => system.name)
        .join(', ') || 'structural integrity and ageing M&E plant'
    return `${conditionAssessment.summary} Focus remediation on ${focusSystems} to maintain operational efficiency.`
  }, [conditionAssessment])

  const handleTabChange = useCallback(
    (_event: SyntheticEvent, nextValue: DueDiligenceTab) => {
      setActiveTab(nextValue)
    },
    [],
  )

  if (!capturedProperty) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-150)',
        }}
      >
        <Box
          className="ob-seamless-panel ob-seamless-panel--glass"
          sx={{
            p: 'var(--ob-space-150)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--ob-space-100)',
          }}
        >
          <Typography variant="h4" sx={{ m: 0, fontWeight: 600 }}>
            No captured property in context
          </Typography>
          <Typography color="text.secondary">
            Capture a site first, then return here to review checklist progress,
            condition assessment, inspection history, and scenario overrides.
          </Typography>
          <Box sx={{ display: 'flex', gap: 'var(--ob-space-100)' }}>
            <Link to={capturePath}>
              <Button variant="primary">Open Capture</Button>
            </Link>
          </Box>
        </Box>
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
        className="ob-seamless-panel ob-seamless-panel--glass"
        sx={{
          p: 'var(--ob-space-150)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-100)',
        }}
      >
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            gap: 'var(--ob-space-100)',
            flexWrap: 'wrap',
          }}
        >
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <Typography variant="h4" sx={{ m: 0, fontWeight: 600 }}>
              {propertyLabel ?? 'Captured property'}
            </Typography>
            <Typography color="text.secondary">
              {districtLabel
                ? `${districtLabel} • Property due diligence workspace`
                : 'Property due diligence workspace'}
            </Typography>
          </Box>
          <Link to={capturePath}>
            <Button variant="secondary">Back to Capture</Button>
          </Link>
        </Box>

        <Box
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 'var(--ob-space-075)',
          }}
        >
          {scenarioOptions.map((scenario) => (
            <Button
              key={scenario}
              variant={activeScenario === scenario ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setActiveScenario(scenario)}
            >
              {scenario === 'all'
                ? 'All scenarios'
                : (scenarioLookup.get(scenario)?.label ??
                  formatScenarioLabel(scenario))}
            </Button>
          ))}
        </Box>

        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab value="checklist" label="Checklist" />
          <Tab value="condition" label="Condition Assessment" />
          <Tab value="history" label="Inspection History" />
          <Tab value="overrides" label="Scenario Overrides" />
        </Tabs>
      </Box>

      {activeTab === 'checklist' && (
        <DueDiligenceChecklistSection
          capturedProperty={capturedProperty}
          checklistItems={checklistItems}
          filteredChecklistItems={filteredChecklistItems}
          displaySummary={displaySummary}
          activeScenario={activeScenario}
          activeScenarioDetails={activeScenarioDetails}
          selectedCategory={selectedCategory}
          isLoadingChecklist={isLoadingChecklist}
          setSelectedCategory={setSelectedCategory}
          handleChecklistUpdate={handleChecklistUpdate}
        />
      )}

      {activeTab === 'condition' && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {isLoadingCondition ? (
            <Box className="condition-assessment__empty-state condition-assessment__empty-panel">
              <p>Analysing building condition...</p>
            </Box>
          ) : !conditionAssessment ? (
            <Box className="condition-assessment__empty-state condition-assessment__empty-state--warning condition-assessment__empty-panel">
              <p>
                Unable to load condition assessment. Refresh the capture or log
                an inspection to continue.
              </p>
            </Box>
          ) : (
            <>
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr', lg: '1fr 2fr' },
                  gap: 'var(--ob-space-150)',
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
                  attachments={conditionAssessment.attachments.map(
                    (attachment) => ({
                      label: attachment.label,
                      url: attachment.url ?? null,
                    }),
                  )}
                />

                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--ob-space-150)',
                  }}
                >
                  <ImmediateActionsGrid actions={immediateActions} />
                  {aiInsight && <AIInsightPanel insight={aiInsight} />}
                  {assessmentSaveMessage && (
                    <Typography color="text.secondary">
                      {assessmentSaveMessage}
                    </Typography>
                  )}
                </Box>
              </Box>

              {combinedConditionInsights.length > 0 && (
                <Box
                  className="ob-seamless-panel ob-seamless-panel--glass"
                  sx={{
                    p: 'var(--ob-space-150)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--ob-space-100)',
                  }}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      flexWrap: 'wrap',
                      gap: 'var(--ob-space-075)',
                    }}
                  >
                    <Typography variant="h4" sx={{ m: 0, fontWeight: 600 }}>
                      Condition Insights
                    </Typography>
                    <Typography color="text.secondary">
                      {insightSubtitle}
                    </Typography>
                  </Box>
                  <Box
                    sx={{
                      display: 'grid',
                      gap: 'var(--ob-space-100)',
                      gridTemplateColumns:
                        'repeat(auto-fit, minmax(240px, 1fr))',
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
              )}

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
                  const systemSeverity = classifySystemSeverity(
                    system.rating,
                    delta,
                  )

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
                      badgeVisuals={getSeverityVisuals(systemSeverity)}
                      deltaVisuals={getDeltaVisuals(delta)}
                    />
                  )
                })}
              </Box>
            </>
          )}
        </Box>
      )}

      {activeTab === 'history' && (
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', lg: '320px 1fr' },
            gap: 'var(--ob-space-150)',
            alignItems: 'start',
          }}
        >
          <InspectionHistorySummary
            hasProperty={!!capturedProperty}
            isLoading={isLoadingAssessmentHistory}
            error={assessmentHistoryError}
            latestEntry={latestAssessmentEntry}
            previousEntry={previousAssessmentEntry}
            formatScenario={(scenario) =>
              formatScenarioLabel(
                (scenario as DevelopmentScenario | 'all' | null | undefined) ??
                  null,
              )
            }
            formatTimestamp={formatRecordedTimestamp}
            onViewTimeline={() => setHistoryViewMode('timeline')}
            onLogInspection={() => openAssessmentEditor('new')}
          />
          <Box
            className="ob-seamless-panel ob-seamless-panel--glass"
            sx={{ p: 'var(--ob-space-150)' }}
          >
            <InspectionHistoryContent
              historyViewMode={historyViewMode}
              setHistoryViewMode={setHistoryViewMode}
              assessmentHistoryError={assessmentHistoryError}
              isLoadingAssessmentHistory={isLoadingAssessmentHistory}
              assessmentHistory={assessmentHistory}
              activeScenario={activeScenario}
              latestAssessmentEntry={latestAssessmentEntry}
              previousAssessmentEntry={previousAssessmentEntry}
              comparisonSummary={comparisonSummary}
              systemComparisons={systemComparisons}
              recommendedActionDiff={recommendedActionDiff}
              scenarioComparisonVisible={scenarioComparisonVisible}
              scenarioComparisonRef={scenarioComparisonRef}
              scenarioComparisonTableRows={scenarioComparisonTableRows}
              scenarioAssessments={scenarioAssessments}
              formatScenarioLabel={formatScenarioLabel}
              formatRecordedTimestamp={formatRecordedTimestamp}
            />
          </Box>
        </Box>
      )}

      {activeTab === 'overrides' && (
        <Box
          className="ob-seamless-panel ob-seamless-panel--glass"
          sx={{
            p: 'var(--ob-space-150)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--ob-space-125)',
          }}
        >
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              gap: 'var(--ob-space-100)',
              flexWrap: 'wrap',
            }}
          >
            <Box>
              <Typography variant="h4" sx={{ m: 0, fontWeight: 600 }}>
                Scenario Overrides
              </Typography>
              <Typography color="text.secondary">
                Compare manual assessments across scenarios and export the due
                diligence report pack.
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 'var(--ob-space-075)' }}>
              <Button
                variant="primary"
                size="sm"
                onClick={() => handleReportExport('json')}
                disabled={!capturedProperty || isExportingReport}
              >
                {isExportingReport ? 'Exporting…' : 'JSON'}
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => handleReportExport('pdf')}
                disabled={!capturedProperty || isExportingReport}
              >
                {isExportingReport ? 'Exporting…' : 'PDF'}
              </Button>
            </Box>
          </Box>

          {reportExportMessage && (
            <Typography color="text.secondary">
              {reportExportMessage}
            </Typography>
          )}

          {dueDiligenceMatrixRows.length > 0 && (
            <Box
              className="ob-seamless-panel"
              sx={{
                p: 'var(--ob-space-125)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--ob-space-125)',
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  gap: 'var(--ob-space-100)',
                  flexWrap: 'wrap',
                }}
              >
                <Box>
                  <Typography variant="h4" sx={{ m: 0, fontWeight: 600 }}>
                    Due Diligence Matrix
                  </Typography>
                  <Typography color="text.secondary">
                    Checklist progress, condition scoring, and risk vectors
                    remain due diligence metrics and are tracked here per
                    scenario.
                  </Typography>
                </Box>
                <Box
                  sx={{
                    display: 'flex',
                    gap: 'var(--ob-space-100)',
                    flexWrap: 'wrap',
                  }}
                >
                  <Box
                    className="ob-seamless-panel"
                    sx={{ p: 'var(--ob-space-100)' }}
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
                      AVG_CONDITION
                    </Typography>
                    <Typography
                      sx={{
                        fontSize: 'var(--ob-font-size-lg)',
                        fontWeight: 700,
                      }}
                    >
                      {dueDiligenceMatrixSummary.avgCondition !== null
                        ? `${dueDiligenceMatrixSummary.avgCondition}/100`
                        : '—'}
                    </Typography>
                  </Box>
                  <Box
                    className="ob-seamless-panel"
                    sx={{ p: 'var(--ob-space-100)' }}
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
                      RISK_VECTORS
                    </Typography>
                    <Typography
                      sx={{
                        fontSize: 'var(--ob-font-size-lg)',
                        fontWeight: 700,
                      }}
                    >
                      {dueDiligenceMatrixSummary.elevatedRiskCount}
                    </Typography>
                  </Box>
                  <Box
                    className="ob-seamless-panel"
                    sx={{ p: 'var(--ob-space-100)' }}
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
                      PATHS_TRACKED
                    </Typography>
                    <Typography
                      sx={{
                        fontSize: 'var(--ob-font-size-lg)',
                        fontWeight: 700,
                      }}
                    >
                      {dueDiligenceMatrixSummary.trackedPaths}
                    </Typography>
                  </Box>
                </Box>
              </Box>

              <Box
                sx={{
                  display: 'grid',
                  gap: 'var(--ob-space-100)',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                }}
              >
                {dueDiligenceMatrixRows.map((row) => (
                  <Box
                    key={row.key}
                    className="ob-seamless-panel"
                    sx={{
                      p: 'var(--ob-space-125)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 'var(--ob-space-100)',
                    }}
                  >
                    <Box
                      sx={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-start',
                        gap: 'var(--ob-space-075)',
                      }}
                    >
                      <Box>
                        <Typography variant="h5" sx={{ m: 0, fontWeight: 600 }}>
                          {row.label}
                        </Typography>
                        <Typography color="text.secondary">
                          {row.recordedAt
                            ? formatRecordedTimestamp(row.recordedAt)
                            : 'Assessment pending'}
                        </Typography>
                      </Box>
                      <Typography
                        sx={{
                          fontSize: 'var(--ob-font-size-2xs)',
                          fontWeight: 600,
                          letterSpacing: '0.08em',
                          textTransform: 'uppercase',
                          color: 'text.secondary',
                        }}
                      >
                        {row.source === 'manual' ? 'RECORDED' : 'HEURISTIC'}
                      </Typography>
                    </Box>

                    <Box
                      sx={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
                        gap: 'var(--ob-space-075)',
                      }}
                    >
                      <Box>
                        <Typography
                          sx={{
                            fontSize: 'var(--ob-font-size-2xs)',
                            fontWeight: 600,
                            letterSpacing: '0.08em',
                            textTransform: 'uppercase',
                            color: 'text.secondary',
                          }}
                        >
                          AVG_CONDITION
                        </Typography>
                        <Typography sx={{ fontWeight: 700 }}>
                          {row.conditionScore !== null
                            ? `${row.conditionScore}/100`
                            : '—'}
                        </Typography>
                      </Box>
                      <Box>
                        <Typography
                          sx={{
                            fontSize: 'var(--ob-font-size-2xs)',
                            fontWeight: 600,
                            letterSpacing: '0.08em',
                            textTransform: 'uppercase',
                            color: 'text.secondary',
                          }}
                        >
                          RISK_VECTOR
                        </Typography>
                        <Typography sx={{ fontWeight: 700 }}>
                          {row.riskLevel ? row.riskLevel.toUpperCase() : '—'}
                        </Typography>
                      </Box>
                    </Box>

                    <SegmentedGauge
                      label="DILIGENCE GAUGE"
                      value={row.checklistPercent ?? 0}
                      valueLabel={
                        row.checklistPercent !== null
                          ? `${row.checklistPercent}%`
                          : '—'
                      }
                    />
                  </Box>
                ))}
              </Box>
            </Box>
          )}

          {scenarioAssessmentsError ? (
            <Typography color="error.main">
              {scenarioAssessmentsError}
            </Typography>
          ) : isLoadingScenarioAssessments ? (
            <Typography color="text.secondary">
              Loading scenario overrides...
            </Typography>
          ) : scenarioOverrideEntries.length === 0 ? (
            <Box
              className="ob-seamless-panel"
              sx={{ p: 'var(--ob-space-100)' }}
            >
              <Typography color="text.secondary">
                No scenario-specific overrides recorded yet. Save an inspection
                for a specific scenario to compare outcomes.
              </Typography>
            </Box>
          ) : (
            <>
              {scenarioOverrideEntries.length > 1 && baseScenarioAssessment && (
                <Box
                  component="label"
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--ob-space-075)',
                    flexWrap: 'wrap',
                    fontSize: 'var(--ob-font-size-xs)',
                    color: 'text.secondary',
                  }}
                >
                  <Typography component="span" sx={{ fontWeight: 600 }}>
                    Baseline:
                  </Typography>
                  <select
                    value={baseScenarioAssessment.scenario ?? ''}
                    onChange={(event) =>
                      setScenarioComparisonBase(
                        event.target.value as DevelopmentScenario,
                      )
                    }
                    className="condition-assessment__scenario-select"
                  >
                    {scenarioOverrideEntries.map((entry) => (
                      <option
                        key={entry.scenario ?? 'all'}
                        value={entry.scenario ?? ''}
                      >
                        {formatScenarioLabel(entry.scenario)}
                      </option>
                    ))}
                  </select>
                </Box>
              )}

              {baseScenarioAssessment && (
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
                    Baseline:{' '}
                    {formatScenarioLabel(baseScenarioAssessment.scenario)}
                  </Typography>
                  <Box
                    sx={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: 'var(--ob-space-075)',
                      alignItems: 'center',
                      fontSize: 'var(--ob-font-size-xs)',
                    }}
                  >
                    <Typography component="span" sx={{ fontWeight: 600 }}>
                      {baseScenarioAssessment.overallRating}
                    </Typography>
                    <Typography component="span" color="text.secondary">
                      {baseScenarioAssessment.overallScore}/100
                    </Typography>
                    <Typography
                      component="span"
                      color="text.secondary"
                      sx={{ textTransform: 'capitalize' }}
                    >
                      {baseScenarioAssessment.riskLevel} risk
                    </Typography>
                  </Box>
                </Box>
              )}

              {scenarioComparisonEntries.length > 0 ? (
                <Box
                  sx={{
                    display: 'grid',
                    gap: 'var(--ob-space-100)',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                  }}
                >
                  {scenarioComparisonEntries.map((entry) => {
                    const scoreDelta = baseScenarioAssessment
                      ? entry.overallScore - baseScenarioAssessment.overallScore
                      : 0
                    const ratingDelta = baseScenarioAssessment
                      ? describeRatingChange(
                          entry.overallRating,
                          baseScenarioAssessment.overallRating,
                        )
                      : null
                    const riskDelta = baseScenarioAssessment
                      ? describeRiskChange(
                          entry.riskLevel,
                          baseScenarioAssessment.riskLevel,
                        )
                      : null

                    return (
                      <Box
                        key={`${entry.scenario ?? 'all'}-${entry.recordedAt ?? 'draft'}`}
                        className="ob-seamless-panel"
                        sx={{
                          p: 'var(--ob-space-125)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: 'var(--ob-space-075)',
                        }}
                      >
                        <Typography variant="h5" sx={{ m: 0, fontWeight: 600 }}>
                          {formatScenarioLabel(entry.scenario)}
                        </Typography>
                        <Typography color="text.secondary">
                          {formatRecordedTimestamp(entry.recordedAt)}
                        </Typography>
                        <Box
                          sx={{
                            display: 'flex',
                            flexWrap: 'wrap',
                            gap: 'var(--ob-space-075)',
                            alignItems: 'center',
                          }}
                        >
                          <Typography sx={{ fontWeight: 600 }}>
                            {entry.overallRating}
                          </Typography>
                          <Typography color="text.secondary">
                            {entry.overallScore}/100
                          </Typography>
                          <Typography
                            color="text.secondary"
                            sx={{ textTransform: 'capitalize' }}
                          >
                            {entry.riskLevel} risk
                          </Typography>
                          {baseScenarioAssessment && (
                            <Typography
                              sx={{
                                color:
                                  scoreDelta > 0
                                    ? 'success.main'
                                    : scoreDelta < 0
                                      ? 'error.main'
                                      : 'text.secondary',
                                fontWeight: 600,
                              }}
                            >
                              {formatDeltaValue(scoreDelta)}
                            </Typography>
                          )}
                        </Box>
                        <Typography color="text.primary">
                          {entry.summary}
                        </Typography>
                        {ratingDelta && (
                          <Typography color="text.secondary">
                            {ratingDelta.text}
                          </Typography>
                        )}
                        {riskDelta && (
                          <Typography color="text.secondary">
                            {riskDelta.text}
                          </Typography>
                        )}
                      </Box>
                    )
                  })}
                </Box>
              ) : (
                <Typography color="text.secondary">
                  Capture another scenario to compare against the selected
                  baseline.
                </Typography>
              )}
            </>
          )}
        </Box>
      )}
    </Box>
  )
}
