/**
 * Condition Assessment Editor Modal
 *
 * Modal dialog for logging or editing inspection entries.
 * Receives all data and handlers via props from the parent page.
 */

import { createPortal } from 'react-dom'
import type { DevelopmentScenario } from '../../../../../api/siteAcquisition'
import type {
  AssessmentDraftSystem,
  ConditionAssessmentDraft,
} from '../../types'
import type { ScenarioOption } from '../../constants'
import {
  SCENARIO_OPTIONS,
  CONDITION_RATINGS,
  CONDITION_RISK_LEVELS,
} from '../../constants'

// ============================================================================
// Types
// ============================================================================

export interface ConditionAssessmentEditorProps {
  // State
  isOpen: boolean
  mode: 'new' | 'edit'
  draft: ConditionAssessmentDraft
  isSaving: boolean

  // Scenario filter
  activeScenario: 'all' | DevelopmentScenario
  scenarioFocusOptions: Array<'all' | DevelopmentScenario>
  scenarioLookup: Map<DevelopmentScenario, ScenarioOption>
  formatScenarioLabel: (
    scenario: DevelopmentScenario | 'all' | null | undefined,
  ) => string

  // Handlers (stable callbacks from parent)
  onClose: () => void
  onReset: () => void
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => Promise<void>
  onFieldChange: (field: keyof ConditionAssessmentDraft, value: string) => void
  onSystemChange: (
    index: number,
    field: keyof AssessmentDraftSystem,
    value: string,
  ) => void
  setActiveScenario: (scenario: 'all' | DevelopmentScenario) => void
}

// ============================================================================
// Component
// ============================================================================

