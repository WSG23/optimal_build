/**
 * Manual Inspection Controls Component
 *
 * Button group for logging/editing manual inspections with status display.
 * Pure presentational component - receives only labels, flags, and stable handlers.
 *
 * Uses Protocol Alpha (primary) for "Log inspection" command
 * Uses Protocol Beta (secondary) for "Edit latest" system action
 */

import { Button } from '@/components/canonical/Button'

// ============================================================================
// Types
// ============================================================================

export interface InspectionStatusItem {
  label: string
  value: string
}

export interface ManualInspectionControlsProps {
  /** Whether a property is captured */
  hasProperty: boolean
  /** Whether there's an existing assessment to edit */
  hasExistingAssessment: boolean
  /** Save message to display (success/error) */
  saveMessage: string | null
  /** Status items to display (label-value pairs), null if no inspection logged */
  statusItems: InspectionStatusItem[] | null
  /** Handler to log a new inspection */
  onLogNew: () => void
  /** Handler to edit the latest inspection */
  onEditLatest: () => void
}

// ============================================================================
// Component
// ============================================================================

export function ManualInspectionControls({
  hasProperty,
  hasExistingAssessment,
  saveMessage,
  statusItems,
  onLogNew,
  onEditLatest,
}: ManualInspectionControlsProps) {
  return (
    <div
      style={{
        border: '1px solid var(--ob-color-border-subtle)',
        borderRadius: 'var(--ob-radius-sm)',
        padding: 'var(--ob-space-150)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-100)',
        background: 'var(--ob-color-bg-surface)',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 'var(--ob-space-075)',
        }}
      >
        <div
          style={{
            maxWidth: '520px',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--ob-space-035)',
          }}
        >
          <h3
            style={{
              margin: 0,
              fontSize: 'var(--ob-font-size-lg)',
              fontWeight: 600,
            }}
          >
            Manual inspection capture
          </h3>
          <p
            style={{
              margin: 0,
              fontSize: 'var(--ob-font-size-sm)',
              color: 'var(--ob-color-text-secondary)',
              lineHeight: 'var(--ob-line-height-normal)',
            }}
          >
            Log a fresh site visit or update the latest inspection without
            waiting for automated sync.
          </p>
        </div>
        <div
          style={{
            display: 'flex',
            gap: 'var(--ob-space-075)',
            flexWrap: 'wrap',
          }}
        >
          <Button
            variant="primary"
            size="sm"
            onClick={onLogNew}
            disabled={!hasProperty}
          >
            Log inspection
          </Button>
          {hasExistingAssessment && (
            <Button
              variant="secondary"
              size="sm"
              onClick={onEditLatest}
              disabled={!hasProperty}
            >
              Edit latest
            </Button>
          )}
        </div>
      </div>
      {saveMessage && (
        <p
          style={{
            margin: 0,
            fontSize: 'var(--ob-font-size-sm)',
            color: saveMessage.includes('success')
              ? 'var(--ob-success-600)'
              : 'var(--ob-error-600)',
          }}
        >
          {saveMessage}
        </p>
      )}
      {hasProperty ? (
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 'var(--ob-space-065)',
            fontSize: 'var(--ob-font-size-sm)',
            color: 'var(--ob-color-text-secondary)',
          }}
        >
          {statusItems && statusItems.length > 0 ? (
            <>
              {statusItems.map((item, index) => (
                <span key={item.label}>
                  {item.label}: <strong>{item.value}</strong>
                  {index < statusItems.length - 1 && (
                    <span style={{ margin: '0 var(--ob-space-025)' }}>•</span>
                  )}
                </span>
              ))}
            </>
          ) : (
            <span>
              No manual inspections logged yet - use &quot;Log inspection&quot;
              to create one.
            </span>
          )}
        </div>
      ) : (
        <p
          style={{
            margin: 0,
            fontSize: 'var(--ob-font-size-sm)',
            color: 'var(--ob-color-text-muted)',
          }}
        >
          Capture a property to enable manual inspection logging.
        </p>
      )}
    </div>
  )
}
