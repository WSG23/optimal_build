import { z, type ZodIssue } from 'zod'

import { apiClient } from '../api'

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
  weight: z.number().optional().default(0),
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
  console.log('[fetchGraphIntelligence] Calling API with workspaceId:', workspaceId)
  try {
    const response = await apiClient.get<unknown>('/api/v1/analytics/intelligence/graph', {
      params: { workspaceId },
    })
    console.log('[fetchGraphIntelligence] Response received:', response.data)
    const payload = parseOrThrow(
      graphResponseSchema,
      response.data,
      'Graph intelligence payload failed validation',
    )
    console.log('[fetchGraphIntelligence] Validation passed, payload:', payload)
    const normalized = normaliseGraphResponse(payload)
    console.log('[fetchGraphIntelligence] Returning normalized:', normalized)
    return normalized
  } catch (error) {
    console.error('[fetchGraphIntelligence] Error caught:', error)
    if (error instanceof IntelligenceValidationError) {
      throw error
    }
    throw new IntelligenceRequestError('Unable to load graph intelligence', error)
  }
}

export async function fetchPredictiveIntelligence(
  workspaceId: string,
): Promise<PredictiveIntelligenceResponse> {
  console.log('[fetchPredictiveIntelligence] Calling API')
  try {
    const response = await apiClient.get<unknown>(
      '/api/v1/analytics/intelligence/predictive',
      { params: { workspaceId } },
    )
    console.log('[fetchPredictiveIntelligence] Response:', response.data)
    const payload = parseOrThrow(
      predictiveResponseSchema,
      response.data,
      'Predictive intelligence payload failed validation',
    )
    console.log('[fetchPredictiveIntelligence] Returning:', payload)
    return normalisePredictiveResponse(payload)
  } catch (error) {
    console.error('[fetchPredictiveIntelligence] Error:', error)
    if (error instanceof IntelligenceValidationError) {
      throw error
    }
    throw new IntelligenceRequestError('Unable to load predictive intelligence', error)
  }
}

export async function fetchCrossCorrelationIntelligence(
  workspaceId: string,
): Promise<CrossCorrelationIntelligenceResponse> {
  console.log('[fetchCrossCorrelationIntelligence] Calling API')
  try {
    const response = await apiClient.get<unknown>(
      '/api/v1/analytics/intelligence/cross-correlation',
      { params: { workspaceId } },
    )
    console.log('[fetchCrossCorrelationIntelligence] Response:', response.data)
    const payload = parseOrThrow(
      correlationResponseSchema,
      response.data,
      'Cross-correlation intelligence payload failed validation',
    )
    console.log('[fetchCrossCorrelationIntelligence] Returning:', payload)
    return normaliseCorrelationResponse(payload)
  } catch (error) {
    console.error('[fetchCrossCorrelationIntelligence] Error:', error)
    if (error instanceof IntelligenceValidationError) {
      throw error
    }
    throw new IntelligenceRequestError('Unable to load correlation intelligence', error)
  }
}

export const advancedAnalyticsService = {
  fetchGraphIntelligence,
  fetchPredictiveIntelligence,
  fetchCrossCorrelationIntelligence,
}
