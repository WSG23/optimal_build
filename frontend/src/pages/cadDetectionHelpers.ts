import type { OverlaySuggestion } from '../api/client'
import type { DetectionStatus } from '../modules/cad/types'

export interface AggregatedSuggestion {
  key: string
  suggestion: OverlaySuggestion
  count: number
  status: DetectionStatus
  missingMetricKey?: string
  totalArea: number
  severity: OverlaySuggestion['severity'] | null
}

export type OverlaySeverity = 'high' | 'medium' | 'low' | 'none'

export type SeverityBuckets = Record<OverlaySeverity, number>

const SEVERITY_PRIORITY: Array<OverlaySuggestion['severity'] | null> = [
  'high',
  'medium',
  'low',
  null,
]

const ALL_SEVERITIES: OverlaySeverity[] = ['high', 'medium', 'low', 'none']

const STATUS_PRIORITY: DetectionStatus[] = [
  'pending',
  'rejected',
  'approved',
  'source',
]

export const DEFAULT_VISIBLE_SEVERITIES = ALL_SEVERITIES

export function normaliseStatus(status: string): DetectionStatus {
  const value = status.toLowerCase()
  if (value === 'approved') {
    return 'approved'
  }
  if (value === 'rejected') {
    return 'rejected'
  }
  if (value === 'pending') {
    return 'pending'
  }
  return 'source'
}

function normaliseSeverity(
  severity: OverlaySuggestion['severity'],
): OverlaySuggestion['severity'] | null {
  if (typeof severity !== 'string') {
    return null
  }
  const value = severity.toLowerCase()
  if (value === 'high' || value === 'medium' || value === 'low') {
    return value
  }
  return null
}

function getSeverityPriority(
  severity: OverlaySuggestion['severity'] | null,
): number {
  const priority = SEVERITY_PRIORITY.indexOf(severity ?? null)
  return priority === -1 ? SEVERITY_PRIORITY.length : priority
}

function getStatusPriority(status: DetectionStatus): number {
  const priority = STATUS_PRIORITY.indexOf(status)
  return priority === -1 ? STATUS_PRIORITY.length : priority
}

function getSuggestionTimestamp(suggestion: OverlaySuggestion): number {
  const updated = Date.parse(suggestion.updatedAt)
  if (Number.isFinite(updated)) {
    return updated
  }
  const created = Date.parse(suggestion.createdAt)
  if (Number.isFinite(created)) {
    return created
  }
  return 0
}

function getMissingMetricKey(
  suggestion: OverlaySuggestion,
): string | undefined {
  const payload = suggestion.enginePayload as {
    missing_metric?: unknown
    metric?: unknown
  }
  if (typeof payload?.missing_metric === 'string') {
    return payload.missing_metric
  }
  if (typeof payload?.metric === 'string') {
    return payload.metric
  }
  return undefined
}

export function filterLatestUnitSpaceSuggestions(
  suggestions: OverlaySuggestion[],
): OverlaySuggestion[] {
  const latestByCode = new Map<string, number>()
  for (const suggestion of suggestions) {
    if (!suggestion.code.startsWith('unit_space_')) {
      continue
    }
    const timestamp = getSuggestionTimestamp(suggestion)
    const existing = latestByCode.get(suggestion.code)
    if (existing == null || timestamp > existing) {
      latestByCode.set(suggestion.code, timestamp)
    }
  }

  const seen = new Set<string>()
  return suggestions.filter((suggestion) => {
    if (!suggestion.code.startsWith('unit_space_')) {
      return true
    }
    const latestTimestamp = latestByCode.get(suggestion.code)
    if (latestTimestamp == null) {
      return true
    }
    const timestamp = getSuggestionTimestamp(suggestion)
    if (timestamp !== latestTimestamp) {
      return false
    }
    if (seen.has(suggestion.code)) {
      return false
    }
    seen.add(suggestion.code)
    return true
  })
}

