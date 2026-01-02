/**
 * Condition Assessment Section Component
 *
 * Displays the property condition assessment with:
 * - 12-column grid layout (4:8 split) - AI Studio pattern
 * - Left: Overall rating gauge (4 cols)
 * - Right: Immediate actions + AI insight + CTAs (8 cols)
 * - Below: Systems grid, Inspection history, Scenario overrides
 *
 * Receives all data and handlers via props (no internal state).
 */

import { Grid, Box, Typography } from '@mui/material'

import type {
  ConditionAssessment,
  DevelopmentScenario,
} from '../../../../../api/siteAcquisition'
import type { ScenarioOption } from '../../constants'
import { formatDeltaValue } from '../../utils'
import {
  classifySystemSeverity,
  getSeverityVisuals,
  getDeltaVisuals,
} from '../../utils/insights'
import { InsightCard } from './InsightCard'
import { SystemRatingCard } from './SystemRatingCard'
import { OverallAssessmentCard } from './OverallAssessmentCard'
import {
  ImmediateActionsGrid,
  type ImmediateAction,
} from './ImmediateActionsGrid'
import { AIInsightPanel } from './AIInsightPanel'

// ============================================================================
// Types
// ============================================================================

export interface SystemComparison {
  name: string
  previous: { rating: string; score: number } | null
  scoreDelta: number | null | undefined
}

export interface ConditionInsight {
  id: string
  severity: 'critical' | 'warning' | 'info' | 'positive'
  title: string
  detail: string
  specialist?: string | null
}

export interface ConditionAssessmentSectionProps {
  // Core data
  capturedProperty: unknown | null
  conditionAssessment: ConditionAssessment | null
  isLoadingCondition: boolean

  // Assessment history
  latestAssessmentEntry: ConditionAssessment | null
  previousAssessmentEntry: ConditionAssessment | null
  assessmentHistoryError: string | null
  isLoadingAssessmentHistory: boolean
  assessmentSaveMessage: string | null

  // Scenario assessments
  scenarioAssessments: ConditionAssessment[]
  isLoadingScenarioAssessments: boolean
  scenarioAssessmentsError: string | null
  scenarioOverrideEntries: ConditionAssessment[]
  baseScenarioAssessment: ConditionAssessment | null
  scenarioComparisonEntries: ConditionAssessment[]

  // Insights
  combinedConditionInsights: ConditionInsight[]
  insightSubtitle: string
  systemComparisonMap: Map<string, SystemComparison>

  // Export state
  isExportingReport: boolean

  // Lookup helpers
  scenarioLookup: Map<DevelopmentScenario, ScenarioOption>

  // Formatters (stable callbacks from parent)
  formatRecordedTimestamp: (timestamp?: string | null) => string
  formatScenarioLabel: (
    scenario: DevelopmentScenario | 'all' | null | undefined,
  ) => string
  describeRatingChange: (
    current: string,
    reference: string,
  ) => { text: string; tone: 'positive' | 'negative' | 'neutral' }
  describeRiskChange: (
    current: string,
    reference: string,
  ) => { text: string; tone: 'positive' | 'negative' | 'neutral' }

  // Handlers (stable callbacks from parent)
  openAssessmentEditor: (mode: 'new' | 'edit') => void
  setScenarioComparisonBase: (scenario: DevelopmentScenario) => void
  handleReportExport: (format: 'json' | 'pdf') => void
  setHistoryModalOpen: (open: boolean) => void

  // Inline component (will be extracted separately in Phase 1)
  InlineInspectionHistorySummary: React.ComponentType
}

// ============================================================================
// Component
// ============================================================================

