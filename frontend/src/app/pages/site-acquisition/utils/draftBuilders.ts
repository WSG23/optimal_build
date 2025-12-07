/**
 * Draft builders for assessment forms and offline checklist data
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
import {
  DEFAULT_CONDITION_SYSTEMS,
  OFFLINE_CHECKLIST_TEMPLATES,
} from '../constants'
import { DEFAULT_SCENARIO_ORDER } from '../../../../api/siteAcquisition'
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
// Offline Checklist Builder
// ============================================================================

/**
 * Build checklist items from offline templates for given scenarios
 * Used when backend is unavailable or for demo/testing
 */
export function buildOfflineChecklistItems(
  propertyId: string,
  scenarios: DevelopmentScenario[] | null,
): ChecklistItem[] {
  const scenarioSet = new Set<DevelopmentScenario>(scenarios ?? [])
  if (scenarioSet.size === 0) {
    DEFAULT_SCENARIO_ORDER.forEach((scenario) => scenarioSet.add(scenario))
  }

  const scenarioRank = new Map(
    DEFAULT_SCENARIO_ORDER.map((scenario, index) => [scenario, index]),
  )

  const selectedTemplates = OFFLINE_CHECKLIST_TEMPLATES.filter((template) =>
    scenarioSet.has(template.developmentScenario),
  )

  selectedTemplates.sort((a, b) => {
    const scenarioDiff =
      (scenarioRank.get(a.developmentScenario) ?? Number.MAX_SAFE_INTEGER) -
      (scenarioRank.get(b.developmentScenario) ?? Number.MAX_SAFE_INTEGER)
    if (scenarioDiff !== 0) {
      return scenarioDiff
    }
    const aOrder = a.displayOrder ?? 0
    const bOrder = b.displayOrder ?? 0
    return aOrder - bOrder
  })

  return selectedTemplates.map((template, index) => ({
    id: `${template.developmentScenario}-${index}-${propertyId}`,
    propertyId,
    developmentScenario: template.developmentScenario,
    category: template.category,
    itemTitle: template.itemTitle,
    itemDescription: template.itemDescription,
    status: 'pending' as const,
    priority: template.priority,
    assignedTo: null,
    dueDate: null,
    completedAt: null,
    notes: null,
    requiresProfessional: template.requiresProfessional,
    professionalType: template.professionalType ?? null,
    typicalDurationDays: template.typicalDurationDays ?? null,
    displayOrder: template.displayOrder,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }))
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
