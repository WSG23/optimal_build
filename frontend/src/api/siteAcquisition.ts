/**
 * Site Acquisition API client for developers
 * Wraps GPS logging and feasibility APIs with developer-specific features
 */

import {
  fetchChecklistSummary as fetchChecklistSummaryFromAgents,
  fetchPropertyChecklist as fetchPropertyChecklistFromAgents,
  logPropertyByGps,
  buildUrl,
  updateChecklistItem as updateChecklistItemFromAgents,
  fetchChecklistTemplates as fetchChecklistTemplatesFromAgents,
  createChecklistTemplate as createChecklistTemplateFromAgents,
  updateChecklistTemplate as updateChecklistTemplateFromAgents,
  deleteChecklistTemplate as deleteChecklistTemplateFromAgents,
  importChecklistTemplates as importChecklistTemplatesFromAgents,
  OFFLINE_PROPERTY_ID,
  DEFAULT_SCENARIO_ORDER,
  type ChecklistItem,
  type ChecklistStatus,
  type ChecklistSummary,
  type ChecklistTemplate as AgentsChecklistTemplate,
  type ChecklistTemplateDraft as AgentsChecklistTemplateDraft,
  type ChecklistTemplateUpdate as AgentsChecklistTemplateUpdate,
  type ChecklistTemplateImportResult as AgentsChecklistTemplateImportResult,
  type ChecklistCategory,
  type ChecklistPriority,
  type DevelopmentScenario,
  type GpsCaptureSummary,
  type UpdateChecklistRequest,
} from './agents'

export interface SiteAcquisitionRequest {
  latitude: number
  longitude: number
  developmentScenarios: DevelopmentScenario[]
}

// Future: Will extend GpsCaptureSummary with developer-specific fields
// dueDiligenceChecklist?: DueDiligenceItem[]
// conditionAssessment?: PropertyCondition
// scenarioComparison?: ScenarioComparison[]
export type SiteAcquisitionResult = GpsCaptureSummary

export interface ConditionSystem {
  name: string
  rating: string
  score: number
  notes: string
  recommendedActions: string[]
}

export interface ConditionAssessment {
  propertyId: string
  scenario?: DevelopmentScenario | null
  overallScore: number
  overallRating: string
  riskLevel: string
  summary: string
  scenarioContext?: string | null
  systems: ConditionSystem[]
  recommendedActions: string[]
  recordedAt?: string | null
}

export interface ConditionAssessmentUpsertRequest {
  scenario?: DevelopmentScenario | 'all'
  overallRating: string
  overallScore: number
  riskLevel: string
  summary: string
  scenarioContext?: string | null
  systems: ConditionSystem[]
  recommendedActions: string[]
}

export type ChecklistTemplate = AgentsChecklistTemplate
export type ChecklistTemplateDraft = AgentsChecklistTemplateDraft
export type ChecklistTemplateUpdate = AgentsChecklistTemplateUpdate
export type ChecklistTemplateImportResult =
  AgentsChecklistTemplateImportResult

/**
 * Capture a property for site acquisition with enhanced developer features
 */
export async function capturePropertyForDevelopment(
  request: SiteAcquisitionRequest,
  signal?: AbortSignal,
): Promise<SiteAcquisitionResult> {
  // For now, directly call the GPS logger
  // In the future, this will call a developer-specific endpoint
  const result = await logPropertyByGps(
    {
      latitude: request.latitude,
      longitude: request.longitude,
      developmentScenarios: request.developmentScenarios,
    },
    undefined,
    signal,
  )

  // Return the GPS capture result as-is for now
  // Future enhancements will add developer-specific data
  return result
}

/**
 * Fetch due diligence checklist for a property
 */
export async function fetchPropertyChecklist(
  propertyId: string,
  developmentScenario?: DevelopmentScenario,
  status?: ChecklistStatus,
): Promise<ChecklistItem[]> {
  return fetchPropertyChecklistFromAgents(propertyId, developmentScenario, status)
}

/**
 * Fetch checklist summary statistics
 */
export async function fetchChecklistSummary(
  propertyId: string,
): Promise<ChecklistSummary | null> {
  return fetchChecklistSummaryFromAgents(propertyId)
}

/**
 * Update a checklist item status or notes
 */
export async function updateChecklistItem(
  checklistId: string,
  updates: UpdateChecklistRequest,
): Promise<ChecklistItem | null> {
  return updateChecklistItemFromAgents(checklistId, updates)
}

/**
 * Fetch developer condition assessment for the property.
 */
