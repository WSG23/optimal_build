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

  // History state
  quickAnalysisHistoryCount: number
  scenarioComparisonVisible: boolean

  // Callbacks
  setActiveScenario: (scenario: 'all' | DevelopmentScenario) => void
  onCompareScenarios: () => void
  onOpenQuickAnalysisHistory: () => void
  onOpenDueDiligence: () => void
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
  quickAnalysisHistoryCount,
  scenarioComparisonVisible,
  setActiveScenario,
  onCompareScenarios,
  onOpenQuickAnalysisHistory,
  onOpenDueDiligence,
  formatScenarioLabel,
}: ScenarioFocusSectionProps) {
  return (
    <section className="scenario-focus">
      {/* Header on background - Content vs Context pattern */}
      <h3 className="scenario-focus__title">Scenario Focus</h3>
      <p className="scenario-focus__description">
        Switch context to review instant zoning, envelope, and capture scenario
        scans for the selected development path.
      </p>

      {/* Content - seamless glass surface */}
      <div className="ob-seamless-panel ob-seamless-panel--glass scenario-focus__surface">
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
              onClick={onOpenDueDiligence}
              className="scenario-focus__action-btn"
            >
              Open Due Diligence
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
              </button>
            )
          })}
        </div>
      </div>
    </section>
  )
}
