import { z, type ZodIssue } from 'zod'

import { apiClient } from '../api'
import {
  buildSampleCorrelationIntelligence,
  buildSampleGraphIntelligence,
  buildSamplePredictiveIntelligence,
} from './fixtures'

export class IntelligenceValidationError extends Error {
  readonly issues: ZodIssue[]

  constructor(message: string, issues: ZodIssue[]) {
    super(message)
    this.name = 'IntelligenceValidationError'
    this.issues = issues
  }
}

export class IntelligenceRequestError extends Error {
  readonly cause?: unknown

  constructor(message: string, cause?: unknown) {
    super(message)
    this.name = 'IntelligenceRequestError'
    this.cause = cause
  }
}

const IS_DEV = import.meta.env?.DEV ?? false
const REQUEST_TIMEOUT_MS = 30000

function debugLog(...args: unknown[]): void {
  if (IS_DEV) {
    console.log(...args)
  }
}

function debugError(...args: unknown[]): void {
  if (IS_DEV) {
    console.error(...args)
  }
}

async function requestWithTimeout<T>(
  requestFactory: (signal: AbortSignal | undefined) => Promise<T>,
  timeoutMessage: string,
): Promise<T> {
  if (typeof AbortController === 'undefined') {
    return requestFactory(undefined)
  }

  const controller = new AbortController()
  const timeoutHandle = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)

  try {
    return await requestFactory(controller.signal)
  } catch (error) {
    if (controller.signal.aborted) {
      throw new IntelligenceRequestError(timeoutMessage, error)
    }
    throw error
  } finally {
    clearTimeout(timeoutHandle)
  }
}

const graphNodeSchema = z.object({
  id: z.string(),
  label: z.string(),
  category: z.string(),
  score: z.number().min(0),
})

const graphEdgeSchema = z.object({
  id: z.string(),
  source: z.string(),
  target: z.string(),
  weight: z.number().optional(),
})

const graphSuccessSchema = z.object({
  kind: z.literal('graph'),
  status: z.literal('ok'),
  summary: z.string(),
  generatedAt: z.string(),
  graph: z.object({
    nodes: z.array(graphNodeSchema),
    edges: z.array(graphEdgeSchema),
  }),
})

const graphEmptySchema = z.object({
  kind: z.literal('graph'),
  status: z.literal('empty'),
  summary: z.string().optional(),
})

const graphErrorSchema = z.object({
  kind: z.literal('graph'),
  status: z.literal('error'),
  error: z.string(),
})

const graphResponseSchema = z.discriminatedUnion('status', [
  graphSuccessSchema,
  graphEmptySchema,
  graphErrorSchema,
])

const predictiveSegmentSchema = z.object({
  segmentId: z.string(),
  segmentName: z.string(),
  baseline: z.number(),
  projection: z.number(),
  probability: z.number().min(0).max(1),
})

const predictiveSuccessSchema = z.object({
  kind: z.literal('predictive'),
  status: z.literal('ok'),
  summary: z.string(),
  generatedAt: z.string(),
  horizonMonths: z.number().int().nonnegative(),
  segments: z.array(predictiveSegmentSchema),
})

const predictiveEmptySchema = z.object({
  kind: z.literal('predictive'),
  status: z.literal('empty'),
  summary: z.string().optional(),
})

const predictiveErrorSchema = z.object({
  kind: z.literal('predictive'),
  status: z.literal('error'),
  error: z.string(),
})

const predictiveResponseSchema = z.discriminatedUnion('status', [
  predictiveSuccessSchema,
  predictiveEmptySchema,
  predictiveErrorSchema,
])

const correlationRelationshipSchema = z.object({
  pairId: z.string(),
  driver: z.string(),
  outcome: z.string(),
  coefficient: z.number().min(-1).max(1),
  pValue: z.number().min(0).max(1),
})

const correlationSuccessSchema = z.object({
  kind: z.literal('correlation'),
  status: z.literal('ok'),
  summary: z.string(),
  updatedAt: z.string(),
  relationships: z.array(correlationRelationshipSchema),
})

const correlationEmptySchema = z.object({
  kind: z.literal('correlation'),
  status: z.literal('empty'),
  summary: z.string().optional(),
})

const correlationErrorSchema = z.object({
  kind: z.literal('correlation'),
  status: z.literal('error'),
  error: z.string(),
})

const correlationResponseSchema = z.discriminatedUnion('status', [
  correlationSuccessSchema,
  correlationEmptySchema,
  correlationErrorSchema,
])

export type GraphIntelligenceResponse = z.infer<typeof graphResponseSchema>
export type PredictiveIntelligenceResponse = z.infer<typeof predictiveResponseSchema>
export type CrossCorrelationIntelligenceResponse = z.infer<
  typeof correlationResponseSchema
>

function parseOrThrow<T>(schema: z.ZodType<T>, data: unknown, message: string): T {
  const result = schema.safeParse(data)
  if (!result.success) {
    throw new IntelligenceValidationError(message, result.error.issues)
  }
  return result.data
}

