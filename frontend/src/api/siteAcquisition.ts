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

export interface ConditionInsight {
  id: string
  severity: 'critical' | 'warning' | 'positive' | 'info'
  title: string
  detail: string
  specialist?: string | null
}

export interface ConditionAttachment {
  label: string
  url?: string | null
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
  inspectorName?: string | null
  recordedBy?: string | null
  recordedAt?: string | null
  attachments: ConditionAttachment[]
  insights: ConditionInsight[]
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
  inspectorName?: string | null
  recordedAt?: string | null
  attachments: ConditionAttachment[]
}

export type ChecklistTemplate = AgentsChecklistTemplate
export type ChecklistTemplateDraft = AgentsChecklistTemplateDraft
export type ChecklistTemplateUpdate = AgentsChecklistTemplateUpdate
export type ChecklistTemplateImportResult =
  AgentsChecklistTemplateImportResult

function mapConditionAssessmentPayload(
  payload: Record<string, unknown>,
  fallbackPropertyId: string,
): ConditionAssessment {
  const propertyId = String(payload.property_id ?? fallbackPropertyId)
  const systems = Array.isArray(payload.systems)
    ? payload.systems.map((system: Record<string, unknown>) => ({
        name: String(system.name ?? ''),
        rating: String(system.rating ?? ''),
        score: Number(system.score ?? 0),
        notes: String(system.notes ?? ''),
        recommendedActions: Array.isArray(system.recommended_actions)
          ? (system.recommended_actions as string[])
          : [],
      }))
    : []

  const insights = Array.isArray(payload.insights)
    ? payload.insights
        .map((entry: Record<string, unknown>, index: number): ConditionInsight => {
          const rawSeverity = String(entry.severity ?? 'warning').toLowerCase()
          const severity: ConditionInsight['severity'] = (
            ['critical', 'warning', 'positive', 'info'].includes(rawSeverity)
              ? rawSeverity
              : 'warning'
          ) as ConditionInsight['severity']
          const specialistValue =
            typeof entry.specialist === 'string' && entry.specialist.trim() !== ''
              ? entry.specialist
              : null
          return {
            id: String(entry.id ?? `insight-${index}`),
            severity,
            title: String(entry.title ?? 'Condition insight'),
            detail: String(entry.detail ?? ''),
            specialist: specialistValue,
          }
        })
        .filter((insight) => insight.detail !== '')
    : []

  const attachments = Array.isArray(payload.attachments)
    ? payload.attachments
        .map((entry: Record<string, unknown>) => {
          const label = String(entry.label ?? '').trim()
          const urlValue =
            typeof entry.url === 'string' && entry.url.trim().length > 0
              ? entry.url.trim()
              : null
          if (!label && !urlValue) {
            return null
          }
          return {
            label: label || (urlValue ?? ''),
            url: urlValue,
          }
        })
        .filter((item): item is ConditionAttachment => item !== null)
    : []

  return {
    propertyId,
    scenario:
      typeof payload.scenario === 'string'
        ? (payload.scenario as DevelopmentScenario)
        : typeof payload.scenario === 'undefined' && typeof payload['scenario'] === 'string'
        ? (payload['scenario'] as DevelopmentScenario)
        : (payload.scenario as DevelopmentScenario | null | undefined) ?? null,
    overallScore: Number(payload.overall_score ?? payload.overallScore ?? 0),
    overallRating: String(payload.overall_rating ?? payload.overallRating ?? 'C'),
    riskLevel: String(payload.risk_level ?? payload.riskLevel ?? 'moderate'),
    summary: String(payload.summary ?? ''),
    scenarioContext:
      typeof payload.scenario_context === 'string'
        ? payload.scenario_context
        : typeof payload.scenarioContext === 'string'
        ? payload.scenarioContext
        : null,
    systems,
    recommendedActions: Array.isArray(payload.recommended_actions)
      ? (payload.recommended_actions as string[])
      : Array.isArray(payload.recommendedActions)
      ? (payload.recommendedActions as string[])
      : [],
    inspectorName:
      typeof payload.inspector_name === 'string'
        ? payload.inspector_name
        : typeof payload.inspectorName === 'string'
        ? payload.inspectorName
        : null,
    recordedBy:
      typeof payload.recorded_by === 'string'
        ? payload.recorded_by
        : typeof payload.recordedBy === 'string'
        ? payload.recordedBy
        : null,
    recordedAt:
      typeof payload.recorded_at === 'string'
        ? payload.recorded_at
        : typeof payload.recordedAt === 'string'
        ? payload.recordedAt
        : null,
    attachments,
    insights,
  }
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
  return mapConditionAssessmentPayload(payload, propertyId)
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
  return mapConditionAssessmentPayload(data, propertyId)
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

  return data.map((entry: Record<string, unknown>) =>
    mapConditionAssessmentPayload(entry, propertyId),
  )
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

  return data.map((entry: Record<string, unknown>) =>
    mapConditionAssessmentPayload(entry, propertyId),
  )
}

