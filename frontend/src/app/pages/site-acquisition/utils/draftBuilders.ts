/**
 * Draft builders for assessment forms and checklist data
 *
 * Pure functions for constructing draft objects from existing data.
 */

import type {
  ChecklistItem,
  ChecklistSummary,
  ConditionAssessment,
  DevelopmentScenario,
} from '../../../../api/siteAcquisition'
import type { AssessmentDraftSystem, ConditionAssessmentDraft } from '../types'
import { DEFAULT_CONDITION_SYSTEMS } from '../constants'
import { formatDateTimeLocalInput } from './formatters'

// ============================================================================
// Assessment Draft Builder
// ============================================================================

/**
 * Build a draft object for the condition assessment form
 * Populates from existing assessment or creates defaults
 */
export function buildAssessmentDraft(
  assessment: ConditionAssessment | null,
  activeScenario: DevelopmentScenario | 'all',
): ConditionAssessmentDraft {
  const targetScenario =
    assessment?.scenario ?? (activeScenario === 'all' ? 'all' : activeScenario)
  const systemsFromAssessment = assessment?.systems ?? []

  const systems: AssessmentDraftSystem[] = (
    systemsFromAssessment.length > 0
      ? systemsFromAssessment
      : DEFAULT_CONDITION_SYSTEMS.map((name) => ({
          name,
          rating: 'B',
          score: 70,
          notes: '',
          recommendedActions: '',
        }))
  ).map((system) => ({
    name: system.name,
    rating: system.rating,
    score: String(system.score ?? 0),
    notes: system.notes ?? '',
    recommendedActions: Array.isArray(system.recommendedActions)
      ? system.recommendedActions.join('\n')
      : '',
  }))

  const recordedAtLocal = formatDateTimeLocalInput(
    assessment?.recordedAt ?? null,
  )
  const attachmentsText = (assessment?.attachments ?? [])
    .map((attachment) =>
      attachment.url
        ? `${attachment.label} | ${attachment.url}`
        : attachment.label,
    )
    .join('\n')

  return {
    scenario: targetScenario,
    overallRating: assessment?.overallRating ?? 'B',
    overallScore: String(assessment?.overallScore ?? 75),
    riskLevel: assessment?.riskLevel ?? 'moderate',
    summary: assessment?.summary ?? '',
    scenarioContext: assessment?.scenarioContext ?? '',
    systems,
    recommendedActionsText: assessment?.recommendedActions
      ? assessment.recommendedActions.join('\n')
      : '',
    inspectorName: assessment?.inspectorName ?? '',
    recordedAtLocal,
    attachmentsText,
  }
}

// ============================================================================
// Checklist Summary Computation
// ============================================================================

/**
 * Compute a summary of checklist progress from items
 * Used when backend summary is unavailable
 */
export function computeChecklistSummary(
  items: ChecklistItem[],
  propertyId: string,
): ChecklistSummary {
  const totals = {
    total: items.length,
    completed: 0,
    inProgress: 0,
    pending: 0,
    notApplicable: 0,
  }

  const byCategoryStatus: Record<
    string,
    {
      total: number
      completed: number
      inProgress: number
      pending: number
      notApplicable: number
    }
  > = {}

  items.forEach((item) => {
    switch (item.status) {
      case 'completed':
        totals.completed += 1
        break
      case 'in_progress':
        totals.inProgress += 1
        break
      case 'not_applicable':
        totals.notApplicable += 1
        break
      default:
        totals.pending += 1
        break
    }

    const categoryEntry = byCategoryStatus[item.category] ?? {
      total: 0,
      completed: 0,
      inProgress: 0,
      pending: 0,
      notApplicable: 0,
    }

    categoryEntry.total += 1
    if (item.status === 'completed') {
      categoryEntry.completed += 1
    } else if (item.status === 'in_progress') {
      categoryEntry.inProgress += 1
    } else if (item.status === 'not_applicable') {
      categoryEntry.notApplicable += 1
    } else {
      categoryEntry.pending += 1
    }

    byCategoryStatus[item.category] = categoryEntry
  })

  const completionPercentage =
    totals.total > 0 ? Math.round((totals.completed / totals.total) * 100) : 0

  return {
    propertyId,
    total: totals.total,
    completed: totals.completed,
    inProgress: totals.inProgress,
    pending: totals.pending,
    notApplicable: totals.notApplicable,
    completionPercentage,
    byCategoryStatus,
  }
}
