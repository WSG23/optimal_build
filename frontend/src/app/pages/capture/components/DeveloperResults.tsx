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

import { useState, useMemo } from 'react'
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

export interface DeveloperResultsProps {
  result: SiteAcquisitionResult
  selectedScenarios: DevelopmentScenario[]
}

export function DeveloperResults({
  result,
  selectedScenarios,
}: DeveloperResultsProps) {
  // Active scenario for filtering
  const [activeScenario, setActiveScenario] =
    useState<DevelopmentScenario | null>(selectedScenarios[0] ?? null)

  // Geometry detail level for 3D preview (API accepts 'simple' | 'medium')
  const [geometryDetail, setGeometryDetail] = useState<'simple' | 'medium'>(
    'medium',
  )

  // Preview job state
  const {
    layers,
    focusLayerId,
    colorLegendEntries,
    isLoading: previewLoading,
    error: previewError,
    refreshPreview,
    setFocusLayerId,
    toggleLayerVisibility,
    soloLayer,
    showAllLayers,
    updateColorLegendEntry,
    addColorLegendEntry,
    removeColorLegendEntry,
  } = usePreviewJob(result.propertyId, result.previewJob)

  // Checklist state
  const {
    checklistItems,
    selectedCategory,
    isLoading: checklistLoading,
    setSelectedCategory,
    toggleItemCompletion,
    progress,
  } = useChecklist(result.propertyId, activeScenario)

  // Condition assessment state
  const {
    conditionAssessment,
    latestInspection,
    previousInspection,
    isLoading: conditionLoading,
    saveAssessment,
    exportPdf,
  } = useConditionAssessment(result.propertyId)

  // Scenario comparison state
  const {
    quickAnalysisScenarios,
    feasibilitySignals,
    isLoading: scenarioLoading,
  } = useScenarioComparison(result.propertyId, selectedScenarios)

  // Build overview cards from result
  const overviewCards = useMemo(() => {
    return buildOverviewCards(result)
  }, [result])

  // Handle refresh preview
  const handleRefreshPreview = () => {
    refreshPreview(geometryDetail)
  }

  return (
    <div className="site-acquisition__developer-results">
      {/* Property Overview Section */}
      <PropertyOverviewSection cards={overviewCards} isLoading={false} />

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
                value={geometryDetail}
                onChange={(e) =>
                  setGeometryDetail(e.target.value as 'simple' | 'medium')
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
              onClick={handleRefreshPreview}
              disabled={previewLoading}
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
            previewUrl={result.previewJob?.conceptMeshUrl}
            metadataUrl={result.previewJob?.previewMetadataUrl}
            status={result.previewJob?.status ?? 'pending'}
            thumbnailUrl={result.previewJob?.thumbnailUrl}
          />

          {/* Preview Layers Table */}
          <PreviewLayersTable
            layers={layers}
            focusLayerId={focusLayerId}
            colorLegendEntries={colorLegendEntries}
            onToggleVisibility={toggleLayerVisibility}
            onSoloLayer={soloLayer}
            onFocusLayer={setFocusLayerId}
            onShowAll={showAllLayers}
            onUpdateLegendEntry={updateColorLegendEntry}
            onAddLegendEntry={addColorLegendEntry}
            onRemoveLegendEntry={removeColorLegendEntry}
          />
        </Box>

        {previewError && (
          <Typography color="error" sx={{ mt: 'var(--ob-space-050)' }}>
            {previewError}
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
        propertyId={result.propertyId}
        items={checklistItems}
        selectedCategory={selectedCategory}
        isLoading={checklistLoading}
        progress={progress}
        onCategoryChange={setSelectedCategory}
        onToggleItem={toggleItemCompletion}
      />

      {/* Multi-Scenario Comparison */}
      <MultiScenarioComparisonSection
        propertyId={result.propertyId}
        capturedProperty={result}
        activeScenario={activeScenario}
        onScenarioChange={setActiveScenario}
        quickAnalysisScenarios={quickAnalysisScenarios}
        feasibilitySignals={feasibilitySignals}
        isLoading={scenarioLoading}
      />

      {/* Condition Assessment */}
      <ConditionAssessmentSection
        propertyId={result.propertyId}
        conditionAssessment={conditionAssessment}
        latestInspection={latestInspection}
        previousInspection={previousInspection}
        isLoading={conditionLoading}
        onSaveAssessment={saveAssessment}
        onExportPdf={exportPdf}
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

// Helper to build overview cards from result
function buildOverviewCards(result: SiteAcquisitionResult) {
  const cards = []

  // Location card
  if (result.address) {
    cards.push({
      type: 'location' as const,
      title: 'Location & Tenure',
      data: {
        address: result.address.fullAddress,
        district: result.address.district,
        tenure: result.tenure ?? 'Freehold',
      },
    })
  }

  // Build envelope card
  if (result.buildEnvelope) {
    cards.push({
      type: 'envelope' as const,
      title: 'Build Envelope',
      data: {
        zone: result.buildEnvelope.zone,
        plotRatio: result.buildEnvelope.plotRatio,
        siteArea: result.buildEnvelope.siteArea,
        maxGfa: result.buildEnvelope.maxGfa,
      },
    })
  }

  // Heritage card
  if (result.heritageContext) {
    cards.push({
      type: 'heritage' as const,
      title: 'Heritage Context',
      data: {
        riskLevel: result.heritageContext.riskLevel,
        constraints: result.heritageContext.constraints,
      },
    })
  }

  // Financial snapshot
  if (result.financialSnapshot) {
    cards.push({
      type: 'financial' as const,
      title: 'Financial Snapshot',
      data: {
        estimatedRevenue: result.financialSnapshot.estimatedRevenue,
        estimatedCapex: result.financialSnapshot.estimatedCapex,
        currency: result.currencySymbol ?? '$',
      },
    })
  }

  return cards
}

function formatScenarioLabel(value: DevelopmentScenario) {
  switch (value) {
    case 'raw_land':
      return 'Raw Land'
    case 'existing_building':
      return 'Existing Building'
    case 'heritage_property':
      return 'Heritage'
    case 'underused_asset':
      return 'Underused'
    case 'mixed_use_redevelopment':
      return 'Mixed-Use'
    default:
      return value
  }
}
