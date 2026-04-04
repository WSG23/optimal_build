import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  buildQuickScreenAssessmentSummary,
  buildQuickScreenScenarioDescription,
  clearQuickScreenFinanceDraft,
  readQuickScreenFinanceDraft,
  saveQuickScreenFinanceDraft,
} from '../quickScreenDraft'

describe('quick screen finance draft', () => {
  beforeEach(() => {
    const storage = new Map<string, string>()
    vi.stubGlobal('window', {
      sessionStorage: {
        getItem: (key: string) => storage.get(key) ?? null,
        setItem: (key: string, value: string) => {
          storage.set(key, value)
        },
        removeItem: (key: string) => {
          storage.delete(key)
        },
      },
    })
  })

  afterEach(() => {
    clearQuickScreenFinanceDraft()
    vi.unstubAllGlobals()
  })

  it('persists assessment metadata alongside the scenario draft', () => {
    saveQuickScreenFinanceDraft({
      createdAt: '2026-04-03T12:00:00Z',
      projectName: 'Singapore quick screen',
      scenario: {
        name: 'Quick screen handoff',
        currency: 'SGD',
        costEscalation: {
          amount: '1000000',
          basePeriod: '2026-Q2',
          seriesName: 'construction_cost_index',
          jurisdiction: 'SG',
        },
        cashFlow: {
          discountRate: '0.08',
          cashFlows: ['-1000000', '1200000'],
        },
      },
      assessment: {
        generatedAt: '2026-04-03T10:00:00Z',
        ruleCorpusStatus: {
          zoneCode: 'SG:R',
          coverageState: 'approved',
          confidence: 'high',
          counts: {
            applicable: 4,
            approved: 4,
            published: 4,
            traceable: 4,
            needsReview: 0,
            rejected: 0,
          },
          appliedRuleIds: [1001, 1002],
        },
        sourceNotes: ['Geocoding: mock provider in sandbox mode'],
        recommendedRuleIds: ['ura-plot-ratio'],
      },
    })

    const draft = readQuickScreenFinanceDraft()

    expect(draft?.assessment?.generatedAt).toBe('2026-04-03T10:00:00Z')
    expect(draft?.assessment?.ruleCorpusStatus?.coverageState).toBe('approved')
    expect(draft?.assessment?.recommendedRuleIds).toEqual(['ura-plot-ratio'])
  })

  it('builds a finance description that preserves quick screen context', () => {
    const lines = buildQuickScreenAssessmentSummary({
      generatedAt: '2026-04-03T10:00:00Z',
      ruleCorpusStatus: {
        zoneCode: 'SG:R',
        coverageState: 'partial',
        confidence: 'medium',
        counts: {
          applicable: 5,
          approved: 3,
          published: 4,
          traceable: 4,
          needsReview: 1,
          rejected: 0,
        },
        appliedRuleIds: [1101],
      },
      sourceNotes: ['URA: fallback assumptions applied'],
      recommendedRuleIds: ['ura-height-control'],
    })

    expect(lines).toEqual([
      'Rule corpus: partial (medium confidence, 3/5 approved).',
      'Recommended rules: ura-height-control.',
      'Source note: URA: fallback assumptions applied',
    ])

    const description = buildQuickScreenScenarioDescription(
      'Seeded from the standalone deal calculator.',
      {
        generatedAt: '2026-04-03T10:00:00Z',
        ruleCorpusStatus: {
          zoneCode: 'SG:R',
          coverageState: 'partial',
          confidence: 'medium',
          counts: {
            applicable: 5,
            approved: 3,
            published: 4,
            traceable: 4,
            needsReview: 1,
            rejected: 0,
          },
          appliedRuleIds: [1101],
        },
        sourceNotes: ['URA: fallback assumptions applied'],
        recommendedRuleIds: ['ura-height-control'],
      },
    )

    expect(description).toContain('[Quick screen context]')
    expect(description).toContain('Rule corpus: partial (medium confidence, 3/5 approved).')
    expect(description).toContain('Source note: URA: fallback assumptions applied')
  })
})
