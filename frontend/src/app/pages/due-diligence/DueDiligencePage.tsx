import {
  Suspense,
  lazy,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'
import type { SyntheticEvent } from 'react'
import { Box, Tab, Tabs, Typography } from '@mui/material'

import type {
  DevelopmentScenario,
  SiteAcquisitionResult,
} from '../../../api/siteAcquisition'
import { Button } from '../../../components/canonical/Button'
import { Link, useRouterParams } from '../../../router'
import { loadCaptureForProject } from '../capture/utils/captureStorage'
import { useChecklist } from '../site-acquisition/hooks/useChecklist'
import { useConditionAssessment } from '../site-acquisition/hooks/useConditionAssessment'
import { useDueDiligenceScenarioComparison } from '../site-acquisition/hooks/useDueDiligenceScenarioComparison'
import { buildImmediateActions } from './components/conditionAssessmentUtils'

const DueDiligenceChecklistSection = lazy(async () => {
  const module =
    await import('../site-acquisition/components/checklist/DueDiligenceChecklistSection')
  return { default: module.DueDiligenceChecklistSection }
})

const InspectionHistorySummary = lazy(async () => {
  const module =
    await import('../site-acquisition/components/InspectionHistorySummary')
  return { default: module.InspectionHistorySummary }
})

const InspectionHistoryContent = lazy(async () => {
  const module =
    await import('../site-acquisition/components/inspection-history')
  return { default: module.InspectionHistoryContent }
})

const ConditionAssessmentTab = lazy(async () => {
  const module = await import('./components/ConditionAssessmentTab')
  return { default: module.ConditionAssessmentTab }
})

const OverridesTab = lazy(async () => {
  const module = await import('./components/OverridesTab')
  return { default: module.OverridesTab }
})

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
    checklistError,
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
        return '\u2014'
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

  const immediateActions = useMemo(
    () => buildImmediateActions(conditionAssessment?.recommendedActions ?? []),
    [conditionAssessment?.recommendedActions],
  )

  const handleTabChange = useCallback(
    (_event: SyntheticEvent, nextValue: DueDiligenceTab) => {
      setActiveTab(nextValue)
    },
    [],
  )

  const tabFallback = (
    <Box
      className="ob-seamless-panel ob-seamless-panel--glass"
      sx={{
        p: 'var(--ob-space-150)',
        minHeight: 240,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <Typography color="text.secondary">
        Loading due diligence view...
      </Typography>
    </Box>
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
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-25)',
            }}
          >
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
        <Suspense fallback={tabFallback}>
          <DueDiligenceChecklistSection
            capturedProperty={capturedProperty}
            checklistItems={checklistItems}
            filteredChecklistItems={filteredChecklistItems}
            displaySummary={displaySummary}
            activeScenario={activeScenario}
            activeScenarioDetails={activeScenarioDetails}
            selectedCategory={selectedCategory}
            isLoadingChecklist={isLoadingChecklist}
            checklistError={checklistError}
            setSelectedCategory={setSelectedCategory}
            handleChecklistUpdate={handleChecklistUpdate}
          />
        </Suspense>
      )}

      {activeTab === 'condition' && (
        <Suspense fallback={tabFallback}>
          <ConditionAssessmentTab
            conditionAssessment={conditionAssessment}
            isLoadingCondition={isLoadingCondition}
            assessmentSaveMessage={assessmentSaveMessage}
            immediateActions={immediateActions}
            combinedConditionInsights={combinedConditionInsights}
            insightSubtitle={insightSubtitle}
            systemComparisonMap={systemComparisonMap}
            formatRecordedTimestamp={formatRecordedTimestamp}
          />
        </Suspense>
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
          <Suspense fallback={tabFallback}>
            <InspectionHistorySummary
              hasProperty={!!capturedProperty}
              isLoading={isLoadingAssessmentHistory}
              error={assessmentHistoryError}
              latestEntry={latestAssessmentEntry}
              previousEntry={previousAssessmentEntry}
              formatScenario={(scenario) =>
                formatScenarioLabel(
                  (scenario as
                    | DevelopmentScenario
                    | 'all'
                    | null
                    | undefined) ?? null,
                )
              }
              formatTimestamp={formatRecordedTimestamp}
              onViewTimeline={() => setHistoryViewMode('timeline')}
              onLogInspection={() => openAssessmentEditor('new')}
            />
          </Suspense>
          <Box
            className="ob-seamless-panel ob-seamless-panel--glass"
            sx={{ p: 'var(--ob-space-150)' }}
          >
            <Suspense
              fallback={
                <Typography color="text.secondary">
                  Loading inspection history...
                </Typography>
              }
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
            </Suspense>
          </Box>
        </Box>
      )}

      {activeTab === 'overrides' && (
        <Suspense fallback={tabFallback}>
          <OverridesTab
            capturedProperty={capturedProperty}
            isExportingReport={isExportingReport}
            reportExportMessage={reportExportMessage}
            handleReportExport={handleReportExport}
            scenarioOverrideEntries={scenarioOverrideEntries}
            baseScenarioAssessment={baseScenarioAssessment}
            scenarioComparisonEntries={scenarioComparisonEntries}
            scenarioComparisonTableRows={scenarioComparisonTableRows}
            isLoadingScenarioAssessments={isLoadingScenarioAssessments}
            scenarioAssessmentsError={scenarioAssessmentsError}
            setScenarioComparisonBase={setScenarioComparisonBase}
            formatScenarioLabel={formatScenarioLabel}
            formatRecordedTimestamp={formatRecordedTimestamp}
          />
        </Suspense>
      )}
    </Box>
  )
}
