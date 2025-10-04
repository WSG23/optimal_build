import assert from 'node:assert/strict'
import { afterEach, beforeEach, describe, it } from 'node:test'
import { JSDOM } from 'jsdom'
import { cleanup, render, screen } from '@testing-library/react'
import React from 'react'

import { TranslationProvider } from '../../../i18n'
import {
  type CrossCorrelationIntelligenceResponse,
  type GraphIntelligenceResponse,
  type PredictiveIntelligenceResponse,
  IntelligenceValidationError,
} from '../../../services/analytics/advancedAnalytics'
import AdvancedIntelligencePage from '../AdvancedIntelligence'

describe('AdvancedIntelligencePage', () => {
  let dom: JSDOM

  beforeEach(() => {
    dom = new JSDOM('<!doctype html><html><body></body></html>', {
      url: 'http://localhost/visualizations/intelligence',
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

  it('renders derived workspace metrics when fetchers succeed', async () => {
    const graphSuccess: GraphIntelligenceResponse = {
      kind: 'graph',
      status: 'ok',
      summary: 'Two core actors are tightly connected to the permitting office.',
      generatedAt: '2025-05-01T12:00:00Z',
      graph: {
        nodes: [
          { id: 'a', label: 'Developer A', category: 'actor', score: 0.82 },
          { id: 'b', label: 'Inspector B', category: 'official', score: 0.67 },
        ],
        edges: [{ id: 'ab', source: 'a', target: 'b', weight: 0.91 }],
      },
    }

    const predictiveSuccess: PredictiveIntelligenceResponse = {
      kind: 'predictive',
      status: 'ok',
      summary: 'Adoption is accelerating in the downtown corridor.',
      generatedAt: '2025-05-01T12:00:00Z',
      horizonMonths: 12,
      segments: [
        {
          segmentId: 'seg-1',
          segmentName: 'Downtown residential',
          baseline: 120,
          projection: 168,
          probability: 0.82,
        },
        {
          segmentId: 'seg-2',
          segmentName: 'Mixed-use pilots',
          baseline: 95,
          projection: 102,
          probability: 0.38,
        },
      ],
    }

    const correlationSuccess: CrossCorrelationIntelligenceResponse = {
      kind: 'correlation',
      status: 'ok',
      summary: 'Training programmes continue to correlate with faster approvals.',
      updatedAt: '2025-05-01T12:00:00Z',
      relationships: [
        {
          pairId: 'rel-1',
          driver: 'Planner enablement hours',
          outcome: 'Permit turnaround',
          coefficient: -0.68,
          pValue: 0.015,
        },
        {
          pairId: 'rel-2',
          driver: 'Digital submissions',
          outcome: 'Approval rate',
          coefficient: 0.54,
          pValue: 0.04,
        },
      ],
    }

    render(
      <TranslationProvider>
        <AdvancedIntelligencePage
          workspaceId="workspace-alpha"
          services={{
            fetchGraphIntelligence: async () => graphSuccess,
            fetchPredictiveIntelligence: async () => predictiveSuccess,
            fetchCrossCorrelationIntelligence: async () => correlationSuccess,
          }}
        />
      </TranslationProvider>,
    )

    await screen.findByText(
      'Current adoption likelihood across cohorts: 60%',
    )

    assert.ok(
      screen.getByText(/Graph density:\s+2 nodes \/ 1 edges/),
      'graph metrics are rendered',
    )
    assert.ok(
      screen.getByText(/Average projected uplift: 23\.7%/),
      'predictive uplift is derived from payload data',
    )
    assert.ok(
      screen.getByText(/Planner enablement hours → Permit turnaround/),
      'correlation relationships are listed',
    )
  })

  it('surfaces validation failures as predictive errors', async () => {
    const graphSuccess: GraphIntelligenceResponse = {
      kind: 'graph',
      status: 'ok',
      summary: 'Graph ready.',
      generatedAt: '2025-05-01T12:00:00Z',
      graph: {
        nodes: [{ id: '1', label: 'Actor', category: 'actor', score: 0.4 }],
        edges: [],
      },
    }

    const correlationSuccess: CrossCorrelationIntelligenceResponse = {
      kind: 'correlation',
      status: 'ok',
      summary: 'Correlations ready.',
      updatedAt: '2025-05-01T12:00:00Z',
      relationships: [],
    }

    render(
      <TranslationProvider>
        <AdvancedIntelligencePage
          workspaceId="workspace-beta"
          services={{
            fetchGraphIntelligence: async () => graphSuccess,
            fetchPredictiveIntelligence: async () => {
              throw new IntelligenceValidationError('segments missing probability', [])
            },
            fetchCrossCorrelationIntelligence: async () => correlationSuccess,
          }}
        />
      </TranslationProvider>,
    )

    const predictiveError = await screen.findByText(
      /Unable to load predictive intelligence: segments missing probability/,
    )
    assert.ok(predictiveError)
    assert.ok(
      screen.getByText(/Graph density:\s+1 nodes \/ 0 edges/),
      'graph still renders on predictive failure',
    )
  })

  it('renders explicit empty states when payloads are empty', async () => {
    const graphEmpty: GraphIntelligenceResponse = {
      kind: 'graph',
      status: 'empty',
      summary: 'No graph signals.',
    }

    const predictiveEmpty: PredictiveIntelligenceResponse = {
      kind: 'predictive',
      status: 'empty',
      summary: 'No predictive signals.',
    }

    const correlationEmpty: CrossCorrelationIntelligenceResponse = {
      kind: 'correlation',
      status: 'empty',
      summary: 'No correlation signals.',
    }

    render(
      <TranslationProvider>
        <AdvancedIntelligencePage
          workspaceId="workspace-gamma"
          services={{
            fetchGraphIntelligence: async () => graphEmpty,
            fetchPredictiveIntelligence: async () => predictiveEmpty,
            fetchCrossCorrelationIntelligence: async () => correlationEmpty,
          }}
        />
      </TranslationProvider>,
    )

    await screen.findByText(
      /No relationship intelligence is available for this workspace yet\./,
    )
    assert.ok(
      screen.getByText(
        /Predictive models have not produced any actionable signals for this workspace\./,
      ),
    )
    assert.ok(
      screen.getByText(
        /There are no significant cross correlations detected for this workspace\./,
      ),
    )
  })
})
