import { afterEach, describe, expect, it } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import React from 'react'

import type {
  AssetFinancialSummary,
  FinanceAssetBreakdown as FinanceAssetBreakdownType,
} from '../../../../api/finance'
import i18n from '../../../../i18n'
import { TranslationProvider } from '../../../../i18n'
import { FinanceAssetBreakdown } from '../FinanceAssetBreakdown'

describe('FinanceAssetBreakdown component', () => {
  afterEach(() => {
    cleanup()
  })

  const summary: AssetFinancialSummary = {
    totalEstimatedRevenueSgd: '123600.00',
    totalEstimatedCapexSgd: '85000.00',
    dominantRiskProfile: 'moderate',
    notes: ['Aggregate performance from optimiser base case.'],
  }

  const breakdowns: FinanceAssetBreakdownType[] = [
    {
      assetType: 'Office',
      allocationPct: '0.55',
      noiAnnualSgd: '91200.00',
      estimatedCapexSgd: '50000.00',
      paybackYears: '5.49',
      absorptionMonths: '6.0',
      riskLevel: 'balanced',
      notes: [],
    },
    {
      assetType: 'Retail',
      allocationPct: '0.25',
      noiAnnualSgd: '32400.00',
      estimatedCapexSgd: '15000.00',
      paybackYears: '4.63',
      absorptionMonths: '8.0',
      riskLevel: 'moderate',
      notes: [],
    },
  ]

  it('renders summary metrics and table rows', () => {
    render(
      <TranslationProvider>
        <FinanceAssetBreakdown
          summary={summary}
          breakdowns={breakdowns}
          currency="SGD"
        />
      </TranslationProvider>,
    )

    expect(screen.getByText(i18n.t('finance.assets.title'))).toBeTruthy()
    expect(screen.getByText(i18n.t('finance.assets.totals.revenue'))).toBeTruthy()
    expect(screen.getAllByText('Office').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Retail').length).toBeGreaterThan(0)
    expect(
      screen.getByText('Aggregate performance from optimiser base case.'),
    ).toBeTruthy()
  })

  it('shows empty state when no data available', () => {
    render(
      <TranslationProvider>
        <FinanceAssetBreakdown summary={null} breakdowns={[]} currency="SGD" />
      </TranslationProvider>,
    )

    expect(screen.getByText(i18n.t('finance.assets.title'))).toBeTruthy()
    expect(
      screen.getByText(i18n.t('finance.assets.empty')),
    ).toBeTruthy()
  })
  it('renders allocation legend segments', () => {
    render(
      <TranslationProvider>
        <FinanceAssetBreakdown
          summary={summary}
          breakdowns={breakdowns}
          currency="SGD"
        />
      </TranslationProvider>,
    )

    expect(screen.getAllByText(/55\.0%/).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/25\.0%/).length).toBeGreaterThan(0)
  })
})
