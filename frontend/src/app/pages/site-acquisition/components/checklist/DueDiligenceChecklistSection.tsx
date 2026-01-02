/**
 * Due Diligence Checklist Section Component
 *
 * Displays the checklist grouped by category with progress tracking.
 * Receives all data and handlers via props (no internal state).
 *
 * NOTE: Scenario tabs have been REMOVED from this component.
 * The global ScenarioFocusSection is the single source of truth for scenario filtering.
 * This eliminates UI redundancy where scenario selection appeared in multiple places.
 *
 * @see ScenarioFocusSection - Global scenario filter
 */

import type {
  ChecklistItem,
  DevelopmentScenario,
} from '../../../../../api/siteAcquisition'
import { Button } from '../../../../../components/canonical/Button'
import { Link } from '../../../../../router'
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
  displaySummary: ChecklistSummary | null
  activeScenario: 'all' | DevelopmentScenario
  activeScenarioDetails: ScenarioOption | null | undefined
  selectedCategory: string | null
  isLoadingChecklist: boolean

  // Handlers (stable callbacks from parent hook)
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
  displaySummary,
  activeScenario,
  activeScenarioDetails,
  selectedCategory,
  isLoadingChecklist,
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
            style={{ textDecoration: 'none' }}
          >
            <Button variant="secondary" size="sm">
              Manage templates
            </Button>
          </Link>
        </div>
      </div>

      {/* Content - seamless glass surface */}
      {/* NOTE: Scenario tabs REMOVED - use ScenarioFocusSection for global filtering */}
      <div className="ob-seamless-panel ob-seamless-panel--glass due-diligence__surface">
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
