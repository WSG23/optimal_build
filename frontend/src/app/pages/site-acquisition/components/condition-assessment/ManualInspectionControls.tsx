/**
 * Manual Inspection Controls Component
 *
 * Button group for logging/editing manual inspections with status display.
 * Pure presentational component - receives only labels, flags, and stable handlers.
 */

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
        border: '1px solid #e5e5e7',
        borderRadius: '12px',
        padding: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '0.75rem',
        }}
      >
        <div
          style={{
            maxWidth: '520px',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.35rem',
          }}
        >
          <h3
            style={{
              margin: 0,
              fontSize: '1.0625rem',
              fontWeight: 600,
            }}
          >
            Manual inspection capture
          </h3>
          <p style={{ margin: 0, fontSize: '0.9rem', color: '#4b5563', lineHeight: 1.5 }}>
            Log a fresh site visit or update the latest inspection without waiting for
            automated sync.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={onLogNew}
            disabled={!hasProperty}
            style={{
              border: '1px solid #1d1d1f',
              background: hasProperty ? '#1d1d1f' : '#f5f5f7',
              color: hasProperty ? 'white' : '#1d1d1f88',
              borderRadius: '9999px',
              padding: '0.45rem 1.1rem',
              fontSize: '0.8125rem',
              fontWeight: 600,
              cursor: hasProperty ? 'pointer' : 'not-allowed',
            }}
          >
            Log inspection
          </button>
          {hasExistingAssessment && (
            <button
              type="button"
              onClick={onEditLatest}
              disabled={!hasProperty}
              style={{
                border: '1px solid #1d1d1f',
                background: 'white',
                color: '#1d1d1f',
                borderRadius: '9999px',
                padding: '0.45rem 1.1rem',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: hasProperty ? 'pointer' : 'not-allowed',
              }}
            >
              Edit latest
            </button>
          )}
        </div>
      </div>
      {saveMessage && (
        <p
          style={{
            margin: 0,
            fontSize: '0.85rem',
            color: saveMessage.includes('success') ? '#15803d' : '#c53030',
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
            gap: '0.6rem',
            fontSize: '0.85rem',
            color: '#4b5563',
          }}
        >
          {statusItems && statusItems.length > 0 ? (
            <>
              {statusItems.map((item, index) => (
                <span key={item.label}>
                  {item.label}: <strong>{item.value}</strong>
                  {index < statusItems.length - 1 && <span style={{ margin: '0 0.25rem' }}>•</span>}
                </span>
              ))}
            </>
          ) : (
            <span>
              No manual inspections logged yet - use &quot;Log inspection&quot; to create one.
            </span>
          )}
        </div>
      ) : (
        <p style={{ margin: 0, fontSize: '0.85rem', color: '#6b7280' }}>
          Capture a property to enable manual inspection logging.
        </p>
      )}
    </div>
  )
}