export function deriveAreaSqm(suggestion: OverlaySuggestion): number {
  const payload = suggestion.enginePayload
  const payloadWithArea = payload as { area_sqm?: unknown }
  const payloadWithAffectedArea = payload as { affected_area_sqm?: unknown }
  const directArea =
    typeof payloadWithArea.area_sqm === 'number'
      ? payloadWithArea.area_sqm
      : typeof payloadWithAffectedArea.affected_area_sqm === 'number'
        ? payloadWithAffectedArea.affected_area_sqm
        : null
  if (typeof directArea === 'number') {
    return directArea
  }
  if (typeof suggestion.score === 'number') {
    return Math.max(0, Math.round(suggestion.score * 1000) / 10)
  }
  return 0
}

export function aggregateOverlaySuggestions(
  suggestions: OverlaySuggestion[],
): AggregatedSuggestion[] {
  const groups = new Map<
    string,
    {
      key: string
      latest: OverlaySuggestion
      latestTimestamp: number
      status: DetectionStatus
      firstIndex: number
      missingMetricKey?: string
      count: number
      totalArea: number
      severity: OverlaySuggestion['severity'] | null
    }
  >()

  suggestions.forEach((suggestion, index) => {
    const status = normaliseStatus(suggestion.status)
    const missingMetricKey = getMissingMetricKey(suggestion)
    const groupKey = missingMetricKey ?? suggestion.code
    const timestamp = getSuggestionTimestamp(suggestion)
    const area = deriveAreaSqm(suggestion)
    const severity = normaliseSeverity(suggestion.severity)
    const existing = groups.get(groupKey)
    if (!existing) {
      groups.set(groupKey, {
        key: groupKey,
        latest: suggestion,
        latestTimestamp: timestamp,
        status,
        firstIndex: index,
        missingMetricKey,
        count: 1,
        totalArea: area,
        severity,
      })
      return
    }

    existing.count += 1
    existing.totalArea += area
    if (getStatusPriority(status) < getStatusPriority(existing.status)) {
      existing.status = status
    }
    if (!existing.missingMetricKey && missingMetricKey) {
      existing.missingMetricKey = missingMetricKey
    }
    if (timestamp >= existing.latestTimestamp) {
      existing.latest = suggestion
      existing.latestTimestamp = timestamp
    }
    if (
      severity &&
      (existing.severity == null ||
        getSeverityPriority(severity) < getSeverityPriority(existing.severity))
    ) {
      existing.severity = severity
    }
  })

  return Array.from(groups.values())
    .sort((a, b) => a.firstIndex - b.firstIndex)
    .map((group) => ({
      key: group.key,
      suggestion: group.latest,
      count: group.count,
      status: group.status,
      missingMetricKey: group.missingMetricKey,
      totalArea: group.totalArea,
      severity: group.severity ?? normaliseSeverity(group.latest.severity),
    }))
}

export function countSeverityBuckets(
  suggestions: AggregatedSuggestion[],
  visibleStatuses: DetectionStatus[],
): SeverityBuckets {
  const buckets: SeverityBuckets = {
    high: 0,
    medium: 0,
    low: 0,
    none: 0,
  }
  suggestions.forEach((item) => {
    if (!visibleStatuses.includes(item.status)) {
      return
    }
    const severity = item.severity
    if (severity === 'high' || severity === 'medium' || severity === 'low') {
      buckets[severity] += 1
    } else {
      buckets.none += 1
    }
  })
  return buckets
}

export function calculateSeverityPercentages(
  summary: SeverityBuckets,
): Record<OverlaySeverity, number> {
  const total = summary.high + summary.medium + summary.low + summary.none
  if (total === 0) {
    return {
      high: 0,
      medium: 0,
      low: 0,
      none: 0,
    }
  }
  const toPercent = (value: number) =>
    Math.round((value / total) * 100 * 10) / 10
  return {
    high: toPercent(summary.high),
    medium: toPercent(summary.medium),
    low: toPercent(summary.low),
    none: toPercent(summary.none),
  }
}
