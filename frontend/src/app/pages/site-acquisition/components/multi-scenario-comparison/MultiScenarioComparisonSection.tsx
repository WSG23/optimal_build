/**
 * Multi-Scenario Comparison Section Component
 *
 * "Differential Analysis Matrix" - Tactical transformation of scenario comparison.
 *
 * Design Principles (AI Studio):
 * - Information Density vs Visual Noise: Strict visual hierarchy with typography tokens
 * - Responsive Resilience: Fluid grid with graceful degradation
 * - Functional Color Language: Cyan (Primary), Red (Critical), Indigo (AI Intelligence), Slate (Neutral)
 * - Progressive Disclosure: AI insights behind expandable buttons
 * - Summary Footer: Aggregate stats at bottom
 *
 * Phase 5 Transformation:
 * - "Asset Path Modules" with vertical glow-bar for focus indicator
 * - Scenario-coded system markers (PATH_RAW, PATH_ENBLOC, etc.)
 * - "Analysis Coverage" with 8 segmented blocks (machined edge style)
 * - "Intel Tapes" for Feasibility Signals with telemetry headers + signal strength
 * - "Intel Feed" at bottom for navigation into deeper feasibility workflows
 * - "Matrix Summary" footer with tactical labels
 */

import { useMemo } from 'react'

import ArrowRight from '@mui/icons-material/ArrowForward'

import type {
  DevelopmentScenario,
  CapturedProperty,
} from '../../../../../api/siteAcquisition'
import { Button } from '../../../../../components/canonical/Button'
import { SegmentedGauge } from '../../../../../components/canonical/SegmentedGauge'
import { SystemMarker } from '../../../../../components/canonical/SystemMarker'
import { Link } from '../../../../../router'
import type {
  CaptureScenarioComparisonDatum,
  FeasibilitySignalEntry,
  ScenarioOption,
} from '../../types'
import { formatCategoryName } from '../../utils/formatters'
import { FeasibilityIntelTape } from './FeasibilityIntelTape'
import { calculateSignalStrength, getSignalId } from './telemetry'

// ============================================================================
// Types
// ============================================================================

interface SummaryStats {
  avgCoverage: number | null
  totalRisks: number
  totalOpportunities: number
  scenariosTracked: number
}

type CaptureMetricDisplay = {
  label: string
  value: string
}

const CAPTURE_METRIC_PRIORITY = [
  'potential_gfa_sqm',
  'gfa_uplift_sqm',
  'plot_ratio',
  'site_area_sqm',
  'conservation_status',
] as const

const CAPTURE_METRIC_LABELS: Record<string, string> = {
  potential_gfa_sqm: 'BUILDABLE GFA',
  gfa_uplift_sqm: 'GFA UPLIFT',
  plot_ratio: 'PLOT RATIO',
  site_area_sqm: 'SITE AREA',
  conservation_status: 'CONSERVATION',
}

function formatCountMetric(value: number): string {
  return new Intl.NumberFormat('en-SG', {
    maximumFractionDigits: 0,
  }).format(value)
}

function formatAreaMetric(value: number): string {
  return `${formatCountMetric(value)} sqm`
}

function formatPercentMetric(value: number): string {
  return `${formatCountMetric(value)}%`
}

function findCaptureMetric(
  row: CaptureScenarioComparisonDatum,
): CaptureScenarioComparisonDatum['quickMetrics'][number] | null {
  for (const key of CAPTURE_METRIC_PRIORITY) {
    const match = row.quickMetrics.find((metric) => metric.key === key)
    if (match) {
      return match
    }
  }
  return null
}

