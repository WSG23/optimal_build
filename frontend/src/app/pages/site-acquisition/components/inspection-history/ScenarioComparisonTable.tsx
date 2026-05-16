/**
 * Scenario Comparison Table
 *
 * Detailed comparison table shown when scenarioComparisonVisible is true.
 * Extracted from HistoryCompareView for component size management.
 */

import type React from 'react'
import { type CSSProperties, type ReactElement } from 'react'
import type { RefObject } from 'react'
import { List as VirtualList } from 'react-window'
import type { ScenarioComparisonDatum } from '../../types'

// ============================================================================
// Virtualization Constants
// ============================================================================

/** Only virtualize when the row count exceeds this threshold */
const VIRTUALIZE_THRESHOLD = 15

/** Average row height in pixels (rows vary 85-240px; 120px is a good average) */
const ROW_HEIGHT = 120

/** Maximum visible height before scrolling */
const MAX_HEIGHT = 600

export interface ScenarioComparisonTableProps {
  scenarioComparisonRef: RefObject<HTMLDivElement | null>
  scenarioComparisonTableRows: ScenarioComparisonDatum[]
  formatRecordedTimestamp: (timestamp: string | null | undefined) => string
}

// ============================================================================
// Virtualized Comparison Row (react-window v2 API)
// ============================================================================

interface VirtualComparisonRowProps {
  rows: ScenarioComparisonDatum[]
  formatRecordedTimestamp: (timestamp: string | null | undefined) => string
}

function renderComparisonRowContent(
  row: ScenarioComparisonDatum,
  formatRecordedTimestamp: (timestamp: string | null | undefined) => string,
) {
  return (
    <>
      <td
        style={{
          padding: 'var(--ob-space-085) var(--ob-space-100)',
          borderBottom: '1px solid var(--ob-color-border-primary)',
          whiteSpace: 'nowrap',
        }}
      >
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--ob-space-025)',
            alignItems: 'flex-start',
          }}
        >
          <span style={{ fontWeight: 'var(--ob-font-weight-semibold)' }}>
            {row.label}
          </span>
          {row.recordedAt && (
            <span
              style={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'var(--ob-color-text-secondary)',
              }}
            >
              {formatRecordedTimestamp(row.recordedAt)}
            </span>
          )}
        </div>
      </td>
      <td
        style={{
          padding: 'var(--ob-space-085) var(--ob-space-100)',
          borderBottom: '1px solid var(--ob-color-border-primary)',
          color: 'var(--ob-color-text-primary)',
          fontSize: 'var(--ob-font-size-sm)',
          maxWidth: '220px',
        }}
      >
        {row.quickHeadline ?? '\u2014'}
      </td>
      <td
        style={{
          padding: 'var(--ob-space-085) var(--ob-space-100)',
          borderBottom: '1px solid var(--ob-color-border-primary)',
          color: 'var(--ob-color-text-primary)',
          fontSize: 'var(--ob-font-size-sm)',
          maxWidth: '220px',
        }}
      >
        {row.quickMetrics.length === 0 ? (
          '\u2014'
        ) : (
          <ul
            style={{
              margin: 0,
              paddingLeft: 'var(--ob-space-120)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-025)',
            }}
          >
            {row.quickMetrics.map((metric) => (
              <li key={`${row.key}-${metric.label}`}>
                {metric.label}: {metric.value}
              </li>
            ))}
          </ul>
        )}
      </td>
      <td
        style={{
          padding: 'var(--ob-space-085) var(--ob-space-100)',
          borderBottom: '1px solid var(--ob-color-border-primary)',
          color: 'var(--ob-color-text-primary)',
          fontSize: 'var(--ob-font-size-sm)',
          whiteSpace: 'nowrap',
        }}
      >
        {row.conditionRating ? (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-025)',
            }}
          >
            <strong>{row.conditionRating}</strong>
            <span>
              {row.conditionScore !== null
                ? `${row.conditionScore}/100`
                : '\u2014'}{' '}
              {row.riskLevel ? `\u00b7 ${row.riskLevel} risk` : ''}
            </span>
          </div>
        ) : (
          '\u2014'
        )}
      </td>
      <td
        style={{
          padding: 'var(--ob-space-085) var(--ob-space-100)',
          borderBottom: '1px solid var(--ob-color-border-primary)',
          color: 'var(--ob-color-text-primary)',
          fontSize: 'var(--ob-font-size-sm)',
          whiteSpace: 'nowrap',
        }}
      >
        {row.checklistCompleted !== null && row.checklistTotal !== null
          ? `${row.checklistCompleted}/${row.checklistTotal}` +
            (row.checklistPercent !== null ? ` (${row.checklistPercent}%)` : '')
          : '\u2014'}
      </td>
      <td
        style={{
          padding: 'var(--ob-space-085) var(--ob-space-100)',
          borderBottom: '1px solid var(--ob-color-border-primary)',
          color: 'var(--ob-color-text-primary)',
          fontSize: 'var(--ob-font-size-sm)',
          maxWidth: '240px',
        }}
      >
        {row.primaryInsight ? (
          <>
            <strong>{row.primaryInsight.title}</strong>
            <div>{row.primaryInsight.detail}</div>
          </>
        ) : row.insights.length > 0 ? (
          <div>{row.insights[0].title}</div>
        ) : (
          '\u2014'
        )}
      </td>
      <td
        style={{
          padding: 'var(--ob-space-085) var(--ob-space-100)',
          borderBottom: '1px solid var(--ob-color-border-primary)',
          color: 'var(--ob-color-text-primary)',
          fontSize: 'var(--ob-font-size-sm)',
          maxWidth: 'var(--ob-size-drop-zone-lg)',
        }}
      >
        {row.recommendedAction ?? '\u2014'}
      </td>
      <td
        style={{
          padding: 'var(--ob-space-085) var(--ob-space-100)',
          borderBottom: '1px solid var(--ob-color-border-primary)',
          color: 'var(--ob-color-text-primary)',
          fontSize: 'var(--ob-font-size-sm)',
          whiteSpace: 'nowrap',
        }}
      >
        {row.inspectorName ?? '\u2014'}
      </td>
      <td
        style={{
          padding: 'var(--ob-space-085) var(--ob-space-100)',
          borderBottom: '1px solid var(--ob-color-border-primary)',
          color: 'var(--ob-color-text-primary)',
          fontSize: 'var(--ob-font-size-sm)',
          whiteSpace: 'nowrap',
        }}
      >
        {row.source === 'manual' ? 'Manual inspection' : 'Automated baseline'}
      </td>
    </>
  )
}

