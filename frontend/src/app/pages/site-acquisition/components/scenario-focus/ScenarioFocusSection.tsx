/**
 * Scenario Focus Section Component
 *
 * Displays the scenario selector bar with toggle buttons for switching between
 * development scenarios. Shows active scenario summary, comparison/history buttons,
 * and progress indicators for each scenario.
 */

import type { DevelopmentScenario } from '../../../../../api/siteAcquisition'
import type { ScenarioOption } from '../../types'

// ============================================================================
// Types
// ============================================================================

/** Simple progress stats shape returned by useScenarioComparison hook */
type ProgressStats = { total: number; completed: number } | null | undefined

export interface ScenarioFocusSectionProps {
  // Data
  scenarioFocusOptions: Array<'all' | DevelopmentScenario>
  scenarioLookup: Map<DevelopmentScenario, ScenarioOption>
  activeScenario: 'all' | DevelopmentScenario
  activeScenarioSummary: {
    label: string
    headline: string
    detail?: string | null
  }
  scenarioChecklistProgress: Record<
    string,
    { total: number; completed: number }
  >
  displaySummary: ProgressStats

  // History state
  quickAnalysisHistoryCount: number
  scenarioComparisonVisible: boolean

  // Callbacks
  setActiveScenario: (scenario: 'all' | DevelopmentScenario) => void
  onCompareScenarios: () => void
  onOpenQuickAnalysisHistory: () => void
  onOpenInspectionHistory: () => void
  formatScenarioLabel: (
    scenario: DevelopmentScenario | 'all' | null | undefined,
  ) => string
}

// ============================================================================
// Component
// ============================================================================

