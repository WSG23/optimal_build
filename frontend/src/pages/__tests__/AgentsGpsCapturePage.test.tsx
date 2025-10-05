import assert from 'node:assert/strict'
import { afterEach, beforeEach, describe, it } from 'node:test'

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import React from 'react'
import { JSDOM } from 'jsdom'

import { TranslationProvider } from '../../i18n'
import type { GpsCaptureSummary } from '../../api/agents'
import { AgentsGpsCapturePage } from '../AgentsGpsCapturePage'

describe('AgentsGpsCapturePage', () => {
  let dom: JSDOM

  beforeEach(() => {
    dom = new JSDOM('<!doctype html><html><body></body></html>', {
      url: 'http://localhost/agents/site-capture',
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

    let callCount = 0
    const stub = async () => {
      callCount += 1
      return summary
    }

    render(
      <TranslationProvider>
        <AgentsGpsCapturePage logPropertyFn={stub} />
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
      assert.equal(callCount, 1)
    })

    assert.ok(
      screen.getByRole('heading', { name: /Raw land potential/i })
    )
    assert.ok(screen.getByText(/Max GFA 20,000 sqm/i))
  })
})
