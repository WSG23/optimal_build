import assert from 'node:assert/strict'
import { afterEach, beforeEach, describe, it } from 'node:test'

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import React from 'react'

import { TranslationProvider } from '../../i18n'
import type { GpsCaptureSummary } from '../../api/agents'
import { AgentsGpsCapturePage } from '../AgentsGpsCapturePage'

describe('AgentsGpsCapturePage', () => {
  beforeEach(() => {
    cleanup()
    window.history.replaceState(null, '', 'http://localhost/agents/site-capture')
  })

  afterEach(() => {
    cleanup()
  })

  it('submits coordinates and renders quick analysis cards', async () => {
    const summary: GpsCaptureSummary = {
      propertyId: 'mock-id',
      address: {
        fullAddress: '1 Example Street',
      },
      coordinates: { latitude: 1.3, longitude: 103.85 },
      existingUse: 'Office Building',
      uraZoning: { zoneDescription: 'Commercial' },
      propertyInfo: null,
      nearbyAmenities: null,
      quickAnalysis: {
        generatedAt: '2025-01-01T00:00:00Z',
        scenarios: [
          {
            scenario: 'raw_land',
            headline: 'Max GFA 20,000 sqm',
            metrics: { plot_ratio: 4, nearby_development_count: 1 },
            notes: ['Example note'],
          },
        ],
      },
      timestamp: '2025-01-01T00:00:00Z',
    }

    let captureCalls = 0
    const captureStub = async () => {
      captureCalls += 1
      return summary
    }

    let marketCalls = 0
    const marketStub = async () => {
      marketCalls += 1
      return {
        propertyId: summary.propertyId,
        report: {
          property_type: 'office',
          location: 'D01',
          period: { start: '2025-01-01', end: '2025-06-01' },
          comparables_analysis: { transaction_count: 3 },
          generated_at: '2025-07-01T00:00:00Z',
        },
      }
    }

    let packCalls = 0
    let lastPackType: string | null = null
    const packStub = async (_propertyId: string, packType: 'universal' | 'investment' | 'sales' | 'lease') => {
      packCalls += 1
      lastPackType = packType
      return {
        packType,
        propertyId: summary.propertyId,
        filename: `${packType}_pack.pdf`,
        downloadUrl: 'https://example.com/pack.pdf',
        generatedAt: '2025-07-02T08:00:00Z',
        sizeBytes: 52_428,
      }
    }

    render(
      <TranslationProvider>
        <AgentsGpsCapturePage
          logPropertyFn={captureStub}
          fetchMarketIntelligenceFn={marketStub}
          generatePackFn={packStub}
        />
      </TranslationProvider>,
    )

    fireEvent.change(screen.getByLabelText(/Latitude/i), {
      target: { value: '1.3' },
    })
    fireEvent.change(screen.getByLabelText(/Longitude/i), {
      target: { value: '103.85' },
    })

    fireEvent.click(
      screen.getByRole('button', { name: /Generate quick analysis/i }),
    )

    await waitFor(() => {
      assert.equal(captureCalls, 1)
    })
    await waitFor(() => {
      assert.equal(marketCalls, 1)
    })

    assert.ok(
      screen.getByRole('heading', { name: /Raw land potential/i })
    )
    assert.ok(screen.getByText(/Max GFA 20,000 sqm/i))
    assert.ok(screen.getByRole('heading', { name: /Market intelligence/i }))
    assert.ok(screen.getByText(/Transactions/i))
    assert.ok(screen.getByText(/Add VITE_MAPBOX_ACCESS_TOKEN/))

    fireEvent.change(screen.getByLabelText(/Pack type/i), {
      target: { value: 'sales' },
    })

    fireEvent.click(
      screen.getByRole('button', { name: /Generate professional pack/i }),
    )

    await waitFor(() => {
      assert.equal(packCalls, 1)
      assert.equal(lastPackType, 'sales')
    })

    assert.ok(
      screen.getByRole('link', { name: /Download sales_pack\.pdf/i }),
    )
  })
})
