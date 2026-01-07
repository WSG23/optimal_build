/**
 * DeveloperResults - Developer workspace wrapper for unified capture page
 *
 * Renders the full developer workspace sections after capture:
 * - Property Overview Section
 * - Development Preview (3D Viewer + Asset Mix)
 * - Preview Layers Table
 * - Scenario Focus Section
 * - Due Diligence Checklist
 * - Multi-Scenario Comparison
 * - Condition Assessment
 * - Finance Project CTA
 *
 * This component should be lazy-loaded to avoid bundle bloat for agent users.
 */

import { useState, useMemo, useCallback } from 'react'
import { Box, Typography, Select, MenuItem, FormControl } from '@mui/material'
import RefreshIcon from '@mui/icons-material/Refresh'

import type { SiteAcquisitionResult } from '../../../../api/siteAcquisition'
import type { DevelopmentScenario } from '../../../../api/agents'
import { Button } from '../../../../components/canonical/Button'
import { Link } from '../../../../router'

// Import Site Acquisition components
import { PropertyOverviewSection } from '../../site-acquisition/components/property-overview/PropertyOverviewSection'
import { Preview3DViewer } from '../../../components/site-acquisition/Preview3DViewer'
import { PreviewLayersTable } from '../../site-acquisition/components/property-overview/PreviewLayersTable'
import { DueDiligenceChecklistSection } from '../../site-acquisition/components/checklist/DueDiligenceChecklistSection'
import { MultiScenarioComparisonSection } from '../../site-acquisition/components/multi-scenario-comparison/MultiScenarioComparisonSection'
import { ConditionAssessmentSection } from '../../site-acquisition/components/condition-assessment/ConditionAssessmentSection'

// Import Site Acquisition hooks
import { usePreviewJob } from '../../site-acquisition/hooks/usePreviewJob'
import { useChecklist } from '../../site-acquisition/hooks/useChecklist'
import { useConditionAssessment } from '../../site-acquisition/hooks/useConditionAssessment'
import { useScenarioComparison } from '../../site-acquisition/hooks/useScenarioComparison'

// Import constants for scenario lookup
import {
  SCENARIO_OPTIONS,
  CONDITION_RATINGS,
  CONDITION_RISK_LEVELS,
} from '../../site-acquisition/constants'

// Import card builder utility
import { buildPropertyOverviewCards } from '../../site-acquisition/utils/cardBuilders'

// Import InspectionHistorySummary for inline usage
import { InspectionHistorySummary } from '../../site-acquisition/components/InspectionHistorySummary'

// Import OptimalIntelligenceCard for AI insights
import { OptimalIntelligenceCard } from '../../site-acquisition/components/OptimalIntelligenceCard'

export interface DeveloperResultsProps {
  result: SiteAcquisitionResult
  selectedScenarios: DevelopmentScenario[]
}

