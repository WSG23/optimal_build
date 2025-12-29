/**
 * Due Diligence Checklist Section Component
 *
 * Displays the checklist grouped by category with progress tracking.
 * Receives all data and handlers via props (no internal state).
 */

import { Link } from '../../../../../router'
import type {
  ChecklistItem,
  DevelopmentScenario,
} from '../../../../../api/siteAcquisition'
import type { ScenarioOption } from '../../constants'
import { formatCategoryName } from '../../utils'

// ============================================================================
// Types
// ============================================================================

export interface ChecklistSummary {
  completed: number
  total: number
  completionPercentage: number
}

export interface DueDiligenceChecklistSectionProps {
  // Data
  capturedProperty: unknown | null
  checklistItems: ChecklistItem[]
  filteredChecklistItems: ChecklistItem[]
  availableChecklistScenarios: DevelopmentScenario[]
  scenarioLookup: Map<DevelopmentScenario, ScenarioOption>
  displaySummary: ChecklistSummary | null
  activeScenario: 'all' | DevelopmentScenario
  activeScenarioDetails: ScenarioOption | null | undefined
  selectedCategory: string | null
  isLoadingChecklist: boolean

  // Handlers (stable callbacks from parent hook)
  setActiveScenario: (scenario: 'all' | DevelopmentScenario) => void
  setSelectedCategory: (category: string | null) => void
  handleChecklistUpdate: (
    itemId: string,
    status: 'pending' | 'in_progress' | 'completed' | 'not_applicable',
  ) => void
}

// ============================================================================
// Component
// ============================================================================

