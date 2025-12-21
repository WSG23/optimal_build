import { useMemo } from 'react'

import { ensureIdentityHeaders } from './identity'

export interface DetectedFloorSummary {
  name: string
  unitIds: string[]
}

export interface CadImportSummary {
  importId: string
  fileName: string
  contentType: string | null
  sizeBytes: number
  uploadedAt: string
  parseStatus: ParseJobStatus
  detectedFloors: DetectedFloorSummary[]
  detectedUnits: string[]
  vectorSummary: Record<string, unknown> | null
  zoneCode: string | null
  overrides: Record<string, number> | null
}

export type ParseJobStatus =
  | 'pending'
  | 'queued'
  | 'running'
  | 'completed'
  | 'failed'

export interface ParseStatusUpdate {
  importId: string
  status: ParseJobStatus
  requestedAt: string | null
  completedAt: string | null
  jobId: string | null
  detectedFloors: DetectedFloorSummary[]
  detectedUnits: string[]
  metadata: Record<string, unknown> | null
  error?: string | null
}

export interface OverlayDecisionRecord {
  id: number
  decision: string
  decidedBy: string | null
  decidedAt: string
  notes: string | null
}

export interface OverlaySuggestion {
  id: number
  projectId: number
  sourceGeometryId: number
  code: string
  title: string
  rationale: string | null
  severity: string | null
  status: string
  engineVersion: string | null
  enginePayload: Record<string, unknown>
  score: number | null
  geometryChecksum: string
  createdAt: string
  updatedAt: string
  decidedAt: string | null
  decidedBy: string | null
  decisionNotes: string | null
  decision: OverlayDecisionRecord | null
}

export interface AuditEvent {
  id: number
  projectId: number
  eventType: string
  recordedAt: string
  baselineSeconds: number | null
  actualSeconds: number | null
  context: Record<string, unknown>
}

export interface RuleMatch {
  text: string
  score: number
  hints: string[]
}

export interface RuleSummary {
  id: number
  parameterKey: string
  operator: string
  value: string
  unit?: string | null
  authority?: string | null
  topic?: string | null
  reviewStatus?: string | null
  overlays: string[]
  advisoryHints: string[]
  normalized: RuleMatch[]
}

export interface PipelineSuggestion {
  id: string
  title: string
  description: string
  focus: string
  automationScore: number
  reviewHoursSaved: number
  estimatedSavingsPercent: number
  relatedRuleIds: number[]
}

export interface ExportLayerMapConfig {
  source?: Record<string, string>
  overlays?: Record<string, string>
  styles?: Record<string, Record<string, unknown>>
  defaultSourceLayer?: string
  defaultOverlayLayer?: string
}

export interface ExportRequestOptions {
  format: 'dxf' | 'dwg' | 'ifc' | 'pdf'
  includeSource?: boolean
  includeApprovedOverlays?: boolean
  includePendingOverlays?: boolean
  includeRejectedOverlays?: boolean
  layerMap?: ExportLayerMapConfig
  pendingWatermark?: string
}

export interface ExportArtifactResponse {
  blob: Blob
  filename: string | null
  renderer: string | null
  fallback: boolean
  watermark: string | null
}

export interface ProjectRoiMetrics {
  projectId: number
  iterations: number
  totalSuggestions: number
  decidedSuggestions: number
  acceptedSuggestions: number
  acceptanceRate: number
  reviewHoursSaved: number
  automationScore: number
  savingsPercent: number
  paybackWeeks: number
  baselineHours: number
  actualHours: number
}

interface ImportResultResponse {
  import_id: string
  filename: string
  content_type: string | null
  size_bytes: number
  storage_path: string
  vector_storage_path: string | null
  uploaded_at: string
  layer_metadata: unknown[]
  detected_floors: { name: string; unit_ids: string[] }[] | null
  detected_units: string[] | null
  vector_summary: Record<string, unknown> | null
  parse_status: ParseJobStatus
  zone_code?: string | null
  metric_overrides?: Record<string, number> | null
}

