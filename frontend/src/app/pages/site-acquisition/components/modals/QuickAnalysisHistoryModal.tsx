/**
 * Quick Analysis History Modal
 *
 * Displays historical snapshots of quick analysis results across scenarios.
 * Uses createPortal to render outside the main component tree.
 */

import { createPortal } from 'react-dom'
import { IconButton } from '@mui/material'
import { Close } from '@mui/icons-material'
import type { DevelopmentScenario } from '../../../../../api/siteAcquisition'
import type {
  QuickAnalysisSnapshot,
  ScenarioOption,
  ScenarioComparisonMetric,
} from '../../types'
import { formatTimestamp } from '../../utils/formatters'

// ============================================================================
// Types
// ============================================================================

export interface QuickAnalysisHistoryModalProps {
  isOpen: boolean
  onClose: () => void
  quickAnalysisHistory: QuickAnalysisSnapshot[]
  scenarioLookup: Map<DevelopmentScenario, ScenarioOption>
  formatScenarioLabel: (
    scenario: DevelopmentScenario | 'all' | null | undefined,
  ) => string
  summariseScenarioMetrics: (
    metrics: Record<string, unknown>,
  ) => ScenarioComparisonMetric[]
  formatScenarioMetricValue: (key: string, value: unknown) => string
}

// ============================================================================
// Component
// ============================================================================

