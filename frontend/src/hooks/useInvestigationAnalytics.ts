import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import {
  advancedAnalyticsService,
  fetchCrossCorrelationIntelligence,
  fetchGraphIntelligence,
  fetchPredictiveIntelligence,
  type CrossCorrelationIntelligenceResponse,
  type GraphIntelligenceResponse,
  type PredictiveIntelligenceResponse,
} from '../services/analytics/advancedAnalytics'

const IS_DEV = import.meta.env?.DEV ?? false
const CACHE_TTL_MS = 60000

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

export interface InvestigationAnalyticsServices {
  fetchGraphIntelligence: typeof fetchGraphIntelligence
  fetchPredictiveIntelligence: typeof fetchPredictiveIntelligence
  fetchCrossCorrelationIntelligence: typeof fetchCrossCorrelationIntelligence
}

const defaultServices: InvestigationAnalyticsServices = advancedAnalyticsService

export type GraphIntelligenceState =
  | GraphIntelligenceResponse
  | { kind: 'graph'; status: 'loading' }

export type PredictiveIntelligenceState =
  | PredictiveIntelligenceResponse
  | { kind: 'predictive'; status: 'loading' }

export type CrossCorrelationIntelligenceState =
  | CrossCorrelationIntelligenceResponse
  | { kind: 'correlation'; status: 'loading' }

export interface UseInvestigationAnalyticsResult {
  graph: GraphIntelligenceState
  predictive: PredictiveIntelligenceState
  correlation: CrossCorrelationIntelligenceState
  isLoading: boolean
  refetch: () => Promise<void>
}

const loadingGraphState: GraphIntelligenceState = {
  kind: 'graph',
  status: 'loading',
}
const loadingPredictiveState: PredictiveIntelligenceState = {
  kind: 'predictive',
  status: 'loading',
}
const loadingCorrelationState: CrossCorrelationIntelligenceState = {
  kind: 'correlation',
  status: 'loading',
}

function toGraphErrorState(reason: unknown): GraphIntelligenceResponse {
  return {
    kind: 'graph',
    status: 'error',
    error:
      reason instanceof Error
        ? reason.message
        : 'Unknown graph intelligence error',
  }
}

function toPredictiveErrorState(
  reason: unknown,
): PredictiveIntelligenceResponse {
  return {
    kind: 'predictive',
    status: 'error',
    error:
      reason instanceof Error
        ? reason.message
        : 'Unknown predictive intelligence error',
  }
}

function toCorrelationErrorState(
  reason: unknown,
): CrossCorrelationIntelligenceResponse {
  return {
    kind: 'correlation',
    status: 'error',
    error:
      reason instanceof Error
        ? reason.message
        : 'Unknown correlation intelligence error',
  }
}

interface CachedAnalyticsEntry {
  graph: GraphIntelligenceState
  predictive: PredictiveIntelligenceState
  correlation: CrossCorrelationIntelligenceState
  timestamp: number
}

