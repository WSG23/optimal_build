import { assert, describe, it } from 'vitest'

import type { OverlaySuggestion } from '../../api/client'
import {
  aggregateOverlaySuggestions,
  countSeverityBuckets,
  calculateSeverityPercentages,
  filterLatestUnitSpaceSuggestions,
} from '../cadDetectionHelpers'

let nextId = 1000

function buildSuggestion(
  overrides: Partial<OverlaySuggestion>,
): OverlaySuggestion {
  nextId += 1
  return {
    id: nextId,
    projectId: 401,
    sourceGeometryId: 501,
    code: 'rule_data_missing_front_setback_m',
    title: 'Provide front setback data',
    rationale: null,
    severity: null,
    status: 'pending',
    engineVersion: '2024.1',
    enginePayload: {},
    score: null,
    geometryChecksum: 'checksum',
    createdAt: '2025-01-01T00:00:00.000Z',
    updatedAt: '2025-01-01T00:00:00.000Z',
    decidedAt: null,
    decidedBy: null,
    decisionNotes: null,
    decision: null,
    ...overrides,
  }
}

describe('CadDetection overlay aggregation helpers', () => {
  it('keeps only the newest unit space overlays', () => {
    const suggestions: OverlaySuggestion[] = [
      buildSuggestion({
        id: 1,
        code: 'unit_space_A1',
        updatedAt: '2025-01-01T01:00:00.000Z',
        enginePayload: { area_sqm: 25 },
      }),
      buildSuggestion({
        id: 2,
        code: 'unit_space_A1',
        updatedAt: '2025-01-01T02:00:00.000Z',
        enginePayload: { area_sqm: 26 },
      }),
      buildSuggestion({
        id: 3,
        code: 'unit_space_B4',
        updatedAt: '2025-01-01T01:30:00.000Z',
        enginePayload: { area_sqm: 28 },
      }),
      buildSuggestion({
        id: 4,
        code: 'heritage_conservation',
      }),
    ]

    const filtered = filterLatestUnitSpaceSuggestions(suggestions)
    const codes = filtered.map((item) => item.code)

    assert.equal(filtered.length, 3)
    assert.deepEqual(codes.sort(), [
      'heritage_conservation',
      'unit_space_A1',
      'unit_space_B4',
    ])

    const selected = filtered.find((item) => item.code === 'unit_space_A1')
    assert(selected, 'expected latest unit_space overlay to remain')
    assert.equal(selected?.updatedAt, '2025-01-01T02:00:00.000Z')
  })

  it('aggregates overlays by metric or code with counts and status priority', () => {
    const now = '2025-01-02T00:00:00.000Z'
    const suggestions: OverlaySuggestion[] = [
      buildSuggestion({
        id: 101,
        status: 'approved',
        code: 'rule_data_missing_front_setback_m',
        updatedAt: '2025-01-01T03:00:00.000Z',
        severity: 'low',
        enginePayload: { missing_metric: 'front_setback_m', area_sqm: 12 },
      }),
      buildSuggestion({
        id: 102,
        status: 'pending',
        code: 'rule_violation_zoning_site_coverage_max_percent',
        enginePayload: {
          missing_metric: 'front_setback_m',
          area_sqm: 18,
        },
        updatedAt: now,
        severity: 'high',
      }),
      buildSuggestion({
        id: 103,
        status: 'rejected',
        code: 'unit_space_A1',
        enginePayload: { area_sqm: 20 },
        updatedAt: '2025-01-01T04:00:00.000Z',
        severity: 'medium',
      }),
      buildSuggestion({
        id: 104,
        status: 'approved',
        code: 'unit_space_A1',
        enginePayload: { area_sqm: 22 },
        updatedAt: now,
      }),
    ]

    const aggregated = aggregateOverlaySuggestions(suggestions)
    const byKey = Object.fromEntries(aggregated.map((item) => [item.key, item]))

    assert.equal(aggregated.length, 2)

    const metricGroup = byKey.front_setback_m
    assert(metricGroup, 'expected front_setback_m group')
    assert.equal(metricGroup.count, 2)
    assert.equal(metricGroup.status, 'pending')
    assert.equal(metricGroup.totalArea, 30)
    assert.equal(metricGroup.suggestion.id, 102)
    assert.equal(metricGroup.missingMetricKey, 'front_setback_m')
    assert.equal(metricGroup.severity, 'high')

    const unitGroup = byKey.unit_space_A1
    assert(unitGroup, 'expected unit space aggregation')
    assert.equal(unitGroup.count, 2)
    assert.equal(unitGroup.status, 'rejected')
    assert.equal(unitGroup.totalArea, 42)
    assert.equal(unitGroup.suggestion.id, 104)
    assert.equal(unitGroup.severity, 'medium')
  })

  it('counts severities across visible statuses', () => {
    const suggestions: OverlaySuggestion[] = [
      buildSuggestion({
        id: 201,
        code: 'rule_A',
        severity: 'high',
        status: 'pending',
      }),
      buildSuggestion({
        id: 202,
        code: 'rule_B',
        severity: 'medium',
        status: 'pending',
      }),
      buildSuggestion({
        id: 203,
        code: 'rule_C',
        severity: 'low',
        status: 'approved',
      }),
      buildSuggestion({
        id: 204,
        code: 'rule_D',
        severity: 'high',
        status: 'approved',
      }),
      buildSuggestion({
        id: 205,
        code: 'rule_E',
        severity: 'medium',
        status: 'rejected',
      }),
      buildSuggestion({
        id: 206,
        code: 'rule_F',
        severity: 'low',
        status: 'pending',
      }),
      buildSuggestion({
        id: 207,
        code: 'rule_G',
        severity: null,
        status: 'pending',
      }),
    ]

    const aggregated = aggregateOverlaySuggestions(suggestions)
    const pendingCounts = countSeverityBuckets(aggregated, ['pending'])
    assert.deepEqual(pendingCounts, { high: 1, medium: 1, low: 1, none: 1 })
    const pendingPercentages = calculateSeverityPercentages(pendingCounts)
    assert.deepEqual(pendingPercentages, {
      high: 25,
      medium: 25,
      low: 25,
      none: 25,
    })

    const broadCounts = countSeverityBuckets(aggregated, [
      'pending',
      'approved',
    ])
    assert.deepEqual(broadCounts, { high: 2, medium: 1, low: 2, none: 1 })
    const broadPercentages = calculateSeverityPercentages(broadCounts)
    assert.deepEqual(broadPercentages, {
      high: 33.3,
      medium: 16.7,
      low: 33.3,
      none: 16.7,
    })
  })
})