export function QuickAnalysisHistoryModal({
  isOpen,
  onClose,
  quickAnalysisHistory,
  scenarioLookup,
  formatScenarioLabel,
  summariseScenarioMetrics,
  formatScenarioMetricValue,
}: QuickAnalysisHistoryModalProps) {
  if (!isOpen) return null

  return createPortal(
    <div
      role="presentation"
      onClick={(event) => {
        if (event.target === event.currentTarget) {
          onClose()
        }
      }}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'var(--ob-overlay-dark)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--ob-space-200)',
        zIndex: 1000,
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Quick analysis history"
        onClick={(event) => event.stopPropagation()}
        style={{
          background: 'var(--ob-color-bg-surface)',
          borderRadius: 'var(--ob-radius-lg)',
          maxWidth: '900px',
          width: '100%',
          maxHeight: '85vh',
          overflowY: 'auto',
          boxShadow: 'var(--ob-shadow-lg)',
          padding: 'var(--ob-space-200)',
          position: 'relative',
        }}
      >
        <IconButton
          onClick={onClose}
          aria-label="Close quick analysis history"
          sx={{
            position: 'absolute',
            top: 'var(--ob-space-100)',
            right: 'var(--ob-space-100)',
            color: 'var(--ob-color-text-muted)',
          }}
        >
          <Close />
        </IconButton>
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--ob-space-150)',
          }}
        >
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-025)',
            }}
          >
            <h2
              style={{
                margin: 0,
                fontSize: 'var(--ob-font-size-xl)',
                fontWeight: 600,
                letterSpacing: 'var(--ob-letter-spacing-tight)',
              }}
            >
              Quick analysis history
            </h2>
            <p
              style={{
                margin: 0,
                fontSize: 'var(--ob-font-size-sm)',
                color: 'var(--ob-color-text-secondary)',
              }}
            >
              Review the last {quickAnalysisHistory.length} generated snapshots
              of multi-scenario feasibility metrics.
            </p>
          </div>
          {quickAnalysisHistory.length === 0 ? (
            <p
              style={{
                margin: 0,
                fontSize: 'var(--ob-font-size-sm)',
                color: 'var(--ob-color-text-muted)',
              }}
            >
              Capture a property to build the quick analysis history timeline.
            </p>
          ) : (
            quickAnalysisHistory.map((snapshot) => (
              <article
                key={`${snapshot.propertyId}-${snapshot.generatedAt}`}
                style={{
                  border: '1px solid var(--ob-color-border-subtle)',
                  borderRadius: 'var(--ob-radius-sm)',
                  padding: 'var(--ob-space-150)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--ob-space-100)',
                  background: 'var(--ob-color-bg-muted)',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'baseline',
                    flexWrap: 'wrap',
                    gap: 'var(--ob-space-050)',
                  }}
                >
                  <h3
                    style={{
                      margin: 0,
                      fontSize: 'var(--ob-font-size-lg)',
                      fontWeight: 600,
                      letterSpacing: 'var(--ob-letter-spacing-tight)',
                    }}
                  >
                    Generated {formatTimestamp(snapshot.generatedAt)}
                  </h3>
                  <span
                    style={{
                      fontSize: 'var(--ob-font-size-xs)',
                      color: 'var(--ob-color-text-muted)',
                    }}
                  >
                    Property ID: {snapshot.propertyId}
                  </span>
                </div>
                <div
                  style={{
                    display: 'grid',
                    gap: 'var(--ob-space-100)',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                  }}
                >
                  {snapshot.scenarios.map((scenario) => {
                    const scenarioKey =
                      typeof scenario.scenario === 'string'
                        ? (scenario.scenario as DevelopmentScenario)
                        : 'raw_land'
                    const label =
                      scenarioLookup.get(scenarioKey)?.label ??
                      formatScenarioLabel(scenarioKey)
                    const metrics = summariseScenarioMetrics(
                      scenario.metrics ?? {},
                    )
                    return (
                      <section
                        key={`${snapshot.generatedAt}-${scenarioKey}`}
                        style={{
                          border: '1px solid var(--ob-color-border-subtle)',
                          borderRadius: 'var(--ob-radius-sm)',
                          padding: 'var(--ob-space-100)',
                          background: 'var(--ob-color-bg-surface)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: 'var(--ob-space-065)',
                        }}
                      >
                        <div
                          style={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 'var(--ob-space-025)',
                          }}
                        >
                          <span
                            style={{
                              fontSize: 'var(--ob-font-size-xs)',
                              color: 'var(--ob-color-text-muted)',
                              textTransform: 'uppercase',
                            }}
                          >
                            Scenario
                          </span>
                          <span
                            style={{
                              fontSize: 'var(--ob-font-size-base)',
                              fontWeight: 600,
                              color: 'var(--ob-color-text-primary)',
                            }}
                          >
                            {label}
                          </span>
                        </div>
                        {scenario.headline && (
                          <p
                            style={{
                              margin: 0,
                              fontSize: 'var(--ob-font-size-sm)',
                              color: 'var(--ob-color-text-secondary)',
                            }}
                          >
                            {scenario.headline}
                          </p>
                        )}
                        {metrics.length > 0 ? (
                          <ul
                            style={{
                              margin: 0,
                              padding: 0,
                              listStyle: 'none',
                              display: 'flex',
                              flexDirection: 'column',
                              gap: 'var(--ob-space-035)',
                            }}
                          >
                            {metrics.map((metric) => (
                              <li key={`${scenarioKey}-${metric.key}`}>
                                <span
                                  style={{
                                    display: 'block',
                                    fontSize: 'var(--ob-font-size-xs)',
                                    letterSpacing:
                                      'var(--ob-letter-spacing-widest)',
                                    textTransform: 'uppercase',
                                    color: 'var(--ob-color-text-muted)',
                                  }}
                                >
                                  {metric.label}
                                </span>
                                <span
                                  style={{
                                    fontSize: 'var(--ob-font-size-sm)',
                                    fontWeight: 600,
                                    color: 'var(--ob-color-text-primary)',
                                  }}
                                >
                                  {formatScenarioMetricValue(
                                    metric.key,
                                    metric.value,
                                  )}
                                </span>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p
                            style={{
                              margin: 0,
                              fontSize: 'var(--ob-font-size-xs)',
                              color: 'var(--ob-color-text-muted)',
                            }}
                          >
                            No quantitative metrics captured for this scenario
                            run.
                          </p>
                        )}
                      </section>
                    )
                  })}
                </div>
              </article>
            ))
          )}
        </div>
      </div>
    </div>,
    document.body,
  )
}
