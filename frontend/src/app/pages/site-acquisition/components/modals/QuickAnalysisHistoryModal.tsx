/**
 * Quick Analysis History Modal
 *
 * Displays historical snapshots of quick analysis results across scenarios.
 * Uses createPortal to render outside the main component tree.
 */

import { createPortal } from 'react-dom'
import type { DevelopmentScenario } from '../../../../../api/siteAcquisition'
import type { QuickAnalysisSnapshot, ScenarioOption, ScenarioComparisonMetric } from '../../types'
import { formatTimestamp } from '../../utils/formatters'

// ============================================================================
// Types
// ============================================================================

export interface QuickAnalysisHistoryModalProps {
  isOpen: boolean
  onClose: () => void
  quickAnalysisHistory: QuickAnalysisSnapshot[]
  scenarioLookup: Map<DevelopmentScenario, ScenarioOption>
  formatScenarioLabel: (scenario: DevelopmentScenario | 'all' | null | undefined) => string
  summariseScenarioMetrics: (metrics: Record<string, unknown>) => ScenarioComparisonMetric[]
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
        background: 'rgba(0,0,0,0.45)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem',
        zIndex: 1000,
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Quick analysis history"
        onClick={(event) => event.stopPropagation()}
        style={{
          background: 'white',
          borderRadius: '16px',
          maxWidth: '900px',
          width: '100%',
          maxHeight: '85vh',
          overflowY: 'auto',
          boxShadow: '0 20px 40px rgba(0,0,0,0.25)',
          padding: '2rem',
          position: 'relative',
        }}
      >
        <button
          type="button"
          onClick={onClose}
          aria-label="Close quick analysis history"
          style={{
            position: 'absolute',
            top: '1rem',
            right: '1rem',
            border: 'none',
            background: 'transparent',
            fontSize: '1.5rem',
            cursor: 'pointer',
            color: '#6e6e73',
          }}
        >
          ×
        </button>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
            <h2
              style={{
                margin: 0,
                fontSize: '1.4rem',
                fontWeight: 600,
                letterSpacing: '-0.01em',
              }}
            >
              Quick analysis history
            </h2>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#4b5563' }}>
              Review the last {quickAnalysisHistory.length} generated snapshots of
              multi-scenario feasibility metrics.
            </p>
          </div>
          {quickAnalysisHistory.length === 0 ? (
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#6b7280' }}>
              Capture a property to build the quick analysis history timeline.
            </p>
          ) : (
            quickAnalysisHistory.map((snapshot) => (
              <article
                key={`${snapshot.propertyId}-${snapshot.generatedAt}`}
                style={{
                  border: '1px solid #e5e7eb',
                  borderRadius: '14px',
                  padding: '1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1rem',
                  background: '#f9fafb',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'baseline',
                    flexWrap: 'wrap',
                    gap: '0.5rem',
                  }}
                >
                  <h3
                    style={{
                      margin: 0,
                      fontSize: '1.05rem',
                      fontWeight: 600,
                      letterSpacing: '-0.01em',
                    }}
                  >
                    Generated {formatTimestamp(snapshot.generatedAt)}
                  </h3>
                  <span style={{ fontSize: '0.8rem', color: '#6b7280' }}>
                    Property ID: {snapshot.propertyId}
                  </span>
                </div>
                <div
                  style={{
                    display: 'grid',
                    gap: '1rem',
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
                          border: '1px solid #e5e7eb',
                          borderRadius: '12px',
                          padding: '1rem',
                          background: 'white',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '0.6rem',
                        }}
                      >
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                          <span
                            style={{ fontSize: '0.75rem', color: '#6b7280', textTransform: 'uppercase' }}
                          >
                            Scenario
                          </span>
                          <span
                            style={{ fontSize: '1rem', fontWeight: 600, color: '#111827' }}
                          >
                            {label}
                          </span>
                        </div>
                        {scenario.headline && (
                          <p style={{ margin: 0, fontSize: '0.85rem', color: '#374151' }}>
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
                              gap: '0.35rem',
                            }}
                          >
                            {metrics.map((metric) => (
                              <li key={`${scenarioKey}-${metric.key}`}>
                                <span
                                  style={{
                                    display: 'block',
                                    fontSize: '0.75rem',
                                    letterSpacing: '0.06em',
                                    textTransform: 'uppercase',
                                    color: '#9ca3af',
                                  }}
                                >
                                  {metric.label}
                                </span>
                                <span
                                  style={{ fontSize: '0.9rem', fontWeight: 600, color: '#1f2937' }}
                                >
                                  {formatScenarioMetricValue(metric.key, metric.value)}
                                </span>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p style={{ margin: 0, fontSize: '0.8rem', color: '#6b7280' }}>
                            No quantitative metrics captured for this scenario run.
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
