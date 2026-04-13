import { describe, expect, it } from 'vitest'

import type { ConditionAssessment } from '../../../api/siteAcquisition'
import {
  buildHistoryComparisonSummary,
  buildHistoryRecommendedActionDiff,
  buildHistorySystemComparisons,
} from './historyComparisons'

function buildAssessment(
  overrides: Partial<ConditionAssessment> = {},
): ConditionAssessment {
  return {
    propertyId: 'property-1',
    scenario: 'raw_land',
    overallScore: 80,
    overallRating: 'B',
    riskLevel: 'high',
    summary: 'Summary',
    scenarioContext: null,
    systems: [],
    recommendedActions: [],
    inspectorName: 'Inspector',
    recordedBy: 'inspector@example.com',
    recordedAt: '2026-04-10T10:00:00Z',
    attachments: [],
    insights: [],
    ...overrides,
  }
}

describe('historyComparisons', () => {
  it('builds comparison summary for two assessments', () => {
    const current = buildAssessment({
      overallScore: 92,
      overallRating: 'A',
      riskLevel: 'moderate',
    })
    const baseline = buildAssessment({
      overallScore: 77,
      overallRating: 'C',
      riskLevel: 'high',
    })

    expect(buildHistoryComparisonSummary(current, baseline)).toEqual({
      scoreDelta: 15,
      ratingTrend: 'improved',
      riskTrend: 'improved',
      ratingChanged: true,
      riskChanged: true,
    })
  })

  it('builds action diff for two assessments', () => {
    const current = buildAssessment({
      recommendedActions: ['Inspect facade', 'Replace panel'],
    })
    const baseline = buildAssessment({
      recommendedActions: ['Replace panel', 'Stabilize canopy'],
    })

    expect(buildHistoryRecommendedActionDiff(current, baseline)).toEqual({
      newActions: ['Inspect facade'],
      clearedActions: ['Stabilize canopy'],
    })
  })

  it('builds system comparisons across mismatched system sets', () => {
    const current = buildAssessment({
      systems: [
        {
          name: 'Structure',
          rating: 'A',
          score: 90,
          notes: 'Strong',
          recommendedActions: [],
        },
        {
          name: 'Electrical',
          rating: 'B',
          score: 78,
          notes: 'Stable',
          recommendedActions: [],
        },
      ],
    })
    const baseline = buildAssessment({
      systems: [
        {
          name: 'Structure',
          rating: 'C',
          score: 60,
          notes: 'Weak',
          recommendedActions: [],
        },
      ],
    })

    expect(buildHistorySystemComparisons(current, baseline)).toEqual([
      {
        name: 'Structure',
        latest: {
          name: 'Structure',
          rating: 'A',
          score: 90,
          notes: 'Strong',
          recommendedActions: [],
        },
        previous: {
          name: 'Structure',
          rating: 'C',
          score: 60,
          notes: 'Weak',
          recommendedActions: [],
        },
        scoreDelta: 30,
      },
      {
        name: 'Electrical',
        latest: {
          name: 'Electrical',
          rating: 'B',
          score: 78,
          notes: 'Stable',
          recommendedActions: [],
        },
        previous: null,
        scoreDelta: undefined,
      },
    ])
  })
})