interface ParseStatusResponse {
  import_id: string
  status: ParseJobStatus
  requested_at: string | null
  completed_at: string | null
  result?: {
    detected_floors?: { name: string; unit_ids: string[] }[]
    detected_units?: string[]
    metadata?: Record<string, unknown>
    [key: string]: unknown
  } | null
  error?: string | null
  job_id?: string | null
}

interface OverlaySuggestionResponse {
  id: number
  project_id: number
  source_geometry_id: number
  code: string
  title: string
  rationale: string | null
  severity: string | null
  status: string
  engine_version: string | null
  engine_payload: Record<string, unknown> | null
  score: number | null
  geometry_checksum: string
  created_at: string
  updated_at: string
  decided_at: string | null
  decided_by: string | null
  decision_notes: string | null
  decision: {
    id: number
    decision: string
    decided_by: string | null
    decided_at: string
    notes: string | null
  } | null
}

interface OverlayListingResponse {
  items: OverlaySuggestionResponse[]
  count: number
}

interface OverlayDecisionResponse {
  item: OverlaySuggestionResponse
}

interface OverlayRunResponse {
  status: string
  project_id: number
  job_id?: string | null
  created?: number
  updated?: number
  evaluated?: number
}

interface RulesResponse {
  items: RuleSummary[]
}

interface AuditLogResponse {
  id: number
  project_id: number
  event_type: string
  baseline_seconds: number | null
  actual_seconds: number | null
  context: Record<string, unknown> | null
  recorded_at: string
}

interface AuditResponse {
  items: AuditLogResponse[]
  count: number
}

interface RoiResponse {
  project_id: number
  iterations: number
  total_suggestions: number
  decided_suggestions: number
  accepted_suggestions: number
  acceptance_rate: number
  review_hours_saved: number
  automation_score: number
  savings_percent: number
  payback_weeks: number
  baseline_hours: number
  actual_hours: number
}

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

export class ApiClient {
  private readonly baseUrl: string

  constructor(baseUrl: string = '/') {
    const envBaseUrl = import.meta.env.VITE_API_BASE_URL
    const fallbackBase = import.meta.env.VITE_API_BASE
    const candidates = [
      baseUrl,
      envBaseUrl,
      fallbackBase,
      typeof window !== 'undefined' ? window.location.origin : undefined,
      'http://localhost:9400',
    ] as Array<string | undefined>

    this.baseUrl =
      candidates.find((value) => {
        if (typeof value !== 'string') {
          return false
        }
        const trimmed = value.trim()
        return trimmed.length > 0 && trimmed !== '/'
      }) ?? 'http://localhost:9400'
  }

  private buildUrl(path: string) {
    if (/^https?:/i.test(path)) {
      return path
    }
    const trimmed = path.startsWith('/') ? path.slice(1) : path
    const root =
      this.baseUrl ||
      (typeof window !== 'undefined'
        ? window.location.origin
        : 'http://localhost:9400')
    try {
      return new URL(trimmed, root.endsWith('/') ? root : `${root}/`).toString()
    } catch (error) {
      if (typeof window !== 'undefined') {
        return new URL(trimmed, `${window.location.origin}/`).toString()
      }
      throw error
    }
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const headers = new Headers(init?.headers)
    ensureIdentityHeaders(headers)

    const requestInit: RequestInit = {
      ...init,
      headers,
    }

    const response = await fetch(this.buildUrl(path), requestInit)
    if (!response.ok) {
      const message = await response.text()
      throw new Error(
        message || `Request to ${path} failed with ${String(response.status)}`,
      )
    }
    if (response.status === 204) {
      return undefined as T
    }
    const text = await response.text()
    if (!text || text.trim() === '') {
      return undefined as T
    }
    try {
      return JSON.parse(text) as T
    } catch {
      throw new Error(
        `Invalid JSON response from ${path}: ${text.slice(0, 100)}`,
      )
    }
  }

