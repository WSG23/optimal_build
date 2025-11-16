import type { FinanceSensitivityOutcome } from '../../../api/finance'

export interface SensitivitySummaryItem {
  parameter: string
  baseLabel: string | null
  baseValue: number | null
  bestDelta: SensitivityDelta | null
  worstDelta: SensitivityDelta | null
  deltas: SensitivityDelta[]
  maxMagnitude: number
}

export interface SensitivityDelta {
  label: string
  scenario: string
  delta: number
  isBase?: boolean
}

export function buildSensitivitySummaries(
  outcomes: FinanceSensitivityOutcome[],
): SensitivitySummaryItem[] {
  const groups = new Map<string, FinanceSensitivityOutcome[]>()
  for (const outcome of outcomes) {
    const key = outcome.parameter || 'unknown'
    if (!groups.has(key)) {
      groups.set(key, [])
    }
    groups.get(key)?.push(outcome)
  }

  const summaries: SensitivitySummaryItem[] = []
  groups.forEach((entries, parameter) => {
    const parsed = entries
      .map((entry) => ({
        ...entry,
        npvValue: entry.npv != null ? Number(entry.npv) : null,
      }))
      .filter((entry) => entry.npvValue !== null) as Array<
      FinanceSensitivityOutcome & { npvValue: number }
    >
    if (parsed.length === 0) {
      return
    }

    const baseEntry =
      parsed.find((entry) => entry.deltaValue === '0' || /base/i.test(entry.scenario)) ??
      parsed.find((entry) => entry.deltaLabel && /base/i.test(entry.deltaLabel))

    const baseValue = baseEntry?.npvValue ?? null
    const deltaSummaries =
      baseValue === null
        ? []
        : parsed.map((entry) => ({
            label: entry.deltaLabel ?? entry.scenario,
            scenario: entry.scenario,
            delta: entry.npvValue - baseValue,
            isBase: entry === baseEntry,
          }))
    const comparative = deltaSummaries.filter((entry) => !entry.isBase)

    const bestDelta =
      comparative.length > 0
        ? comparative.reduce((best, candidate) =>
            candidate.delta > (best?.delta ?? Number.NEGATIVE_INFINITY)
              ? candidate
              : best,
          )
        : null
    const worstDelta =
      comparative.length > 0
        ? comparative.reduce((worst, candidate) =>
            candidate.delta < (worst?.delta ?? Number.POSITIVE_INFINITY)
              ? candidate
              : worst,
          )
        : null
    const maxMagnitude = deltaSummaries.reduce(
      (max, entry) => Math.max(max, Math.abs(entry.delta)),
      0,
    )

    summaries.push({
      parameter,
      baseLabel: baseEntry?.deltaLabel ?? baseEntry?.scenario ?? null,
      baseValue,
      bestDelta,
      worstDelta,
      deltas: deltaSummaries,
      maxMagnitude,
    })
  })
  return summaries
}
