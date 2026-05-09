/**
 * System Comparison Panel
 *
 * Displays system-level score comparisons between two inspection assessments.
 * Extracted from HistoryCompareView for component size management.
 */

import { type CSSProperties, type ReactElement } from 'react'
import { List as VirtualList } from 'react-window'
import type { SystemComparisonEntry } from '../../types'

// ============================================================================
// Virtualization Constants
// ============================================================================

/** Only virtualize when the row count exceeds this threshold */
const VIRTUALIZE_THRESHOLD = 20

/** Height of a single system comparison row in pixels */
const ROW_HEIGHT = 56

/** Maximum visible rows before scrolling */
const MAX_VISIBLE_ROWS = 15

export interface SystemComparisonPanelProps {
  systemComparisons: SystemComparisonEntry[]
}

// ============================================================================
// Shared Row Renderer
// ============================================================================

function renderSystemRow(entry: SystemComparisonEntry) {
  const scoreDeltaValue =
    typeof entry.scoreDelta === 'number' ? entry.scoreDelta : null
  return (
    <>
      <span style={{ fontWeight: 'var(--ob-font-weight-semibold)' }}>
        {entry.name}
      </span>
      <span>
        {entry.latest
          ? `${entry.latest.rating} \u00b7 ${entry.latest.score}/100`
          : '\u2014'}
      </span>
      <span>
        {entry.previous
          ? `${entry.previous.rating} \u00b7 ${entry.previous.score}/100`
          : '\u2014'}
      </span>
      <span
        style={{
          fontWeight: 'var(--ob-font-weight-semibold)',
          color:
            scoreDeltaValue === null
              ? 'var(--ob-color-text-secondary)'
              : scoreDeltaValue > 0
                ? 'var(--ob-success-700)'
                : scoreDeltaValue < 0
                  ? 'var(--ob-error-700)'
                  : 'var(--ob-color-text-secondary)',
        }}
      >
        {scoreDeltaValue === null
          ? '\u2014'
          : scoreDeltaValue > 0
            ? `+${scoreDeltaValue}`
            : scoreDeltaValue}
      </span>
    </>
  )
}

function getRowBackground(entry: SystemComparisonEntry): string {
  const scoreDeltaValue =
    typeof entry.scoreDelta === 'number' ? entry.scoreDelta : null
  const isImproved = scoreDeltaValue !== null && scoreDeltaValue > 0
  const isDeclined = scoreDeltaValue !== null && scoreDeltaValue < 0
  return isImproved
    ? 'var(--ob-success-50)'
    : isDeclined
      ? 'var(--ob-color-surface-error)'
      : 'transparent'
}

// ============================================================================
// Virtualized System Row (react-window v2 API)
// ============================================================================

interface VirtualSystemRowProps {
  entries: SystemComparisonEntry[]
}

function VirtualSystemRow(
  props: {
    ariaAttributes: {
      'aria-posinset': number
      'aria-setsize': number
      role: 'listitem'
    }
    index: number
    style: CSSProperties
  } & VirtualSystemRowProps,
): ReactElement {
  const { index, style, entries } = props
  const entry = entries[index]
  return (
    <div
      style={{
        ...style,
        display: 'grid',
        gridTemplateColumns: 'minmax(160px, 2fr) repeat(3, minmax(110px, 1fr))',
        gap: '0.4rem',
        alignItems: 'center',
        fontSize: 'var(--ob-font-size-sm)',
        color: 'var(--ob-color-text-primary)',
        padding: '0.55rem 0.6rem',
        borderRadius: 'var(--ob-radius-xs)',
        background: getRowBackground(entry),
        boxSizing: 'border-box',
      }}
    >
      {renderSystemRow(entry)}
    </div>
  )
}

// ============================================================================
// Component
// ============================================================================

export function SystemComparisonPanel({
  systemComparisons,
}: SystemComparisonPanelProps) {
  const highlightedDeltaRows = systemComparisons.filter(
    (entry) => typeof entry.scoreDelta === 'number' && entry.scoreDelta !== 0,
  )
  const shouldVirtualize = systemComparisons.length > VIRTUALIZE_THRESHOLD

  return (
    <div
      style={{
        border: '1px solid var(--ob-color-border-primary)',
        borderRadius: 'var(--ob-radius-sm)',
        padding: '1.25rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
      }}
    >
      <h4
        style={{
          margin: 0,
          fontSize: 'var(--ob-font-size-sm)',
          fontWeight: 'var(--ob-font-weight-semibold)',
        }}
      >
        System comparison
      </h4>
      <div style={{ display: 'grid', rowGap: '0.6rem' }}>
        {/* Header row */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns:
              'minmax(160px, 2fr) repeat(3, minmax(110px, 1fr))',
            fontSize: 'var(--ob-font-size-xs)',
            fontWeight: 'var(--ob-font-weight-semibold)',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            color: 'var(--ob-color-text-secondary)',
          }}
        >
          <span>System</span>
          <span>Current</span>
          <span>Previous</span>
          <span>Delta Score</span>
        </div>

        {/* System rows */}
        {shouldVirtualize ? (
          <VirtualList
            rowComponent={VirtualSystemRow}
            rowCount={systemComparisons.length}
            rowHeight={ROW_HEIGHT}
            rowProps={{ entries: systemComparisons }}
            overscanCount={5}
            style={{
              height:
                Math.min(systemComparisons.length, MAX_VISIBLE_ROWS) *
                ROW_HEIGHT,
            }}
          />
        ) : (
          systemComparisons.map((entry) => (
            <div
              key={entry.name}
              style={{
                display: 'grid',
                gridTemplateColumns:
                  'minmax(160px, 2fr) repeat(3, minmax(110px, 1fr))',
                gap: '0.4rem',
                alignItems: 'center',
                fontSize: 'var(--ob-font-size-sm)',
                color: 'var(--ob-color-text-primary)',
                padding: '0.55rem 0.6rem',
                borderRadius: 'var(--ob-radius-xs)',
                background: getRowBackground(entry),
              }}
            >
              {renderSystemRow(entry)}
            </div>
          ))
        )}
      </div>
      {highlightedDeltaRows.length > 0 ? (
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '0.5rem',
            fontSize: 'var(--ob-font-size-xs)',
            color: 'var(--ob-color-text-secondary)',
          }}
        >
          {highlightedDeltaRows.map((entry) => {
            const delta = entry.scoreDelta as number
            return (
              <span
                key={`delta-chip-${entry.name}`}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.3rem',
                  padding: '0.2rem 0.5rem',
                  borderRadius: 'var(--ob-radius-pill)',
                  background:
                    delta > 0
                      ? 'var(--ob-success-50)'
                      : 'var(--ob-color-surface-error)',
                  color:
                    delta > 0
                      ? 'var(--ob-success-800)'
                      : 'var(--ob-color-status-error)',
                }}
              >
                <strong>{entry.name}</strong>
                {delta > 0 ? `+${delta}` : delta}
              </span>
            )
          })}
        </div>
      ) : null}
    </div>
  )
}
