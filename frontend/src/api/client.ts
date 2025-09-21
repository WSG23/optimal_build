import { useMemo } from 'react'

export interface OverlayInsights {
  zoneCode: string | null
  overlays: string[]
  advisoryHints: string[]
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

export interface AuditEvent {
  ruleId: number
  baseline: string
  updated: string
}

export interface CadParseJob {
  jobId: string
  fileName: string
  zoneCode: string | null
  overlays: string[]
  hints: string[]
  status: 'queued' | 'processing' | 'ready' | 'error'
  message?: string
}

export interface ParseStatusUpdate {
  jobId: string
  status: 'processing' | 'ready' | 'error'
  overlays: string[]
  hints: string[]
  zoneCode: string | null
  updatedAt: string
  message?: string
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
  watermark: string | null
}

interface BuildableResponse {
  zone_code?: string | null
  overlays?: string[]
  advisory_hints?: string[]
}

interface RulesResponse {
  items: RuleSummary[]
}

interface AuditResponse {
  items: { rule_id: number; baseline: string; updated: string }[]
}

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

export class ApiClient {
  private readonly baseUrl: string

  constructor(baseUrl: string = import.meta.env.VITE_API_BASE_URL ?? '/') {
    this.baseUrl = baseUrl
  }

  private buildUrl(path: string) {
    if (/^https?:/i.test(path)) {
      return path
    }
    const trimmed = path.startsWith('/') ? path.slice(1) : path
    const root = this.baseUrl || '/'
    return new URL(trimmed, root.endsWith('/') ? root : `${root}/`).toString()
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(this.buildUrl(path), init)
    if (!response.ok) {
      const message = await response.text()
      throw new Error(message || `Request to ${path} failed with ${response.status}`)
    }
    if (response.status === 204) {
      return undefined as T
    }
    return (await response.json()) as T
  }

  async getOverlayInsights(input: { zoneCode?: string; address?: string }): Promise<OverlayInsights> {
    const payload = input.address
      ? { address: input.address }
      : {
          geometry: {
            type: 'Feature',
            properties: {
              zone_code: input.zoneCode ?? 'RA',
            },
          },
        }
    const data = await this.request<BuildableResponse>('api/v1/screen/buildable', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })
    return {
      zoneCode: data.zone_code ?? input.zoneCode ?? null,
      overlays: data.overlays ?? [],
      advisoryHints: data.advisory_hints ?? [],
    }
  }

  async listRules(): Promise<RuleSummary[]> {
    const data = await this.request<RulesResponse>('api/v1/rules')
    return data.items
  }

  async listAuditTrail(ruleId?: number): Promise<AuditEvent[]> {
    const url = ruleId ? `api/v1/review/diffs?rule_id=${ruleId}` : 'api/v1/review/diffs'
    const data = await this.request<AuditResponse>(url)
    return data.items.map((item) => ({
      ruleId: item.rule_id,
      baseline: item.baseline,
      updated: item.updated,
    }))
  }

  async uploadCadDrawing(
    file: Pick<File, 'name' | 'size'>,
    options: { zoneCode?: string; address?: string } = {},
  ): Promise<CadParseJob> {
    const insights = await this.getOverlayInsights({ zoneCode: options.zoneCode, address: options.address })
    const jobId = `cad-${Date.now().toString(36)}-${Math.random().toString(16).slice(2, 8)}`
    const hasInsights = insights.overlays.length > 0 || insights.advisoryHints.length > 0
    return {
      jobId,
      fileName: file.name,
      zoneCode: insights.zoneCode,
      overlays: insights.overlays,
      hints: insights.advisoryHints,
      status: hasInsights ? 'ready' : 'processing',
      message: hasInsights ? undefined : 'Awaiting overlay enrichment',
    }
  }

  async exportProject(projectId: number, options: ExportRequestOptions): Promise<ExportArtifactResponse> {
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

    const response = await fetch(this.buildUrl(`api/v1/export/${projectId}`), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const message = await response.text()
      throw new Error(message || `Export request failed with status ${response.status}`)
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
      watermark: response.headers.get('X-Export-Watermark'),
    }
  }

  pollParseStatus(options: {
    jobId: string
    zoneCode?: string | null
    onUpdate: (update: ParseStatusUpdate) => void
    intervalMs?: number
    timeoutMs?: number
  }) {
    const { jobId, zoneCode = null, onUpdate, intervalMs = 2000, timeoutMs = 15000 } = options
    let cancelled = false
    const startedAt = Date.now()

    const loop = async () => {
      while (!cancelled) {
        try {
          const insight = zoneCode ? await this.getOverlayInsights({ zoneCode }) : null
          const status: ParseStatusUpdate = {
            jobId,
            status: insight && insight.overlays.length > 0 ? 'ready' : 'processing',
            overlays: insight?.overlays ?? [],
            hints: insight?.advisoryHints ?? [],
            zoneCode: insight?.zoneCode ?? zoneCode,
            updatedAt: new Date().toISOString(),
          }
          onUpdate(status)
          if (status.status === 'ready') {
            break
          }
        } catch (error) {
          onUpdate({
            jobId,
            status: 'error',
            overlays: [],
            hints: [],
            zoneCode,
            updatedAt: new Date().toISOString(),
            message: error instanceof Error ? error.message : 'Unknown error',
          })
          break
        }

        if (timeoutMs && Date.now() - startedAt >= timeoutMs) {
          onUpdate({
            jobId,
            status: 'error',
            overlays: [],
            hints: [],
            zoneCode,
            updatedAt: new Date().toISOString(),
            message: 'Polling timed out',
          })
          break
        }

        await delay(intervalMs)
      }
    }

    loop().catch((error: unknown) => {
      const message = error instanceof Error ? error.message : 'Unknown error'
      onUpdate({
        jobId,
        status: 'error',
        overlays: [],
        hints: [],
        zoneCode,
        updatedAt: new Date().toISOString(),
        message,
      })
    })

    return () => {
      cancelled = true
    }
  }

  subscribeToOverlayUpdates(options: {
    zoneCode: string
    onUpdate: (insights: OverlayInsights) => void
    intervalMs?: number
  }) {
    const { zoneCode, onUpdate, intervalMs = 5000 } = options
    let cancelled = false

    const loop = async () => {
      while (!cancelled) {
        try {
          const insight = await this.getOverlayInsights({ zoneCode })
          onUpdate(insight)
        } catch (error) {
          onUpdate({
            zoneCode,
            overlays: [],
            advisoryHints: [
              error instanceof Error ? error.message : 'Unable to refresh overlays at the moment.',
            ],
          })
          break
        }
        await delay(intervalMs)
      }
    }

    loop().catch(() => {
      /* no-op: consumers already notified through onUpdate */
    })

    return () => {
      cancelled = true
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
      const related = topicRules.filter((rule) =>
        rule.overlays.some((overlay) => overlays.has(overlay)) ||
        rule.advisoryHints.some((hint) => hints.has(hint)),
      )
      const automationScore = related.length > 0 ? Math.min(0.95, 0.5 + related.length / (topicRules.length * 1.5)) : 0.45
      const savings = Math.round(automationScore * 100 * 0.3)
      const reviewHours = Math.max(2, Math.round(topicRules.length * automationScore))

      suggestions.push({
        id: `pipeline-${topic.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`,
        title: `${topic} fast-track`,
        description:
          related.length > 0
            ? `Prioritise ${related.length} overlays-triggered checks within the ${topic} rules.`
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
          description: 'Baseline review workflow across zoning, fire safety and environmental health topics.',
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
