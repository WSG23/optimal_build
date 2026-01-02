/**
 * Preview Layers Table - Master Table (Single Source of Truth)
 *
 * Consolidated component that provides ALL layer data and controls:
 * - Visibility toggle (Eye icon)
 * - Layer metrics (Allocation, GFA, NIA, Height, Floors)
 * - Risk level indicator
 * - Solo and Focus actions
 * - Inline accordion editor for legend entries (color, label, description)
 *
 * Eliminates redundancy from:
 * - LayerBreakdownCards (removed)
 * - MassingLayersPanel (removed)
 * - ColorLegendEditor (integrated inline)
 *
 * @see frontend/UX_ARCHITECTURE.md - Single Source of Truth pattern
 */

import { useState, Fragment } from 'react'

import {
  Visibility,
  VisibilityOff,
  Edit,
  ExpandMore,
  ExpandLess,
} from '@mui/icons-material'

import { Button } from '../../../../../components/canonical/Button'
import type {
  PreviewLayerMetadata,
  PreviewLegendEntry,
} from '../../previewMetadata'
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

  // Legend editor props (integrated from ColorLegendEditor)
  /** Legend entries for inline editing */
  legendEntries?: PreviewLegendEntry[]
  /** Called when a legend field changes */
  onLegendChange?: (
    assetType: string,
    field: 'label' | 'color' | 'description',
    value: string,
  ) => void
  /** Whether there are pending legend changes */
  legendHasPendingChanges?: boolean
  /** Called to reset legend to defaults */
  onLegendReset?: () => void
}

// ============================================================================
// Risk Level Helper
// ============================================================================

function getRiskLevel(
  layer: PreviewLayerMetadata,
): 'low' | 'medium' | 'high' | null {
  // Infer risk from allocation percentage
  const pct = layer.metrics.allocationPct
  if (pct == null) return null
  if (pct >= 40) return 'high'
  if (pct >= 20) return 'medium'
  return 'low'
}

