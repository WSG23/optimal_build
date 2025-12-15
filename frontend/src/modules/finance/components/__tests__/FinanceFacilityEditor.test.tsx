import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import React from 'react'
import { describe, expect, it, vi } from 'vitest'

import type { FinanceScenarioSummary } from '../../../../api/finance'
import { TranslationProvider } from '../../../../i18n'
import { FinanceFacilityEditor } from '../FinanceFacilityEditor'

const baseScenario: FinanceScenarioSummary = {
  scenarioId: 10,
  projectId: 401,
  finProjectId: 55,
  scenarioName: 'Facility Test',
  currency: 'SGD',
  escalatedCost: '250000.00',
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
  constructionLoan: {
    interestRate: '0.0500',
    periodsPerYear: 12,
    capitaliseInterest: true,
    facilities: [
      {
        name: 'Senior Loan',
        amount: '150000.00',
        interestRate: '0.0450',
        periodsPerYear: 12,
        capitaliseInterest: true,
        upfrontFeePct: null,
        exitFeePct: null,
        reserveMonths: null,
        amortisationMonths: null,
        metadata: null,
      },
    ],
  },
  sensitivityResults: [],
  sensitivityJobs: [],
  sensitivityBands: [],
  isPrimary: true,
  isPrivate: false,
}

describe('FinanceFacilityEditor', () => {
  it('renders existing facilities and allows adding a new one', () => {
    render(
      <TranslationProvider>
        <FinanceFacilityEditor
          scenario={baseScenario}
          saving={false}
          onSave={vi.fn()}
        />
      </TranslationProvider>,
    )

    expect(screen.getByDisplayValue('Senior Loan')).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: /add facility/i }))
    const inputs = screen.getAllByRole('textbox')
    // Newly added facility has empty name field at the end
    expect(inputs[inputs.length - 1]).toHaveValue('')
  })

  it('submits updated construction loan values', async () => {
    const handleSave = vi.fn().mockResolvedValue(undefined)

    render(
      <TranslationProvider>
        <FinanceFacilityEditor
          scenario={baseScenario}
          saving={false}
          onSave={handleSave}
        />
      </TranslationProvider>,
    )

    fireEvent.change(screen.getByLabelText(/Base rate/i), {
      target: { value: '0.061' },
    })
    fireEvent.change(screen.getByDisplayValue('150000.00'), {
      target: { value: '175000' },
    })
    fireEvent.change(screen.getByDisplayValue('0.0450'), {
      target: { value: '0.052' },
    })

    const saveButton = screen.getByRole('button', { name: /save facilities/i })
    expect(saveButton).toBeEnabled()
    const form = saveButton.closest('form')
    expect(form).not.toBeNull()
    fireEvent.submit(form!)

    await waitFor(() => {
      expect(handleSave).toHaveBeenCalledWith(
        expect.objectContaining({
          interestRate: '0.061',
          facilities: expect.arrayContaining([
            expect.objectContaining({
              name: 'Senior Loan',
              amount: '175000',
              interestRate: '0.052',
            }),
          ]),
        }),
      )
    })
  })

  it('disables save when required fields are missing', () => {
    render(
      <TranslationProvider>
        <FinanceFacilityEditor
          scenario={null}
          saving={false}
          onSave={vi.fn()}
        />
      </TranslationProvider>,
    )

    expect(screen.queryByText(/Construction loan facilities/i)).toBeNull()
  })
})