export async function fetchConditionAssessment(
  propertyId: string,
  scenario?: DevelopmentScenario | 'all',
): Promise<ConditionAssessment | null> {
  const params = new URLSearchParams()
  if (scenario && scenario !== 'all') {
    params.append('scenario', scenario)
  }

  const url = buildUrl(
    `api/v1/developers/properties/${propertyId}/condition-assessment${
      params.toString() ? `?${params.toString()}` : ''
    }`,
  )
  const response = await fetch(url)
  if (!response.ok) {
    console.error('Failed to fetch condition assessment:', response.statusText)
    return null
  }

  const payload = await response.json()
  return {
    propertyId: payload.property_id ?? propertyId,
    scenario:
      typeof payload.scenario === 'string'
        ? (payload.scenario as DevelopmentScenario)
        : null,
    overallScore: Number(payload.overall_score ?? 0),
    overallRating: payload.overall_rating ?? 'C',
    riskLevel: payload.risk_level ?? 'moderate',
    summary: payload.summary ?? '',
    scenarioContext: payload.scenario_context ?? null,
    systems: Array.isArray(payload.systems)
      ? payload.systems.map((system: Record<string, unknown>) => ({
          name: String(system.name ?? ''),
          rating: String(system.rating ?? ''),
          score: Number(system.score ?? 0),
          notes: String(system.notes ?? ''),
          recommendedActions: Array.isArray(system.recommended_actions)
            ? (system.recommended_actions as string[])
            : [],
        }))
      : [],
    recommendedActions: Array.isArray(payload.recommended_actions)
      ? (payload.recommended_actions as string[])
      : [],
    recordedAt:
      typeof payload.recorded_at === 'string' ? payload.recorded_at : null,
  }
}

export async function saveConditionAssessment(
  propertyId: string,
  payload: ConditionAssessmentUpsertRequest,
): Promise<ConditionAssessment | null> {
  const response = await fetch(
    buildUrl(`api/v1/developers/properties/${propertyId}/condition-assessment`),
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
  )

  if (!response.ok) {
    console.error('Failed to save condition assessment:', response.statusText)
    return null
  }

  const data = await response.json()
  return {
    propertyId: data.property_id ?? propertyId,
    scenario:
      typeof data.scenario === 'string'
        ? (data.scenario as DevelopmentScenario)
        : null,
    overallScore: Number(data.overall_score ?? 0),
    overallRating: data.overall_rating ?? 'C',
    riskLevel: data.risk_level ?? 'moderate',
    summary: data.summary ?? '',
    scenarioContext: data.scenario_context ?? null,
    systems: Array.isArray(data.systems)
      ? data.systems.map((system: Record<string, unknown>) => ({
          name: String(system.name ?? ''),
          rating: String(system.rating ?? ''),
          score: Number(system.score ?? 0),
          notes: String(system.notes ?? ''),
          recommendedActions: Array.isArray(system.recommended_actions)
            ? (system.recommended_actions as string[])
            : [],
        }))
      : [],
    recommendedActions: Array.isArray(data.recommended_actions)
      ? (data.recommended_actions as string[])
      : [],
    recordedAt:
      typeof data.recorded_at === 'string' ? data.recorded_at : null,
  }
}

export async function fetchConditionAssessmentHistory(
  propertyId: string,
  scenario?: DevelopmentScenario | 'all',
  limit = 20,
): Promise<ConditionAssessment[]> {
  const params = new URLSearchParams()
  if (scenario && scenario !== 'all') {
    params.append('scenario', scenario)
  }
  if (limit) {
    params.append('limit', String(limit))
  }

  const url = buildUrl(
    `api/v1/developers/properties/${propertyId}/condition-assessment/history${
      params.toString() ? `?${params.toString()}` : ''
    }`,
  )
  const response = await fetch(url)
  if (!response.ok) {
    console.error('Failed to fetch condition assessment history:', response.statusText)
    return []
  }

  const data = await response.json()
  if (!Array.isArray(data)) {
    return []
  }

  return data.map((entry: Record<string, unknown>): ConditionAssessment => ({
    propertyId: entry.property_id ?? propertyId,
    scenario:
      typeof entry.scenario === 'string'
        ? (entry.scenario as DevelopmentScenario)
        : null,
    overallScore: Number(entry.overall_score ?? 0),
    overallRating: entry.overall_rating ?? 'C',
    riskLevel: entry.risk_level ?? 'moderate',
    summary: entry.summary ?? '',
    scenarioContext: entry.scenario_context ?? null,
    systems: Array.isArray(entry.systems)
      ? entry.systems.map((system: Record<string, unknown>) => ({
          name: String(system.name ?? ''),
          rating: String(system.rating ?? ''),
          score: Number(system.score ?? 0),
          notes: String(system.notes ?? ''),
          recommendedActions: Array.isArray(system.recommended_actions)
            ? (system.recommended_actions as string[])
            : [],
        }))
      : [],
    recommendedActions: Array.isArray(entry.recommended_actions)
      ? (entry.recommended_actions as string[])
      : [],
    recordedAt:
      typeof entry.recorded_at === 'string' ? entry.recorded_at : null,
  }))
}

