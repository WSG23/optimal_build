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
    <section className="scenario-focus">
      {/* Header on background - Content vs Context pattern */}
      <h3 className="scenario-focus__title">Scenario Focus</h3>
      <p className="scenario-focus__description">
        Switch context to see checklist, feasibility, and inspections for the
        selected development path.
      </p>

      {/* Content in card */}
      <div className="ob-card-module scenario-focus__card">
        <div className="scenario-focus__summary">
          <div className="scenario-focus__summary-info">
            <span className="scenario-focus__summary-label">
              {activeScenarioSummary.label}
            </span>
            <span className="scenario-focus__summary-headline">
              {activeScenarioSummary.headline}
            </span>
            {activeScenarioSummary.detail && (
              <span className="scenario-focus__summary-detail">
                {activeScenarioSummary.detail}
              </span>
            )}
          </div>
          <div className="scenario-focus__actions">
            <button
              type="button"
              onClick={onCompareScenarios}
              disabled={!scenarioComparisonVisible}
              className={`scenario-focus__action-btn ${scenarioComparisonVisible ? 'scenario-focus__action-btn--primary' : ''}`}
            >
              Compare scenarios
            </button>
            <button
              type="button"
              onClick={onOpenQuickAnalysisHistory}
              disabled={quickAnalysisHistoryCount === 0}
              className="scenario-focus__action-btn"
            >
              Quick analysis history ({quickAnalysisHistoryCount})
            </button>
            <button
              type="button"
              onClick={onOpenInspectionHistory}
              className="scenario-focus__action-btn"
            >
              Inspection history
            </button>
          </div>
        </div>

        <div className="scenario-focus__options">
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
                className={`scenario-focus__option ${isActive ? 'scenario-focus__option--active' : ''}`}
              >
                <span className="scenario-focus__option-icon">{icon}</span>
                <span>{label}</span>
                {progressLabel && (
                  <span
                    className={`scenario-focus__option-progress ${isActive ? 'scenario-focus__option-progress--active' : ''}`}
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
      </div>
    </section>
  )
}
