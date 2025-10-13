/**
 * Site Acquisition API client for developers
 * Wraps GPS logging and feasibility APIs with developer-specific features
 */

import { logPropertyByGps, type DevelopmentScenario, type GpsCaptureSummary } from './agents'

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

export type { DevelopmentScenario, GpsCaptureSummary }