function VirtualComparisonRow(
  props: {
    ariaAttributes: {
      'aria-posinset': number
      'aria-setsize': number
      role: 'listitem'
    }
    index: number
    style: CSSProperties
  } & VirtualComparisonRowProps,
): ReactElement {
  const { index, style, rows, formatRecordedTimestamp } = props
  const row = rows[index]
  return (
    <table
      style={{
        ...style,
        width: '100%',
        borderCollapse: 'collapse',
        minWidth: '960px',
      }}
    >
      <tbody>
        <tr key={`comparison-table-${row.key}`}>
          {renderComparisonRowContent(row, formatRecordedTimestamp)}
        </tr>
      </tbody>
    </table>
  )
}

// ============================================================================
// Component
// ============================================================================

export function ScenarioComparisonTable({
  scenarioComparisonRef,
  scenarioComparisonTableRows,
  formatRecordedTimestamp,
}: ScenarioComparisonTableProps) {
  const shouldVirtualize =
    scenarioComparisonTableRows.length > VIRTUALIZE_THRESHOLD

  return (
    <div ref={scenarioComparisonRef as React.RefObject<HTMLDivElement>}>
      <details
        open
        style={{
          border: '1px solid var(--ob-color-border-primary)',
          borderRadius: 'var(--ob-radius-sm)',
          background: 'var(--ob-color-bg-primary)',
          overflow: 'hidden',
        }}
      >
        <summary
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 'var(--ob-space-075)',
            padding: 'var(--ob-space-085) var(--ob-space-100)',
            fontSize: 'var(--ob-font-size-sm)',
            fontWeight: 'var(--ob-font-weight-semibold)',
            cursor: 'pointer',
            listStyle: 'none',
          }}
        >
          <span>Detailed comparison table</span>
          <span
            aria-hidden="true"
            style={{
              fontSize: 'var(--ob-font-size-xs)',
              color: 'var(--ob-color-text-secondary)',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
            }}
          >
            Collapse
          </span>
        </summary>
        <div
          style={{
            borderTop: '1px solid var(--ob-color-border-primary)',
            overflowX: 'auto',
          }}
        >
          <table
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              minWidth: '960px',
            }}
          >
            <thead style={{ background: 'var(--ob-color-bg-primary)' }}>
              <tr>
                {[
                  'Scenario',
                  'Quick headline',
                  'Key metrics',
                  'Condition',
                  'Checklist',
                  'Key insight',
                  'Next action',
                  'Inspector',
                  'Source',
                ].map((header) => (
                  <th
                    key={header}
                    style={{
                      textAlign: 'left',
                      padding: 'var(--ob-space-085) var(--ob-space-100)',
                      fontSize: 'var(--ob-font-size-xs)',
                      letterSpacing: '0.08em',
                      textTransform: 'uppercase',
                      color: 'var(--ob-color-text-secondary)',
                      borderBottom: '1px solid var(--ob-color-border-primary)',
                    }}
                  >
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
          </table>
          {shouldVirtualize ? (
            <VirtualList
              rowComponent={VirtualComparisonRow}
              rowCount={scenarioComparisonTableRows.length}
              rowHeight={ROW_HEIGHT}
              rowProps={{
                rows: scenarioComparisonTableRows,
                formatRecordedTimestamp,
              }}
              overscanCount={5}
              style={{
                height: Math.min(
                  scenarioComparisonTableRows.length * ROW_HEIGHT,
                  MAX_HEIGHT,
                ),
              }}
            />
          ) : (
            <table
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                minWidth: '960px',
              }}
            >
              <tbody>
                {scenarioComparisonTableRows.map((row) => (
                  <tr key={`comparison-table-${row.key}`}>
                    {renderComparisonRowContent(row, formatRecordedTimestamp)}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </details>
    </div>
  )
}