function getPrimaryCaptureMetric(
  row: CaptureScenarioComparisonDatum,
  capturedProperty: CapturedProperty | null,
): CaptureMetricDisplay {
  const quickMetric = findCaptureMetric(row)
  if (quickMetric) {
    return {
      label: CAPTURE_METRIC_LABELS[quickMetric.key] ?? quickMetric.label,
      value: quickMetric.value,
    }
  }

  const envelope = capturedProperty?.buildEnvelope
  const heritageContext = capturedProperty?.heritageContext
  switch (row.key) {
    case 'existing_building':
    case 'underused_asset':
      if (envelope?.additionalPotentialGfaSqm != null) {
        return {
          label: 'GFA UPLIFT',
          value: formatAreaMetric(envelope.additionalPotentialGfaSqm),
        }
      }
      if (envelope?.currentGfaSqm != null) {
        return {
          label: 'CURRENT GFA',
          value: formatAreaMetric(envelope.currentGfaSqm),
        }
      }
      break
    case 'heritage_property':
      if (heritageContext?.risk) {
        return {
          label: 'HERITAGE RISK',
          value: heritageContext.risk.toUpperCase(),
        }
      }
      if (heritageContext?.overlay?.name) {
        return {
          label: 'OVERLAY',
          value: heritageContext.overlay.name,
        }
      }
      break
    default:
      break
  }

  if (envelope?.maxBuildableGfaSqm != null) {
    return {
      label: 'BUILDABLE GFA',
      value: formatAreaMetric(envelope.maxBuildableGfaSqm),
    }
  }
  if (envelope?.allowablePlotRatio != null) {
    return {
      label: 'PLOT RATIO',
      value: envelope.allowablePlotRatio.toFixed(2),
    }
  }
  if (envelope?.buildingHeightLimitM != null) {
    return {
      label: 'HEIGHT LIMIT',
      value: `${formatCountMetric(envelope.buildingHeightLimitM)} m`,
    }
  }
  if (envelope?.siteCoveragePct != null) {
    return {
      label: 'SITE COVERAGE',
      value: formatPercentMetric(envelope.siteCoveragePct),
    }
  }

  return {
    label: 'ENVELOPE',
    value: 'PENDING',
  }
}

function getConstraintDisplay(
  scenarioSignals: FeasibilitySignalEntry | undefined,
): string {
  if (!scenarioSignals || scenarioSignals.risks.length === 0) {
    return 'CLEAR'
  }
  return scenarioSignals.risks.length === 1
    ? '1 FLAG'
    : `${scenarioSignals.risks.length} FLAGS`
}

function getAnalysisCoverage(
  row: CaptureScenarioComparisonDatum,
  capturedProperty: CapturedProperty | null,
  quickAnalysisTimestamp: string | null,
): number {
  const envelope = capturedProperty?.buildEnvelope
  const visualizationStatus =
    capturedProperty?.visualization?.status?.toLowerCase()
  const baseChecks = [
    !!quickAnalysisTimestamp,
    !!row.quickHeadline,
    !!findCaptureMetric(row),
    envelope?.zoneCode !== null && envelope?.zoneCode !== undefined,
    envelope?.allowablePlotRatio !== null &&
      envelope?.allowablePlotRatio !== undefined,
    envelope?.maxBuildableGfaSqm !== null &&
      envelope?.maxBuildableGfaSqm !== undefined,
    envelope?.buildingHeightLimitM !== null &&
      envelope?.buildingHeightLimitM !== undefined,
    envelope?.siteCoveragePct !== null &&
      envelope?.siteCoveragePct !== undefined,
    !!visualizationStatus && visualizationStatus !== 'placeholder',
  ]
  if (row.key === 'heritage_property') {
    baseChecks.push(!!capturedProperty?.heritageContext)
  }
  const presentCount = baseChecks.filter(Boolean).length
  return Math.round((presentCount / baseChecks.length) * 100)
}

export interface MultiScenarioComparisonSectionProps {
  // Data
  capturedProperty: CapturedProperty | null
  quickAnalysisScenariosCount: number
  scenarioComparisonData: CaptureScenarioComparisonDatum[]
  feasibilitySignals: FeasibilitySignalEntry[]
  comparisonScenariosCount: number
  activeScenario: 'all' | DevelopmentScenario
  scenarioLookup: Map<DevelopmentScenario, ScenarioOption>
  propertyId: string | null

  // Callbacks
  setActiveScenario: (scenario: 'all' | DevelopmentScenario) => void
  formatRecordedTimestamp: (timestamp: string | null | undefined) => string
}

// ============================================================================
// Component
// ============================================================================

