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
  type ChecklistItem,
  type ChecklistStatus,
  type ChecklistSummary,
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
  overallScore: number
  overallRating: string
  riskLevel: string
  summary: string
  scenarioContext?: string | null
  systems: ConditionSystem[]
  recommendedActions: string[]
}

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
  }
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
}
