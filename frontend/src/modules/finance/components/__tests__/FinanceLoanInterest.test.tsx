import { afterEach, describe, expect, it } from 'vitest'

import { cleanup, render, screen } from '@testing-library/react'
import React from 'react'

import type { ConstructionLoanInterest } from '../../../../api/finance'
import { TranslationProvider } from '../../../../i18n'
import { FinanceLoanInterest } from '../FinanceLoanInterest'

describe('FinanceLoanInterest component', () => {
  afterEach(() => {
    cleanup()
  })

  const schedule: ConstructionLoanInterest = {
    currency: 'SGD',
    interestRate: '0.045',
    periodsPerYear: 12,
    capitalised: true,
    totalInterest: '120000.00',
    upfrontFeeTotal: '1500.00',
    exitFeeTotal: null,
    facilities: [
      {
        name: 'Senior Loan',
        amount: '2500000.00',
        interestRate: '0.040',
        periodsPerYear: 12,
        capitalised: true,
        totalInterest: '80000.00',
        upfrontFee: '1500.00',
        exitFee: null,
      },
      {
        name: 'Mezz Loan',
        amount: '500000.00',
        interestRate: '0.085',
        periodsPerYear: 12,
        capitalised: false,
        totalInterest: '40000.00',
        upfrontFee: null,
        exitFee: null,
      },
    ],
    entries: [
      {
        period: 'Q1',
        openingBalance: '0.00',
        closingBalance: '2500000.00',
        averageBalance: '1250000.00',
        interestAccrued: '56250.00',
      },
      {
        period: 'Q2',
        openingBalance: '2556250.00',
        closingBalance: '5000000.00',
        averageBalance: '3778125.00',
        interestAccrued: '141679.69',
      },
    ],
  }

  it('renders summary, facility breakdown, and period table', () => {
    render(
      <TranslationProvider>
        <FinanceLoanInterest schedule={schedule} />
      </TranslationProvider>,
    )

    expect(screen.getByText('Construction loan interest')).toBeVisible()
    expect(screen.getByText('Total accrued interest')).toBeVisible()
    expect(screen.getByText('Upfront fees')).toBeVisible()
    expect(screen.getByText('Facility breakdown')).toBeVisible()
    expect(screen.getByText('Senior Loan')).toBeVisible()
    expect(screen.getByText('Mezz Loan')).toBeVisible()
    expect(screen.getByText('Q1')).toBeVisible()
    expect(screen.getByText('Q2')).toBeVisible()
  })

  it('renders nothing when schedule is null', () => {
    const { container } = render(
      <TranslationProvider>
        <FinanceLoanInterest schedule={null} />
      </TranslationProvider>,
    )

    expect(container.textContent).toBe('')
  })
})