  public async get<T>(
    path: string,
    config?: RequestInit & { params?: Record<string, string> },
  ): Promise<{ data: T }> {
    let finalUrl = this.buildUrl(path)
    if (config?.params) {
      const searchParams = new URLSearchParams(config.params)
      const separator = finalUrl.includes('?') ? '&' : '?'
      finalUrl = `${finalUrl}${separator}${searchParams.toString()}`
    }
    const data = await this.request<T>(finalUrl, {
      method: 'GET',
      headers: config?.headers,
    })
    return { data }
  }

  public async post<T>(
    path: string,
    body?: unknown,
    config?: RequestInit & { params?: Record<string, string> },
  ): Promise<{ data: T }> {
    let finalUrl = this.buildUrl(path)
    if (config?.params) {
      const searchParams = new URLSearchParams(config.params)
      const separator = finalUrl.includes('?') ? '&' : '?'
      finalUrl = `${finalUrl}${separator}${searchParams.toString()}`
    }
    const headers: HeadersInit = { 'Content-Type': 'application/json' }
    if (config?.headers) {
      Object.assign(headers, config.headers)
    }
    const data = await this.request<T>(finalUrl, {
      method: 'POST',
      body: JSON.stringify(body),
      headers,
    })
    return { data }
  }

  public async delete<T>(
    path: string,
    config?: RequestInit & { params?: Record<string, string> },
  ): Promise<{ data: T }> {
    let finalUrl = this.buildUrl(path)
    if (config?.params) {
      const searchParams = new URLSearchParams(config.params)
      const separator = finalUrl.includes('?') ? '&' : '?'
      finalUrl = `${finalUrl}${separator}${searchParams.toString()}`
    }
    const data = await this.request<T>(finalUrl, {
      method: 'DELETE',
      headers: config?.headers,
    })
    return { data }
  }

  private mapImportResult(payload: ImportResultResponse): CadImportSummary {
    const detectedFloorsSource = Array.isArray(payload.detected_floors)
      ? payload.detected_floors
      : []
    const detectedUnitsSource = Array.isArray(payload.detected_units)
      ? payload.detected_units
      : []

    return {
      importId: payload.import_id,
      fileName: payload.filename,
      contentType: payload.content_type,
      sizeBytes: payload.size_bytes,
      uploadedAt: payload.uploaded_at,
      parseStatus: payload.parse_status,
      detectedFloors: detectedFloorsSource.map((floor) => ({
        name: floor.name,
        unitIds: Array.isArray(floor.unit_ids) ? floor.unit_ids : [],
      })),
      detectedUnits: [...detectedUnitsSource],
      vectorSummary: payload.vector_summary ?? null,
      zoneCode: payload.zone_code ?? null,
      overrides:
        payload.metric_overrides && typeof payload.metric_overrides === 'object'
          ? Object.fromEntries(
              Object.entries(payload.metric_overrides).flatMap(
                ([key, value]) =>
                  typeof value === 'number' ? [[key, value]] : [],
              ),
            )
          : null,
    }
  }

  private mapParseStatus(payload: ParseStatusResponse): ParseStatusUpdate {
    const result =
      payload.result && typeof payload.result === 'object'
        ? payload.result
        : null
    const detectedFloorsSource = Array.isArray(result?.detected_floors)
      ? result.detected_floors
      : []
    const detectedUnitsSource = Array.isArray(result?.detected_units)
      ? result.detected_units
      : []
    const metadataValue = result?.metadata ?? null

    return {
      importId: payload.import_id,
      status: payload.status,
      requestedAt: payload.requested_at,
      completedAt: payload.completed_at,
      jobId: payload.job_id ?? null,
      detectedFloors: detectedFloorsSource.map((floor) => ({
        name: floor.name,
        unitIds: Array.isArray(floor.unit_ids) ? floor.unit_ids : [],
      })),
      detectedUnits: [...detectedUnitsSource],
      metadata: metadataValue,
      error: payload.error ?? null,
    }
  }

