/**
 * Color Legend Editor Component
 *
 * Allows editing of color legend entries (label, color, description)
 * for the 3D preview. Changes are applied via a single onChange callback.
 */

import type { PreviewLegendEntry } from '../../previewMetadata'
import { toTitleCase } from '../../utils/formatters'

// ============================================================================
// Types
// ============================================================================

export interface ColorLegendEditorProps {
  /** Legend entries to edit */
  entries: PreviewLegendEntry[]
  /** Whether there are pending changes not yet synced with preview */
  hasPendingChanges: boolean
  /** Called when any field of an entry changes */
  onChange: (
    assetType: string,
    field: 'label' | 'color' | 'description',
    value: string,
  ) => void
  /** Called when user wants to reset to defaults */
  onReset: () => void
}

// ============================================================================
// Component
// ============================================================================

export function ColorLegendEditor({
  entries,
  hasPendingChanges,
  onChange,
  onReset,
}: ColorLegendEditorProps) {
  if (entries.length === 0) {
    return null
  }

  return (
    <section
      style={{
        marginTop: 'var(--ob-space-125)',
        border: '1px solid var(--ob-color-border-subtle, #e5e7eb)',
        borderRadius: 'var(--ob-radius-sm)',
        padding: 'var(--ob-space-125)',
        background: 'var(--ob-color-bg-surface, #ffffff)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-100)',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 'var(--ob-space-075)',
          alignItems: 'center',
        }}
      >
        <div>
          <h2
            style={{
              margin: 0,
              fontSize: 'var(--ob-font-size-base)',
              fontWeight: 'var(--ob-font-weight-semibold)',
              letterSpacing: '-0.01em',
              color: 'var(--ob-color-text-primary, #111827)',
            }}
          >
            Colour legend editor
          </h2>
          <p
            style={{
              margin: 0,
              fontSize: 'var(--ob-font-size-sm)',
              color: 'var(--ob-color-text-secondary, #4b5563)',
            }}
          >
            Update the palette, labels, and descriptions before regenerating the
            preview so property captures and developer decks stay consistent.
          </p>
        </div>
        <span
          style={{
            fontSize: 'var(--ob-font-size-sm)',
            fontWeight: 'var(--ob-font-weight-semibold)',
            color: hasPendingChanges
              ? 'var(--ob-color-status-warning, #b45309)'
              : 'var(--ob-color-status-success, #10b981)',
          }}
        >
          {hasPendingChanges
            ? 'Palette edits pending preview refresh'
            : 'Palette synced with latest preview'}
        </span>
      </div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: 'var(--ob-space-100)',
        }}
      >
        {entries.map((entry) => (
          <div
            key={entry.assetType}
            style={{
              border: '1px solid var(--ob-color-border-subtle, #e5e7eb)',
              borderRadius: 'var(--ob-radius-sm)',
              padding: 'var(--ob-space-085)',
              background: 'var(--ob-color-bg-surface, #f9fafb)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-065)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-050)',
              }}
            >
              <strong
                style={{
                  fontSize: 'var(--ob-font-size-sm)',
                  color: 'var(--ob-color-text-primary, #111827)',
                }}
              >
                {toTitleCase(entry.label)}
              </strong>
              <input
                type="color"
                aria-label={`Colour for ${toTitleCase(entry.label)}`}
                value={entry.color}
                onChange={(event) =>
                  onChange(entry.assetType, 'color', event.target.value)
                }
                style={{
                  width: '44px',
                  height: '44px',
                  border: '1px solid var(--ob-color-border-default, #d1d5db)',
                  borderRadius: 'var(--ob-radius-md)',
                  padding: 0,
                  background: 'var(--ob-color-bg-surface, #fff)',
                }}
              />
            </div>
            <label
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--ob-space-035)',
                fontSize: 'var(--ob-font-size-sm-minus)',
                color: 'var(--ob-color-text-secondary, #4b5563)',
              }}
            >
              Label
              <input
                type="text"
                value={entry.label}
                onChange={(event) =>
                  onChange(entry.assetType, 'label', event.target.value)
                }
                style={{
                  padding: 'var(--ob-space-035) var(--ob-space-050)',
                  borderRadius: 'var(--ob-radius-md)',
                  border: '1px solid var(--ob-color-border-default, #d1d5db)',
                  fontSize: 'var(--ob-font-size-sm)',
                }}
              />
            </label>
            <label
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--ob-space-035)',
                fontSize: 'var(--ob-font-size-sm-minus)',
                color: 'var(--ob-color-text-secondary, #4b5563)',
              }}
            >
              Description
              <textarea
                value={entry.description ?? ''}
                onChange={(event) =>
                  onChange(entry.assetType, 'description', event.target.value)
                }
                rows={2}
                style={{
                  resize: 'vertical',
                  minHeight: '56px',
                  padding: 'var(--ob-space-035) var(--ob-space-050)',
                  borderRadius: 'var(--ob-radius-md)',
                  border: '1px solid var(--ob-color-border-default, #d1d5db)',
                  fontSize: 'var(--ob-font-size-sm)',
                }}
              />
            </label>
          </div>
        ))}
      </div>
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 'var(--ob-space-075)',
          alignItems: 'center',
        }}
      >
        <button
          type="button"
          onClick={onReset}
          disabled={entries.length === 0}
          style={{
            padding: 'var(--ob-space-050) var(--ob-space-085)',
            borderRadius: 'var(--ob-radius-pill)',
            border: '1px solid var(--ob-color-border-default, #d1d5db)',
            background: 'var(--ob-color-bg-surface, #f9fafb)',
            fontWeight: 'var(--ob-font-weight-semibold)',
            color: 'var(--ob-color-text-primary, #111827)',
            fontSize: 'var(--ob-font-size-sm)',
            cursor: entries.length === 0 ? 'not-allowed' : 'pointer',
            opacity: entries.length === 0 ? 0.5 : 1,
          }}
        >
          Reset to preview defaults
        </button>
        <p
          style={{
            margin: 0,
            fontSize: 'var(--ob-font-size-sm)',
            color: 'var(--ob-color-text-secondary, #4b5563)',
          }}
        >
          Use "Refresh preview render" after editing the palette so GLTF colours
          match the updated legend.
        </p>
      </div>
    </section>
  )
}
