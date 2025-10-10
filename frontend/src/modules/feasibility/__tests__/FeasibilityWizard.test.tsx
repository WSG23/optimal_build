import assert from 'node:assert/strict'
import { beforeEach, describe, it } from 'node:test'

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import React from 'react'

import { TranslationProvider } from '../../../i18n'

describe('FeasibilityWizard marketing pack integration', () => {
  beforeEach(() => {
    cleanup()
    window.history.replaceState({}, '', '/feasibility?propertyId=abc123')
  })

  it('prefills the property id from the query string and generates a pack', async () => {
    let calls = 0
    let lastArgs: { propertyId: string; packType: string } | null = null

    const { FeasibilityWizard } = await import('../FeasibilityWizard')

    const packStub = async (propertyId: string, packType: 'universal' | 'investment' | 'sales' | 'lease') => {
      calls += 1
      lastArgs = { propertyId, packType }
      return {
        packType,
        propertyId,
        filename: `${packType}_pack.pdf`,
        downloadUrl: 'https://example.com/pack.pdf',
        generatedAt: '2025-07-02T08:00:00Z',
        sizeBytes: 64_000,
      }
    }

    render(
      <TranslationProvider>
        <FeasibilityWizard generatePackFn={packStub} />
      </TranslationProvider>,
    )

    const propertyInput = await screen.findByTestId('feasibility-pack-property')
    assert.equal((propertyInput as HTMLInputElement).value, 'abc123')

    fireEvent.change(screen.getByTestId('feasibility-pack-type'), {
      target: { value: 'investment' },
    })

    fireEvent.click(screen.getByTestId('feasibility-pack-submit'))

    await waitFor(() => {
      assert.equal(calls, 1)
    })
    assert.deepEqual(lastArgs, { propertyId: 'abc123', packType: 'investment' })

    await screen.findByRole('link', {
      name: /Download investment_pack\.pdf/i,
    })
  })
})