export async function fetchScenarioAssessments(
  propertyId: string,
): Promise<ConditionAssessment[]> {
  const url = buildUrl(
    `api/v1/developers/properties/${propertyId}/condition-assessment/scenarios`,
  )

  const response = await fetch(url)
  if (!response.ok) {
    console.error('Failed to fetch scenario assessments:', response.statusText)
    return []
  }

  const data = await response.json()
  if (!Array.isArray(data)) {
    return []
  }

  return data.map((entry: Record<string, unknown>): ConditionAssessment => ({
    propertyId: entry.property_id ?? propertyId,
    scenario:
      typeof entry.scenario === 'string'
        ? (entry.scenario as DevelopmentScenario)
        : null,
    overallScore: Number(entry.overall_score ?? 0),
    overallRating: entry.overall_rating ?? 'C',
    riskLevel: entry.risk_level ?? 'moderate',
    summary: entry.summary ?? '',
    scenarioContext: entry.scenario_context ?? null,
    systems: Array.isArray(entry.systems)
      ? entry.systems.map((system: Record<string, unknown>) => ({
          name: String(system.name ?? ''),
          rating: String(system.rating ?? ''),
          score: Number(system.score ?? 0),
          notes: String(system.notes ?? ''),
          recommendedActions: Array.isArray(system.recommended_actions)
            ? (system.recommended_actions as string[])
            : [],
        }))
      : [],
    recommendedActions: Array.isArray(entry.recommended_actions)
      ? (entry.recommended_actions as string[])
      : [],
    recordedAt:
      typeof entry.recorded_at === 'string' ? entry.recorded_at : null,
  }))
}

export interface ConditionReportChecklistSummary {
  total: number
  completed: number
  inProgress: number
  pending: number
  notApplicable: number
  completionPercentage: number
}

export interface ConditionReport {
  propertyId: string
  propertyName?: string | null
  address?: string | null
  generatedAt: string
  scenarioAssessments: ConditionAssessment[]
  history: ConditionAssessment[]
  checklistSummary?: ConditionReportChecklistSummary | null
}

export async function exportConditionReport(
  propertyId: string,
  format: 'json' | 'pdf' = 'json',
): Promise<{ blob: Blob; filename: string }> {
  const url = buildUrl(
    `api/v1/developers/properties/${propertyId}/condition-assessment/report?format=${format}`,
  )
  const response = await fetch(url)
  if (!response.ok) {
    let detail = response.statusText
    try {
      const errorPayload = await response.json()
      if (typeof errorPayload.detail === 'string') {
        detail = errorPayload.detail
      }
    } catch (_err) {
      // ignore JSON parsing errors and fall back to status text
    }
    throw new Error(detail || 'Failed to export condition report.')
  }

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
  const extension = format === 'pdf' ? 'pdf' : 'json'
  const filename = `condition-report-${propertyId}-${timestamp}.${extension}`

  if (format === 'pdf') {
    const blob = await response.blob()
    return { blob, filename }
  }

  const data: ConditionReport = await response.json()
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: 'application/json',
  })
  return { blob, filename }
}

export {
  fetchChecklistTemplatesFromAgents as fetchChecklistTemplates,
  createChecklistTemplateFromAgents as createChecklistTemplate,
  updateChecklistTemplateFromAgents as updateChecklistTemplate,
  deleteChecklistTemplateFromAgents as deleteChecklistTemplate,
  importChecklistTemplatesFromAgents as importChecklistTemplates,
}

export type {
  ChecklistItem,
  ChecklistStatus,
  ChecklistSummary,
  DevelopmentScenario,
  GpsCaptureSummary,
  UpdateChecklistRequest,
  ConditionAssessment,
  ConditionSystem,
  ConditionAssessmentUpsertRequest,
  ConditionReport,
  ConditionReportChecklistSummary,
  ChecklistTemplate,
  ChecklistTemplateDraft,
  ChecklistTemplateUpdate,
  ChecklistTemplateImportResult,
  ChecklistCategory,
  ChecklistPriority,
}

export { OFFLINE_PROPERTY_ID, DEFAULT_SCENARIO_ORDER }
