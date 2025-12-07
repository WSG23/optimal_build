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
    <section
      style={{
        background: 'white',
        border: '1px solid #d2d2d7',
        borderRadius: '18px',
        padding: '2rem',
        marginBottom: '2rem',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: '1.5rem',
        }}
      >
        <div>
          <h2
            style={{
              fontSize: '1.5rem',
              fontWeight: 600,
              marginBottom: '0.5rem',
              letterSpacing: '-0.01em',
            }}
          >
            Due Diligence Checklist
          </h2>
          {displaySummary && (
            <p
              style={{
                margin: 0,
                fontSize: '0.9375rem',
                color: '#6e6e73',
              }}
            >
              {activeScenario === 'all'
                ? 'Overall progress'
                : `${activeScenarioDetails?.label ?? 'Scenario'}`}
              : {displaySummary.completed} of {displaySummary.total} items
              completed ({displaySummary.completionPercentage.toFixed(0)}%)
            </p>
          )}
          {activeScenarioDetails?.description && (
            <p
              style={{
                margin: '0.25rem 0 0',
                fontSize: '0.875rem',
                color: '#86868b',
              }}
            >
              {activeScenarioDetails.description}
            </p>
          )}
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
          }}
        >
          <Link
            to="/app/site-acquisition/checklist-templates"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              background: '#eff3ff',
              borderRadius: '999px',
              padding: '0.4rem 0.9rem',
              fontWeight: 600,
              color: '#1d4ed8',
              textDecoration: 'none',
              border: '1px solid #c7dafc',
            }}
          >
            Manage templates
          </Link>
        </div>
      </div>

      {/* Scenario filter tabs */}
      {availableChecklistScenarios.length > 0 && (
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '0.75rem',
            marginBottom: '1.5rem',
          }}
        >
          <button
            type="button"
            onClick={() => setActiveScenario('all')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem 0.85rem',
              borderRadius: '9999px',
              border: `1px solid ${activeScenario === 'all' ? '#1d1d1f' : '#d2d2d7'}`,
              background: activeScenario === 'all' ? '#1d1d1f' : '#f5f5f7',
              color: activeScenario === 'all' ? 'white' : '#1d1d1f',
              cursor: 'pointer',
              fontSize: '0.875rem',
              fontWeight: 500,
              transition: 'all 0.2s ease',
            }}
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
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem 0.85rem',
                  borderRadius: '9999px',
                  border: `1px solid ${isActive ? '#1d1d1f' : '#d2d2d7'}`,
                  background: isActive ? '#1d1d1f' : '#f5f5f7',
                  color: isActive ? 'white' : '#1d1d1f',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  transition: 'all 0.2s ease',
                }}
              >
                {option?.icon ? (
                  <span style={{ fontSize: '1rem' }}>{option.icon}</span>
                ) : null}
                <span>{option?.label ?? formatCategoryName(scenario)}</span>
              </button>
            )
          })}
        </div>
      )}

      {/* Content states */}
      {isLoadingChecklist ? (
        <div
          style={{
            padding: '3rem 2rem',
            textAlign: 'center',
            color: '#6e6e73',
          }}
        >
          <p>Loading checklist...</p>
        </div>
      ) : !capturedProperty ? (
        <div
          style={{
            padding: '3rem 2rem',
            textAlign: 'center',
            color: '#6e6e73',
            background: '#f5f5f7',
            borderRadius: '12px',
          }}
        >
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📋</div>
          <p style={{ margin: 0, fontSize: '1.0625rem' }}>
            Capture a property to view the comprehensive due diligence checklist
          </p>
          <p style={{ margin: '0.5rem 0 0', fontSize: '0.9375rem' }}>
            Automatically generated based on selected development scenarios
          </p>
        </div>
      ) : checklistItems.length === 0 ? (
        <div
          style={{
            padding: '2rem',
            textAlign: 'center',
            color: '#6e6e73',
            background: '#f5f5f7',
            borderRadius: '12px',
          }}
        >
          <p>No checklist items found for this property.</p>
        </div>
      ) : filteredChecklistItems.length === 0 ? (
        <div
          style={{
            padding: '2rem',
            textAlign: 'center',
            color: '#6e6e73',
            background: '#f5f5f7',
            borderRadius: '12px',
          }}
        >
          <p>
            No checklist items for{' '}
            {activeScenarioDetails?.label ?? 'this scenario'} yet.
          </p>
        </div>
      ) : (
        <>
          {/* Progress bar */}
          {displaySummary && (
            <div
              style={{
                marginBottom: '1.5rem',
                background: '#f5f5f7',
                borderRadius: '12px',
                height: '8px',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${displaySummary.completionPercentage}%`,
                  height: '100%',
                  background:
                    'linear-gradient(90deg, #0071e3 0%, #005bb5 100%)',
                  transition: 'width 0.3s ease',
                }}
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
            <div
              key={category}
              style={{
                marginBottom: '1.5rem',
                border: '1px solid #e5e5e7',
                borderRadius: '12px',
                overflow: 'hidden',
              }}
            >
              <button
                type="button"
                onClick={() =>
                  setSelectedCategory(
                    selectedCategory === category ? null : category,
                  )
                }
                style={{
                  width: '100%',
                  padding: '1rem 1.25rem',
                  background: '#f5f5f7',
                  border: 'none',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  cursor: 'pointer',
                  fontSize: '1rem',
                  fontWeight: 600,
                  textAlign: 'left',
                }}
              >
                <span>{formatCategoryName(category)}</span>
                <span
                  style={{
                    fontSize: '0.875rem',
                    color: '#6e6e73',
                  }}
                >
                  {items.filter((item) => item.status === 'completed').length}/
                  {items.length}
                </span>
              </button>
              {(selectedCategory === category || selectedCategory === null) && (
                <div style={{ padding: '0' }}>
                  {items.map((item) => (
                    <div
                      key={item.id}
                      style={{
                        padding: '1rem 1.25rem',
                        borderTop: '1px solid #e5e5e7',
                        display: 'flex',
                        gap: '1rem',
                        alignItems: 'flex-start',
                      }}
                    >
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
                        style={{
                          padding: '0.5rem',
                          border: '1px solid #d2d2d7',
                          borderRadius: '8px',
                          fontSize: '0.875rem',
                          background: 'white',
                          cursor: 'pointer',
                        }}
                      >
                        <option value="pending">Pending</option>
                        <option value="in_progress">In Progress</option>
                        <option value="completed">Completed</option>
                        <option value="not_applicable">Not Applicable</option>
                      </select>
                      <div style={{ flex: 1 }}>
                        <div
                          style={{
                            display: 'flex',
                            gap: '0.75rem',
                            alignItems: 'center',
                            marginBottom: '0.25rem',
                          }}
                        >
                          <h4
                            style={{
                              margin: 0,
                              fontSize: '0.9375rem',
                              fontWeight: 600,
                            }}
                          >
                            {item.itemTitle}
                          </h4>
                          {item.priority === 'critical' && (
                            <span
                              style={{
                                padding: '0.125rem 0.5rem',
                                background: '#fee2e2',
                                color: '#991b1b',
                                fontSize: '0.75rem',
                                fontWeight: 600,
                                borderRadius: '6px',
                              }}
                            >
                              CRITICAL
                            </span>
                          )}
                          {item.priority === 'high' && (
                            <span
                              style={{
                                padding: '0.125rem 0.5rem',
                                background: '#fef3c7',
                                color: '#92400e',
                                fontSize: '0.75rem',
                                fontWeight: 600,
                                borderRadius: '6px',
                              }}
                            >
                              HIGH
                            </span>
                          )}
                        </div>
                        {item.itemDescription && (
                          <p
                            style={{
                              margin: '0.5rem 0 0',
                              fontSize: '0.875rem',
                              color: '#6e6e73',
                              lineHeight: 1.5,
                            }}
                          >
                            {item.itemDescription}
                          </p>
                        )}
                        {item.requiresProfessional && item.professionalType && (
                          <p
                            style={{
                              margin: '0.5rem 0 0',
                              fontSize: '0.8125rem',
                              color: '#0071e3',
                            }}
                          >
                            Requires: {item.professionalType}
                          </p>
                        )}
                        {item.dueDate && (
                          <p
                            style={{
                              margin: '0.25rem 0 0',
                              fontSize: '0.8125rem',
                              color: '#6e6e73',
                            }}
                          >
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
    </section>
  )
}
