/**
 * Condition Assessment Editor Modal
 *
 * Modal dialog for logging or editing inspection entries.
 * Receives all data and handlers via props from the parent page.
 */

import { createPortal } from 'react-dom'
import { IconButton } from '@mui/material'
import { Close } from '@mui/icons-material'
import { Button } from '@/components/canonical/Button'
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
        aria-label="Manual inspection editor"
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
          aria-label="Close inspection editor"
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
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            flexWrap: 'wrap',
            gap: 'var(--ob-space-100)',
            marginBottom: 'var(--ob-space-150)',
          }}
        >
          <div
            style={{
              maxWidth: '540px',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-035)',
            }}
          >
            <h2
              style={{
                margin: 0,
                fontSize: 'var(--ob-font-size-2xl)',
                fontWeight: 600,
                letterSpacing: 'var(--ob-letter-spacing-tight)',
              }}
            >
              {mode === 'new'
                ? 'Log manual inspection'
                : 'Edit latest inspection'}
            </h2>
            <p
              style={{
                margin: 0,
                fontSize: 'var(--ob-font-size-md)',
                color: 'var(--ob-color-text-secondary)',
                lineHeight: 'var(--ob-line-height-relaxed)',
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
                  gap: 'var(--ob-space-050)',
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
                        borderRadius: 'var(--ob-radius-pill)',
                        border: `1px solid ${isActive ? 'var(--ob-brand-700)' : 'var(--ob-color-border-subtle)'}`,
                        background: isActive
                          ? 'var(--ob-brand-100)'
                          : 'var(--ob-color-bg-surface)',
                        color: isActive
                          ? 'var(--ob-brand-700)'
                          : 'var(--ob-color-text-primary)',
                        padding: 'var(--ob-space-025) var(--ob-space-085)',
                        fontSize: 'var(--ob-font-size-xs)',
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
          <Button
            variant="ghost"
            size="sm"
            onClick={onReset}
            disabled={isSaving}
          >
            Reset draft
          </Button>
        </div>

        <form
          onSubmit={onSubmit}
          style={{ display: 'grid', gap: 'var(--ob-space-125)' }}
        >
          <div
            style={{
              display: 'grid',
              gap: 'var(--ob-space-100)',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            }}
          >
            <label
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--ob-space-035)',
              }}
            >
              <span
                style={{
                  fontSize: 'var(--ob-font-size-sm-minus)',
                  fontWeight: 600,
                }}
              >
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
                  borderRadius: 'var(--ob-radius-md)',
                  border: '1px solid var(--ob-color-border-subtle)',
                  padding: 'var(--ob-space-050) var(--ob-space-075)',
                  fontSize: 'var(--ob-font-size-sm)',
                  background: 'var(--ob-color-bg-surface)',
                  color: 'var(--ob-color-text-primary)',
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
                gap: 'var(--ob-space-035)',
              }}
            >
              <span
                style={{
                  fontSize: 'var(--ob-font-size-sm-minus)',
                  fontWeight: 600,
                }}
              >
                Overall rating
              </span>
              <select
                value={draft.overallRating}
                onChange={(e) => onFieldChange('overallRating', e.target.value)}
                style={{
                  borderRadius: 'var(--ob-radius-md)',
                  border: '1px solid var(--ob-color-border-subtle)',
                  padding: 'var(--ob-space-050) var(--ob-space-075)',
                  fontSize: 'var(--ob-font-size-sm)',
                  background: 'var(--ob-color-bg-surface)',
                  color: 'var(--ob-color-text-primary)',
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
                gap: 'var(--ob-space-035)',
              }}
            >
              <span
                style={{
                  fontSize: 'var(--ob-font-size-sm-minus)',
                  fontWeight: 600,
                }}
              >
                Overall score
              </span>
              <input
                type="number"
                min={0}
                max={100}
                value={draft.overallScore}
                onChange={(e) => onFieldChange('overallScore', e.target.value)}
                style={{
                  borderRadius: 'var(--ob-radius-md)',
                  border: '1px solid var(--ob-color-border-subtle)',
                  padding: 'var(--ob-space-050) var(--ob-space-075)',
                  fontSize: 'var(--ob-font-size-sm)',
                  background: 'var(--ob-color-bg-surface)',
                  color: 'var(--ob-color-text-primary)',
                }}
              />
            </label>
            <label
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--ob-space-035)',
              }}
            >
              <span
                style={{
                  fontSize: 'var(--ob-font-size-sm-minus)',
                  fontWeight: 600,
                }}
              >
                Risk level
              </span>
              <select
                value={draft.riskLevel}
                onChange={(e) => onFieldChange('riskLevel', e.target.value)}
                style={{
                  borderRadius: 'var(--ob-radius-md)',
                  border: '1px solid var(--ob-color-border-subtle)',
                  padding: 'var(--ob-space-050) var(--ob-space-075)',
                  fontSize: 'var(--ob-font-size-sm)',
                  background: 'var(--ob-color-bg-surface)',
                  color: 'var(--ob-color-text-primary)',
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
                gap: 'var(--ob-space-035)',
              }}
            >
              <span
                style={{
                  fontSize: 'var(--ob-font-size-sm-minus)',
                  fontWeight: 600,
                }}
              >
                Inspector name
              </span>
              <input
                type="text"
                value={draft.inspectorName}
                onChange={(e) => onFieldChange('inspectorName', e.target.value)}
                placeholder="e.g. Jane Tan"
                style={{
                  borderRadius: 'var(--ob-radius-md)',
                  border: '1px solid var(--ob-color-border-subtle)',
                  padding: 'var(--ob-space-050) var(--ob-space-075)',
                  fontSize: 'var(--ob-font-size-sm)',
                  background: 'var(--ob-color-bg-surface)',
                  color: 'var(--ob-color-text-primary)',
                }}
              />
            </label>
            <label
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--ob-space-035)',
              }}
            >
              <span
                style={{
                  fontSize: 'var(--ob-font-size-sm-minus)',
                  fontWeight: 600,
                }}
              >
                Inspection date &amp; time
              </span>
              <input
                type="datetime-local"
                value={draft.recordedAtLocal}
                onChange={(e) =>
                  onFieldChange('recordedAtLocal', e.target.value)
                }
                style={{
                  borderRadius: 'var(--ob-radius-md)',
                  border: '1px solid var(--ob-color-border-subtle)',
                  padding: 'var(--ob-space-050) var(--ob-space-075)',
                  fontSize: 'var(--ob-font-size-sm)',
                  background: 'var(--ob-color-bg-surface)',
                  color: 'var(--ob-color-text-primary)',
                }}
              />
            </label>
          </div>

          <label
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-035)',
            }}
          >
            <span
              style={{
                fontSize: 'var(--ob-font-size-sm-minus)',
                fontWeight: 600,
              }}
            >
              Summary
            </span>
            <textarea
              value={draft.summary}
              onChange={(e) => onFieldChange('summary', e.target.value)}
              rows={3}
              style={{
                borderRadius: 'var(--ob-radius-md)',
                border: '1px solid var(--ob-color-border-subtle)',
                padding: 'var(--ob-space-075)',
                fontSize: 'var(--ob-font-size-sm)',
                background: 'var(--ob-color-bg-surface)',
                color: 'var(--ob-color-text-primary)',
              }}
            />
          </label>

          <label
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-035)',
            }}
          >
            <span
              style={{
                fontSize: 'var(--ob-font-size-sm-minus)',
                fontWeight: 600,
              }}
            >
              Scenario context
            </span>
            <textarea
              value={draft.scenarioContext}
              onChange={(e) => onFieldChange('scenarioContext', e.target.value)}
              rows={2}
              style={{
                borderRadius: 'var(--ob-radius-md)',
                border: '1px solid var(--ob-color-border-subtle)',
                padding: 'var(--ob-space-075)',
                fontSize: 'var(--ob-font-size-sm)',
                background: 'var(--ob-color-bg-surface)',
                color: 'var(--ob-color-text-primary)',
              }}
            />
          </label>

          <label
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-035)',
            }}
          >
            <span
              style={{
                fontSize: 'var(--ob-font-size-sm-minus)',
                fontWeight: 600,
              }}
            >
              Attachments (one per line as &quot;Label | URL&quot;)
            </span>
            <textarea
              value={draft.attachmentsText}
              onChange={(e) => onFieldChange('attachmentsText', e.target.value)}
              rows={3}
              placeholder="Site photo | https://example.com/photo.jpg"
              style={{
                borderRadius: 'var(--ob-radius-md)',
                border: '1px solid var(--ob-color-border-subtle)',
                padding: 'var(--ob-space-075)',
                fontSize: 'var(--ob-font-size-sm)',
                background: 'var(--ob-color-bg-surface)',
                color: 'var(--ob-color-text-primary)',
              }}
            />
          </label>

          <div style={{ display: 'grid', gap: 'var(--ob-space-100)' }}>
            {draft.systems.map((system, index) => (
              <div
                key={`${system.name}-${index}`}
                style={{
                  border: '1px solid var(--ob-color-border-subtle)',
                  borderRadius: 'var(--ob-radius-sm)',
                  padding: 'var(--ob-space-100)',
                  display: 'grid',
                  gap: 'var(--ob-space-075)',
                  background: 'var(--ob-color-bg-surface)',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: 'var(--ob-space-050)',
                  }}
                >
                  <label
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 'var(--ob-space-035)',
                    }}
                  >
                    <span
                      style={{
                        fontSize: 'var(--ob-font-size-xs)',
                        fontWeight: 600,
                      }}
                    >
                      System
                    </span>
                    <input
                      type="text"
                      value={system.name}
                      onChange={(e) =>
                        onSystemChange(index, 'name', e.target.value)
                      }
                      style={{
                        borderRadius: 'var(--ob-radius-md)',
                        border: '1px solid var(--ob-color-border-subtle)',
                        padding: 'var(--ob-space-050) var(--ob-space-075)',
                        fontSize: 'var(--ob-font-size-sm)',
                        minWidth: '12rem',
                        background: 'var(--ob-color-bg-surface)',
                        color: 'var(--ob-color-text-primary)',
                      }}
                    />
                  </label>
                  <div
                    style={{
                      display: 'flex',
                      gap: 'var(--ob-space-050)',
                      flexWrap: 'wrap',
                    }}
                  >
                    <label
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 'var(--ob-space-035)',
                      }}
                    >
                      <span
                        style={{
                          fontSize: 'var(--ob-font-size-xs)',
                          fontWeight: 600,
                        }}
                      >
                        Rating
                      </span>
                      <input
                        type="text"
                        value={system.rating}
                        onChange={(e) =>
                          onSystemChange(index, 'rating', e.target.value)
                        }
                        style={{
                          borderRadius: 'var(--ob-radius-md)',
                          border: '1px solid var(--ob-color-border-subtle)',
                          padding: 'var(--ob-space-050) var(--ob-space-075)',
                          fontSize: 'var(--ob-font-size-sm)',
                          width: '6rem',
                          background: 'var(--ob-color-bg-surface)',
                          color: 'var(--ob-color-text-primary)',
                        }}
                      />
                    </label>
                    <label
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 'var(--ob-space-035)',
                      }}
                    >
                      <span
                        style={{
                          fontSize: 'var(--ob-font-size-xs)',
                          fontWeight: 600,
                        }}
                      >
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
                          borderRadius: 'var(--ob-radius-md)',
                          border: '1px solid var(--ob-color-border-subtle)',
                          padding: 'var(--ob-space-050) var(--ob-space-075)',
                          fontSize: 'var(--ob-font-size-sm)',
                          width: '6rem',
                          background: 'var(--ob-color-bg-surface)',
                          color: 'var(--ob-color-text-primary)',
                        }}
                      />
                    </label>
                  </div>
                </div>

                <label
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--ob-space-035)',
                  }}
                >
                  <span
                    style={{
                      fontSize: 'var(--ob-font-size-xs)',
                      fontWeight: 600,
                    }}
                  >
                    Notes
                  </span>
                  <textarea
                    value={system.notes}
                    onChange={(e) =>
                      onSystemChange(index, 'notes', e.target.value)
                    }
                    rows={2}
                    style={{
                      borderRadius: 'var(--ob-radius-md)',
                      border: '1px solid var(--ob-color-border-subtle)',
                      padding: 'var(--ob-space-075)',
                      fontSize: 'var(--ob-font-size-sm)',
                      background: 'var(--ob-color-bg-surface)',
                      color: 'var(--ob-color-text-primary)',
                    }}
                  />
                </label>

                <label
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--ob-space-035)',
                  }}
                >
                  <span
                    style={{
                      fontSize: 'var(--ob-font-size-xs)',
                      fontWeight: 600,
                    }}
                  >
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
                      borderRadius: 'var(--ob-radius-md)',
                      border: '1px solid var(--ob-color-border-subtle)',
                      padding: 'var(--ob-space-075)',
                      fontSize: 'var(--ob-font-size-sm)',
                      background: 'var(--ob-color-bg-surface)',
                      color: 'var(--ob-color-text-primary)',
                    }}
                  />
                </label>
              </div>
            ))}
          </div>

          <label
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-035)',
            }}
          >
            <span
              style={{
                fontSize: 'var(--ob-font-size-sm-minus)',
                fontWeight: 600,
              }}
            >
              Additional recommended actions
            </span>
            <textarea
              value={draft.recommendedActionsText}
              onChange={(e) =>
                onFieldChange('recommendedActionsText', e.target.value)
              }
              rows={3}
              style={{
                borderRadius: 'var(--ob-radius-md)',
                border: '1px solid var(--ob-color-border-subtle)',
                padding: 'var(--ob-space-075)',
                fontSize: 'var(--ob-font-size-sm)',
                background: 'var(--ob-color-bg-surface)',
                color: 'var(--ob-color-text-primary)',
              }}
            />
          </label>

          <div
            style={{
              display: 'flex',
              justifyContent: 'flex-end',
              gap: 'var(--ob-space-075)',
              flexWrap: 'wrap',
            }}
          >
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              type="submit"
              disabled={isSaving}
            >
              {isSaving ? 'Saving…' : 'Save inspection'}
            </Button>
          </div>
        </form>
      </div>
    </div>,
    document.body,
  )
}
