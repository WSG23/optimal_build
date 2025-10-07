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
import {
  buildSampleCorrelationIntelligence,
  buildSampleGraphIntelligence,
  buildSamplePredictiveIntelligence,
} from '../services/analytics/fixtures'

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

const loadingGraphState: GraphIntelligenceState = { kind: 'graph', status: 'loading' }
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
    error: reason instanceof Error ? reason.message : 'Unknown graph intelligence error',
  }
}

function toPredictiveErrorState(reason: unknown): PredictiveIntelligenceResponse {
  return {
    kind: 'predictive',
    status: 'error',
    error:
      reason instanceof Error ? reason.message : 'Unknown predictive intelligence error',
  }
}

function toCorrelationErrorState(reason: unknown): CrossCorrelationIntelligenceResponse {
  return {
    kind: 'correlation',
    status: 'error',
    error:
      reason instanceof Error ? reason.message : 'Unknown correlation intelligence error',
  }
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

  const loadAnalytics = useCallback(async () => {
    console.log('[useInvestigationAnalytics] Starting to load analytics for workspace:', workspaceId)
    setIsLoading(true)
    setGraph(loadingGraphState)
    setPredictive(loadingPredictiveState)
    setCorrelation(loadingCorrelationState)

    try {
      const [graphResult, predictiveResult, correlationResult] = await Promise.allSettled([
        services.fetchGraphIntelligence(workspaceId),
        services.fetchPredictiveIntelligence(workspaceId),
        services.fetchCrossCorrelationIntelligence(workspaceId),
      ])
      console.log('[useInvestigationAnalytics] All promises settled:', { graphResult, predictiveResult, correlationResult })

      const allRejected =
        graphResult.status === 'rejected' &&
        predictiveResult.status === 'rejected' &&
        correlationResult.status === 'rejected'

      if (allRejected) {
        setGraph(buildSampleGraphIntelligence())
        setPredictive(buildSamplePredictiveIntelligence())
        setCorrelation(buildSampleCorrelationIntelligence())
        return
      }

      if (graphResult.status === 'fulfilled') {
        console.log('[useInvestigationAnalytics] Setting graph data:', graphResult.value)
        setGraph(graphResult.value)
      } else {
        console.log('[useInvestigationAnalytics] Graph failed:', graphResult.reason)
        setGraph(toGraphErrorState(graphResult.reason))
      }

      if (predictiveResult.status === 'fulfilled') {
        console.log('[useInvestigationAnalytics] Setting predictive data:', predictiveResult.value)
        setPredictive(predictiveResult.value)
      } else {
        console.log('[useInvestigationAnalytics] Predictive failed:', predictiveResult.reason)
        setPredictive(toPredictiveErrorState(predictiveResult.reason))
      }

      if (correlationResult.status === 'fulfilled') {
        console.log('[useInvestigationAnalytics] Setting correlation data:', correlationResult.value)
        setCorrelation(correlationResult.value)
      } else {
        console.log('[useInvestigationAnalytics] Correlation failed:', correlationResult.reason)
        setCorrelation(toCorrelationErrorState(correlationResult.reason))
      }
    } catch (error) {
      setGraph(buildSampleGraphIntelligence())
      setPredictive(buildSamplePredictiveIntelligence())
      setCorrelation(buildSampleCorrelationIntelligence())
    } finally {
      console.log('[useInvestigationAnalytics] Setting isLoading to false')
      setIsLoading(false)
    }
  }, [services, workspaceId])

  useEffect(() => {
    loadAnalytics().catch(() => {
      // Errors are captured via the settled promise handling above.
    })
  }, [loadAnalytics])

  const refetch = useCallback(async () => {
    await loadAnalytics()
  }, [loadAnalytics])

  return {
    graph,
    predictive,
    correlation,
    isLoading,
    refetch,
  }
}