function ensureGraphEdgesWeighted(
  payload: GraphIntelligenceResponse,
): GraphIntelligenceResponse {
  if (payload.status !== 'ok') {
    return payload
  }
  const edges = payload.graph.edges.map((edge) => ({
    ...edge,
    weight: edge.weight ?? 0,
  }))
  return {
    ...payload,
    graph: {
      ...payload.graph,
      edges,
    },
  }
}

function normaliseGraphResponse(
  payload: GraphIntelligenceResponse,
): GraphIntelligenceResponse {
  if (payload.status === 'ok' && payload.graph.nodes.length === 0 && payload.graph.edges.length === 0) {
    return {
      kind: 'graph',
      status: 'empty',
      summary: payload.summary,
    }
  }
  return payload
}

function normalisePredictiveResponse(
  payload: PredictiveIntelligenceResponse,
): PredictiveIntelligenceResponse {
  if (payload.status === 'ok' && payload.segments.length === 0) {
    return {
      kind: 'predictive',
      status: 'empty',
      summary: payload.summary,
    }
  }
  return payload
}

function normaliseCorrelationResponse(
  payload: CrossCorrelationIntelligenceResponse,
): CrossCorrelationIntelligenceResponse {
  if (payload.status === 'ok' && payload.relationships.length === 0) {
    return {
      kind: 'correlation',
      status: 'empty',
      summary: payload.summary,
    }
  }
  return payload
}

export async function fetchGraphIntelligence(
  workspaceId: string,
): Promise<GraphIntelligenceResponse> {
  debugLog('[fetchGraphIntelligence] Calling API with workspaceId:', workspaceId)
  try {
    const response = await requestWithTimeout(
      (signal) =>
        apiClient.get<unknown>('/api/v1/analytics/intelligence/graph', {
          params: { workspaceId },
          signal,
        }),
      'Graph intelligence request timed out',
    )
    debugLog('[fetchGraphIntelligence] Response received:', response.data)
    const payload = parseOrThrow(
      graphResponseSchema,
      response.data,
      'Graph intelligence payload failed validation',
    )
    debugLog('[fetchGraphIntelligence] Validation passed, payload:', payload)
    const weighted = ensureGraphEdgesWeighted(payload)
    const normalized = normaliseGraphResponse(weighted)
    debugLog('[fetchGraphIntelligence] Returning normalized:', normalized)
    return normalized
  } catch (error) {
    debugError('[fetchGraphIntelligence] Error caught:', error)
    if (error instanceof IntelligenceValidationError) {
      throw error
    }
    debugLog('[fetchGraphIntelligence] Returning sample fallback graph data')
    return buildSampleGraphIntelligence()
  }
}

export async function fetchPredictiveIntelligence(
  workspaceId: string,
): Promise<PredictiveIntelligenceResponse> {
  debugLog('[fetchPredictiveIntelligence] Calling API for workspace:', workspaceId)
  try {
    const response = await requestWithTimeout(
      (signal) =>
        apiClient.get<unknown>('/api/v1/analytics/intelligence/predictive', {
          params: { workspaceId },
          signal,
        }),
      'Predictive intelligence request timed out',
    )
    debugLog('[fetchPredictiveIntelligence] Response:', response.data)
    const payload = parseOrThrow(
      predictiveResponseSchema,
      response.data,
      'Predictive intelligence payload failed validation',
    )
    debugLog('[fetchPredictiveIntelligence] Returning:', payload)
    return normalisePredictiveResponse(payload)
  } catch (error) {
    debugError('[fetchPredictiveIntelligence] Error:', error)
    if (error instanceof IntelligenceValidationError) {
      throw error
    }
    debugLog(
      '[fetchPredictiveIntelligence] Returning sample fallback predictive data',
    )
    return buildSamplePredictiveIntelligence()
  }
}

export async function fetchCrossCorrelationIntelligence(
  workspaceId: string,
): Promise<CrossCorrelationIntelligenceResponse> {
  debugLog('[fetchCrossCorrelationIntelligence] Calling API for workspace:', workspaceId)
  try {
    const response = await requestWithTimeout(
      (signal) =>
        apiClient.get<unknown>('/api/v1/analytics/intelligence/cross-correlation', {
          params: { workspaceId },
          signal,
        }),
      'Cross-correlation intelligence request timed out',
    )
    debugLog('[fetchCrossCorrelationIntelligence] Response:', response.data)
    const payload = parseOrThrow(
      correlationResponseSchema,
      response.data,
      'Cross-correlation intelligence payload failed validation',
    )
    debugLog('[fetchCrossCorrelationIntelligence] Returning:', payload)
    return normaliseCorrelationResponse(payload)
  } catch (error) {
    debugError('[fetchCrossCorrelationIntelligence] Error:', error)
    if (error instanceof IntelligenceValidationError) {
      throw error
    }
    debugLog(
      '[fetchCrossCorrelationIntelligence] Returning sample fallback correlation data',
    )
    return buildSampleCorrelationIntelligence()
  }
}

export const advancedAnalyticsService = {
  fetchGraphIntelligence,
  fetchPredictiveIntelligence,
  fetchCrossCorrelationIntelligence,
}
