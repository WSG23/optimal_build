import { afterEach, describe, expect, it } from 'vitest'

import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import React from 'react'

import type { FinanceSensitivityOutcome } from '../../../../api/finance'
import i18n from '../../../../i18n'
import { TranslationProvider } from '../../../../i18n'
import { FinanceSensitivityTable } from '../FinanceSensitivityTable'

const outcomes: FinanceSensitivityOutcome[] = [
  {
    parameter: 'Rent',
    scenario: 'low',
    deltaLabel: '-8.00%',
    deltaValue: '-8',
    npv: '1100000.00',
    irr: '0.1020',
    escalatedCost: '24850000.00',
    totalInterest: '1789200.00',
    notes: [],
  },
  {
    parameter: 'Rent',
    scenario: 'high',
    deltaLabel: '+6.00%',
    deltaValue: '6',
    npv: '1250000.00',
    irr: '0.1180',
    escalatedCost: '24850000.00',
    totalInterest: '1789200.00',
    notes: [],
  },
  {
    parameter: 'Construction Cost',
    scenario: 'low',
    deltaLabel: '-5.00%',
    deltaValue: '-5',
    npv: '1200000.00',
    irr: '0.1120',
    escalatedCost: '37000000.00',
    totalInterest: '1789200.00',
    notes: [],
  },
]

describe('FinanceSensitivityTable', () => {
  afterEach(() => {
    cleanup()
  })

  it('renders controls and sensitivity table, handling toggles and downloads', () => {
    let toggledParameter: string | null = null
    let csvClicked = 0
    let jsonClicked = 0
    let selectAllClicked = 0

    render(
      <TranslationProvider>
        <FinanceSensitivityTable
          outcomes={outcomes}
          currency="SGD"
          parameters={['Rent', 'Construction Cost']}
          selectedParameters={['Rent', 'Construction Cost']}
          onToggleParameter={(parameter) => {
            toggledParameter = parameter
          }}
          onSelectAll={() => {
            selectAllClicked += 1
          }}
          onDownloadCsv={() => {
            csvClicked += 1
          }}
          onDownloadJson={() => {
            jsonClicked += 1
          }}
        />
      </TranslationProvider>,
    )

    expect(
      screen.getByText(i18n.t('finance.sensitivity.title')),
    ).toBeTruthy()
    const rentCheckbox = screen.getByLabelText('Rent')
    fireEvent.click(rentCheckbox)
    expect(toggledParameter).toBe('Rent')

    const selectAllButton = screen.getByRole('button', {
      name: i18n.t('finance.sensitivity.controls.selectAll'),
    })
    fireEvent.click(selectAllButton)
    expect(selectAllClicked).toBe(1)

    const csvButton = screen.getByRole('button', {
      name: i18n.t('finance.sensitivity.actions.downloadCsv'),
    })
    fireEvent.click(csvButton)
    expect(csvClicked).toBe(1)

    const jsonButton = screen.getByRole('button', {
      name: i18n.t('finance.sensitivity.actions.downloadJson'),
    })
    fireEvent.click(jsonButton)
    expect(jsonClicked).toBe(1)
  })

  it('renders empty state when no data provided', () => {
    render(
      <TranslationProvider>
        <FinanceSensitivityTable
          outcomes={[]}
          currency="SGD"
          parameters={[]}
          selectedParameters={[]}
          onToggleParameter={() => {
            /* noop */
          }}
          onSelectAll={() => {
            /* noop */
          }}
          onDownloadCsv={() => {
            /* noop */
          }}
          onDownloadJson={() => {
            /* noop */
          }}
        />
      </TranslationProvider>,
    )

    expect(
      screen.getByText(i18n.t('finance.sensitivity.empty')),
    ).toBeTruthy()
  })
})