  private mapOverlaySuggestion(
    payload: OverlaySuggestionResponse,
  ): OverlaySuggestion {
    return {
      id: payload.id,
      projectId: payload.project_id,
      sourceGeometryId: payload.source_geometry_id,
      code: payload.code,
      title: payload.title,
      rationale: payload.rationale,
      severity: payload.severity,
      status: payload.status,
      engineVersion: payload.engine_version,
      enginePayload: payload.engine_payload ?? {},
      score: payload.score,
      geometryChecksum: payload.geometry_checksum,
      createdAt: payload.created_at,
      updatedAt: payload.updated_at,
      decidedAt: payload.decided_at,
      decidedBy: payload.decided_by,
      decisionNotes: payload.decision_notes,
      decision: payload.decision
        ? {
            id: payload.decision.id,
            decision: payload.decision.decision,
            decidedBy: payload.decision.decided_by,
            decidedAt: payload.decision.decided_at,
            notes: payload.decision.notes,
          }
        : null,
    }
  }

  async uploadCadDrawing(
    file: File | Blob,
    options: {
      inferWalls?: boolean
      projectId?: number
      zoneCode?: string
    } = {},
  ): Promise<CadImportSummary> {
    const formData = new FormData()
    const derivedName =
      typeof File !== 'undefined' &&
      file instanceof File &&
      typeof file.name === 'string'
        ? file.name
        : 'upload.dxf'
    formData.append('file', file, derivedName)
    if (options.inferWalls) {
      formData.append('infer_walls', 'true')
    }
    if (
      typeof options.projectId === 'number' &&
      !Number.isNaN(options.projectId)
    ) {
      formData.append('project_id', options.projectId.toString())
    }
    if (typeof options.zoneCode === 'string' && options.zoneCode.trim()) {
      formData.append('zone_code', options.zoneCode.trim())
    }

    const headers = new Headers()
    ensureIdentityHeaders(headers)

    const payload = await this.request<ImportResultResponse>('api/v1/import', {
      method: 'POST',
      body: formData,
      headers,
    })
    return this.mapImportResult(payload)
  }

  async triggerParse(importId: string): Promise<ParseStatusUpdate> {
    const payload = await this.request<ParseStatusResponse>(
      `api/v1/parse/${importId}`,
      {
        method: 'POST',
      },
    )
    return this.mapParseStatus(payload)
  }

  async fetchParseStatus(importId: string): Promise<ParseStatusUpdate> {
    const payload = await this.request<ParseStatusResponse>(
      `api/v1/parse/${importId}`,
    )
    return this.mapParseStatus(payload)
  }

  pollParseStatus(options: {
    importId: string
    onUpdate: (update: ParseStatusUpdate) => void
    intervalMs?: number
    timeoutMs?: number
  }) {
    const { importId, onUpdate, intervalMs = 2000, timeoutMs = 60000 } = options
    let cancelled = false
    const startedAt = Date.now()

    const loop = async () => {
      while (!cancelled) {
        try {
          const update = await this.fetchParseStatus(importId)
          onUpdate(update)
          if (update.status === 'completed' || update.status === 'failed') {
            break
          }
        } catch (error) {
          const message =
            error instanceof Error ? error.message : 'Unknown error'
          onUpdate({
            importId,
            status: 'failed',
            requestedAt: null,
            completedAt: null,
            jobId: null,
            detectedFloors: [],
            detectedUnits: [],
            metadata: null,
            error: message,
          })
          break
        }

        if (timeoutMs && Date.now() - startedAt >= timeoutMs) {
          onUpdate({
            importId,
            status: 'failed',
            requestedAt: null,
            completedAt: null,
            jobId: null,
            detectedFloors: [],
            detectedUnits: [],
            metadata: null,
            error: 'Polling timed out',
          })
          break
        }

        await delay(intervalMs)
      }
    }

    loop().catch((error: unknown) => {
      const message = error instanceof Error ? error.message : 'Unknown error'
      onUpdate({
        importId,
        status: 'failed',
        requestedAt: null,
        completedAt: null,
        jobId: null,
        detectedFloors: [],
        detectedUnits: [],
        metadata: null,
        error: message,
      })
    })

    return () => {
      cancelled = true
    }
  }

  async listOverlaySuggestions(
    projectId: number,
  ): Promise<OverlaySuggestion[]> {
    const payload = await this.request<OverlayListingResponse>(
      `api/v1/overlay/${String(projectId)}`,
    )
    return payload.items.map((item) => this.mapOverlaySuggestion(item))
  }