export function ConditionAssessmentEditor({
  isOpen,
  mode,
  draft,
  isSaving,
  activeScenario,
  scenarioFocusOptions,
  scenarioLookup,
  formatScenarioLabel,
  onClose,
  onReset,
  onSubmit,
  onFieldChange,
  onSystemChange,
  setActiveScenario,
}: ConditionAssessmentEditorProps) {
  if (!isOpen) {
    return null
  }

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
        aria-label="Manual inspection editor"
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
          aria-label="Close inspection editor"
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

        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            flexWrap: 'wrap',
            gap: '1rem',
            marginBottom: '1.5rem',
          }}
        >
          <div
            style={{
              maxWidth: '540px',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.35rem',
            }}
          >
            <h2
              style={{
                margin: 0,
                fontSize: '1.5rem',
                fontWeight: 600,
                letterSpacing: '-0.01em',
              }}
            >
              {mode === 'new'
                ? 'Log manual inspection'
                : 'Edit latest inspection'}
            </h2>
            <p
              style={{
                margin: 0,
                fontSize: '0.95rem',
                color: '#4b5563',
                lineHeight: 1.6,
              }}
            >
              {mode === 'new'
                ? 'Capture a manual inspection entry for the active scenario. All fields are required unless noted.'
                : 'Update the most recent inspection. Saving will append a new entry to the inspection history.'}
            </p>
            {scenarioFocusOptions.length > 0 && (
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '0.55rem',
                }}
              >
                {scenarioFocusOptions.map((option) => {
                  const isActive = activeScenario === option
                  const label =
                    option === 'all'
                      ? 'All scenarios'
                      : (scenarioLookup.get(option)?.label ??
                        formatScenarioLabel(option))
                  return (
                    <button
                      key={`editor-filter-${option}`}
                      type="button"
                      onClick={() => setActiveScenario(option)}
                      style={{
                        borderRadius: '9999px',
                        border: `1px solid ${isActive ? '#1d4ed8' : '#d2d2d7'}`,
                        background: isActive ? '#dbeafe' : 'white',
                        color: isActive ? '#1d4ed8' : '#1d1d1f',
                        padding: '0.3rem 0.9rem',
                        fontSize: '0.78rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      {label}
                    </button>
                  )
                })}
              </div>
            )}
          </div>
          <button
            type="button"
            onClick={onReset}
            disabled={isSaving}
            style={{
              border: '1px solid #d2d2d7',
              background: 'white',
              color: '#1d1d1f',
              borderRadius: '9999px',
              padding: '0.45rem 1rem',
              fontSize: '0.8125rem',
              fontWeight: 600,
              cursor: isSaving ? 'not-allowed' : 'pointer',
            }}
          >
            Reset draft
          </button>
        </div>

        <form onSubmit={onSubmit} style={{ display: 'grid', gap: '1.25rem' }}>
          <div
            style={{
              display: 'grid',
              gap: '1rem',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            }}
          >
            <label
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.4rem',
              }}
            >
              <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>
                Scenario
              </span>
              <select
                value={draft.scenario}
                onChange={(e) =>
                  onFieldChange(
                    'scenario',
                    e.target.value as DevelopmentScenario | 'all',
                  )
                }
                style={{
                  borderRadius: '8px',
                  border: '1px solid #d2d2d7',
                  padding: '0.55rem 0.75rem',
                  fontSize: '0.9rem',
                }}
              >
                <option value="all">All scenarios</option>
                {SCENARIO_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.4rem',
              }}
            >
              <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>
                Overall rating
              </span>
              <select
                value={draft.overallRating}
                onChange={(e) => onFieldChange('overallRating', e.target.value)}
                style={{
                  borderRadius: '8px',
                  border: '1px solid #d2d2d7',
                  padding: '0.55rem 0.75rem',
                  fontSize: '0.9rem',
                }}
              >
                {CONDITION_RATINGS.map((rating) => (
                  <option key={rating} value={rating}>
                    {rating}
                  </option>
                ))}
              </select>
            </label>
            <label
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.4rem',
              }}
            >
              <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>
                Overall score
              </span>
              <input
                type="number"
                min={0}
                max={100}
                value={draft.overallScore}
                onChange={(e) => onFieldChange('overallScore', e.target.value)}
                style={{
                  borderRadius: '8px',
                  border: '1px solid #d2d2d7',
                  padding: '0.55rem 0.75rem',
                  fontSize: '0.9rem',
                }}
              />
            </label>
            <label
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.4rem',
              }}
            >
              <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>
                Risk level
              </span>
              <select
                value={draft.riskLevel}
                onChange={(e) => onFieldChange('riskLevel', e.target.value)}
                style={{
                  borderRadius: '8px',
                  border: '1px solid #d2d2d7',
                  padding: '0.55rem 0.75rem',
                  fontSize: '0.9rem',
                }}
              >
                {CONDITION_RISK_LEVELS.map((risk) => (
                  <option key={risk} value={risk}>
                    {risk.charAt(0).toUpperCase() + risk.slice(1)}
                  </option>
                ))}
              </select>
            </label>
            <label
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.4rem',
              }}
            >
              <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>
                Inspector name
              </span>
              <input
                type="text"
                value={draft.inspectorName}
                onChange={(e) => onFieldChange('inspectorName', e.target.value)}
                placeholder="e.g. Jane Tan"
                style={{
                  borderRadius: '8px',
                  border: '1px solid #d2d2d7',
                  padding: '0.55rem 0.75rem',
                  fontSize: '0.9rem',
                }}
              />
            </label>
            <label
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.4rem',
              }}
            >
              <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>
                Inspection date &amp; time
              </span>
              <input
                type="datetime-local"
                value={draft.recordedAtLocal}
                onChange={(e) =>
                  onFieldChange('recordedAtLocal', e.target.value)
                }
                style={{
                  borderRadius: '8px',
                  border: '1px solid #d2d2d7',
                  padding: '0.55rem 0.75rem',
                  fontSize: '0.9rem',
                }}
              />
            </label>
          </div>

          <label
            style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}
          >
            <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>
              Summary
            </span>
            <textarea
              value={draft.summary}
              onChange={(e) => onFieldChange('summary', e.target.value)}
              rows={3}
              style={{
                borderRadius: '8px',
                border: '1px solid #d2d2d7',
                padding: '0.75rem',
                fontSize: '0.9rem',
              }}
            />
          </label>

          <label
            style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}
          >
            <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>
              Scenario context
            </span>
            <textarea
              value={draft.scenarioContext}
              onChange={(e) => onFieldChange('scenarioContext', e.target.value)}
              rows={2}
              style={{
                borderRadius: '8px',
                border: '1px solid #d2d2d7',
                padding: '0.75rem',
                fontSize: '0.9rem',
              }}
            />
          </label>

          <label
            style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}
          >
            <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>
              Attachments (one per line as &quot;Label | URL&quot;)
            </span>
            <textarea
              value={draft.attachmentsText}
              onChange={(e) => onFieldChange('attachmentsText', e.target.value)}
              rows={3}
              placeholder="Site photo | https://example.com/photo.jpg"
              style={{
                borderRadius: '8px',
                border: '1px solid #d2d2d7',
                padding: '0.75rem',
                fontSize: '0.9rem',
              }}
            />
          </label>

          <div style={{ display: 'grid', gap: '1rem' }}>
            {draft.systems.map((system, index) => (
              <div
                key={`${system.name}-${index}`}
                style={{
                  border: '1px solid #e5e5e7',
                  borderRadius: '12px',
                  padding: '1rem',
                  display: 'grid',
                  gap: '0.75rem',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: '0.5rem',
                  }}
                >
                  <label
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.4rem',
                    }}
                  >
                    <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>
                      System
                    </span>
                    <input
                      type="text"
                      value={system.name}
                      onChange={(e) =>
                        onSystemChange(index, 'name', e.target.value)
                      }
                      style={{
                        borderRadius: '8px',
                        border: '1px solid #d2d2d7',
                        padding: '0.55rem 0.75rem',
                        fontSize: '0.9rem',
                        minWidth: '12rem',
                      }}
                    />
                  </label>
                  <div
                    style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}
                  >
                    <label
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.35rem',
                      }}
                    >
                      <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>
                        Rating
                      </span>
                      <input
                        type="text"
                        value={system.rating}
                        onChange={(e) =>
                          onSystemChange(index, 'rating', e.target.value)
                        }
                        style={{
                          borderRadius: '8px',
                          border: '1px solid #d2d2d7',
                          padding: '0.55rem 0.75rem',
                          fontSize: '0.9rem',
                          width: '6rem',
                        }}
                      />
                    </label>
                    <label
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.35rem',
                      }}
                    >
                      <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>
                        Score
                      </span>
                      <input
                        type="number"
                        min={0}
                        max={100}
                        value={system.score}
                        onChange={(e) =>
                          onSystemChange(index, 'score', e.target.value)
                        }
                        style={{
                          borderRadius: '8px',
                          border: '1px solid #d2d2d7',
                          padding: '0.55rem 0.75rem',
                          fontSize: '0.9rem',
                          width: '6rem',
                        }}
                      />
                    </label>
                  </div>
                </div>

                <label
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.35rem',
                  }}
                >
                  <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>
                    Notes
                  </span>
                  <textarea
                    value={system.notes}
                    onChange={(e) =>
                      onSystemChange(index, 'notes', e.target.value)
                    }
                    rows={2}
                    style={{
                      borderRadius: '8px',
                      border: '1px solid #d2d2d7',
                      padding: '0.7rem',
                      fontSize: '0.9rem',
                    }}
                  />
                </label>

                <label
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.35rem',
                  }}
                >
                  <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>
                    Recommended actions (one per line)
                  </span>
                  <textarea
                    value={system.recommendedActions}
                    onChange={(e) =>
                      onSystemChange(
                        index,
                        'recommendedActions',
                        e.target.value,
                      )
                    }
                    rows={2}
                    style={{
                      borderRadius: '8px',
                      border: '1px solid #d2d2d7',
                      padding: '0.7rem',
                      fontSize: '0.9rem',
                    }}
                  />
                </label>
              </div>
            ))}
          </div>

          <label
            style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}
          >
            <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>
              Additional recommended actions
            </span>
            <textarea
              value={draft.recommendedActionsText}
              onChange={(e) =>
                onFieldChange('recommendedActionsText', e.target.value)
              }
              rows={3}
              style={{
                borderRadius: '8px',
                border: '1px solid #d2d2d7',
                padding: '0.75rem',
                fontSize: '0.9rem',
              }}
            />
          </label>

          <div
            style={{
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '0.75rem',
              flexWrap: 'wrap',
            }}
          >
            <button
              type="button"
              onClick={onClose}
              disabled={isSaving}
              style={{
                border: '1px solid #d2d2d7',
                background: 'white',
                color: '#1d1d1f',
                borderRadius: '9999px',
                padding: '0.55rem 1.25rem',
                fontSize: '0.875rem',
                fontWeight: 600,
                cursor: isSaving ? 'not-allowed' : 'pointer',
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              style={{
                border: 'none',
                background: '#1d1d1f',
                color: 'white',
                borderRadius: '9999px',
                padding: '0.55rem 1.5rem',
                fontSize: '0.875rem',
                fontWeight: 600,
                cursor: isSaving ? 'not-allowed' : 'pointer',
              }}
            >
              {isSaving ? 'Saving…' : 'Save inspection'}
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body,
  )
}
