import { describe, expect, it, vi } from 'vitest'
import React from 'react'
import { render, screen } from '@testing-library/react'

import type {
  DevelopmentScenario,
  CapturedProperty,
} from '../../../../api/siteAcquisition'
import type {
  ScenarioComparisonDatum,
  FeasibilitySignalEntry,
  ScenarioOption,
} from '../types'
import { MultiScenarioComparisonSection } from '../components/multi-scenario-comparison/MultiScenarioComparisonSection'

vi.mock('../../../../components/canonical/Button', () => ({
  Button: ({ children }: { children: React.ReactNode }) => (
    <button type="button">{children}</button>
  ),
}))

vi.mock('../../../../components/canonical/SegmentedGauge', () => ({
  SegmentedGauge: ({
    label,
    valueLabel,
  }: {
    label: string
    valueLabel: string
  }) => (
    <div>
      <span>{label}</span>
      <span>{valueLabel}</span>
    </div>
  ),
}))

vi.mock('../../../../components/canonical/SystemMarker', () => ({
  SystemMarker: ({
    children,
  }: {
    children: React.ReactNode
    active?: boolean
  }) => <span>{children}</span>,
}))

vi.mock('../../../../router', () => ({
  Link: ({
    children,
    className,
    to,
  }: {
    children: React.ReactNode
    className?: string
    to: string
  }) => (
    <a href={to} className={className}>
      {children}
    </a>
  ),
}))

describe('MultiScenarioComparisonSection', () => {
  it('renders recorded timestamps and feasibility link', () => {
    const scenarioLookup = new Map<DevelopmentScenario, ScenarioOption>([
      [
        'raw_land' as DevelopmentScenario,
        {
          value: 'raw_land' as DevelopmentScenario,
          label: 'Raw',
          icon: 'R',
        },
      ],
      [
        'en_bloc' as DevelopmentScenario,
        {
          value: 'en_bloc' as DevelopmentScenario,
          label: 'Enbloc',
          icon: 'E',
        },
      ],
    ])

    const scenarioComparisonData: ScenarioComparisonDatum[] = [
      {
        key: 'raw_land' as DevelopmentScenario,
        label: 'Raw land',
        icon: 'R',
        quickHeadline: null,
        quickMetrics: [{ key: 'rev', label: 'Revenue', value: '$1.0M' }],
        conditionRating: null,
        conditionScore: null,
        riskLevel: 'low',
        checklistCompleted: 1,
        checklistTotal: 2,
        checklistPercent: 50,
        insights: [],
        primaryInsight: null,
        recommendedAction: null,
        recordedAt: '2026-01-05T01:07:47Z',
        inspectorName: null,
        source: 'heuristic',
      },
      {
        key: 'en_bloc' as DevelopmentScenario,
        label: 'En bloc',
        icon: 'E',
        quickHeadline: null,
        quickMetrics: [{ key: 'rev', label: 'Revenue', value: '$2.0M' }],
        conditionRating: null,
        conditionScore: null,
        riskLevel: 'high',
        checklistCompleted: 0,
        checklistTotal: 2,
        checklistPercent: 0,
        insights: [],
        primaryInsight: null,
        recommendedAction: null,
        recordedAt: null,
        inspectorName: null,
        source: 'heuristic',
      },
    ]

    const feasibilitySignals: FeasibilitySignalEntry[] = [
      {
        scenario: 'raw_land' as DevelopmentScenario,
        label: 'Raw land',
        opportunities: ['Opportunity A'],
        risks: ['Risk A'],
      },
    ]

    render(
      <MultiScenarioComparisonSection
        capturedProperty={
          {
            propertyId: 'asset-1',
            quickAnalysis: { generatedAt: '2026-01-05T01:07:47Z' },
          } as unknown as CapturedProperty
        }
        quickAnalysisScenariosCount={2}
        scenarioComparisonData={scenarioComparisonData}
        feasibilitySignals={feasibilitySignals}
        comparisonScenariosCount={2}
        activeScenario="all"
        scenarioLookup={scenarioLookup}
        propertyId="asset-1"
        isExportingReport={false}
        reportExportMessage={null}
        setActiveScenario={vi.fn()}
        handleReportExport={vi.fn()}
        formatRecordedTimestamp={(timestamp) =>
          timestamp ? `FMT:${timestamp}` : '—'
        }
      />,
    )

    expect(screen.getAllByText('RECORDED').length).toBeGreaterThan(0)
    expect(
      screen.getAllByText('FMT:2026-01-05T01:07:47Z').length,
    ).toBeGreaterThan(0)
    expect(screen.getByRole('link', { name: /full feasibility/i })).toHaveClass(
      'multi-scenario__full-feasibility-link',
    )
    expect(screen.getByText('LAST UPDATED')).toBeInTheDocument()
  })
})
