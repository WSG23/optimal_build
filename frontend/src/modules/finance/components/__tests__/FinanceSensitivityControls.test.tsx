import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import React from 'react'
import { describe, expect, it, vi } from 'vitest'

import type { FinanceScenarioSummary } from '../../../../api/finance'
import { TranslationProvider } from '../../../../i18n'
import { FinanceSensitivityControls } from '../FinanceSensitivityControls'

const scenario: FinanceScenarioSummary = {
  scenarioId: 42,
  projectId: 401,
  finProjectId: 99,
  scenarioName: 'Summary Scenario',
  currency: 'SGD',
  escalatedCost: '1000000.00',
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
  results: [],
  dscrTimeline: [],
  capitalStack: null,
  drawdownSchedule: null,
  assetMixSummary: null,
  assetBreakdowns: [],
  constructionLoanInterest: null,
  constructionLoan: null,
  sensitivityResults: [],
  sensitivityJobs: [],
  sensitivityBands: [
    { parameter: 'Rent', low: '-5', base: '0', high: '6' },
    { parameter: 'Cost', low: '8', base: '0', high: '-4' },
  ],
  isPrimary: true,
  isPrivate: false,
  updatedAt: null,
}

describe('FinanceSensitivityControls', () => {
  it('renders existing bands and submits cleaned values', async () => {
    const onRun = vi.fn().mockResolvedValue(undefined)

    render(
      <TranslationProvider>
        <FinanceSensitivityControls
          scenario={scenario}
          pendingJobs={0}
          onRun={onRun}
        />
      </TranslationProvider>,
    )

    expect(screen.getByDisplayValue('Rent')).toBeInTheDocument()
    fireEvent.change(screen.getByDisplayValue('6'), {
      target: { value: '5' },
    })

    fireEvent.click(screen.getByRole('button', { name: /run sensitivity/i }))

    await waitFor(() => {
      expect(onRun).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({
            parameter: 'Rent',
            high: '5',
          }),
        ]),
      )
    })
  })

  it('renders with empty scenario and allows adding parameters', async () => {
    const onRun = vi.fn()

    render(
      <TranslationProvider>
        <FinanceSensitivityControls
          scenario={{ ...scenario, sensitivityBands: [] }}
          pendingJobs={0}
          onRun={onRun}
        />
      </TranslationProvider>,
    )

    // Component should render with a default parameter
    expect(
      screen.getByRole('button', { name: /add parameter/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /run sensitivity/i }),
    ).toBeInTheDocument()

    // Should have at least one parameter row (component may provide a default)
    const removeButtons = screen.queryAllByRole('button', { name: /remove/i })
    expect(removeButtons.length).toBeGreaterThanOrEqual(1)
  })
})
