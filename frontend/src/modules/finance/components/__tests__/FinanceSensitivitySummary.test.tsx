import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import React from 'react'

import type { FinanceSensitivityOutcome } from '../../../../api/finance'
import { TranslationProvider } from '../../../../i18n'
import { FinanceSensitivitySummary } from '../FinanceSensitivitySummary'
import { buildSensitivitySummaries } from '../sensitivitySummary'

describe('FinanceSensitivitySummary', () => {
  const outcomes: FinanceSensitivityOutcome[] = [
    {
      parameter: 'Rent',
      scenario: 'Low',
      deltaLabel: 'Low (-5%)',
      deltaValue: '-5',
      npv: '1200000',
      irr: '0.09',
      escalatedCost: '950000',
      totalInterest: '350000',
      notes: [],
    },
    {
      parameter: 'Rent',
      scenario: 'Base',
      deltaLabel: 'Base',
      deltaValue: '0',
      npv: '1500000',
      irr: '0.11',
      escalatedCost: '1000000',
      totalInterest: '360000',
      notes: [],
    },
    {
      parameter: 'Rent',
      scenario: 'High',
      deltaLabel: 'High (+6%)',
      deltaValue: '6',
      npv: '1700000',
      irr: '0.13',
      escalatedCost: '980000',
      totalInterest: '365000',
      notes: [],
    },
  ]

  it('builds summaries with best and worst deltas', () => {
    const summaries = buildSensitivitySummaries(outcomes)
    expect(summaries).toHaveLength(1)
    const summary = summaries[0]
    expect(summary.bestDelta?.delta).toBeCloseTo(200000)
    expect(summary.worstDelta?.delta).toBeCloseTo(-300000)
    expect(summary.deltas).toHaveLength(3)
    expect(summary.deltas.find((delta) => delta.isBase)).toBeDefined()
  })

  it('renders cards for each summary entry', () => {
    const summaries = buildSensitivitySummaries(outcomes)
    render(
      <TranslationProvider>
        <FinanceSensitivitySummary summaries={summaries} currency="SGD" />
      </TranslationProvider>,
    )

    expect(screen.getByText('Parameter impact summary')).toBeVisible()
    expect(screen.getByText('Rent')).toBeVisible()
    expect(screen.getByText(/Upside scenario/i)).toBeVisible()
    expect(screen.getByText(/Downside scenario/i)).toBeVisible()
    expect(screen.getByText(/Scenario deltas/i)).toBeVisible()
    expect(screen.getByText(/Base/i)).toBeVisible()
  })
})
