import assert from 'node:assert/strict'
import { afterEach, beforeEach, describe, it } from 'node:test'
import { JSDOM } from 'jsdom'
import React from 'react'
import { cleanup, render, screen } from '@testing-library/react'

import { TranslationProvider } from '../i18n'
import AnalyticsPage, {
  type AnalyticsServices,
  type NormalizedQueryMetrics,
} from './Analytics'

describe('AnalyticsPage query metrics', () => {
  let dom: JSDOM

  beforeEach(() => {
    dom = new JSDOM('<!doctype html><html><body></body></html>', {
      url: 'http://localhost/analytics',
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

  it('renders normalized metrics when available', async () => {
    const services: AnalyticsServices = {
      fetchQueryMetrics: async () => ({
        byId: {
          q1: {
            id: 'q1',
            statement: 'SELECT * FROM buildings LIMIT 5',
            averageDurationMs: 12,
            executionCount: 3,
            lastRunAt: '2024-05-01T00:00:00Z',
          },
        },
        allIds: ['q1'],
      }),
    }

    render(
      <TranslationProvider>
        <AnalyticsPage services={services} />
      </TranslationProvider>,
    )

    const list = await screen.findByTestId('query-metrics-list')
    assert.ok(list)
    assert.match(list.textContent ?? '', /SELECT \* FROM buildings/i)
    assert.equal(screen.queryByTestId('query-metrics-empty'), null)
  })

  it('shows an explicit empty state when no recent queries exist', async () => {
    const services: AnalyticsServices = {
      fetchQueryMetrics: async () => ({ byId: {}, allIds: [] }),
    }

    render(
      <TranslationProvider>
        <AnalyticsPage services={services} />
      </TranslationProvider>,
    )

    const emptyState = await screen.findByTestId('query-metrics-empty')
    assert.ok(emptyState)
    assert.equal(emptyState.textContent?.trim(), 'No recent queries have been recorded yet.')
    assert.equal(screen.queryByTestId('query-metrics-list'), null)
  })

  it('retains the empty normalized snapshot from the remote source', async () => {
    const payload: NormalizedQueryMetrics = { byId: {}, allIds: [] }
    let callCount = 0

    const services: AnalyticsServices = {
      fetchQueryMetrics: async () => {
        callCount += 1
        return payload
      },
    }

    render(
      <TranslationProvider>
        <AnalyticsPage services={services} />
      </TranslationProvider>,
    )

    const emptyState = await screen.findByTestId('query-metrics-empty')
    assert.ok(emptyState)
    assert.equal(emptyState.textContent?.trim(), 'No recent queries have been recorded yet.')
    assert.equal(callCount, 1)
  })

  it('surfaces errors without discarding the last snapshot', async () => {
    const services: AnalyticsServices = {
      fetchQueryMetrics: async () => {
        throw new Error('network down')
      },
    }

    render(
      <TranslationProvider>
        <AnalyticsPage services={services} />
      </TranslationProvider>,
    )

    const alert = await screen.findByRole('alert')
    assert.match(alert.textContent ?? '', /network down/i)

    const emptyState = await screen.findByTestId('query-metrics-empty')
    assert.ok(emptyState)
    assert.equal(emptyState.textContent?.trim(), 'No recent queries have been recorded yet.')
  })
})
