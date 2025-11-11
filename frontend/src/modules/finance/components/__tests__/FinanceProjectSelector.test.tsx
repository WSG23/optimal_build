import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import React from 'react'

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
      <TranslationProvider>
        <FinanceProjectSelector
          selectedProjectId="alpha"
          selectedProjectName="Alpha Project"
          options={options}
          onProjectChange={handleChange}
        />
      </TranslationProvider>,
    )

    fireEvent.change(screen.getByLabelText(/Recent captures/i), {
      target: { value: 'beta' },
    })
    expect(handleChange).toHaveBeenCalledWith('beta', 'Beta Project')
  })

  it('submits manual project id', () => {
    const handleChange = vi.fn()
    render(
      <TranslationProvider>
        <FinanceProjectSelector
          selectedProjectId="alpha"
          selectedProjectName="Alpha Project"
          options={options}
          onProjectChange={handleChange}
        />
      </TranslationProvider>,
    )

    fireEvent.change(screen.getByLabelText(/Project ID/i), {
      target: { value: 'gamma-project' },
    })
    fireEvent.click(screen.getByText(/Load project/i))

    expect(handleChange).toHaveBeenCalledWith('gamma-project', null)
  })
})