export function DueDiligenceChecklistSection({
  capturedProperty,
  checklistItems,
  filteredChecklistItems,
  availableChecklistScenarios,
  scenarioLookup,
  displaySummary,
  activeScenario,
  activeScenarioDetails,
  selectedCategory,
  isLoadingChecklist,
  setActiveScenario,
  setSelectedCategory,
  handleChecklistUpdate,
}: DueDiligenceChecklistSectionProps) {
  return (
    <section className="due-diligence">
      {/* Header on background - Content vs Context pattern */}
      <div className="due-diligence__header">
        <div className="due-diligence__header-content">
          <h2 className="due-diligence__title">Due Diligence Checklist</h2>
          {displaySummary && (
            <p className="due-diligence__subtitle">
              {activeScenario === 'all'
                ? 'Overall progress'
                : `${activeScenarioDetails?.label ?? 'Scenario'}`}
              : {displaySummary.completed} of {displaySummary.total} items
              completed ({displaySummary.completionPercentage.toFixed(0)}%)
            </p>
          )}
          {activeScenarioDetails?.description && (
            <p className="due-diligence__description">
              {activeScenarioDetails.description}
            </p>
          )}
        </div>
        <div className="due-diligence__header-actions">
          <Link
            to="/app/site-acquisition/checklist-templates"
            className="due-diligence__link-btn"
          >
            Manage templates
          </Link>
        </div>
      </div>

      {/* Content in card - Content vs Context pattern */}
      <div className="ob-card-module due-diligence__card">
        {/* Scenario filter tabs */}
        {availableChecklistScenarios.length > 0 && (
          <div className="due-diligence__scenario-tabs">
            <button
              type="button"
              onClick={() => setActiveScenario('all')}
              className={`due-diligence__scenario-tab ${activeScenario === 'all' ? 'due-diligence__scenario-tab--active' : ''}`}
            >
              All scenarios
            </button>
            {availableChecklistScenarios.map((scenario) => {
              const option = scenarioLookup.get(scenario)
              const isActive = activeScenario === scenario
              return (
                <button
                  key={scenario}
                  type="button"
                  onClick={() => setActiveScenario(scenario)}
                  className={`due-diligence__scenario-tab ${isActive ? 'due-diligence__scenario-tab--active' : ''}`}
                >
                  {option?.icon ? (
                    <span className="due-diligence__scenario-icon">
                      {option.icon}
                    </span>
                  ) : null}
                  <span>{option?.label ?? formatCategoryName(scenario)}</span>
                </button>
              )
            })}
          </div>
        )}

        {/* Content states */}
        {isLoadingChecklist ? (
          <div className="due-diligence__empty-state">
            <p>Loading checklist...</p>
          </div>
        ) : !capturedProperty ? (
          <div className="due-diligence__empty-state due-diligence__empty-state--prominent">
            <div className="due-diligence__empty-icon">📋</div>
            <p className="due-diligence__empty-title">
              Capture a property to view the comprehensive due diligence
              checklist
            </p>
            <p className="due-diligence__empty-subtitle">
              Automatically generated based on selected development scenarios
            </p>
          </div>
        ) : checklistItems.length === 0 ? (
          <div className="due-diligence__empty-state">
            <p>No checklist items found for this property.</p>
          </div>
        ) : filteredChecklistItems.length === 0 ? (
          <div className="due-diligence__empty-state">
            <p>
              No checklist items for{' '}
              {activeScenarioDetails?.label ?? 'this scenario'} yet.
            </p>
          </div>
        ) : (
          <>
            {/* Progress bar */}
            {displaySummary && (
              <div className="due-diligence__progress-track">
                <div
                  className="due-diligence__progress-fill"
                  style={{ width: `${displaySummary.completionPercentage}%` }}
                />
              </div>
            )}

            {/* Group by category */}
            {Object.entries(
              filteredChecklistItems.reduce(
                (acc, item) => {
                  const category = item.category
                  if (!acc[category]) {
                    acc[category] = []
                  }
                  acc[category].push(item)
                  return acc
                },
                {} as Record<string, ChecklistItem[]>,
              ),
            ).map(([category, items]: [string, ChecklistItem[]]) => (
              <div key={category} className="due-diligence__category">
                <button
                  type="button"
                  onClick={() =>
                    setSelectedCategory(
                      selectedCategory === category ? null : category,
                    )
                  }
                  className="due-diligence__category-header"
                >
                  <span>{formatCategoryName(category)}</span>
                  <span className="due-diligence__category-count">
                    {items.filter((item) => item.status === 'completed').length}
                    /{items.length}
                  </span>
                </button>
                {(selectedCategory === category ||
                  selectedCategory === null) && (
                  <div className="due-diligence__category-items">
                    {items.map((item) => (
                      <div key={item.id} className="due-diligence__item">
                        <select
                          value={item.status}
                          onChange={(e) =>
                            handleChecklistUpdate(
                              item.id,
                              e.target.value as
                                | 'pending'
                                | 'in_progress'
                                | 'completed'
                                | 'not_applicable',
                            )
                          }
                          className="due-diligence__item-select"
                        >
                          <option value="pending">Pending</option>
                          <option value="in_progress">In Progress</option>
                          <option value="completed">Completed</option>
                          <option value="not_applicable">Not Applicable</option>
                        </select>
                        <div className="due-diligence__item-content">
                          <div className="due-diligence__item-header">
                            <h4 className="due-diligence__item-title">
                              {item.itemTitle}
                            </h4>
                            {item.priority === 'critical' && (
                              <span className="due-diligence__priority due-diligence__priority--critical">
                                CRITICAL
                              </span>
                            )}
                            {item.priority === 'high' && (
                              <span className="due-diligence__priority due-diligence__priority--high">
                                HIGH
                              </span>
                            )}
                          </div>
                          {item.itemDescription && (
                            <p className="due-diligence__item-description">
                              {item.itemDescription}
                            </p>
                          )}
                          {item.requiresProfessional &&
                            item.professionalType && (
                              <p className="due-diligence__item-professional">
                                Requires: {item.professionalType}
                              </p>
                            )}
                          {item.dueDate && (
                            <p className="due-diligence__item-due">
                              Due: {new Date(item.dueDate).toLocaleDateString()}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </>
        )}
      </div>
    </section>
  )
}
