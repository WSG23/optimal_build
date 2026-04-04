import { afterEach, describe, expect, it, vi } from 'vitest'

import { evaluateDealCalculator } from '../dealCalculator'

describe('deal calculator API', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('maps provenance and finance summary from the standalone calculator response', async () => {
    const originalFetch = globalThis.fetch
    globalThis.fetch = (async () =>
      ({
        ok: true,
        json: async () => ({
          generatedAt: '2026-04-03T10:00:00Z',
          site: {
            inputMode: 'address',
            formattedAddress: '1 Marina Boulevard',
            jurisdictionCode: 'SG',
            landUse: 'residential',
            zoneCode: 'R',
            geocodingSource: {
              provider: 'google_maps',
              state: 'mock',
              configured: false,
              synthetic: true,
            },
            uraSource: {
              provider: 'ura',
              state: 'live',
              configured: true,
              synthetic: false,
            },
          },
          buildEnvelope: {
            siteAreaSqm: 5000,
            allowablePlotRatio: 3.5,
            maxBuildableGfaSqm: 17500,
            assumptions: ['Rule corpus coverage: approved (high confidence).'],
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
              appliedRuleIds: [1001],
            },
          },
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
            appliedRuleIds: [1001],
          },
          recommendedRuleIds: ['ura-plot-ratio'],
          feasibilitySummary: {
            maxPermissibleGfaSqm: 17500,
            estimatedAchievableGfaSqm: 14350,
            estimatedUnitCount: 168,
            siteCoveragePercent: 41,
            remarks: 'Within range',
            accuracyRange: '±10-12%',
          },
          feasibilityRules: [
            {
              id: 'ura-plot-ratio',
              title: 'Plot ratio within URA envelope',
              status: 'warning',
              notes: 'Maintain a compliance buffer.',
            },
          ],
          recommendations: ['Validate remaining zoning assumptions.'],
          financeSummary: {
            totalCapexSgd: '120000000',
            npvSgd: '18000000',
            irr: '0.1825',
            dscr: '1.34',
            notes: ['Quick screen only.'],
          },
          assetBreakdowns: [
            {
              assetType: 'Residential',
              allocationPct: '100',
              niaSqm: '14350',
              rentPsmMonth: '9.5',
              noiAnnualSgd: '9600000',
              estimatedCapexSgd: '120000000',
              absorptionMonths: '18',
              riskLevel: 'balanced',
              notes: ['Derived from quick screen'],
            },
          ],
        }),
      }) as Response) as typeof globalThis.fetch

    try {
      const result = await evaluateDealCalculator({
        address: '1 Marina Boulevard',
      })

      expect(result.site.formattedAddress).toBe('1 Marina Boulevard')
      expect(result.site.geocodingSource?.state).toBe('mock')
      expect(result.site.uraSource?.state).toBe('live')
      expect(result.ruleCorpusStatus?.coverageState).toBe('approved')
      expect(result.feasibilitySummary.maxPermissibleGfaSqm).toBe(17500)
      expect(result.financeSummary.npvSgd).toBe(18000000)
      expect(result.financeSummary.irr).toBe(0.1825)
      expect(result.assetBreakdowns[0]?.assetType).toBe('Residential')
    } finally {
      globalThis.fetch = originalFetch
    }
  })
})