export function DeveloperResults({
  result,
  selectedScenarios,
}: DeveloperResultsProps) {
  // Active scenario for filtering
  const [activeScenario, setActiveScenario] = useState<
    DevelopmentScenario | 'all'
  >(selectedScenarios[0] ?? 'all')

  // Scenario lookup map for labels
  const scenarioLookup = useMemo(
    () => new Map(SCENARIO_OPTIONS.map((option) => [option.value, option])),
    [],
  )

  // Preview job state - use hook with options object
  const {
    previewJob,
    previewDetailLevel,
    setPreviewDetailLevel,
    isRefreshingPreview,
    previewLayerMetadata,
    previewLayerVisibility,
    previewFocusLayerId,
    isPreviewMetadataLoading,
    previewMetadataError,
    hiddenLayerCount,
    colorLegendEntries,
    legendHasPendingChanges,
    handleRefreshPreview,
    handleToggleLayerVisibility,
    handleSoloPreviewLayer,
    handleShowAllLayers,
    handleFocusLayer,
    handleResetLayerFocus,
    handleLegendEntryChange,
    handleLegendReset,
  } = usePreviewJob({ capturedProperty: result })

  // Unified layer action handler for PreviewLayersTable
  const handleLayerAction = useCallback(
    (layerId: string, action: 'toggle' | 'solo' | 'focus') => {
      switch (action) {
        case 'toggle':
          handleToggleLayerVisibility(layerId)
          break
        case 'solo':
          handleSoloPreviewLayer(layerId)
          break
        case 'focus':
          handleFocusLayer(layerId)
          break
      }
    },
    [handleToggleLayerVisibility, handleSoloPreviewLayer, handleFocusLayer],
  )

  // Checklist state - pass options object matching the hook signature
  const {
    checklistItems,
    filteredChecklistItems,
    selectedCategory,
    isLoadingChecklist: checklistLoading,
    setSelectedCategory,
    handleChecklistUpdate,
    displaySummary,
    activeScenarioDetails,
    scenarioChecklistProgress,
  } = useChecklist({ capturedProperty: result })

  // Condition assessment state - extract all required values
  const {
    conditionAssessment,
    latestAssessmentEntry,
    previousAssessmentEntry,
    isLoadingCondition,
    isExportingReport,
    reportExportMessage,
    handleReportExport,
    assessmentHistory,
    scenarioAssessments,
    isLoadingAssessmentHistory,
    assessmentHistoryError,
    isLoadingScenarioAssessments,
    scenarioAssessmentsError,
    assessmentSaveMessage,
    openAssessmentEditor,
  } = useConditionAssessment({ capturedProperty: result, activeScenario })

  // History modal state (for Inspection History Summary)
  const [_historyModalOpen, setHistoryModalOpen] = useState(false)

  // Currency symbol for formatting
  const currencySymbol = result.currencySymbol ?? 'S$'

  // Scenario comparison state - pass required options object and extract all values
  const {
    quickAnalysisScenarios,
    comparisonScenarios,
    scenarioComparisonData,
    formatScenarioLabel,
    combinedConditionInsights,
    insightSubtitle,
    systemComparisonMap,
    scenarioOverrideEntries,
    baseScenarioAssessment,
    scenarioComparisonEntries,
    setScenarioComparisonBase,
  } = useScenarioComparison({
    capturedProperty: result,
    activeScenario,
    conditionAssessment,
    assessmentHistory: assessmentHistory ?? [],
    scenarioAssessments: scenarioAssessments ?? [],
    scenarioChecklistProgress: scenarioChecklistProgress ?? {},
    displaySummary,
    currencySymbol,
  })

  // Compute feasibility signals from quick analysis scenarios
  const feasibilitySignals = useMemo(() => {
    if (!quickAnalysisScenarios.length) {
      return []
    }
    return quickAnalysisScenarios.map((entry) => {
      const scenario =
        typeof entry.scenario === 'string' && entry.scenario
          ? (entry.scenario as DevelopmentScenario)
          : 'raw_land'
      const label =
        scenarioLookup.get(scenario)?.label ?? formatScenarioLabel(scenario)
      // Extract signals from quick analysis entry
      const opportunities: string[] = []
      const risks: string[] = []
      // Add opportunity/risk signals based on metrics
      if (entry.estIrr && entry.estIrr > 15) {
        opportunities.push(`Strong IRR: ${entry.estIrr.toFixed(1)}%`)
      }
      if (entry.estIrr && entry.estIrr < 10) {
        risks.push(`Low IRR: ${entry.estIrr.toFixed(1)}%`)
      }
      return {
        scenario,
        label,
        opportunities,
        risks,
      }
    })
  }, [quickAnalysisScenarios, scenarioLookup, formatScenarioLabel])

  // Format timestamp helper
  const formatRecordedTimestamp = useCallback(
    (timestamp?: string | null): string => {
      if (!timestamp) return '—'
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

  // Number formatter for card values
  const formatNumber = useCallback(
    (value: number, options?: Intl.NumberFormatOptions) => {
      return new Intl.NumberFormat('en-SG', {
        maximumFractionDigits: 1,
        ...options,
      }).format(value)
    },
    [],
  )

  // Currency formatter for card values
  const formatCurrency = useCallback(
    (value: number) => {
      return `${currencySymbol}${formatNumber(value, { maximumFractionDigits: 0 })}`
    },
    [currencySymbol, formatNumber],
  )

  // Rating change description for condition assessment
  const describeRatingChange = useCallback(
    (current: string, reference: string) => {
      type Rating = (typeof CONDITION_RATINGS)[number]
      const currentIndex = CONDITION_RATINGS.indexOf(current as Rating)
      const referenceIndex = CONDITION_RATINGS.indexOf(reference as Rating)
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

  // Risk change description for condition assessment
  const describeRiskChange = useCallback(
    (current: string, reference: string) => {
      type RiskLevel = (typeof CONDITION_RISK_LEVELS)[number]
      const currentIndex = CONDITION_RISK_LEVELS.indexOf(current as RiskLevel)
      const referenceIndex = CONDITION_RISK_LEVELS.indexOf(
        reference as RiskLevel,
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

  // Inline Inspection History Summary component (rendered inline within section)
  const InlineInspectionHistorySummaryComponent = useCallback(
    () => (
      <InspectionHistorySummary
        hasProperty={!!result}
        isLoading={isLoadingAssessmentHistory}
        error={assessmentHistoryError}
        latestEntry={latestAssessmentEntry}
        previousEntry={previousAssessmentEntry}
        formatScenario={formatScenarioLabel}
        formatTimestamp={formatRecordedTimestamp}
        onViewTimeline={() => setHistoryModalOpen(true)}
        onLogInspection={() => openAssessmentEditor('new')}
      />
    ),
    [
      result,
      isLoadingAssessmentHistory,
      assessmentHistoryError,
      latestAssessmentEntry,
      previousAssessmentEntry,
      formatScenarioLabel,
      formatRecordedTimestamp,
      openAssessmentEditor,
    ],
  )

  // Build overview cards from result using the official card builder
  const overviewCards = useMemo(() => {
    return buildPropertyOverviewCards({
      capturedProperty: result,
      previewJob: result.previewJob ?? null,
      colorLegendEntries: colorLegendEntries ?? [],
      formatters: {
        formatNumber,
        formatCurrency,
        formatTimestamp: formatRecordedTimestamp,
      },
      currencySymbol,
    })
  }, [
    result,
    colorLegendEntries,
    formatNumber,
    formatCurrency,
    formatRecordedTimestamp,
    currencySymbol,
  ])

  // State for AI insight generation
  const [isGeneratingInsight, setIsGeneratingInsight] = useState(false)

  // Mock AI insight based on captured property data
  const aiInsight = useMemo(() => {
    if (!result) return null
    const scenarios = selectedScenarios
      .map((s) => scenarioLookup.get(s)?.label ?? s)
      .join(', ')
    return `Based on ${result.address?.district ?? 'this location'}'s zoning profile and ${scenarios} development scenarios, this site shows strong potential for mixed-use redevelopment with an estimated IRR of 12-18%. Key considerations include heritage overlay compliance and traffic impact assessments.`
  }, [result, selectedScenarios, scenarioLookup])

  // Handler for generating full report
  const handleGenerateReport = useCallback(async () => {
    setIsGeneratingInsight(true)
    // Simulate API call delay
    await new Promise((resolve) => setTimeout(resolve, 2000))
    setIsGeneratingInsight(false)
    // In production, this would trigger a full AI report generation
  }, [])

  return (
    <div className="site-acquisition__developer-results">
      {/* Property Overview Section */}
      <PropertyOverviewSection cards={overviewCards} />

      {/* AI Insight Card - Key intelligence from Optimal AI */}
      <OptimalIntelligenceCard
        insight={aiInsight}
        hasProperty={!!result}
        onGenerateReport={handleGenerateReport}
        isGenerating={isGeneratingInsight}
      />

      {/* Development Preview Section */}
      <section className="site-acquisition__preview">
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 'var(--ob-space-150)',
          }}
        >
          <Typography
            variant="h6"
            sx={{
              fontWeight: 'var(--ob-font-weight-semibold)',
              color: 'var(--ob-color-text-primary)',
            }}
          >
            Development Preview
          </Typography>
          <Box
            sx={{
              display: 'flex',
              gap: 'var(--ob-space-100)',
              alignItems: 'center',
            }}
          >
            <FormControl size="small">
              <Select
                value={previewDetailLevel}
                onChange={(e) =>
                  setPreviewDetailLevel(e.target.value as 'simple' | 'medium')
                }
                sx={{ minWidth: 'var(--ob-size-600)' }}
              >
                <MenuItem value="simple">Simple</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
              </Select>
            </FormControl>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => handleRefreshPreview(previewDetailLevel)}
              disabled={isRefreshingPreview}
            >
              <RefreshIcon
                sx={{
                  fontSize: 'var(--ob-font-size-md)',
                  mr: 'var(--ob-space-025)',
                }}
              />
              Refresh
            </Button>
          </Box>
        </Box>

        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' },
            gap: 'var(--ob-space-150)',
          }}
        >
          {/* 3D Viewer */}
          <Preview3DViewer
            previewUrl={previewJob?.conceptMeshUrl}
            metadataUrl={previewJob?.previewMetadataUrl}
            status={previewJob?.status ?? 'pending'}
            thumbnailUrl={previewJob?.thumbnailUrl}
          />

          {/* Preview Layers Table */}
          <PreviewLayersTable
            layers={previewLayerMetadata}
            visibility={previewLayerVisibility}
            focusLayerId={previewFocusLayerId}
            hiddenLayerCount={hiddenLayerCount}
            isLoading={isPreviewMetadataLoading}
            error={previewMetadataError}
            onLayerAction={handleLayerAction}
            onShowAll={handleShowAllLayers}
            onResetFocus={handleResetLayerFocus}
            formatNumber={formatNumber}
            legendEntries={colorLegendEntries}
            onLegendChange={handleLegendEntryChange}
            legendHasPendingChanges={legendHasPendingChanges}
            onLegendReset={handleLegendReset}
          />
        </Box>

        {previewMetadataError && (
          <Typography color="error" sx={{ mt: 'var(--ob-space-050)' }}>
            {previewMetadataError}
          </Typography>
        )}
      </section>

      {/* Scenario Focus Section */}
      <section className="site-acquisition__scenario-focus">
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 'var(--ob-space-150)',
          }}
        >
          <Typography
            variant="h6"
            sx={{
              fontWeight: 'var(--ob-font-weight-semibold)',
              color: 'var(--ob-color-text-primary)',
            }}
          >
            Scenario Focus
          </Typography>
          <Box sx={{ display: 'flex', gap: 'var(--ob-space-050)' }}>
            <Button
              key="all"
              variant={activeScenario === 'all' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setActiveScenario('all')}
            >
              All Scenarios
            </Button>
            {selectedScenarios.map((scenario) => (
              <Button
                key={scenario}
                variant={activeScenario === scenario ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setActiveScenario(scenario)}
              >
                {formatScenarioLabel(scenario)}
              </Button>
            ))}
          </Box>
        </Box>
      </section>

      {/* Due Diligence Checklist */}
      <DueDiligenceChecklistSection
        capturedProperty={result}
        checklistItems={checklistItems}
        filteredChecklistItems={filteredChecklistItems}
        displaySummary={displaySummary}
        activeScenario={activeScenario}
        activeScenarioDetails={activeScenarioDetails}
        selectedCategory={selectedCategory}
        isLoadingChecklist={checklistLoading}
        setSelectedCategory={setSelectedCategory}
        handleChecklistUpdate={handleChecklistUpdate}
      />

      {/* Multi-Scenario Comparison */}
      <MultiScenarioComparisonSection
        capturedProperty={result}
        quickAnalysisScenariosCount={quickAnalysisScenarios.length}
        scenarioComparisonData={scenarioComparisonData}
        feasibilitySignals={feasibilitySignals}
        comparisonScenariosCount={comparisonScenarios.length}
        activeScenario={activeScenario}
        scenarioLookup={scenarioLookup}
        propertyId={result.propertyId}
        isExportingReport={isExportingReport}
        reportExportMessage={reportExportMessage}
        setActiveScenario={setActiveScenario}
        handleReportExport={handleReportExport}
        formatRecordedTimestamp={formatRecordedTimestamp}
      />

      {/* Condition Assessment */}
      <ConditionAssessmentSection
        capturedProperty={result}
        conditionAssessment={conditionAssessment}
        isLoadingCondition={isLoadingCondition}
        latestAssessmentEntry={latestAssessmentEntry}
        previousAssessmentEntry={previousAssessmentEntry}
        assessmentHistoryError={assessmentHistoryError}
        isLoadingAssessmentHistory={isLoadingAssessmentHistory}
        assessmentSaveMessage={assessmentSaveMessage}
        scenarioAssessments={scenarioAssessments ?? []}
        isLoadingScenarioAssessments={isLoadingScenarioAssessments}
        scenarioAssessmentsError={scenarioAssessmentsError}
        scenarioOverrideEntries={scenarioOverrideEntries}
        baseScenarioAssessment={baseScenarioAssessment}
        scenarioComparisonEntries={scenarioComparisonEntries}
        combinedConditionInsights={combinedConditionInsights}
        insightSubtitle={insightSubtitle}
        systemComparisonMap={systemComparisonMap}
        isExportingReport={isExportingReport}
        scenarioLookup={scenarioLookup}
        formatRecordedTimestamp={formatRecordedTimestamp}
        formatScenarioLabel={formatScenarioLabel}
        describeRatingChange={describeRatingChange}
        describeRiskChange={describeRiskChange}
        openAssessmentEditor={openAssessmentEditor}
        setScenarioComparisonBase={setScenarioComparisonBase}
        handleReportExport={handleReportExport}
        setHistoryModalOpen={setHistoryModalOpen}
        InlineInspectionHistorySummary={InlineInspectionHistorySummaryComponent}
      />

      {/* Finance CTA */}
      <section className="site-acquisition__finance-cta">
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            py: 'var(--ob-space-200)',
          }}
        >
          <Link to={`/app/financial-control?propertyId=${result.propertyId}`}>
            <Button variant="primary" size="lg">
              Create Finance Project →
            </Button>
          </Link>
        </Box>
      </section>
    </div>
  )
}