export function useInvestigationAnalytics(
  workspaceId: string,
  overrides?: Partial<InvestigationAnalyticsServices>,
): UseInvestigationAnalyticsResult {
  const services = useMemo<InvestigationAnalyticsServices>(() => {
    if (!overrides) {
      return defaultServices
    }
    return {
      ...defaultServices,
      ...overrides,
    }
  }, [overrides])

  // Remove isMountedRef - it doesn't work with React StrictMode

  const [graph, setGraph] = useState<GraphIntelligenceState>(loadingGraphState)
  const [predictive, setPredictive] = useState<PredictiveIntelligenceState>(
    loadingPredictiveState,
  )
  const [correlation, setCorrelation] =
    useState<CrossCorrelationIntelligenceState>(loadingCorrelationState)
  const [isLoading, setIsLoading] = useState(true)
  const cacheRef = useRef<Map<string, CachedAnalyticsEntry>>(new Map())

  const loadAnalytics = useCallback(
    async (forceRefresh = false) => {
      debugLog(
        '[useInvestigationAnalytics] Starting to load analytics for workspace:',
        workspaceId,
        { forceRefresh },
      )
      const cacheKey = workspaceId
      const cachedEntry = cacheRef.current.get(cacheKey)
      const cacheIsFresh =
        !forceRefresh &&
        cachedEntry !== undefined &&
        Date.now() - cachedEntry.timestamp < CACHE_TTL_MS

      if (cacheIsFresh) {
        debugLog(
          '[useInvestigationAnalytics] Serving analytics from cache for workspace:',
          workspaceId,
        )
        setGraph(cachedEntry.graph)
        setPredictive(cachedEntry.predictive)
        setCorrelation(cachedEntry.correlation)
        setIsLoading(false)
        return
      }

      setIsLoading(true)
      setGraph(loadingGraphState)
      setPredictive(loadingPredictiveState)
      setCorrelation(loadingCorrelationState)

      try {
        const [graphResult, predictiveResult, correlationResult] =
          await Promise.allSettled([
            services.fetchGraphIntelligence(workspaceId),
            services.fetchPredictiveIntelligence(workspaceId),
            services.fetchCrossCorrelationIntelligence(workspaceId),
          ])
        debugLog('[useInvestigationAnalytics] All promises settled:', {
          graphResult,
          predictiveResult,
          correlationResult,
        })

        let nextGraph: GraphIntelligenceState
        let nextPredictive: PredictiveIntelligenceState
        let nextCorrelation: CrossCorrelationIntelligenceState

        if (graphResult.status === 'fulfilled') {
          debugLog(
            '[useInvestigationAnalytics] Setting graph data:',
            graphResult.value,
          )
          nextGraph = graphResult.value
        } else {
          debugError(
            '[useInvestigationAnalytics] Graph request failed:',
            graphResult.reason,
          )
          nextGraph = toGraphErrorState(graphResult.reason)
        }

        if (predictiveResult.status === 'fulfilled') {
          debugLog(
            '[useInvestigationAnalytics] Setting predictive data:',
            predictiveResult.value,
          )
          nextPredictive = predictiveResult.value
        } else {
          debugError(
            '[useInvestigationAnalytics] Predictive request failed:',
            predictiveResult.reason,
          )
          nextPredictive = toPredictiveErrorState(predictiveResult.reason)
        }

        if (correlationResult.status === 'fulfilled') {
          debugLog(
            '[useInvestigationAnalytics] Setting correlation data:',
            correlationResult.value,
          )
          nextCorrelation = correlationResult.value
        } else {
          debugError(
            '[useInvestigationAnalytics] Correlation request failed:',
            correlationResult.reason,
          )
          nextCorrelation = toCorrelationErrorState(correlationResult.reason)
        }

        setGraph(nextGraph)
        setPredictive(nextPredictive)
        setCorrelation(nextCorrelation)
        cacheRef.current.set(cacheKey, {
          graph: nextGraph,
          predictive: nextPredictive,
          correlation: nextCorrelation,
          timestamp: Date.now(),
        })
      } catch (error) {
        debugError(
          '[useInvestigationAnalytics] Unexpected error during analytics load:',
          error,
        )
        const errorGraph = toGraphErrorState(error)
        const errorPredictive = toPredictiveErrorState(error)
        const errorCorrelation = toCorrelationErrorState(error)
        setGraph(errorGraph)
        setPredictive(errorPredictive)
        setCorrelation(errorCorrelation)
        cacheRef.current.set(cacheKey, {
          graph: errorGraph,
          predictive: errorPredictive,
          correlation: errorCorrelation,
          timestamp: Date.now(),
        })
      } finally {
        debugLog('[useInvestigationAnalytics] Setting isLoading to false')
        setIsLoading(false)
      }
    },
    [services, workspaceId],
  )

  useEffect(() => {
    loadAnalytics().catch(() => {
      // Errors are captured via the settled promise handling above.
    })
  }, [loadAnalytics])

  const refetch = useCallback(async () => {
    await loadAnalytics(true)
  }, [loadAnalytics])

  return {
    graph,
    predictive,
    correlation,
    isLoading,
    refetch,
  }
}
