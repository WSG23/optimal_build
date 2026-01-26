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
        marginTop: 'var(--ob-space-200)',
        border: '1px solid var(--ob-color-border-subtle)',
        borderRadius: 'var(--ob-radius-sm)',
        padding: 'var(--ob-space-200)',
        background: 'var(--ob-color-bg-default)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-200)',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 'var(--ob-space-150)',
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
              color: 'var(--ob-color-bg-inverse)',
            }}
          >
            Colour legend editor
          </h4>
          <p
            style={{
              margin: 0,
              fontSize: '0.9rem',
              color: 'var(--ob-color-text-secondary)',
            }}
          >
            Update the palette, labels, and descriptions before regenerating the
            preview so property captures and developer decks stay consistent.
          </p>
        </div>
        <span
          style={{
            fontSize: '0.85rem',
            fontWeight: 600,
            color: hasPendingChanges ? '#b45309' : 'var(--ob-color-success)',
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
          gap: 'var(--ob-space-200)',
        }}
      >
        {entries.map((entry) => (
          <div
            key={entry.assetType}
            style={{
              border: '1px solid var(--ob-color-border-subtle)',
              borderRadius: 'var(--ob-radius-sm)',
              padding: 'var(--ob-space-200)',
              background: 'var(--ob-color-bg-muted)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-100)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-100)',
              }}
            >
              <strong
                style={{
                  fontSize: '0.9rem',
                  color: 'var(--ob-color-bg-inverse)',
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
                  width: '36px',
                  height: '24px',
                  border: '1px solid var(--ob-color-border-default)',
                  borderRadius: 'var(--ob-radius-md)',
                  padding: 0,
                  background: 'var(--ob-color-bg-default)',
                }}
              />
            </div>
            <label
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--ob-space-50)',
                fontSize: '0.8rem',
                color: 'var(--ob-color-text-secondary)',
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
                  padding: 'var(--ob-space-100) 0.55rem',
                  borderRadius: 'var(--ob-radius-md)',
                  border: '1px solid var(--ob-color-border-default)',
                  fontSize: '0.9rem',
                }}
              />
            </label>
            <label
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--ob-space-50)',
                fontSize: '0.8rem',
                color: 'var(--ob-color-text-secondary)',
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
                  padding: 'var(--ob-space-100) 0.55rem',
                  borderRadius: 'var(--ob-radius-md)',
                  border: '1px solid var(--ob-color-border-default)',
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
          gap: 'var(--ob-space-150)',
          alignItems: 'center',
        }}
      >
        <button
          type="button"
          onClick={onReset}
          disabled={entries.length === 0}
          style={{
            padding: 'var(--ob-space-100) 0.85rem',
            borderRadius: 'var(--ob-radius-lg)',
            border: '1px solid var(--ob-color-border-default)',
            background: 'var(--ob-color-bg-muted)',
            fontWeight: 600,
            color: 'var(--ob-color-bg-inverse)',
            fontSize: '0.85rem',
            cursor: entries.length === 0 ? 'not-allowed' : 'pointer',
            opacity: entries.length === 0 ? 0.5 : 1,
          }}
        >
          Reset to preview defaults
        </button>
        <p
          style={{
            margin: 0,
            fontSize: '0.85rem',
            color: 'var(--ob-color-text-secondary)',
          }}
        >
          Use "Refresh preview render" after editing the palette so GLTF colours
          match the updated legend.
        </p>
      </div>
    </section>
  )
}
