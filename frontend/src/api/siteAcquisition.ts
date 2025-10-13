/**
 * Site Acquisition API client for developers
 * Wraps GPS logging and feasibility APIs with developer-specific features
 */

import {
  fetchChecklistSummary as fetchChecklistSummaryFromAgents,
  fetchPropertyChecklist as fetchPropertyChecklistFromAgents,
  logPropertyByGps,
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

export type {
  ChecklistItem,
  ChecklistStatus,
  ChecklistSummary,
  DevelopmentScenario,
  GpsCaptureSummary,
  UpdateChecklistRequest,
}
