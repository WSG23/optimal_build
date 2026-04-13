import type { ConditionAssessment } from '../../../../api/siteAcquisition'
import type { SystemComparisonEntry } from '../types'
import { CONDITION_RATINGS, CONDITION_RISK_LEVELS } from '../constants'

export type HistoryComparisonSummary = {
  scoreDelta: number
  ratingTrend: 'improved' | 'declined' | 'same' | 'changed'
  riskTrend: 'improved' | 'declined' | 'same' | 'changed'
  ratingChanged: boolean
  riskChanged: boolean
}

export type HistoryRecommendedActionDiff = {
  newActions: string[]
  clearedActions: string[]
}

export function buildHistoryComparisonSummary(
  currentAssessment: ConditionAssessment | null | undefined,
  baselineAssessment: ConditionAssessment | null | undefined,
): HistoryComparisonSummary | null {
  if (!currentAssessment || !baselineAssessment) {
    return null
  }

  const scoreDelta =
    currentAssessment.overallScore - baselineAssessment.overallScore

  const currentRatingIndex = (CONDITION_RATINGS as readonly string[]).indexOf(
    currentAssessment.overallRating,
  )
  const baselineRatingIndex = (CONDITION_RATINGS as readonly string[]).indexOf(
    baselineAssessment.overallRating,
  )

  let ratingTrend: HistoryComparisonSummary['ratingTrend'] = 'same'
  if (currentRatingIndex !== -1 && baselineRatingIndex !== -1) {
    if (currentRatingIndex < baselineRatingIndex) {
      ratingTrend = 'improved'
    } else if (currentRatingIndex > baselineRatingIndex) {
      ratingTrend = 'declined'
    }
  } else if (
    currentAssessment.overallRating !== baselineAssessment.overallRating
  ) {
    ratingTrend = 'changed'
  }

  const currentRiskIndex = (CONDITION_RISK_LEVELS as readonly string[]).indexOf(
    currentAssessment.riskLevel,
  )
  const baselineRiskIndex = (
    CONDITION_RISK_LEVELS as readonly string[]
  ).indexOf(baselineAssessment.riskLevel)

  let riskTrend: HistoryComparisonSummary['riskTrend'] = 'same'
  if (currentRiskIndex !== -1 && baselineRiskIndex !== -1) {
    if (currentRiskIndex < baselineRiskIndex) {
      riskTrend = 'improved'
    } else if (currentRiskIndex > baselineRiskIndex) {
      riskTrend = 'declined'
    }
  } else if (currentAssessment.riskLevel !== baselineAssessment.riskLevel) {
    riskTrend = 'changed'
  }

  return {
    scoreDelta,
    ratingTrend,
    riskTrend,
    ratingChanged:
      currentAssessment.overallRating !== baselineAssessment.overallRating,
    riskChanged: currentAssessment.riskLevel !== baselineAssessment.riskLevel,
  }
}

export function buildHistoryRecommendedActionDiff(
  currentAssessment: ConditionAssessment | null | undefined,
  baselineAssessment: ConditionAssessment | null | undefined,
): HistoryRecommendedActionDiff {
  if (!currentAssessment || !baselineAssessment) {
    return { newActions: [], clearedActions: [] }
  }

  const currentActionSet = new Set<string>(currentAssessment.recommendedActions)
  const baselineActionSet = new Set<string>(
    baselineAssessment.recommendedActions,
  )

  return {
    newActions: Array.from(currentActionSet).filter(
      (action) => !baselineActionSet.has(action),
    ),
    clearedActions: Array.from(baselineActionSet).filter(
      (action) => !currentActionSet.has(action),
    ),
  }
}

export function buildHistorySystemComparisons(
  currentAssessment: ConditionAssessment | null | undefined,
  baselineAssessment: ConditionAssessment | null | undefined,
): SystemComparisonEntry[] {
  if (!currentAssessment && !baselineAssessment) {
    return []
  }

  const names = new Set<string>()
  ;(currentAssessment?.systems ?? []).forEach((system) => {
    names.add(system.name)
  })
  ;(baselineAssessment?.systems ?? []).forEach((system) => {
    names.add(system.name)
  })

  return Array.from(names).map((name) => {
    const currentSystem =
      currentAssessment?.systems.find(
        (system: ConditionAssessment['systems'][number]) =>
          system.name === name,
      ) ?? null
    const baselineSystem =
      baselineAssessment?.systems.find(
        (system: ConditionAssessment['systems'][number]) =>
          system.name === name,
      ) ?? null

    return {
      name,
      latest: currentSystem,
      previous: baselineSystem,
      scoreDelta:
        currentSystem && baselineSystem
          ? currentSystem.score - baselineSystem.score
          : undefined,
    }
  })
}
