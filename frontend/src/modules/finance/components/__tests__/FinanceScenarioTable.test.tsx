import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from '@testing-library/react'
import React from 'react'

import type { FinanceScenarioSummary } from '../../../../api/finance'
import i18n from '../../../../i18n'
import { TranslationProvider } from '../../../../i18n'
import { FinanceScenarioTable } from '../FinanceScenarioTable'

function buildScenario(
  overrides: Partial<FinanceScenarioSummary> = {},
): FinanceScenarioSummary {
  const base: FinanceScenarioSummary = {
    scenarioId: 1,
    projectId: 401,
    finProjectId: 501,
    scenarioName: 'Base Case',
    currency: 'SGD',
    escalatedCost: '1200000.00',
    costIndex: {
      seriesName: 'construction_all_in',
      jurisdiction: 'SG',
      provider: 'Public',
      basePeriod: '2024-Q1',
      latestPeriod: '2024-Q2',
      scalar: '1.0500',
      baseIndex: null,
      latestIndex: null,
    },
    results: [
      { name: 'npv', value: '250000.00', unit: 'SGD', metadata: {} },
      { name: 'irr', value: '0.12', unit: 'ratio', metadata: {} },
    ],
    dscrTimeline: [
      {
        period: 'Year 1',
        noi: '500000.00',
        debtService: '400000.00',
        dscr: '1.25',
        currency: 'SGD',
      },
    ],
    capitalStack: {
      currency: 'SGD',
      total: '1200000.00',
      equityTotal: '400000.00',
      debtTotal: '800000.00',
      otherTotal: '0.00',
      equityRatio: '0.3333',
      debtRatio: '0.6667',
      otherRatio: '0.0000',
      loanToCost: '0.6667',
      weightedAverageDebtRate: '0.0450',
      slices: [],
    },
    drawdownSchedule: null,
    assetMixSummary: null,
    assetBreakdowns: [],
    constructionLoanInterest: null,
    constructionLoan: null,
    sensitivityResults: [],
    sensitivityJobs: [],
    sensitivityBands: [],
    isPrimary: true,
    isPrivate: false,
    updatedAt: '2025-01-01T00:00:00Z',
  }
  return { ...base, ...overrides }
}

describe('FinanceScenarioTable', () => {
  afterEach(() => cleanup())

  it('renders scenario metrics with translated headers', () => {
    const scenarios: FinanceScenarioSummary[] = [
      buildScenario(),
      buildScenario({
        scenarioId: 2,
        scenarioName: 'Alt Case',
        isPrimary: false,
        results: [
          { name: 'npv', value: '150000.00', unit: 'SGD', metadata: {} },
          { name: 'irr', value: '0.09', unit: 'ratio', metadata: {} },
        ],
        dscrTimeline: [
          {
            period: 'Year 1',
            noi: '450000.00',
            debtService: '400000.00',
            dscr: '1.12',
            currency: 'SGD',
          },
        ],
      }),
    ]

    render(
      <TranslationProvider>
        <FinanceScenarioTable scenarios={scenarios} />
      </TranslationProvider>,
    )

    const cards = screen.getAllByRole('article')
    expect(cards).toHaveLength(2)

    const labels = [
      i18n.t('finance.table.headers.escalatedCost'),
      i18n.t('finance.table.headers.irr'),
      i18n.t('finance.table.headers.minDscr'),
      i18n.t('finance.table.headers.npv'),
    ]

    for (const label of labels) {
      expect(screen.getAllByText(label).length).toBeGreaterThan(0)
    }

    const firstCard = cards[0]
    expect(
      within(firstCard).getByRole('heading', { name: /Base Case/i }),
    ).toBeVisible()
    expect(firstCard.textContent).toContain('SGD')
    expect(firstCard.textContent).toContain('%')

    const secondCard = cards[1]
    expect(
      within(secondCard).getByRole('heading', { name: /Alt Case/i }),
    ).toBeVisible()
    expect(secondCard.textContent).toContain('SGD')
    expect(secondCard.textContent).toContain('%')
  })

  it('allows marking a scenario as primary', () => {
    const onMarkPrimary = vi.fn()
    const scenarios: FinanceScenarioSummary[] = [
      buildScenario({
        scenarioId: 1,
        scenarioName: 'Primary',
        isPrimary: true,
      }),
      buildScenario({
        scenarioId: 2,
        scenarioName: 'Secondary',
        isPrimary: false,
      }),
    ]

    render(
      <TranslationProvider>
        <FinanceScenarioTable
          scenarios={scenarios}
          onMarkPrimary={onMarkPrimary}
          updatingScenarioId={null}
        />
      </TranslationProvider>,
    )

    expect(
      screen.getAllByText(i18n.t('finance.table.badges.primary'))[0],
    ).toBeVisible()

    const button = screen.getByRole('button', {
      name: i18n.t('finance.table.actions.makePrimary'),
    })
    fireEvent.click(button)
    expect(onMarkPrimary).toHaveBeenCalledWith(2)
  })
})
