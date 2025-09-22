import {
  FeasibilityAssessmentRequest,
  FeasibilityAssessmentResponse,
  FeasibilityRule,
  FeasibilityRulesResponse,
  NewFeasibilityProjectInput,
  RuleAssessmentResult,
} from './types'

const API_PREFIX = 'api/v1/feasibility'
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? '/'

interface RawFeasibilityRule {
  id: string
  title: string
  description: string
  authority: string
  topic: string
  parameter_key: string
  operator: string
  value: string
  unit?: string | null
  severity: FeasibilityRule['severity']
  default_selected?: boolean
}

interface RawFeasibilityRulesSummary {
  compliance_focus: string
  notes?: string | null
}

interface RawFeasibilityRulesResponse {
  project_id: string
  rules: RawFeasibilityRule[]
  recommended_rule_ids: string[]
  summary: RawFeasibilityRulesSummary
}

interface RawRuleAssessmentResult extends RawFeasibilityRule {
  status: RuleAssessmentResult['status']
  actual_value?: string | null
  notes?: string | null
}

interface RawBuildableAreaSummary {
  max_permissible_gfa_sqm: number
  estimated_achievable_gfa_sqm: number
  estimated_unit_count: number
  site_coverage_percent: number
  remarks?: string | null
}

interface RawFeasibilityAssessmentResponse {
  project_id: string
  summary: RawBuildableAreaSummary
  rules: RawRuleAssessmentResult[]
  recommendations: string[]
}

function buildUrl(path: string) {
  if (/^https?:/i.test(path)) {
    return path
  }
  const trimmed = path.startsWith('/') ? path.slice(1) : path
  const root = apiBaseUrl || '/'
  return new URL(trimmed, root.endsWith('/') ? root : `${root}/`).toString()
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body && !headers.has('content-type')) {
    headers.set('content-type', 'application/json')
  }

  const response = await fetch(buildUrl(path), { ...init, headers })
  const contentType = response.headers.get('content-type') ?? ''

  if (!response.ok) {
    if (contentType.includes('application/json')) {
      const data = (await response.json()) as { detail?: unknown; error?: unknown }
      const detail = typeof data.detail === 'string' ? data.detail : undefined
      const error = typeof data.error === 'string' ? data.error : undefined
      throw new Error(detail ?? error ?? `Request to ${path} failed with ${response.status}`)
    }

    const message = await response.text()
    throw new Error(message || `Request to ${path} failed with ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  if (contentType.includes('application/json')) {
    return (await response.json()) as T
  }

  return (await response.text()) as unknown as T
}

function mapRule(rule: RawFeasibilityRule): FeasibilityRule {
  return {
    id: rule.id,
    title: rule.title,
    description: rule.description,
    authority: rule.authority,
    topic: rule.topic,
    parameterKey: rule.parameter_key,
    operator: rule.operator,
    value: rule.value,
    unit: rule.unit ?? undefined,
    severity: rule.severity,
    defaultSelected: Boolean(rule.default_selected),
  }
}

function mapRulesResponse(payload: RawFeasibilityRulesResponse): FeasibilityRulesResponse {
  return {
    projectId: payload.project_id,
    rules: payload.rules.map(mapRule),
    recommendedRuleIds: payload.recommended_rule_ids,
    summary: {
      complianceFocus: payload.summary.compliance_focus,
      notes: payload.summary.notes ?? undefined,
    },
  }
}

function mapAssessmentRule(rule: RawRuleAssessmentResult): RuleAssessmentResult {
  const base = mapRule(rule)
  return {
    ...base,
    status: rule.status,
    actualValue: rule.actual_value ?? undefined,
    notes: rule.notes ?? undefined,
  }
}

function mapAssessmentResponse(
  payload: RawFeasibilityAssessmentResponse,
): FeasibilityAssessmentResponse {
  return {
    projectId: payload.project_id,
    summary: {
      maxPermissibleGfaSqm: payload.summary.max_permissible_gfa_sqm,
      estimatedAchievableGfaSqm: payload.summary.estimated_achievable_gfa_sqm,
      estimatedUnitCount: payload.summary.estimated_unit_count,
      siteCoveragePercent: payload.summary.site_coverage_percent,
      remarks: payload.summary.remarks ?? undefined,
    },
    rules: payload.rules.map(mapAssessmentRule),
    recommendations: [...payload.recommendations],
  }
}

export async function fetchFeasibilityRules(
  project: NewFeasibilityProjectInput,
): Promise<FeasibilityRulesResponse> {
  const payload = await request<RawFeasibilityRulesResponse>(`${API_PREFIX}/rules`, {
    method: 'POST',
    body: JSON.stringify(project),
  })

  return mapRulesResponse(payload)
}

export async function submitFeasibilityAssessment(
  assessment: FeasibilityAssessmentRequest,
): Promise<FeasibilityAssessmentResponse> {
  const payload = await request<RawFeasibilityAssessmentResponse>(`${API_PREFIX}/assessment`, {
    method: 'POST',
    body: JSON.stringify(assessment),
  })

  return mapAssessmentResponse(payload)
}