export function ConditionAssessmentSection({
  capturedProperty,
  conditionAssessment,
  isLoadingCondition,
  latestAssessmentEntry,
  previousAssessmentEntry: _previousAssessmentEntry,
  assessmentHistoryError: _assessmentHistoryError,
  isLoadingAssessmentHistory: _isLoadingAssessmentHistory,
  assessmentSaveMessage: _assessmentSaveMessage,
  scenarioAssessments: _scenarioAssessments,
  isLoadingScenarioAssessments,
  scenarioAssessmentsError,
  scenarioOverrideEntries,
  baseScenarioAssessment,
  scenarioComparisonEntries,
  combinedConditionInsights,
  insightSubtitle,
  systemComparisonMap,
  isExportingReport,
  scenarioLookup: _scenarioLookup,
  formatRecordedTimestamp,
  formatScenarioLabel,
  describeRatingChange: _describeRatingChange,
  describeRiskChange: _describeRiskChange,
  openAssessmentEditor,
  setScenarioComparisonBase,
  handleReportExport,
  setHistoryModalOpen: _setHistoryModalOpen,
  InlineInspectionHistorySummary,
}: ConditionAssessmentSectionProps) {
  return (
    <section className="condition-assessment">
      {/* Header on background - Content vs Context pattern */}
      <h2 className="condition-assessment__title">
        Property Condition Assessment
      </h2>
      {/* Seamless Command Surface - glass background, hairline border, no opaque card */}
      <div className="condition-assessment__surface">
        {isLoadingCondition ? (
          <div className="condition-assessment__empty-state">
            <p>Analysing building condition...</p>
          </div>
        ) : !capturedProperty ? (
          <div className="condition-assessment__empty-state condition-assessment__empty-state--prominent">
            <div className="condition-assessment__empty-icon">🏢</div>
            <p className="condition-assessment__empty-title">
              Capture a property to generate the developer condition assessment
            </p>
            <p className="condition-assessment__empty-subtitle">
              Structural, M&amp;E, and compliance insights will appear here with
              targeted actions.
            </p>
          </div>
        ) : !conditionAssessment ? (
          <div
            className={`condition-assessment__empty-state ${(capturedProperty as { propertyId?: string })?.propertyId === 'offline-property' ? '' : 'condition-assessment__empty-state--warning'}`}
          >
            <p>
              {(capturedProperty as { propertyId?: string })?.propertyId ===
              'offline-property'
                ? 'Condition assessment not available in offline mode. Capture a real property to access inspection data.'
                : 'Unable to load condition assessment. Please retry after refreshing the capture.'}
            </p>
          </div>
        ) : (
          <div className="condition-assessment__content">
            {/* 12-column grid layout: 4 cols (gauge) + 8 cols (actions) */}
            <Grid container spacing={2}>
              {/* Left column: Overall Rating Gauge */}
              <Grid item xs={12} lg={4}>
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
                  attachments={conditionAssessment.attachments.map((a) => ({
                    label: a.label,
                    url: a.url ?? null,
                  }))}
                />
              </Grid>

              {/* Right column: Immediate Actions + AI Insight + CTAs */}
              <Grid item xs={12} lg={8}>
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--ob-space-150)',
                    height: '100%',
                  }}
                >
                  {/* Immediate Actions Grid (2x2) */}
                  <ImmediateActionsGrid
                    actions={conditionAssessment.recommendedActions
                      .slice(0, 4)
                      .map(
                        (action, index): ImmediateAction => ({
                          id: `action-${index}`,
                          title: action.split(':')[0] || action.slice(0, 30),
                          description: action.includes(':')
                            ? action.split(':').slice(1).join(':').trim()
                            : action,
                          priority:
                            index === 0
                              ? 'critical'
                              : index === 1
                                ? 'high'
                                : 'medium',
                        }),
                      )}
                  />

                  {/* AI Insight Panel */}
                  {conditionAssessment.summary && (
                    <AIInsightPanel
                      insight={`${conditionAssessment.summary} Focus remediation on ${
                        conditionAssessment.systems
                          .filter((s) => s.rating === 'D' || s.rating === 'F')
                          .map((s) => s.name)
                          .join(', ') ||
                        'structural integrity and ageing M&E plant'
                      } to maintain operational efficiency.`}
                    />
                  )}

                  {/* Consolidated CTAs */}
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'flex-end',
                      gap: 'var(--ob-space-100)',
                      mt: 'auto',
                    }}
                  >
                    <button
                      type="button"
                      onClick={() => openAssessmentEditor('edit')}
                      disabled={!latestAssessmentEntry}
                      className="condition-assessment__cta-btn condition-assessment__cta-btn--ghost"
                    >
                      Manual Inspection Capture
                    </button>
                    <button
                      type="button"
                      onClick={() => openAssessmentEditor('new')}
                      className="condition-assessment__cta-btn condition-assessment__cta-btn--primary"
                    >
                      Log Full Inspection →
                    </button>
                  </Box>
                </Box>
              </Grid>
            </Grid>

            {/* Condition Insights - Seamless panel */}
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
                  <Typography
                    variant="h4"
                    sx={{
                      m: 0,
                      fontSize: 'var(--ob-font-size-base)',
                      fontWeight: 600,
                      letterSpacing: '-0.01em',
                      color: 'text.primary',
                    }}
                  >
                    Condition insights
                  </Typography>
                  <Typography
                    sx={{
                      fontSize: 'var(--ob-font-size-sm)',
                      color: 'text.secondary',
                    }}
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
            )}

            {/* Systems Grid */}
            <Box
              sx={{
                display: 'grid',
                gap: 'var(--ob-space-100)',
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
                    ? comparison?.previous?.score
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

            {/* Consolidated Bottom Row: Inspection History + Scenario Overrides (6:6 grid) */}
            <Grid container spacing={2}>
              {/* Left: Inspection History */}
              <Grid item xs={12} md={6}>
                <InlineInspectionHistorySummary />
              </Grid>

              {/* Right: Scenario Overrides - Seamless panel */}
              <Grid item xs={12} md={6}>
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
                  {/* Header */}
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
                        Scenario Overrides
                      </Typography>
                      <Typography
                        sx={{
                          mt: 'var(--ob-space-025)',
                          fontSize: 'var(--ob-font-size-xs)',
                          color: 'text.secondary',
                        }}
                      >
                        Compare assessments across scenarios.
                      </Typography>
                    </Box>
                    <Box
                      sx={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: 'var(--ob-space-075)',
                      }}
                    >
                      <button
                        type="button"
                        onClick={() => handleReportExport('json')}
                        disabled={!capturedProperty || isExportingReport}
                        className="condition-assessment__export-btn condition-assessment__export-btn--primary"
                      >
                        {isExportingReport ? 'Exporting…' : 'JSON'}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleReportExport('pdf')}
                        disabled={!capturedProperty || isExportingReport}
                        className="condition-assessment__export-btn condition-assessment__export-btn--secondary"
                      >
                        {isExportingReport ? 'Exporting…' : 'PDF'}
                      </button>
                    </Box>
                  </Box>

                  {/* Content */}
                  {scenarioAssessmentsError ? (
                    <Typography
                      sx={{
                        m: 0,
                        fontSize: 'var(--ob-font-size-sm)',
                        color: 'error.main',
                      }}
                    >
                      {scenarioAssessmentsError}
                    </Typography>
                  ) : isLoadingScenarioAssessments ? (
                    <Typography
                      sx={{
                        m: 0,
                        fontSize: 'var(--ob-font-size-sm)',
                        color: 'text.secondary',
                      }}
                    >
                      Loading scenario overrides...
                    </Typography>
                  ) : scenarioOverrideEntries.length === 0 ? (
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
                        No scenario-specific overrides recorded yet. Save an
                        inspection for a specific scenario to compare outcomes.
                      </Typography>
                    </Box>
                  ) : (
                    <Box
                      sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 'var(--ob-space-075)',
                      }}
                    >
                      {/* Baseline selector */}
                      {scenarioOverrideEntries.length > 1 &&
                        baseScenarioAssessment && (
                          <Box
                            component="label"
                            sx={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: 'var(--ob-space-050)',
                              fontSize: 'var(--ob-font-size-xs)',
                              color: 'text.secondary',
                            }}
                          >
                            <Typography
                              component="span"
                              sx={{ fontWeight: 600, fontSize: 'inherit' }}
                            >
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

                      {/* Compact baseline summary - Seamless panel */}
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
                            {formatScenarioLabel(
                              baseScenarioAssessment.scenario,
                            )}
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
                            <Typography
                              component="span"
                              sx={{
                                fontSize: 'inherit',
                                color: 'text.primary',
                                fontWeight: 600,
                              }}
                            >
                              {baseScenarioAssessment.overallRating}
                            </Typography>
                            <Typography
                              component="span"
                              sx={{
                                fontSize: 'inherit',
                                color: 'text.secondary',
                              }}
                            >
                              {baseScenarioAssessment.overallScore}/100
                            </Typography>
                            <Typography
                              component="span"
                              sx={{
                                fontSize: 'inherit',
                                color: 'text.secondary',
                                textTransform: 'capitalize',
                              }}
                            >
                              {baseScenarioAssessment.riskLevel} risk
                            </Typography>
                          </Box>
                        </Box>
                      )}

                      {/* Comparison count */}
                      {scenarioComparisonEntries.length > 0 ? (
                        <Typography
                          sx={{
                            fontSize: 'var(--ob-font-size-xs)',
                            color: 'text.secondary',
                          }}
                        >
                          {scenarioComparisonEntries.length} scenario
                          {scenarioComparisonEntries.length !== 1 ? 's' : ''} to
                          compare
                        </Typography>
                      ) : (
                        <Typography
                          sx={{
                            fontSize: 'var(--ob-font-size-xs)',
                            color: 'text.secondary',
                          }}
                        >
                          Capture another scenario to compare.
                        </Typography>
                      )}
                    </Box>
                  )}
                </Box>
              </Grid>
            </Grid>
          </div>
        )}
      </div>
    </section>
  )
}