function getRiskBadgeStyle(
  risk: 'low' | 'medium' | 'high' | null,
): React.CSSProperties {
  const baseStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 'var(--ob-space-025)',
    padding: '2px 8px',
    borderRadius: 'var(--ob-radius-xs)',
    fontSize: 'var(--ob-font-size-2xs)',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  }

  switch (risk) {
    case 'low':
      return {
        ...baseStyle,
        background: 'var(--ob-success-100)',
        color: 'var(--ob-success-700)',
      }
    case 'medium':
      return {
        ...baseStyle,
        background: 'var(--ob-warning-100)',
        color: 'var(--ob-warning-700)',
      }
    case 'high':
      return {
        ...baseStyle,
        background: 'var(--ob-error-100)',
        color: 'var(--ob-error-700)',
      }
    default:
      return {
        ...baseStyle,
        background: 'var(--ob-neutral-100)',
        color: 'var(--ob-neutral-500)',
      }
  }
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
  // Legend editor props
  legendEntries = [],
  onLegendChange,
  legendHasPendingChanges = false,
  onLegendReset,
}: PreviewLayersTableProps) {
  // Track which row's accordion is expanded
  const [expandedLayerId, setExpandedLayerId] = useState<string | null>(null)

  const toggleAccordion = (layerId: string) => {
    setExpandedLayerId((prev) => (prev === layerId ? null : layerId))
  }

  // Find legend entry for a layer
  const getLegendEntry = (
    layerName: string,
  ): PreviewLegendEntry | undefined => {
    return legendEntries.find(
      (e) =>
        e.assetType.toLowerCase() === layerName.toLowerCase() ||
        e.label.toLowerCase() === layerName.toLowerCase(),
    )
  }

  const hasLegendEditor = legendEntries.length > 0 && onLegendChange

  return (
    <section className="preview-layers-master-table">
      {/* Header */}
      <div className="preview-layers-master-table__header">
        <div className="preview-layers-master-table__header-text">
          <h4 className="preview-layers-master-table__title">
            Development Preview Layers
          </h4>
          <p className="preview-layers-master-table__subtitle">
            Single source of truth for layer visibility, metrics, and legend
            customization
          </p>
        </div>
        <div className="preview-layers-master-table__header-status">
          {isLoading ? (
            <span className="preview-layers-master-table__status preview-layers-master-table__status--loading">
              Loading preview metadata...
            </span>
          ) : error ? (
            <span className="preview-layers-master-table__status preview-layers-master-table__status--error">
              Metadata error: {error}
            </span>
          ) : (
            <>
              <span className="preview-layers-master-table__status">
                {layers.length} layers
                {hiddenLayerCount > 0 && ` · ${hiddenLayerCount} hidden`}
              </span>
              {legendHasPendingChanges && (
                <span className="preview-layers-master-table__status preview-layers-master-table__status--pending">
                  Palette edits pending
                </span>
              )}
            </>
          )}
        </div>
      </div>

      {/* Action Bar */}
      <div className="preview-layers-master-table__actions">
        <Button
          variant="ghost"
          size="sm"
          onClick={onShowAll}
          disabled={
            isLoading ||
            !layers.length ||
            (hiddenLayerCount === 0 && !focusLayerId)
          }
        >
          Show All
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={onResetFocus}
          disabled={!focusLayerId}
        >
          Reset View
        </Button>
        {onLegendReset && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onLegendReset}
            disabled={legendEntries.length === 0}
          >
            Reset Legend
          </Button>
        )}
      </div>

      {/* Empty State */}
      {!isLoading && !error && layers.length === 0 && (
        <p className="preview-layers-master-table__empty">
          Layer metrics will populate once the preview metadata asset is ready.
          Refresh the render if the queue has expired.
        </p>
      )}

      {/* Master Table */}
      {layers.length > 0 && (
        <div className="preview-layers-master-table__table-wrapper">
          <table className="preview-layers-master-table__table">
            <thead>
              <tr>
                <th className="preview-layers-master-table__th preview-layers-master-table__th--visibility">
                  <Visibility sx={{ fontSize: 16, opacity: 0.6 }} />
                </th>
                <th className="preview-layers-master-table__th">Layer</th>
                <th className="preview-layers-master-table__th preview-layers-master-table__th--numeric">
                  Mix %
                </th>
                <th className="preview-layers-master-table__th preview-layers-master-table__th--numeric">
                  GFA
                </th>
                <th className="preview-layers-master-table__th preview-layers-master-table__th--numeric">
                  NIA
                </th>
                <th className="preview-layers-master-table__th preview-layers-master-table__th--numeric">
                  Height
                </th>
                <th className="preview-layers-master-table__th preview-layers-master-table__th--numeric">
                  Floors
                </th>
                <th className="preview-layers-master-table__th">Risk</th>
                <th className="preview-layers-master-table__th preview-layers-master-table__th--actions">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {layers.map((layer, index) => {
                const isVisible = visibility[layer.id] !== false
                const isFocused = focusLayerId === layer.id
                const isExpanded = expandedLayerId === layer.id
                const risk = getRiskLevel(layer)
                const legendEntry = getLegendEntry(layer.name)
                const isZebra = index % 2 === 1

                return (
                  <Fragment key={layer.id}>
                    {/* Main Row */}
                    <tr
                      className={`preview-layers-master-table__row ${isZebra ? 'preview-layers-master-table__row--zebra' : ''} ${isFocused ? 'preview-layers-master-table__row--focused' : ''}`}
                    >
                      {/* Visibility Toggle */}
                      <td className="preview-layers-master-table__td preview-layers-master-table__td--visibility">
                        <button
                          type="button"
                          onClick={() => onLayerAction(layer.id, 'toggle')}
                          className={`preview-layers-master-table__visibility-btn ${isVisible ? '' : 'preview-layers-master-table__visibility-btn--hidden'}`}
                          aria-label={isVisible ? 'Hide layer' : 'Show layer'}
                        >
                          {isVisible ? (
                            <Visibility sx={{ fontSize: 18 }} />
                          ) : (
                            <VisibilityOff sx={{ fontSize: 18 }} />
                          )}
                        </button>
                      </td>

                      {/* Layer Name with Color Swatch */}
                      <td className="preview-layers-master-table__td preview-layers-master-table__td--name">
                        <span
                          className="preview-layers-master-table__color-swatch"
                          style={{
                            background: legendEntry?.color ?? layer.color,
                          }}
                          aria-hidden="true"
                        />
                        <span className="preview-layers-master-table__layer-name">
                          {toTitleCase(legendEntry?.label ?? layer.name)}
                        </span>
                      </td>

                      {/* Allocation % */}
                      <td className="preview-layers-master-table__td preview-layers-master-table__td--numeric">
                        {layer.metrics.allocationPct != null
                          ? `${formatNumber(layer.metrics.allocationPct, {
                              maximumFractionDigits:
                                layer.metrics.allocationPct >= 10 ? 0 : 1,
                            })}%`
                          : '—'}
                      </td>

                      {/* GFA */}
                      <td className="preview-layers-master-table__td preview-layers-master-table__td--numeric">
                        {layer.metrics.gfaSqm != null
                          ? formatNumber(layer.metrics.gfaSqm, {
                              maximumFractionDigits:
                                layer.metrics.gfaSqm >= 1000 ? 0 : 1,
                            })
                          : '—'}
                      </td>

                      {/* NIA */}
                      <td className="preview-layers-master-table__td preview-layers-master-table__td--numeric">
                        {layer.metrics.niaSqm != null
                          ? formatNumber(layer.metrics.niaSqm, {
                              maximumFractionDigits:
                                layer.metrics.niaSqm >= 1000 ? 0 : 1,
                            })
                          : '—'}
                      </td>

                      {/* Height */}
                      <td className="preview-layers-master-table__td preview-layers-master-table__td--numeric">
                        {layer.metrics.heightM != null
                          ? `${formatNumber(layer.metrics.heightM, { maximumFractionDigits: 1 })}m`
                          : '—'}
                      </td>

                      {/* Floors */}
                      <td className="preview-layers-master-table__td preview-layers-master-table__td--numeric">
                        {layer.metrics.floors != null
                          ? formatNumber(layer.metrics.floors, {
                              maximumFractionDigits: 0,
                            })
                          : '—'}
                      </td>

                      {/* Risk Badge */}
                      <td className="preview-layers-master-table__td">
                        <span style={getRiskBadgeStyle(risk)}>
                          {risk ?? 'N/A'}
                        </span>
                      </td>

                      {/* Actions */}
                      <td className="preview-layers-master-table__td preview-layers-master-table__td--actions">
                        <button
                          type="button"
                          onClick={() => onLayerAction(layer.id, 'solo')}
                          className="preview-layers-master-table__action-btn"
                          title="Solo this layer"
                        >
                          Solo
                        </button>
                        <button
                          type="button"
                          onClick={() => onLayerAction(layer.id, 'focus')}
                          className={`preview-layers-master-table__action-btn ${isFocused ? 'preview-layers-master-table__action-btn--active' : ''}`}
                          title={
                            isFocused
                              ? 'Currently focused'
                              : 'Focus on this layer'
                          }
                        >
                          {isFocused ? 'Focused' : 'Focus'}
                        </button>
                        {hasLegendEditor && legendEntry && (
                          <button
                            type="button"
                            onClick={() => toggleAccordion(layer.id)}
                            className={`preview-layers-master-table__action-btn preview-layers-master-table__action-btn--edit ${isExpanded ? 'preview-layers-master-table__action-btn--active' : ''}`}
                            aria-expanded={isExpanded}
                            title="Edit legend details"
                          >
                            <Edit sx={{ fontSize: 14 }} />
                            {isExpanded ? (
                              <ExpandLess sx={{ fontSize: 14 }} />
                            ) : (
                              <ExpandMore sx={{ fontSize: 14 }} />
                            )}
                          </button>
                        )}
                      </td>
                    </tr>

                    {/* Accordion Row - Inline Legend Editor */}
                    {isExpanded && legendEntry && onLegendChange && (
                      <tr className="preview-layers-master-table__accordion-row">
                        <td colSpan={9}>
                          <div className="preview-layers-master-table__accordion-content">
                            {/* Color Picker */}
                            <div className="preview-layers-master-table__editor-field">
                              <label className="preview-layers-master-table__editor-label">
                                Color
                              </label>
                              <input
                                type="color"
                                value={legendEntry.color}
                                onChange={(e) =>
                                  onLegendChange(
                                    legendEntry.assetType,
                                    'color',
                                    e.target.value,
                                  )
                                }
                                className="preview-layers-master-table__color-input"
                                aria-label={`Color for ${legendEntry.label}`}
                              />
                            </div>

                            {/* Label Input */}
                            <div className="preview-layers-master-table__editor-field preview-layers-master-table__editor-field--grow">
                              <label className="preview-layers-master-table__editor-label">
                                Label
                              </label>
                              <input
                                type="text"
                                value={legendEntry.label}
                                onChange={(e) =>
                                  onLegendChange(
                                    legendEntry.assetType,
                                    'label',
                                    e.target.value,
                                  )
                                }
                                className="preview-layers-master-table__text-input"
                                placeholder="Layer label"
                              />
                            </div>

                            {/* Description Input */}
                            <div className="preview-layers-master-table__editor-field preview-layers-master-table__editor-field--wide">
                              <label className="preview-layers-master-table__editor-label">
                                Description
                              </label>
                              <textarea
                                value={legendEntry.description ?? ''}
                                onChange={(e) =>
                                  onLegendChange(
                                    legendEntry.assetType,
                                    'description',
                                    e.target.value,
                                  )
                                }
                                className="preview-layers-master-table__textarea"
                                placeholder="Optional description for reports and decks"
                                rows={2}
                              />
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