export interface ConditionReportChecklistSummary {
  total: number
  completed: number
  inProgress: number
  pending: number
  notApplicable: number
  completionPercentage: number
}

export interface ConditionReportScenarioComparisonEntry {
  scenario?: string | null
  label: string
  recordedAt?: string | null
  overallScore?: number | null
  overallRating?: string | null
  riskLevel?: string | null
  checklistCompleted?: number | null
  checklistTotal?: number | null
  checklistPercent?: number | null
  primaryInsight?: ConditionInsight | null
  insightCount: number
  recommendedAction?: string | null
  inspectorName?: string | null
  source: 'manual' | 'heuristic'
}

export interface ConditionReport {
  propertyId: string
  propertyName?: string | null
  address?: string | null
  generatedAt: string
  scenarioAssessments: ConditionAssessment[]
  history: ConditionAssessment[]
  checklistSummary?: ConditionReportChecklistSummary | null
  scenarioComparison: ConditionReportScenarioComparisonEntry[]
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

  const raw = await response.json()
  const normalized: ConditionReport = {
    propertyId: String(raw.propertyId ?? raw.property_id ?? propertyId),
    propertyName: raw.propertyName ?? raw.property_name ?? null,
    address: raw.address ?? null,
    generatedAt: String(raw.generatedAt ?? raw.generated_at ?? new Date().toISOString()),
    scenarioAssessments: Array.isArray(raw.scenarioAssessments)
      ? raw.scenarioAssessments.map((entry: Record<string, unknown>) =>
          mapConditionAssessmentPayload(entry, propertyId),
        )
      : [],
    history: Array.isArray(raw.history)
      ? raw.history.map((entry: Record<string, unknown>) =>
          mapConditionAssessmentPayload(entry, propertyId),
        )
      : [],
    checklistSummary: raw.checklistSummary ?? raw.checklist_summary ?? null,
    scenarioComparison: Array.isArray(raw.scenarioComparison)
      ? raw.scenarioComparison.map((entry: Record<string, unknown>) => ({
          scenario: typeof entry.scenario === 'string' ? entry.scenario : null,
          label: String(entry.label ?? (entry.scenario ?? 'Scenario')),
          recordedAt:
            typeof entry.recordedAt === 'string'
              ? entry.recordedAt
              : typeof entry.recorded_at === 'string'
              ? entry.recorded_at
              : null,
          overallScore:
            typeof entry.overallScore === 'number'
              ? entry.overallScore
              : typeof entry.overall_score === 'number'
              ? entry.overall_score
              : null,
          overallRating:
            typeof entry.overallRating === 'string'
              ? entry.overallRating
              : typeof entry.overall_rating === 'string'
              ? entry.overall_rating
              : null,
          riskLevel:
            typeof entry.riskLevel === 'string'
              ? entry.riskLevel
              : typeof entry.risk_level === 'string'
              ? entry.risk_level
              : null,
          checklistCompleted:
            typeof entry.checklistCompleted === 'number'
              ? entry.checklistCompleted
              : typeof entry.checklist_completed === 'number'
              ? entry.checklist_completed
              : null,
          checklistTotal:
            typeof entry.checklistTotal === 'number'
              ? entry.checklistTotal
              : typeof entry.checklist_total === 'number'
              ? entry.checklist_total
              : null,
          checklistPercent:
            typeof entry.checklistPercent === 'number'
              ? entry.checklistPercent
              : typeof entry.checklist_percent === 'number'
              ? entry.checklist_percent
              : null,
          primaryInsight:
            entry.primaryInsight
              ? mapConditionAssessmentPayload(
                  { insights: [entry.primaryInsight] },
                  propertyId,
                ).insights[0] ?? null
              : null,
          insightCount: Number(entry.insightCount ?? entry.insight_count ?? 0),
          recommendedAction:
            typeof entry.recommendedAction === 'string'
              ? entry.recommendedAction
              : typeof entry.recommended_action === 'string'
              ? entry.recommended_action
              : null,
          inspectorName:
            typeof entry.inspectorName === 'string'
              ? entry.inspectorName
              : typeof entry.inspector_name === 'string'
              ? entry.inspector_name
              : null,
          source:
            entry.source === 'manual' || entry.source === 'heuristic'
              ? (entry.source as 'manual' | 'heuristic')
              : 'heuristic',
        }))
      : [],
  }

  const blob = new Blob([JSON.stringify(normalized, null, 2)], {
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
