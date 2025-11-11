import assert from 'node:assert/strict'
import { afterEach, beforeEach, describe, it } from 'node:test'
import { JSDOM } from 'jsdom'
import { cleanup, render, screen } from '@testing-library/react'
import React from 'react'

import type { FinanceScenarioSummary } from '../../../../api/finance'
import { TranslationProvider } from '../../../../i18n'
import { FinanceCapitalStack } from '../FinanceCapitalStack'
import { FinanceDrawdownSchedule } from '../FinanceDrawdownSchedule'

describe('Finance capital stack and drawdown components', () => {
  let dom: JSDOM

  beforeEach(() => {
    dom = new JSDOM('<!doctype html><html><body></body></html>', {
      url: 'http://localhost/finance',
    })
    const globalWithDom = globalThis as typeof globalThis & {
      window: Window & typeof globalThis
      document: Document
      navigator: Navigator
    }
    globalWithDom.window = dom.window
    globalWithDom.document = dom.window.document
    globalWithDom.navigator = dom.window.navigator
  })

  afterEach(() => {
    cleanup()
    dom.window.close()
    const globalWithDom = globalThis as {
      window?: Window & typeof globalThis
      document?: Document
      navigator?: Navigator
    }
    delete globalWithDom.window
    delete globalWithDom.document
    delete globalWithDom.navigator
  })

  const baseScenario: FinanceScenarioSummary = {
    scenarioId: 1,
    projectId: 401,
    finProjectId: 12,
    scenarioName: 'Scenario A',
    currency: 'SGD',
    escalatedCost: '1200.00',
    costIndex: {
      seriesName: 'construction_all_in',
      jurisdiction: 'SG',
      provider: 'Test',
      basePeriod: '2024-Q1',
      latestPeriod: '2024-Q4',
      scalar: '1.2000',
      baseIndex: null,
      latestIndex: null,
    },
    results: [],
    dscrTimeline: [],
    capitalStack: {
      currency: 'SGD',
      total: '1200.00',
      equityTotal: '400.00',
      debtTotal: '800.00',
      otherTotal: '0.00',
      equityRatio: '0.3333',
      debtRatio: '0.6667',
      otherRatio: '0.0000',
      loanToCost: '0.6667',
      weightedAverageDebtRate: '0.0650',
      slices: [
        {
          name: 'Sponsor Equity',
          sourceType: 'equity',
          category: 'equity',
          amount: '400.00',
          share: '0.3333',
          rate: null,
          trancheOrder: 0,
          metadata: {},
        },
        {
          name: 'Senior Loan',
          sourceType: 'debt',
          category: 'debt',
          amount: '800.00',
          share: '0.6667',
          rate: '0.0650',
          trancheOrder: 1,
          metadata: {
            facility: {
              upfront_fee_pct: '1.0',
              exit_fee_pct: '2.0',
              reserve_months: 6,
              amortisation_months: 24,
              periods_per_year: 12,
              capitalise_interest: true,
            },
          },
        },
      ],
    },
    drawdownSchedule: {
      currency: 'SGD',
      entries: [
        {
          period: 'M0',
          equityDraw: '150.00',
          debtDraw: '0.00',
          totalDraw: '150.00',
          cumulativeEquity: '150.00',
          cumulativeDebt: '0.00',
          outstandingDebt: '0.00',
        },
        {
          period: 'M1',
          equityDraw: '250.00',
          debtDraw: '300.00',
          totalDraw: '550.00',
          cumulativeEquity: '400.00',
          cumulativeDebt: '300.00',
          outstandingDebt: '300.00',
        },
      ],
      totalEquity: '400.00',
      totalDebt: '800.00',
      peakDebtBalance: '800.00',
      finalDebtBalance: '800.00',
    },
    assetMixSummary: null,
    assetBreakdowns: [],
    constructionLoanInterest: null,
    constructionLoan: null,
    sensitivityResults: [],
    sensitivityJobs: [],
    sensitivityBands: [],
    isPrimary: true,
    isPrivate: false,
    updatedAt: null,
  }

  it('renders the capital stack overview for scenarios with data', () => {
    render(
      <TranslationProvider>
        <FinanceCapitalStack scenarios={[baseScenario]} />
      </TranslationProvider>,
    )

    assert.ok(screen.getByText('Capital stack overview'))
    assert.ok(screen.getByText('Scenario A'))
    assert.ok(screen.getByText('Equity share'))
    assert.ok(screen.getByText('Tranche / facility detail'))
    assert.ok(screen.getByText('Senior Loan'))
    assert.ok(screen.getByText('Interest reserve (months)'))
    assert.ok(screen.getByText('Interest handling'))
  })

  it('renders the drawdown table for scenarios with schedules', () => {
    render(
      <TranslationProvider>
        <FinanceDrawdownSchedule scenarios={[baseScenario]} />
      </TranslationProvider>,
    )

    assert.ok(screen.getByText('Drawdown schedule'))
    assert.ok(screen.getByText('M1'))
    assert.ok(screen.getByText('Equity draw'))
  })
})