export function ScenarioFocusSection({
  scenarioFocusOptions,
  scenarioLookup,
  activeScenario,
  activeScenarioSummary,
  scenarioChecklistProgress,
  displaySummary,
  quickAnalysisHistoryCount,
  scenarioComparisonVisible,
  setActiveScenario,
  onCompareScenarios,
  onOpenQuickAnalysisHistory,
  onOpenInspectionHistory,
  formatScenarioLabel,
}: ScenarioFocusSectionProps) {
  return (
    <section
      style={{
        background: 'var(--ob-color-bg-surface-elevated)',
        border: '1px solid var(--ob-color-border-subtle)',
        borderRadius: 'var(--ob-radius-sm)',
        padding: '1.5rem',
        marginBottom: '2rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem',
          marginBottom: '1rem',
        }}
      >
        <div
          style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}
        >
          <span
            style={{
              fontSize: '0.8125rem',
              fontWeight: 600,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: 'var(--ob-color-text-muted)',
            }}
          >
            Scenario focus
          </span>
          <span
            style={{
              fontSize: '0.95rem',
              color: 'var(--ob-color-text-secondary)',
            }}
          >
            Switch context to see checklist, feasibility, and inspections for
            the selected development path.
          </span>
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            flexWrap: 'wrap',
          }}
        >
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '0.2rem',
              minWidth: '180px',
            }}
          >
            <span
              style={{
                fontWeight: 700,
                color: 'var(--ob-color-text-primary)',
              }}
            >
              {activeScenarioSummary.label}
            </span>
            <span
              style={{
                fontSize: '0.82rem',
                color: 'var(--ob-color-text-secondary)',
              }}
            >
              {activeScenarioSummary.headline}
            </span>
            {activeScenarioSummary.detail && (
              <span
                style={{
                  fontSize: '0.78rem',
                  color: 'var(--ob-color-text-muted)',
                }}
              >
                {activeScenarioSummary.detail}
              </span>
            )}
          </div>
          <div
            style={{
              display: 'flex',
              gap: '0.65rem',
              flexWrap: 'wrap',
            }}
          >
            <button
              type="button"
              onClick={onCompareScenarios}
              disabled={!scenarioComparisonVisible}
              style={{
                borderRadius: 'var(--ob-radius-pill)',
                border: '1px solid var(--ob-color-text-primary)',
                background: scenarioComparisonVisible
                  ? 'var(--ob-color-text-primary)'
                  : 'var(--ob-color-bg-surface-elevated)',
                color: scenarioComparisonVisible
                  ? 'white'
                  : 'var(--ob-color-text-muted)',
                padding: '0.45rem 0.95rem',
                fontSize: '0.78rem',
                fontWeight: 600,
                cursor: scenarioComparisonVisible ? 'pointer' : 'not-allowed',
              }}
            >
              Compare scenarios
            </button>
            <button
              type="button"
              onClick={onOpenQuickAnalysisHistory}
              disabled={quickAnalysisHistoryCount === 0}
              style={{
                borderRadius: 'var(--ob-radius-pill)',
                border: '1px solid var(--ob-color-border-subtle)',
                background:
                  quickAnalysisHistoryCount === 0
                    ? 'var(--ob-color-bg-surface-elevated)'
                    : 'white',
                color:
                  quickAnalysisHistoryCount === 0
                    ? 'var(--ob-color-text-muted)'
                    : 'var(--ob-color-text-primary)',
                padding: '0.45rem 0.95rem',
                fontSize: '0.78rem',
                fontWeight: 600,
                cursor:
                  quickAnalysisHistoryCount === 0 ? 'not-allowed' : 'pointer',
              }}
            >
              Quick analysis history ({quickAnalysisHistoryCount})
            </button>
            <button
              type="button"
              onClick={onOpenInspectionHistory}
              style={{
                borderRadius: 'var(--ob-radius-pill)',
                border: '1px solid var(--ob-color-border-subtle)',
                background: 'white',
                color: 'var(--ob-color-text-primary)',
                padding: '0.45rem 0.95rem',
                fontSize: '0.78rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Inspection history
            </button>
          </div>
        </div>
      </div>
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.75rem',
        }}
      >
        {scenarioFocusOptions.map((scenarioKey) => {
          const option =
            scenarioKey === 'all' ? null : scenarioLookup.get(scenarioKey)
          const label =
            scenarioKey === 'all'
              ? 'All scenarios'
              : (option?.label ?? formatScenarioLabel(scenarioKey))
          const icon = scenarioKey === 'all' ? '🌐' : (option?.icon ?? '🏗️')
          const isActive = activeScenario === scenarioKey
          const progressStats =
            scenarioKey === 'all'
              ? displaySummary
              : scenarioChecklistProgress[scenarioKey]
          const progressLabel = progressStats
            ? `${progressStats.completed}/${progressStats.total || 0}`
            : null
          const progressPercent =
            progressStats && progressStats.total > 0
              ? Math.round(
                  (progressStats.completed / progressStats.total) * 100,
                )
              : null

          return (
            <button
              key={scenarioKey}
              type="button"
              onClick={() => setActiveScenario(scenarioKey)}
              aria-pressed={isActive}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.65rem',
                borderRadius: 'var(--ob-radius-pill)',
                border: `1px solid ${isActive ? 'var(--ob-color-brand-primary)' : 'var(--ob-color-border-subtle)'}`,
                background: isActive ? 'var(--ob-info-50)' : 'white',
                color: isActive
                  ? 'var(--ob-color-brand-primary)'
                  : 'var(--ob-color-text-primary)',
                padding: '0.55rem 1.1rem',
                fontSize: '0.95rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
            >
              <span style={{ fontSize: '1.2rem' }}>{icon}</span>
              <span>{label}</span>
              {progressLabel && (
                <span
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    minWidth: '2.5rem',
                    padding: '0.2rem 0.6rem',
                    borderRadius: 'var(--ob-radius-pill)',
                    background: isActive
                      ? 'var(--ob-color-brand-primary)'
                      : 'var(--ob-color-border-subtle)',
                    color: isActive ? 'white' : 'var(--ob-color-text-primary)',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                  }}
                  title={
                    progressPercent !== null
                      ? `${progressStats?.completed ?? 0} of ${
                          progressStats?.total ?? 0
                        } items completed (${progressPercent}%)`
                      : undefined
                  }
                >
                  {progressLabel}
                </span>
              )}
            </button>
          )
        })}
      </div>
    </section>
  )
}
