/**
 * Preview Layers Table Component
 *
 * Displays and controls preview massing layers with visibility,
 * solo, and zoom actions. Provides a unified onLayerAction callback.
 */

import type { PreviewLayerMetadata } from '../../previewMetadata'
import { toTitleCase } from '../../utils/formatters'

// ============================================================================
// Types
// ============================================================================

export type LayerAction = 'toggle' | 'solo' | 'focus'

export interface PreviewLayersTableProps {
  /** Preview layer metadata */
  layers: PreviewLayerMetadata[]
  /** Layer visibility map (layer id -> visible) */
  visibility: Record<string, boolean>
  /** Currently focused layer id (or null) */
  focusLayerId: string | null
  /** Count of hidden layers */
  hiddenLayerCount: number
  /** Whether metadata is loading */
  isLoading: boolean
  /** Metadata loading error (if any) */
  error: string | null
  /** Unified action callback for toggle, solo, zoom */
  onLayerAction: (layerId: string, action: LayerAction) => void
  /** Called to show all layers */
  onShowAll: () => void
  /** Called to reset view focus */
  onResetFocus: () => void
  /** Number formatter function */
  formatNumber: (value: number, options?: Intl.NumberFormatOptions) => string
}

// ============================================================================
// Component
// ============================================================================

export function PreviewLayersTable({
  layers,
  visibility,
  focusLayerId,
  hiddenLayerCount,
  isLoading,
  error,
  onLayerAction,
  onShowAll,
  onResetFocus,
  formatNumber,
}: PreviewLayersTableProps) {
  return (
    <section
      style={{
        marginTop: '1.5rem',
        border: '1px solid var(--ob-color-border-subtle)',
        borderRadius: 'var(--ob-radius-sm)',
        padding: '1.2rem',
        background: 'white',
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
              color: 'var(--ob-color-text-primary)',
            }}
          >
            Rendered layers
          </h4>
          <p
            style={{
              margin: 0,
              fontSize: '0.9rem',
              color: 'var(--ob-color-text-secondary)',
            }}
          >
            Hide, solo, and zoom specific massing layers directly from the Site
            Acquisition workspace while reviewing the Phase 2B preview.
          </p>
        </div>
        <div
          style={{
            fontSize: '0.85rem',
            fontWeight: 600,
            color: error
              ? 'var(--ob-warning-700)'
              : 'var(--ob-color-text-secondary)',
          }}
        >
          {isLoading
            ? 'Loading preview metadata…'
            : error
              ? `Metadata error: ${error}`
              : `${layers.length} layers${hiddenLayerCount ? ` · ${hiddenLayerCount} hidden` : ''}`}
        </div>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
        <button
          type="button"
          onClick={onShowAll}
          disabled={
            isLoading ||
            !layers.length ||
            (hiddenLayerCount === 0 && !focusLayerId)
          }
          style={{
            padding: '0.35rem 0.8rem',
            borderRadius: 'var(--ob-radius-pill)',
            border: '1px solid var(--ob-color-border-subtle)',
            background: 'var(--ob-color-bg-surface-elevated)',
            fontWeight: 600,
            color: 'var(--ob-color-text-primary)',
            fontSize: '0.85rem',
          }}
        >
          Show all layers
        </button>
        <button
          type="button"
          onClick={onResetFocus}
          disabled={!focusLayerId}
          style={{
            padding: '0.35rem 0.8rem',
            borderRadius: 'var(--ob-radius-pill)',
            border: '1px solid var(--ob-color-border-subtle)',
            background: 'var(--ob-color-bg-surface-elevated)',
            fontWeight: 600,
            color: focusLayerId
              ? 'var(--ob-color-text-primary)'
              : 'var(--ob-color-text-muted)',
            fontSize: '0.85rem',
          }}
        >
          Reset view
        </button>
      </div>
      {!isLoading && !error && layers.length === 0 && (
        <p
          style={{
            margin: 0,
            fontSize: '0.85rem',
            color: 'var(--ob-color-text-secondary)',
          }}
        >
          Layer metrics will populate once the preview metadata asset is ready.
          Refresh the render if the queue has expired.
        </p>
      )}
      {layers.length > 0 && (
        <div style={{ overflowX: 'auto' }}>
          <table
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              minWidth: '640px',
            }}
          >
            <thead>
              <tr
                style={{
                  textAlign: 'left',
                  borderBottom: '1px solid var(--ob-color-border-subtle)',
                }}
              >
                <th
                  style={{
                    padding: '0.5rem',
                    fontSize: '0.8rem',
                    color: 'var(--ob-color-text-muted)',
                  }}
                >
                  Layer
                </th>
                <th
                  style={{
                    padding: '0.5rem',
                    fontSize: '0.8rem',
                    color: 'var(--ob-color-text-muted)',
                  }}
                >
                  Allocation
                </th>
                <th
                  style={{
                    padding: '0.5rem',
                    fontSize: '0.8rem',
                    color: 'var(--ob-color-text-muted)',
                  }}
                >
                  GFA (sqm)
                </th>
                <th
                  style={{
                    padding: '0.5rem',
                    fontSize: '0.8rem',
                    color: 'var(--ob-color-text-muted)',
                  }}
                >
                  NIA (sqm)
                </th>
                <th
                  style={{
                    padding: '0.5rem',
                    fontSize: '0.8rem',
                    color: 'var(--ob-color-text-muted)',
                  }}
                >
                  Est. height (m)
                </th>
                <th
                  style={{
                    padding: '0.5rem',
                    fontSize: '0.8rem',
                    color: 'var(--ob-color-text-muted)',
                  }}
                >
                  Est. floors
                </th>
                <th
                  style={{
                    padding: '0.5rem',
                    fontSize: '0.8rem',
                    color: 'var(--ob-color-text-muted)',
                  }}
                >
                  Controls
                </th>
              </tr>
            </thead>
            <tbody>
              {layers.map((layer) => {
                const isVisible = visibility[layer.id] !== false
                return (
                  <tr
                    key={layer.id}
                    style={{
                      borderBottom: '1px solid var(--ob-color-border-subtle)',
                    }}
                  >
                    <th
                      scope="row"
                      style={{
                        padding: '0.65rem 0.5rem',
                        fontSize: '0.9rem',
                        fontWeight: 600,
                        color: 'var(--ob-color-text-primary)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                      }}
                    >
                      <span
                        style={{
                          display: 'inline-flex',
                          width: '14px',
                          height: '14px',
                          borderRadius: 'var(--ob-radius-pill)',
                          background: layer.color,
                          boxShadow: '0 0 0 1px rgb(255 255 255 / 0.5)',
                        }}
                        aria-hidden="true"
                      />
                      {toTitleCase(layer.name)}
                    </th>
                    <td
                      style={{
                        padding: '0.65rem 0.5rem',
                        color: 'var(--ob-color-text-secondary)',
                      }}
                    >
                      {layer.metrics.allocationPct != null
                        ? `${formatNumber(layer.metrics.allocationPct, {
                            maximumFractionDigits:
                              layer.metrics.allocationPct >= 10 ? 0 : 1,
                          })}%`
                        : '—'}
                    </td>
                    <td
                      style={{
                        padding: '0.65rem 0.5rem',
                        color: 'var(--ob-color-text-secondary)',
                      }}
                    >
                      {layer.metrics.gfaSqm != null
                        ? `${formatNumber(layer.metrics.gfaSqm, {
                            maximumFractionDigits:
                              layer.metrics.gfaSqm >= 1000 ? 0 : 1,
                          })}`
                        : '—'}
                    </td>
                    <td
                      style={{
                        padding: '0.65rem 0.5rem',
                        color: 'var(--ob-color-text-secondary)',
                      }}
                    >
                      {layer.metrics.niaSqm != null
                        ? `${formatNumber(layer.metrics.niaSqm, {
                            maximumFractionDigits:
                              layer.metrics.niaSqm >= 1000 ? 0 : 1,
                          })}`
                        : '—'}
                    </td>
                    <td
                      style={{
                        padding: '0.65rem 0.5rem',
                        color: 'var(--ob-color-text-secondary)',
                      }}
                    >
                      {layer.metrics.heightM != null
                        ? `${formatNumber(layer.metrics.heightM, {
                            maximumFractionDigits: 1,
                          })}`
                        : '—'}
                    </td>
                    <td
                      style={{
                        padding: '0.65rem 0.5rem',
                        color: 'var(--ob-color-text-secondary)',
                      }}
                    >
                      {layer.metrics.floors != null
                        ? formatNumber(layer.metrics.floors, {
                            maximumFractionDigits: 0,
                          })
                        : '—'}
                    </td>
                    <td
                      style={{
                        padding: '0.65rem 0.5rem',
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '0.4rem',
                      }}
                    >
                      <button
                        type="button"
                        onClick={() => onLayerAction(layer.id, 'toggle')}
                        style={{
                          padding: '0.25rem 0.6rem',
                          borderRadius: 'var(--ob-radius-pill)',
                          border: '1px solid var(--ob-color-border-subtle)',
                          background: isVisible
                            ? 'var(--ob-color-bg-surface-elevated)'
                            : 'var(--ob-error-50)',
                          color: isVisible
                            ? 'var(--ob-color-text-primary)'
                            : 'var(--ob-error-700)',
                          fontSize: '0.8rem',
                          fontWeight: 600,
                        }}
                      >
                        {isVisible ? 'Hide' : 'Show'}
                      </button>
                      <button
                        type="button"
                        onClick={() => onLayerAction(layer.id, 'solo')}
                        style={{
                          padding: '0.25rem 0.6rem',
                          borderRadius: 'var(--ob-radius-pill)',
                          border: '1px solid var(--ob-color-border-subtle)',
                          background: 'var(--ob-color-bg-surface-elevated)',
                          fontSize: '0.8rem',
                          fontWeight: 600,
                          color: 'var(--ob-color-text-primary)',
                        }}
                      >
                        Solo
                      </button>
                      <button
                        type="button"
                        onClick={() => onLayerAction(layer.id, 'focus')}
                        style={{
                          padding: '0.25rem 0.6rem',
                          borderRadius: 'var(--ob-radius-pill)',
                          border: '1px solid var(--ob-color-border-subtle)',
                          background:
                            focusLayerId === layer.id
                              ? 'var(--ob-info-100)'
                              : 'var(--ob-color-bg-surface-elevated)',
                          color:
                            focusLayerId === layer.id
                              ? 'var(--ob-color-brand-primary)'
                              : 'var(--ob-color-text-primary)',
                          fontSize: '0.8rem',
                          fontWeight: 600,
                        }}
                      >
                        {focusLayerId === layer.id ? 'Focused' : 'Zoom'}
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
