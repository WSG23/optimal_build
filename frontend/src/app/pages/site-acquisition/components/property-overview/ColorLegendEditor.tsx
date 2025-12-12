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
        marginTop: '1.25rem',
        border: '1px solid #e5e7eb',
        borderRadius: '4px',
        padding: '1.25rem',
        background: '#ffffff',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '0.75rem',
          alignItems: 'center',
        }}
      >
        <div>
          <h4
            style={{
              margin: 0,
              fontSize: '1rem',
              fontWeight: 600,
              letterSpacing: '-0.01em',
              color: '#111827',
            }}
          >
            Colour legend editor
          </h4>
          <p style={{ margin: 0, fontSize: '0.9rem', color: '#4b5563' }}>
            Update the palette, labels, and descriptions before regenerating the
            preview so property captures and developer decks stay consistent.
          </p>
        </div>
        <span
          style={{
            fontSize: '0.85rem',
            fontWeight: 600,
            color: hasPendingChanges ? '#b45309' : '#10b981',
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
          gap: '1rem',
        }}
      >
        {entries.map((entry) => (
          <div
            key={entry.assetType}
            style={{
              border: '1px solid #e5e7eb',
              borderRadius: '4px',
              padding: '0.9rem',
              background: '#f9fafb',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.6rem',
            }}
          >
            <div
              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
            >
              <strong style={{ fontSize: '0.9rem', color: '#111827' }}>
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
                  width: '36px',
                  height: '24px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  padding: 0,
                  background: '#fff',
                }}
              />
            </div>
            <label
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.35rem',
                fontSize: '0.8rem',
                color: '#4b5563',
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
                  padding: '0.4rem 0.55rem',
                  borderRadius: '6px',
                  border: '1px solid #d1d5db',
                  fontSize: '0.9rem',
                }}
              />
            </label>
            <label
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.35rem',
                fontSize: '0.8rem',
                color: '#4b5563',
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
                  padding: '0.4rem 0.55rem',
                  borderRadius: '6px',
                  border: '1px solid #d1d5db',
                  fontSize: '0.9rem',
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
          gap: '0.75rem',
          alignItems: 'center',
        }}
      >
        <button
          type="button"
          onClick={onReset}
          disabled={entries.length === 0}
          style={{
            padding: '0.45rem 0.85rem',
            borderRadius: '9999px',
            border: '1px solid #d1d5db',
            background: '#f9fafb',
            fontWeight: 600,
            color: '#111827',
            fontSize: '0.85rem',
            cursor: entries.length === 0 ? 'not-allowed' : 'pointer',
            opacity: entries.length === 0 ? 0.5 : 1,
          }}
        >
          Reset to preview defaults
        </button>
        <p style={{ margin: 0, fontSize: '0.85rem', color: '#4b5563' }}>
          Use "Refresh preview render" after editing the palette so GLTF colours
          match the updated legend.
        </p>
      </div>
    </section>
  )
}
