import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import React from 'react'

import { DeveloperProvider } from '../../../../contexts/DeveloperContext'
import { TranslationProvider } from '../../../../i18n'
import {
  FinanceProjectSelector,
  type FinanceProjectOption,
} from '../FinanceProjectSelector'

const options: FinanceProjectOption[] = [
  { id: 'alpha', label: 'Alpha Project', projectName: 'Alpha Project' },
  { id: 'beta', label: 'Beta Project', projectName: 'Beta Project' },
]

describe('FinanceProjectSelector', () => {
  it('calls onProjectChange when selecting a recent capture', () => {
    const handleChange = vi.fn()
    render(
      <DeveloperProvider>
        <TranslationProvider>
          <FinanceProjectSelector
            selectedProjectId="alpha"
            selectedProjectName="Alpha Project"
            options={options}
            onProjectChange={handleChange}
          />
        </TranslationProvider>
      </DeveloperProvider>,
    )

    fireEvent.change(screen.getByRole('combobox'), {
      target: { value: 'beta' },
    })
    expect(handleChange).toHaveBeenCalledWith('beta', 'Beta Project')
  })

  it('submits manual project id', () => {
    const handleChange = vi.fn()
    render(
      <DeveloperProvider>
        <TranslationProvider>
          <FinanceProjectSelector
            selectedProjectId="alpha"
            selectedProjectName="Alpha Project"
            options={options}
            onProjectChange={handleChange}
          />
        </TranslationProvider>
      </DeveloperProvider>,
    )

    fireEvent.change(screen.getByRole('combobox'), {
      target: { value: 'manual' },
    })

    fireEvent.change(screen.getByPlaceholderText(/e\.g\./i), {
      target: { value: 'gamma-project' },
    })
    fireEvent.click(screen.getByText(/Load project/i))

    expect(handleChange).toHaveBeenCalledWith('gamma-project', null)
  })
})
