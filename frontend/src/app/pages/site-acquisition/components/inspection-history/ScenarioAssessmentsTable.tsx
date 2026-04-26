/**
 * Scenario Assessments Table
 *
 * Displays scenario-level assessment summaries in a table.
 * Extracted from HistoryCompareView for component size management.
 */

import { type CSSProperties, type ReactElement } from 'react'
import { List as VirtualList } from 'react-window'
import type {
  ConditionAssessment,
  DevelopmentScenario,
} from '../../../../../api/siteAcquisition'

// ============================================================================
// Virtualization Constants
// ============================================================================

/** Only virtualize when the row count exceeds this threshold */
const VIRTUALIZE_THRESHOLD = 20

/** Height of a single assessment row in pixels */
const ROW_HEIGHT = 50

/** Maximum visible rows before scrolling */
const MAX_VISIBLE_ROWS = 15

export interface ScenarioAssessmentsTableProps {
  scenarioAssessments: ConditionAssessment[]
  formatScenarioLabel: (
    scenario: DevelopmentScenario | 'all' | null | undefined,
  ) => string
  formatRecordedTimestamp: (timestamp: string | null | undefined) => string
}

// ============================================================================
// Shared Row Content Renderer
// ============================================================================

function renderAssessmentRowContent(
  assessment: ConditionAssessment,
  formatScenarioLabel: (
    scenario: DevelopmentScenario | 'all' | null | undefined,
  ) => string,
  formatRecordedTimestamp: (timestamp: string | null | undefined) => string,
) {
  return (
    <>
      <td
        style={{
          padding: '0.75rem 1rem',
          borderBottom: '1px solid var(--ob-color-border-primary)',
          fontWeight: 'var(--ob-font-weight-semibold)',
        }}
      >
        {formatScenarioLabel(assessment.scenario)}
      </td>
      <td
        style={{
          padding: '0.75rem 1rem',
          borderBottom: '1px solid var(--ob-color-border-primary)',
          color: 'var(--ob-color-text-secondary)',
          fontSize: 'var(--ob-font-size-sm)',
        }}
      >
        {formatRecordedTimestamp(assessment.recordedAt)}
      </td>
      <td
        style={{
          padding: '0.75rem 1rem',
          borderBottom: '1px solid var(--ob-color-border-primary)',
          fontWeight: 'var(--ob-font-weight-semibold)',
        }}
      >
        {assessment.overallRating}
      </td>
      <td
        style={{
          padding: '0.75rem 1rem',
          borderBottom: '1px solid var(--ob-color-border-primary)',
        }}
      >
        {assessment.overallScore}/100
      </td>
      <td
        style={{
          padding: '0.75rem 1rem',
          borderBottom: '1px solid var(--ob-color-border-primary)',
          textTransform: 'capitalize',
        }}
      >
        {assessment.riskLevel}
      </td>
      <td
        style={{
          padding: '0.75rem 1rem',
          borderBottom: '1px solid var(--ob-color-border-primary)',
          color: 'var(--ob-color-text-secondary)',
        }}
      >
        {assessment.inspectorName?.trim() || '\u2014'}
      </td>
    </>
  )
}

// ============================================================================
// Virtualized Assessment Row (react-window v2 API)
// ============================================================================

interface VirtualAssessmentRowProps {
  assessments: ConditionAssessment[]
  formatScenarioLabel: (
    scenario: DevelopmentScenario | 'all' | null | undefined,
  ) => string
  formatRecordedTimestamp: (timestamp: string | null | undefined) => string
}

function VirtualAssessmentRow(
  props: {
    ariaAttributes: {
      'aria-posinset': number
      'aria-setsize': number
      role: 'listitem'
    }
    index: number
    style: CSSProperties
  } & VirtualAssessmentRowProps,
): ReactElement {
  const {
    index,
    style,
    assessments,
    formatScenarioLabel,
    formatRecordedTimestamp,
  } = props
  const assessment = assessments[index]
  return (
    <table
      style={{
        ...style,
        width: '100%',
        borderCollapse: 'collapse',
        minWidth: '600px',
      }}
    >
      <tbody>
        <tr>
          {renderAssessmentRowContent(
            assessment,
            formatScenarioLabel,
            formatRecordedTimestamp,
          )}
        </tr>
      </tbody>
    </table>
  )
}

// ============================================================================
// Component
// ============================================================================

export function ScenarioAssessmentsTable({
  scenarioAssessments,
  formatScenarioLabel,
  formatRecordedTimestamp,
}: ScenarioAssessmentsTableProps) {
  if (scenarioAssessments.length === 0) {
    return null
  }

  const shouldVirtualize = scenarioAssessments.length > VIRTUALIZE_THRESHOLD

  return (
    <div
      style={{
        border: '1px solid var(--ob-color-border-primary)',
        borderRadius: 'var(--ob-radius-sm)',
        overflow: 'hidden',
      }}
    >
      <h4
        style={{
          margin: 0,
          padding: '1rem 1.25rem',
          fontSize: 'var(--ob-font-size-sm)',
          fontWeight: 'var(--ob-font-weight-semibold)',
          background: 'var(--ob-color-surface-secondary)',
          borderBottom: '1px solid var(--ob-color-border-primary)',
        }}
      >
        Scenario assessments
      </h4>
      <div style={{ overflowX: 'auto' }}>
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            minWidth: '600px',
          }}
        >
          <thead>
            <tr>
              {[
                'Scenario',
                'Recorded',
                'Rating',
                'Score',
                'Risk',
                'Inspector',
              ].map((header) => (
                <th
                  key={header}
                  style={{
                    textAlign: 'left',
                    padding: '0.75rem 1rem',
                    borderBottom: '1px solid var(--ob-color-border-primary)',
                    fontWeight: 'var(--ob-font-weight-semibold)',
                    fontSize: 'var(--ob-font-size-sm)',
                    letterSpacing: '0.04em',
                    textTransform: 'uppercase',
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
            rowComponent={VirtualAssessmentRow}
            rowCount={scenarioAssessments.length}
            rowHeight={ROW_HEIGHT}
            rowProps={{
              assessments: scenarioAssessments,
              formatScenarioLabel,
              formatRecordedTimestamp,
            }}
            overscanCount={5}
            style={{
              height:
                Math.min(scenarioAssessments.length, MAX_VISIBLE_ROWS) *
                ROW_HEIGHT,
            }}
          />
        ) : (
          <table
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              minWidth: '600px',
            }}
          >
            <tbody>
              {scenarioAssessments.map((assessment, index) => (
                <tr key={`scenario-assessment-${assessment.scenario ?? index}`}>
                  {renderAssessmentRowContent(
                    assessment,
                    formatScenarioLabel,
                    formatRecordedTimestamp,
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