  async runOverlay(projectId: number): Promise<{
    status: string
    projectId: number
    jobId: string | null
    created?: number
    updated?: number
    evaluated?: number
  }> {
    const payload = await this.request<OverlayRunResponse>(
      `api/v1/overlay/${String(projectId)}/run`,
      {
        method: 'POST',
      },
    )
    return {
      status: payload.status,
      projectId: payload.project_id,
      jobId: payload.job_id ?? null,
      created: payload.created,
      updated: payload.updated,
      evaluated: payload.evaluated,
    }
  }

  async getLatestImport(projectId: number): Promise<CadImportSummary | null> {
    try {
      const payload = await this.request<ImportResultResponse>(
        `api/v1/import/latest?project_id=${String(projectId)}`,
      )
      return this.mapImportResult(payload)
    } catch (error) {
      if (error instanceof Error && /404/.test(error.message)) {
        return null
      }
      throw error
    }
  }

  async updateImportOverrides(
    importId: string,
    overrides: Record<string, number>,
  ): Promise<CadImportSummary> {
    const payload = await this.request<ImportResultResponse>(
      `api/v1/import/${importId}/overrides`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(overrides),
      },
    )
    return this.mapImportResult(payload)
  }

  async decideOverlay(
    projectId: number,
    input: {
      suggestionId: number
      decision: 'approved' | 'rejected'
      decidedBy?: string
      notes?: string
    },
  ): Promise<OverlaySuggestion> {
    const payload = await this.request<OverlayDecisionResponse>(
      `api/v1/overlay/${String(projectId)}/decision`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          suggestion_id: input.suggestionId,
          decision: input.decision,
          decided_by: input.decidedBy,
          notes: input.notes,
        }),
      },
    )
    return this.mapOverlaySuggestion(payload.item)
  }

  async listAuditTrail(
    projectId: number,
    options: { eventType?: string } = {},
  ): Promise<AuditEvent[]> {
    const searchParams = new URLSearchParams()
    if (options.eventType) {
      searchParams.set('event_type', options.eventType)
    }
    const path = searchParams.size
      ? `api/v1/audit/${String(projectId)}?${searchParams.toString()}`
      : `api/v1/audit/${String(projectId)}`
    const payload = await this.request<AuditResponse>(path)
    return payload.items.map((item) => ({
      id: item.id,
      projectId: item.project_id,
      eventType: item.event_type,
      recordedAt: item.recorded_at,
      baselineSeconds: item.baseline_seconds,
      actualSeconds: item.actual_seconds,
      context: item.context ?? {},
    }))
  }

  async listRules(): Promise<RuleSummary[]> {
    const data = await this.request<RulesResponse>('api/v1/rules')
    return data.items.map((item) => ({
      ...item,
      overlays: Array.isArray(item.overlays) ? item.overlays : [],
      advisoryHints: Array.isArray(item.advisoryHints)
        ? item.advisoryHints
        : [],
    }))
  }

  async getProjectRoi(projectId: number): Promise<ProjectRoiMetrics> {
    const payload = await this.request<RoiResponse>(
      `api/v1/roi/${String(projectId)}`,
    )
    return {
      projectId: payload.project_id,
      iterations: payload.iterations,
      totalSuggestions: payload.total_suggestions,
      decidedSuggestions: payload.decided_suggestions,
      acceptedSuggestions: payload.accepted_suggestions,
      acceptanceRate: payload.acceptance_rate,
      reviewHoursSaved: payload.review_hours_saved,
      automationScore: payload.automation_score,
      savingsPercent: payload.savings_percent,
      paybackWeeks: payload.payback_weeks,
      baselineHours: payload.baseline_hours,
      actualHours: payload.actual_hours,
    }
  }

  async exportProject(
    projectId: number,
    options: ExportRequestOptions,
  ): Promise<ExportArtifactResponse> {
    const body: Record<string, unknown> = {
      format: options.format,
      include_source: options.includeSource ?? true,
      include_approved_overlays: options.includeApprovedOverlays ?? true,
      include_pending_overlays: options.includePendingOverlays ?? false,
      include_rejected_overlays: options.includeRejectedOverlays ?? false,
    }

    if (options.pendingWatermark !== undefined) {
      body.pending_watermark = options.pendingWatermark
    }

    if (options.layerMap) {
      body.layer_map = {
        source: options.layerMap.source ?? {},
        overlays: options.layerMap.overlays ?? {},
        styles: options.layerMap.styles ?? {},
        default_source_layer: options.layerMap.defaultSourceLayer,
        default_overlay_layer: options.layerMap.defaultOverlayLayer,
      }
    }

    const headers = new Headers({ 'Content-Type': 'application/json' })
    ensureIdentityHeaders(headers)

    const response = await fetch(
      this.buildUrl(`api/v1/export/${String(projectId)}`),
      {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      },
    )

    if (!response.ok) {
      const message = await response.text()
      throw new Error(
        message ||
          `Export request failed with status ${String(response.status)}`,
      )
    }

    const blob = await response.blob()
    const disposition = response.headers.get('Content-Disposition')
    let filename: string | null = null
    if (disposition) {
      const match = disposition.match(/filename="?([^";]+)"?/i)
      if (match) {
        filename = match[1]
      }
    }

    return {
      blob,
      filename,
      renderer: response.headers.get('X-Export-Renderer'),
      fallback: response.headers.get('X-Export-Fallback') === '1',
      watermark: response.headers.get('X-Export-Watermark'),
    }
  }

  async getDefaultPipelineSuggestions(
    context: { overlays?: string[]; hints?: string[] } = {},
  ): Promise<PipelineSuggestion[]> {
    const rules = await this.listRules()
    const overlays = new Set(context.overlays ?? [])
    const hints = new Set(context.hints ?? [])
    const byTopic = new Map<string, RuleSummary[]>()

    rules.forEach((rule) => {
      if (rule.topic) {
        byTopic.set(rule.topic, [...(byTopic.get(rule.topic) ?? []), rule])
      }
    })

    const suggestions: PipelineSuggestion[] = []

    byTopic.forEach((topicRules, topic) => {
      const related = topicRules.filter((rule) => {
        const ruleOverlays = Array.isArray(rule.overlays) ? rule.overlays : []
        const ruleHints = Array.isArray(rule.advisoryHints)
          ? rule.advisoryHints
          : []
        return (
          ruleOverlays.some((overlay) => overlays.has(overlay)) ||
          ruleHints.some((hint) => hints.has(hint))
        )
      })
      const automationScore =
        related.length > 0
          ? Math.min(0.95, 0.5 + related.length / (topicRules.length * 1.5))
          : 0.45
      const savings = Math.round(automationScore * 100 * 0.3)
      const reviewHours = Math.max(
        2,
        Math.round(topicRules.length * automationScore),
      )

      suggestions.push({
        id: `pipeline-${topic.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-${suggestions.length}`,
        title: `${topic} fast-track`,
        description:
          related.length > 0
            ? `Prioritise ${String(related.length)} overlays-triggered checks within the ${topic} rules.`
            : `Establish defaults for ${topic} checks before overlays arrive.`,
        focus: topic,
        automationScore,
        reviewHoursSaved: reviewHours,
        estimatedSavingsPercent: savings,
        relatedRuleIds: topicRules.map((rule) => rule.id),
      })
    })

    if (suggestions.length === 0) {
      return [
        {
          id: 'pipeline-default',
          title: 'Core compliance pipeline',
          description:
            'Baseline review workflow across zoning, fire safety and environmental health topics.',
          focus: 'baseline',
          automationScore: 0.5,
          reviewHoursSaved: 6,
          estimatedSavingsPercent: 18,
          relatedRuleIds: rules.slice(0, 6).map((rule) => rule.id),
        },
      ]
    }

    return suggestions.sort((a, b) => b.automationScore - a.automationScore)
  }
}

export function useApiClient() {
  return useMemo(() => new ApiClient(), [])
}