export function MultiScenarioComparisonSection({
  capturedProperty,
  quickAnalysisScenariosCount,
  scenarioComparisonData,
  feasibilitySignals,
  comparisonScenariosCount,
  activeScenario,
  scenarioLookup,
  propertyId,
  setActiveScenario,
  formatRecordedTimestamp,
}: MultiScenarioComparisonSectionProps) {
  const scenarioSignalsByKey = useMemo(
    () =>
      new Map(
        feasibilitySignals.map((entry) => [entry.scenario, entry] as const),
      ),
    [feasibilitySignals],
  )

  // Calculate summary stats for footer (AI Studio: Summary Footer pattern)
  const summaryStats = useMemo((): SummaryStats => {
    const scenarioData = scenarioComparisonData.filter(
      (row) => row.key !== 'all',
    )
    const coverageScores = scenarioData.map((row) =>
      getAnalysisCoverage(
        row,
        capturedProperty,
        capturedProperty?.quickAnalysis?.generatedAt ?? null,
      ),
    )
    const avgCoverage =
      coverageScores.length > 0
        ? Math.round(
            coverageScores.reduce((sum, score) => sum + score, 0) /
              coverageScores.length,
          )
        : null

    const totalRisks = feasibilitySignals.reduce(
      (sum, entry) => sum + entry.risks.length,
      0,
    )
    const totalOpportunities = feasibilitySignals.reduce(
      (sum, entry) => sum + entry.opportunities.length,
      0,
    )

    return {
      avgCoverage,
      totalRisks,
      totalOpportunities,
      scenariosTracked: scenarioData.length,
    }
  }, [capturedProperty, scenarioComparisonData, feasibilitySignals])

  const quickAnalysisTimestamp = useMemo(() => {
    if (!capturedProperty) {
      return null
    }
    return formatRecordedTimestamp(capturedProperty.quickAnalysis?.generatedAt)
  }, [capturedProperty, formatRecordedTimestamp])

  return (
    <section className="multi-scenario">
      {/* Header on background - Content vs Context pattern */}
      <h2 className="multi-scenario__title">Multi-Scenario Comparison</h2>
      {/* Content - direct children (Flat Section Pattern) */}
      {!capturedProperty ? (
        <div className="site-acquisition__empty-state site-acquisition__empty-state--prominent">
          <div className="multi-scenario__empty-icon">📊</div>
          <p className="multi-scenario__empty-title">
            Capture a property to review instant zoning, envelope, and code
            posture
          </p>
          <p className="multi-scenario__empty-subtitle">
            Address-based constraints and quick scenario analysis appear here.
          </p>
        </div>
      ) : quickAnalysisScenariosCount === 0 ? (
        <div className="site-acquisition__empty-state">
          <p>
            Quick analysis metrics unavailable for this capture. Try
            regenerating the scenarios.
          </p>
        </div>
      ) : (
        <>
          {/* Asset Path Modules - Differential Analysis Matrix */}
          <div className="multi-scenario__path-grid">
            {scenarioComparisonData
              .filter((row) => row.key !== 'all') // Skip aggregate row for path modules
              .map((row) => {
                const isActive = activeScenario === row.key
                const scenarioSignals = scenarioSignalsByKey.get(
                  row.key as DevelopmentScenario,
                )
                const analysisCoverage = getAnalysisCoverage(
                  row,
                  capturedProperty,
                  quickAnalysisTimestamp,
                )
                const primaryMetric = getPrimaryCaptureMetric(
                  row,
                  capturedProperty,
                )
                const constraintDisplay = getConstraintDisplay(scenarioSignals)
                const scenarioLabel =
                  scenarioLookup.get(row.key as DevelopmentScenario)?.label ??
                  formatCategoryName(row.key)

                return (
                  <article
                    key={row.key}
                    className={`multi-scenario__path-module ${isActive ? 'multi-scenario__path-module--focus' : ''}`}
                  >
                    {/* Vertical Glow-Bar (focus indicator) */}
                    <div className="multi-scenario__path-glow-bar" />

                    {/* Module Content */}
                    <div className="multi-scenario__path-content">
                      {/* Header: System Marker */}
                      <div className="multi-scenario__path-header">
                        <SystemMarker active={isActive}>
                          {scenarioLabel.toUpperCase()}
                        </SystemMarker>
                        <div className="multi-scenario__path-timestamp">
                          <span className="multi-scenario__path-timestamp-label">
                            ANALYZED
                          </span>
                          <span className="multi-scenario__path-timestamp-value">
                            {quickAnalysisTimestamp ?? '—'}
                          </span>
                        </div>
                      </div>

                      {/* Metrics Grid: envelope/code capture metrics */}
                      <div className="multi-scenario__path-metrics">
                        <div className="multi-scenario__path-metric">
                          <span className="multi-scenario__path-metric-label">
                            {primaryMetric.label}
                          </span>
                          <span className="multi-scenario__path-metric-value multi-scenario__path-metric-value--cyan">
                            {primaryMetric.value}
                          </span>
                        </div>
                        <div className="multi-scenario__path-metric">
                          <span className="multi-scenario__path-metric-label">
                            CONSTRAINT FLAGS
                          </span>
                          <span className="multi-scenario__path-metric-value">
                            {constraintDisplay}
                          </span>
                        </div>
                      </div>

                      {/* Analysis Coverage - Segmented */}
                      <SegmentedGauge
                        label="CAPTURE COVERAGE"
                        value={analysisCoverage}
                        valueLabel={`${analysisCoverage}%`}
                        segments={8}
                      />

                      {/* Enter Matrix CTA */}
                      <button
                        type="button"
                        onClick={() =>
                          setActiveScenario(row.key as DevelopmentScenario)
                        }
                        className="multi-scenario__path-cta"
                      >
                        {isActive ? 'VIEWING MATRIX' : 'ENTER MATRIX'}
                        <ArrowRight
                          sx={{
                            width: 'var(--ob-space-100)',
                            height: 'var(--ob-space-100)',
                            ml: 'var(--ob-space-050)',
                          }}
                        />
                      </button>
                    </div>
                  </article>
                )
              })}
          </div>

          {/* Feasibility Highlights - Header on background, surfaces below */}
          <div className="multi-scenario__feasibility">
            <div className="multi-scenario__intel-feed-header">
              <span className="multi-scenario__intel-feed-label">
                FEASIBILITY_HIGHLIGHTS
              </span>
              {propertyId && (
                <Link
                  to={`/app/asset-feasibility?propertyId=${encodeURIComponent(propertyId)}`}
                  className="multi-scenario__full-feasibility-link"
                >
                  <Button variant="primary" size="sm">
                    Continue To Feasibility →
                  </Button>
                </Link>
              )}
            </div>

            {/* Summary stats moved above intel feed */}
            <div className="multi-scenario__matrix-summary">
              <div className="multi-scenario__matrix-stats">
                <div className="multi-scenario__matrix-stat">
                  <span className="multi-scenario__matrix-value">
                    {summaryStats.scenariosTracked}
                  </span>
                  <span className="multi-scenario__matrix-label">
                    PATHS_TRACKED
                  </span>
                </div>
                <div className="multi-scenario__matrix-stat">
                  <span className="multi-scenario__matrix-value">
                    {summaryStats.avgCoverage !== null
                      ? `${summaryStats.avgCoverage}%`
                      : '—'}
                  </span>
                  <span className="multi-scenario__matrix-label">
                    AVG_COVERAGE
                  </span>
                </div>
                <div className="multi-scenario__matrix-stat multi-scenario__matrix-stat--opportunity">
                  <span className="multi-scenario__matrix-value">
                    {summaryStats.totalOpportunities}
                  </span>
                  <span className="multi-scenario__matrix-label">
                    OPPORTUNITIES
                  </span>
                </div>
                <div className="multi-scenario__matrix-stat multi-scenario__matrix-stat--risk">
                  <span className="multi-scenario__matrix-value">
                    {summaryStats.totalRisks}
                  </span>
                  <span className="multi-scenario__matrix-label">
                    CONSTRAINTS_FLAGGED
                  </span>
                </div>
              </div>
            </div>

            <div className="multi-scenario__intel-feed">
              <div className="multi-scenario__intel-feed-subheader">
                <span className="multi-scenario__intel-feed-subtitle">
                  INSTANT_SIGNALS ({feasibilitySignals.length})
                </span>
              </div>

              {feasibilitySignals.length > 0 ? (
                feasibilitySignals.map((entry) => {
                  const signalStrength = calculateSignalStrength(
                    entry.opportunities.length,
                    entry.risks.length,
                  )
                  const signalId = getSignalId(entry.scenario)

                  return (
                    <FeasibilityIntelTape
                      key={entry.scenario}
                      signalStrength={signalStrength}
                      signalId={signalId}
                      pathLabel={entry.label}
                      timestamp={quickAnalysisTimestamp ?? '—'}
                      opportunities={entry.opportunities}
                      risks={entry.risks}
                    />
                  )
                })
              ) : (
                <p className="multi-scenario__intel-feed-empty">
                  No automated feasibility highlights available yet.
                </p>
              )}
            </div>
          </div>

          {/* Path Focus Notice */}
          {activeScenario !== 'all' && comparisonScenariosCount > 0 && (
            <div className="multi-scenario__focus-notice">
              <strong>SCENARIO FOCUS:</strong> Viewing{' '}
              {scenarioLookup.get(activeScenario)?.label ??
                formatCategoryName(activeScenario)}
              . Switch back to "All scenarios" to compare scenarios
              side-by-side.
            </div>
          )}
        </>
      )}
    </section>
  )
}
